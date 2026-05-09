#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@brief ROS 任务调度器（核心模块）

该模块是整个智能工厂仿真系统的核心，负责管理 10 台机器人的
任务分配、路径规划、冲突检测与死锁解决。

主要功能：
    - 基于优先级的任务队列管理与机器人分配
    - A* 全局路径规划 + 路径平滑
    - 三层碰撞防护（激光避障 → 全局防撞 → 紧急后退）
    - 时空预约与优先级冲突仲裁
    - 全局死锁扫描与强制解锁
    - 人工调度接管（暂停/恢复/手动派遣）
    - 机器人翻倒检测与 Gazebo 复位
    - 实时任务统计发布（供 Dashboard 展示）
"""

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
import json
import time
import math
import threading
from collections import defaultdict, deque
from enum import Enum
import sys
import os

# 导入 A* 路径规划器
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from astar_planner import AStarPlanner


# ============================================================
#  枚举定义
# ============================================================

class TaskType(Enum):
    """
    @brief 任务类型枚举

    定义四种物料运输任务类型，对应工厂内不同的物料流转路线。
    """
    EMPTY_TO_CARDING = "empty_to_carding"       # 空筒 → 梳理区
    GREEN_TO_DRAWING1 = "green_to_drawing1"      # 绿色物料 → 并条一区
    YELLOW_TO_DRAWING2 = "yellow_to_drawing2"    # 黄色物料 → 并条二区
    RED_TO_COMPLETED = "red_to_completed"        # 红色物料 → 成品区


class RobotStatus(Enum):
    """
    @brief 机器人状态枚举
    """
    IDLE = "idle"               # 空闲，等待任务分配
    MOVING = "moving"           # 正在沿路径移动
    LOADING = "loading"         # 在源点装载物料
    UNLOADING = "unloading"     # 在目标点卸载物料
    YIELDING = "yielding"       # 空闲机器人自动让路中
    MANUAL = "manual"           # 人工接管控制中
    PAUSED = "paused"           # 暂停状态（可恢复）


# ============================================================
#  Task 数据类
# ============================================================

class Task:
    """
    @brief 运输任务数据类

    记录单个运输任务的完整生命周期信息。
    """

    def __init__(self, task_id, task_type, source_pos, dest_pos, priority=50):
        """
        @brief 创建运输任务

        @param task_id:    任务唯一编号
        @param task_type:  任务类型（TaskType 枚举）
        @param source_pos: 源点坐标 (x, y)
        @param dest_pos:   目标点坐标 (x, y)
        @param priority:   优先级（数值越大越优先，默认 50）
        """
        self.id = task_id
        self.type = task_type
        self.source = source_pos            # 取货点
        self.destination = dest_pos         # 送货点
        self.priority = priority
        self.assigned_robot = None          # 分配的机器人 ID
        self.status = "pending"             # pending/assigned/loading/delivering/unloading/completed
        self.created_time = time.time()
        self.start_time = None              # 开始执行时间
        self.completion_time = None         # 完成时间
        self.assign_fail_count = 0          # 分配阶段路径规划失败次数
        self.last_assign_attempt_time = 0.0 # 上次分配尝试时间
        self.next_assign_attempt_time = 0.0 # 下次允许分配尝试时间
        self.last_assign_attempt_robot = None # 上次尝试分配的机器人 ID


# ============================================================
#  CleanTaskScheduler - 任务调度器主类
# ============================================================

class CleanTaskScheduler:
    """
    @brief 任务调度器主类

    负责任务分配、路径规划、多机协调、碰撞回避与死锁处理。
    通过 ROS 话题与 Gazebo 仿真环境和 Web 前端交互。
    """

    def __init__(self, num_robots=10):
        """
        @brief 初始化调度器

        初始化 ROS 节点、发布/订阅关系、避障参数、A* 规划器，
        并根据环境变量 EXPERIMENT_MODE 自动启动实验。

        @param num_robots: 机器人总数，默认 10
        """
        rospy.init_node('clean_task_scheduler', anonymous=True)

        # ---------- 基础配置 ----------
        self.num_robots = num_robots
        self.robot_positions = {}           # 机器人位置 {id: (x, y)}
        self.robot_orientations = {}        # 机器人朝向角 {id: float}
        self.robot_status = {}              # 机器人状态 {id: RobotStatus}
        self.robot_current_task = {}        # 机器人当前任务 {id: Task/None}
        self.robot_paths = {}               # 机器人路径点列表 {id: [(x,y)...]}

        # 初始位置配置（用于 Gazebo 复位传送）
        self.robot_spawn_positions = {
            0: (3.5, 1.5, 0.15), 1: (3.5, 3.0, 0.15), 2: (1.0, 3.5, 0.15),
            3: (3.5, 7.0, 0.15), 4: (3.5, 8.5, 0.15), 5: (1.0, 6.5, 0.15),
            6: (13.0, 1.5, 0.15), 7: (13.0, 3.0, 0.15), 8: (13.0, 7.0, 0.15),
            9: (13.0, 8.5, 0.15),
        }

        # ---------- 避障参数 ----------
        self.robot_velocities = {}
        self.collision_check_distance = 1.5     # 减速检测距离（米）
        self.hard_safety_distance = 0.25        # 强制停止距离（米）
        self.critical_safety_distance = 0.15    # 紧急后退距离（米）
        self.collision_escape_block_distance = float(os.environ.get('COLLISION_ESCAPE_BLOCK_DISTANCE', '0.45') or 0.45)

        # ---------- 死锁检测参数 ----------
        self.robot_pair_stuck_history = {}      # 机器人对卡住历史
        self.stuck_detection_window = 2.5       # 卡住检测时间窗口（秒）
        self.stuck_distance_threshold = 0.33    # 距离阈值（米）
        self.deadlock_release_distance = 0.80   # 判定死锁对已分离的距离阈值（米）
        self.stuck_trigger_count = 12           # 触发死锁判定的最小检测次数
        self.deadlock_being_resolved = {}       # 正在处理的死锁 {(r1,r2): cooldown_time}
        self.deadlock_resolve_cooldown = 12.0   # 死锁解锁后冷却时间（秒）
        self.deadlock_retry_window = 40.0       # 同一机器人对重复死锁计数窗口（秒）
        self.deadlock_pair_retry_count = defaultdict(int)   # 同一机器人对死锁重试次数
        self.deadlock_pair_last_time = {}       # 同一机器人对上次触发时间
        self.pair_separation_active = {}        # 正在执行双机分离的 pair {(r1,r2): until}
        self.pair_separation_hold_sec = 8.0     # 双机分离保护时长（秒）
        self.yield_pair_cooldown = {}           # 普通冲突让路对冷却 {(r1,r2): until}
        self.yield_pair_cooldown_sec = 2.5      # 普通让路动作去抖冷却（秒）
        self.yield_repeat_window = 12.0         # 同一机器人重复让路统计窗口（秒）
        self.max_consecutive_yield_same_peer = 3  # 连续对同peer让路阈值
        self.robot_last_yield_peer = {}         # 上次让路对象 {rid: peer}
        self.robot_last_yield_time = defaultdict(float)     # 上次让路时间
        self.robot_consecutive_yield_count = defaultdict(int)  # 连续让路计数
        self.corridor_tokens = {}               # 走廊通行令牌 {cid: {holder, direction, until}}
        self.corridor_token_ttl = 6.0           # 走廊令牌有效时长（秒）
        self.corridor_token_grant_count_total = 0   # 走廊令牌授予次数
        self.corridor_token_reuse_count_total = 0   # 走廊令牌复用命中次数
        self.corridor_token_release_count_total = 0 # 走廊令牌释放次数
        self.corridor_log_throttle_sec = 2.0        # 令牌日志限频（秒）
        self.corridor_last_log_time = defaultdict(float)  # 令牌日志节流时间戳

        # ---------- 传感器与规划数据 ----------
        self.robot_laser_data = {}              # 激光雷达数据 {id: [ranges]}
        self.laser_obstacle_threshold = 0.5     # 激光避障触发距离（米）
        self.spacetime_reservations = {}        # 时空预约表 {id: [(gx, gy, t)]}
        self.reservation_horizon = 8.0          # 预约时间窗口（秒）
        self.reservation_grid_size = 0.6        # 预约栅格大小（米）
        self.reservation_time_tolerance = 0.8   # 时隙冲突容忍窗口（秒）

        # ---------- 优先级与状态管理 ----------
        self.robot_priorities = {}              # 机器人实时优先级 {id: int}
        self.robot_yielding = {}                # 正在让路的机器人 {id: (target_id, until_time)}
        self.robot_yield_count = defaultdict(int)   # 让路次数统计
        self.robot_wait_since = {}              # 移动中等待起始时间 {id: t/None}
        self.wait_speed_threshold = 0.03        # 判定等待的速度阈值（m/s）
        self.wait_boost_interval = 2.0          # 等待增益步长（秒）
        self.wait_boost_step = 6                # 每步等待增益分值
        self.max_wait_priority_boost = 36       # 等待增益上限
        self.priority_inheritance_bonus = 15    # 对方已让路时的继承加分
        self.protected_priority_bonus = 8       # 保护状态额外优先级
        self.robot_flip_detected = {}           # 翻倒检测标志 {id: bool}
        self.robot_flip_count = defaultdict(int)    # 翻倒次数统计
        self.robot_flip_state = {}              # 翻倒状态机 {id: normal/suspected/flipped/recovering}
        self.robot_flip_candidate_since = {}    # 疑似翻倒起始时间 {id: t}
        self.robot_flip_stable_since = {}       # 翻倒后稳定计时起点 {id: t}
        self.robot_flip_last_recover_time = defaultdict(float)  # 上次恢复触发时间
        self.robot_flip_last_confirm_time = defaultdict(float)   # 上次确认翻倒时间（去抖）
        self.robot_flip_recovering = set()      # 正在自动恢复中的机器人
        self.robot_upright_z_baseline = {}      # 机器人竖直高度基线 {id: z}
        self.robot_z_baseline_samples = defaultdict(int)  # 基线样本数
        self.flip_tilt_confirm_rad = 0.95       # 倾角确认阈值（约54°）
        self.flip_tilt_severe_rad = 1.20        # 严重翻倒阈值（约69°）
        self.flip_tilt_clear_rad = 0.35         # 清除翻倒的稳定倾角阈值（约20°）
        self.flip_z_drop_threshold = 0.09       # 相对基线高度下降阈值（米）
        self.flip_z_baseline_alpha = 0.03       # 高度基线 EMA 更新系数
        self.flip_z_min_samples = 20            # 启用高度辅助判据前最小样本数
        self.flip_confirm_duration = 1.0        # 疑似持续多久才判定翻倒（秒）
        self.flip_clear_duration = 1.5          # 信号消失后稳定多久清除翻倒（秒）
        self.flip_repeat_suppress_duration = 12.0  # 连续确认翻倒抑制窗口（秒）
        self.flip_recover_cooldown = 8.0        # 自动恢复冷却（秒）
        self.robot_protected = set()            # 受保护的机器人集合（刚恢复/需避让）
        self.robot_paused_state = {}            # 暂停状态信息 {id: {path, task, target}}
        self.arrival_crowded_cooldown = {}      # 到达拥挤处理冷却 {rid: until}
        self.arrival_crowded_retry = defaultdict(int)       # 到达拥挤连续重试次数

        # ---------- 运行期指标统计 ----------
        self.deadlock_count_total = 0           # 死锁触发次数
        self.yield_count_total = 0              # 让路动作次数
        self.recovery_count_total = 0           # 成功恢复次数
        self.collision_event_count = 0          # 碰撞风险事件次数（按进入事件计）
        self.robot_collision_active = {}        # 机器人当前是否处于碰撞风险中
        self.starvation_prevent_count_total = 0 # 反饥饿策略触发次数
        self.yield_fallback_count_total = 0     # 让路回退hold次数
        self.pair_forced_separation_count_total = 0  # 双机强制分离触发次数
        self.pair_emergency_break_count_total = 0    # 死锁高重试紧急刹停次数
        self.assignment_reject_attempts_total = 0    # 任务分配阶段路径规划失败次数
        self.rejected_task_count_total = 0           # 永久拒绝任务数（当前策略默认0，保留扩展口）
        self.max_assignment_fail_retries = int(os.environ.get('MAX_ASSIGNMENT_FAIL_RETRIES', '80') or 80)
        self.allow_assignment_rejection = (
            (os.environ.get('ALLOW_ASSIGNMENT_REJECTION', '0') or '0').strip().lower()
            in ('1', 'true', 'yes', 'on')
        )
        self.assignment_retry_backoff_base = float(os.environ.get('ASSIGNMENT_RETRY_BACKOFF_BASE', '0.5') or 0.5)
        self.assignment_retry_backoff_max = float(os.environ.get('ASSIGNMENT_RETRY_BACKOFF_MAX', '8.0') or 8.0)
        self.task_completion_time_sum = 0.0          # 已完成任务耗时总和（Total Completion Time）
        self.total_travel_distance = 0.0             # 全体机器人累计行驶距离（米）
        self.robot_last_position = {}                # 上次里程计位置，用于距离累计
        self.computation_time_total = 0.0            # 调度循环累计计算耗时（秒）
        self.computation_time_max = 0.0              # 调度循环最大耗时（秒）
        self.computation_cycle_count = 0             # 调度循环计数
        self.computation_cycle_lt_100ms_count = 0    # 调度循环中 <100ms 的次数
        self.computation_cycle_timestamps = []       # 调度循环结束时间戳与是否<100ms
        self.notification_count_total = 0            # 通知消息数
        self.command_result_count_total = 0          # 命令结果消息数
        self.task_stats_publish_count_total = 0      # 统计消息发布次数
        self.robot_status_publish_count_total = 0    # 机器人状态消息发布次数
        self.deadlock_event_timestamps = []          # 死锁触发时间戳（用于冻结窗口统计）
        self.deadlock_resolution_action_timestamps = []  # 死锁处置动作时间戳
        self.collision_event_timestamps = []         # 碰撞风险事件时间戳
        self.collision_intervention_timestamps = []  # 碰撞风险干预动作时间戳
        self.freeze_window_seconds = float(os.environ.get('FREEZE_WINDOW_SECONDS', '1800') or 1800.0)
        self.persistent_stall_horizon = float(os.environ.get('PERSISTENT_STALL_HORIZON', '8.0') or 8.0)
        self.stall_near_target_tolerance = float(os.environ.get('STALL_NEAR_TARGET_TOLERANCE', '0.75') or 0.75)
        self.stall_replan_cooldown = float(os.environ.get('STALL_REPLAN_COOLDOWN', '3.0') or 3.0)
        self.freeze_detection_grace = float(os.environ.get('FREEZE_DETECTION_GRACE', '10.0') or 10.0)
        self.freeze_effective_robot_threshold = int(os.environ.get('FREEZE_EFFECTIVE_ROBOT_THRESHOLD', '1') or 1)
        self.flow_window_seconds = float(os.environ.get('FLOW_WINDOW_SECONDS', '5.0') or 5.0)
        self.freeze_duration_total = 0.0
        self.freeze_duration_samples = []            # (timestamp, delta_sec)
        self.persistent_stall_duration_total = 0.0
        self.persistent_stall_duration_samples = []  # (timestamp, delta_sec)
        self.robot_progress_timestamps = defaultdict(list)  # {rid: [ts, ...]}
        self.robot_last_stall_replan_time = defaultdict(float)
        self.recovery_trigger_count_total = 0
        self.recovery_trigger_timestamps = []
        self.recovery_success_timestamps = []
        self.last_progress_timestamp = time.time()
        self.last_completed_task_count = 0
        self.flow_window_last_tick = time.time()
        self.flow_window_last_completed = 0
        self.flow_positive_count_total = 0
        self.flow_total_window_count = 0
        self.flow_window_outcomes = []               # (window_end_ts, positive_flag)
        self.penalty_weights = {
            'deadlock': 5.0,
            'yield': 1.0,
            'collision': 20.0,
            'recovery': 2.0,
            'rejected': 8.0,
            'emergency_break': 4.0,
        }
        self.energy_per_meter = 1.0                  # 能耗代理系数（单位能耗/米）

        # ---------- 任务队列管理 ----------
        self.pending_tasks = deque()            # 待分配任务队列
        self.active_tasks = {}                  # 活跃任务 {robot_id: Task}
        self.completed_tasks = []               # 已完成任务列表
        self.task_completion_counts = defaultdict(int)  # 按类型统计完成数
        self.task_type_targets = {
            'empty_to_carding': 0,
            'green_to_drawing1': 0,
            'yellow_to_drawing2': 0,
            'red_to_completed': 0,
        }
        self.system_start_time = time.time()    # 系统启动时间
        self.total_tasks = 0                    # 总任务数

        # ---------- 实验控制状态 ----------
        self.experiment_started = False         # 实验是否已启动
        self.experiment_mode = None             # 实验模式字符串
        self.test_id = (os.environ.get('TEST_ID', '') or '').strip()

        self.algorithm_mode_label = (os.environ.get('ALGORITHM_MODE', 'full') or 'full').strip().lower()
        algorithm_alias_map = {
            'rule_greedy': 'naive',
            'cbs_based': 'path_reservation',
            'auction_based': 'path_only',
            'proposed': 'full',
        }
        self.algorithm_mode = algorithm_alias_map.get(self.algorithm_mode_label, self.algorithm_mode_label)

        if self.algorithm_mode not in ('naive', 'path_only', 'path_reservation', 'full'):
            rospy.logwarn(f"⚠️ Unknown ALGORITHM_MODE={self.algorithm_mode_label}, fallback to full")
            self.algorithm_mode_label = 'full'
            self.algorithm_mode = 'full'

        self.algorithm_family_map = {
            'naive': 'Rule-based (Greedy)',
            'rule_greedy': 'Rule-based (Greedy)',
            'path_only': 'Auction-based',
            'auction_based': 'Auction-based',
            'path_reservation': 'CBS-based',
            'cbs_based': 'CBS-based',
            'full': 'Proposed',
            'proposed': 'Proposed',
        }
        self.algorithm_family = self.algorithm_family_map.get(
            self.algorithm_mode_label,
            self.algorithm_family_map.get(self.algorithm_mode, 'Unknown')
        )

        self.enable_spacetime_reservation = self.algorithm_mode in ('path_reservation', 'full')
        self.enable_deadlock_scan = self.algorithm_mode in ('path_only', 'path_reservation', 'full')
        self.enable_fairness = self.algorithm_mode == 'full'
        self.enable_corridor_token = self.algorithm_mode == 'full'
        self.enable_progressive_recovery = self.algorithm_mode == 'full'

        # ---------- 消融模式开关（仅对 proposed/full 生效） ----------
        raw_ablation_mode = (os.environ.get('ABLATION_MODE', 'A0') or 'A0').strip().upper()
        if raw_ablation_mode in ('NONE', 'OFF', 'DISABLED', 'FALSE', '0'):
            raw_ablation_mode = 'A0'
        valid_ablation_modes = {'A0', 'A1', 'A2', 'A3', 'A4'}
        if raw_ablation_mode not in valid_ablation_modes:
            rospy.logwarn(f"⚠️ Unknown ABLATION_MODE={raw_ablation_mode}, fallback to A0")
            raw_ablation_mode = 'A0'

        self.ablation_mode = raw_ablation_mode
        self.ablation_applied = (self.algorithm_mode == 'full' and self.ablation_mode != 'A0')

        if self.ablation_mode != 'A0' and self.algorithm_mode != 'full':
            rospy.logwarn(
                f"⚠️ ABLATION_MODE={self.ablation_mode} is ignored because algorithm={self.algorithm_mode_label} is not proposed/full"
            )

        if self.algorithm_mode == 'full':
            if self.ablation_mode == 'A1':
                self.enable_spacetime_reservation = False
            elif self.ablation_mode == 'A2':
                self.enable_deadlock_scan = False
            elif self.ablation_mode == 'A3':
                self.enable_fairness = False
            elif self.ablation_mode == 'A4':
                self.enable_progressive_recovery = False

        if not self.test_id and self.algorithm_mode == 'full':
            mode_hint = (os.environ.get('EXPERIMENT_MODE', 'unknown') or 'unknown').strip().lower()
            self.test_id = f"proposed-{mode_hint}-{time.strftime('%Y%m%d_%H%M%S')}"

        rospy.loginfo(
            f"🧠 Algorithm mode={self.algorithm_mode_label} (effective={self.algorithm_mode}, family={self.algorithm_family}), "
            f"ablation={self.ablation_mode}{' (applied)' if self.ablation_applied else ''}, "
            f"reservation={self.enable_spacetime_reservation}, "
            f"deadlock_scan={self.enable_deadlock_scan}, "
            f"fairness={self.enable_fairness}, "
            f"corridor={self.enable_corridor_token}, "
            f"progressive_recovery={self.enable_progressive_recovery}"
        )
        if self.test_id:
            rospy.loginfo(f"🧪 Test ID={self.test_id}")
        
        # ---------- 初始化 A* 路径规划器 ----------
        rospy.loginfo("Init: A* Planner...")
        self.path_planner = AStarPlanner(grid_size=0.1, robot_radius=0.0625)
        self.path_planner.set_obstacles([])

        # ---------- 位置与区域定义 ----------
        self.locations = {
            'empty_storage':    [(2.0, 2.0)],
            'green_storage':    [(2.0, 8.0)],
            'yellow_storage':   [(14.0, 2.0)],
            'red_storage':      [(14.0, 8.0)],
            'completed':        [(14.0, 5.0)],
            'carding_waiting':  [(5.0, 1.5), (5.0, 3.5), (5.0, 5.5), (5.0, 7.5)],
            'drawing1_waiting': [(8.0, 2.5), (8.0, 6.5)],
            'drawing2_waiting': [(10.8, 2.5), (10.8, 6.5)],
        }

        self.regions = {
            'empty_storage':    {'center': (2.0, 2.0),   'radius': 1.0},
            'green_storage':    {'center': (2.0, 8.0),   'radius': 1.0},
            'yellow_storage':   {'center': (14.0, 2.0),  'radius': 1.0},
            'red_storage':      {'center': (14.0, 8.0),  'radius': 1.0},
            'completed':        {'center': (14.0, 5.0),  'radius': 0.9},
            'carding_waiting':  {'center': (5.0, 4.5),   'radius': 3.2},
            'drawing1_waiting': {'center': (8.0, 4.5),   'radius': 2.2},
            'drawing2_waiting': {'center': (10.8, 4.5),  'radius': 2.2},
        }

        # 狭窄通道（用于单向通行令牌）
        self.corridor_zones = {
            'corridor_carding': {'bbox': (4.4, 7.2, 1.0, 8.0)},
            'corridor_drawing1': {'bbox': (7.4, 10.4, 1.6, 7.4)},
            'corridor_drawing2': {'bbox': (10.2, 13.2, 1.6, 7.4)},
        }

        # ---------- ROS 发布者 ----------
        self.cmd_vel_pubs = {}
        for i in range(num_robots):
            self.cmd_vel_pubs[i] = rospy.Publisher(f'/robot_{i}/cmd_vel', Twist, queue_size=10)

        self.task_stats_pub = rospy.Publisher('/factory/task_statistics', String, queue_size=10)
        self.robot_status_pub = rospy.Publisher('/factory/robot_status', String, queue_size=10)
        self.notification_pub = rospy.Publisher('/factory/notifications', String, queue_size=10)
        self.command_result_pub = rospy.Publisher('/factory/command_result', String, queue_size=30)

        # ---------- ROS 订阅者 ----------
        for i in range(num_robots):
            rospy.Subscriber(f'/robot_{i}/odom', Odometry, self.odom_callback, callback_args=i)
            rospy.Subscriber(f'/robot_{i}/scan', LaserScan, self.laser_callback, callback_args=i)

        # 机器人状态初始化
        for i in range(num_robots):
            self.robot_status[i] = RobotStatus.IDLE
            self.robot_current_task[i] = None
            self.robot_paths[i] = []
            self.robot_collision_active[i] = False
            self.robot_wait_since[i] = None
            self.robot_flip_detected[i] = False
            self.robot_flip_state[i] = 'normal'
            self.robot_flip_candidate_since[i] = None
            self.robot_flip_stable_since[i] = None
            self.robot_upright_z_baseline[i] = None

        # 区域追踪与人工任务
        self.region_robots = defaultdict(list)  # 各区域内机器人列表
        self.min_goal_distance = 1.2            # 目标点最小间距
        self.manual_task_info = {}              # 人工调度信息 {id: {duration, is_waiting, ...}}

        rospy.Subscriber('/factory/command', String, self.handle_web_command)
        rospy.Subscriber('/factory/experiment_control', String, self.handle_experiment_control)

        # ---------- 自动启动实验（环境变量模式） ----------
        env_mode = os.environ.get('EXPERIMENT_MODE', None)
        if env_mode:
            rospy.loginfo(f"🚀 自动启动实验 - 模式: {env_mode}")
            self.experiment_mode = env_mode
            self.experiment_started = True
            self.system_start_time = time.time()
            self.reset_robustness_trackers()
            self.generate_tasks(env_mode)
            rospy.loginfo(f"✅ 已生成 {self.total_tasks} 个任务，开始执行")
        else:
            rospy.loginfo("🔄 Scheduler Ready. Waiting for experiment start command...")
            rospy.loginfo("   Use Dashboard to select experiment mode and start.")
    
    # ============================================================
    #  区域追踪与分散策略
    # ============================================================

    def update_region_tracking(self):
        """
        @brief 更新各区域内的机器人列表

        遍历所有机器人位置，判断其所在区域并更新 region_robots 字典。
        """
        self.region_robots.clear()
        for robot_id, pos in self.robot_positions.items():
            region_name = self.get_region_name_for_position(pos)
            if region_name:
                self.region_robots[region_name].append(robot_id)

    def get_region_name_for_position(self, pos):
        """
        @brief 获取指定坐标所属区域名称

        @param pos: 坐标 (x, y)
        @return: 区域名称字符串，不在任何区域内返回 None
        """
        candidates = []
        for r_name, info in self.regions.items():
            cx, cy = info['center']
            dist = math.hypot(pos[0] - cx, pos[1] - cy)
            radius = max(info['radius'], 1e-6)
            if dist <= radius:
                # Use normalized distance to break overlap ties robustly.
                candidates.append((dist / radius, dist, r_name))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    def find_dispersed_goal_in_region(self, region_name, preferred_goal=None):
        """
        @brief 在区域内寻找分散目标点，避免多机拥挤

        在区域内均匀采样候选点（8 方向 × 4 距离），选择距离
        区域内现有机器人最远的点作为目标。

        @param region_name:   区域名称
        @param preferred_goal: 优先目标点（可选）
        @return: 最优目标点 (x, y)
        """
        if region_name not in self.region_robots or not self.region_robots[region_name]:
            return preferred_goal or self.regions[region_name]['center']

        center = self.regions[region_name]['center']
        radius = self.regions[region_name]['radius']

        # 在区域内采样候选点（8 方向 × 4 距离）
        candidates = []
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        dists = [0.3, 0.6, 0.9, 1.2]

        for angle in angles:
            rad = math.radians(angle)
            for d in dists:
                if d < radius:
                    candidates.append((center[0] + d * math.cos(rad),
                                       center[1] + d * math.sin(rad)))

        if preferred_goal:
            candidates.append(preferred_goal)

        # 选择离所有区域内机器人最远的候选点
        best_goal, max_min_dist = None, 0.0
        robots = self.region_robots[region_name]

        for pt in candidates:
            min_dist = min(
                [math.hypot(pt[0] - self.robot_positions[rid][0],
                             pt[1] - self.robot_positions[rid][1])
                 for rid in robots if rid in self.robot_positions],
                default=float('inf')
            )
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_goal = pt

        return best_goal if best_goal else (preferred_goal or center)

    def plan_path_avoiding_region_robots(self, robot_id, start, goal):
        """
        @brief 规划路径时将区域内其他机器人视为动态障碍物

        临时将起点和终点所在区域的其他机器人添加为动态障碍物，
        规划完成后恢复原始障碍物状态。

        @param robot_id: 当前机器人 ID
        @param start:    起点坐标 (x, y)
        @param goal:     终点坐标 (x, y)
        @return: 路径点列表 [(x, y), ...]
        """
        s_reg = self.get_region_name_for_position(start)
        g_reg = self.get_region_name_for_position(goal)
        avoid_ids = set()

        for reg in [s_reg, g_reg]:
            if reg and reg in self.region_robots:
                avoid_ids.update(self.region_robots[reg])
        
        # 临时将区域内机器人添加为动态障碍物
        orig_obstacles = self.path_planner.dynamic_obstacles.copy()
        temp_obstacles = dict(orig_obstacles)
        for other_id in avoid_ids:
            if other_id != robot_id and other_id in self.robot_positions:
                temp_obstacles[other_id] = self.robot_positions[other_id]

        self.path_planner.update_dynamic_obstacles(temp_obstacles)

        task = self.robot_current_task.get(robot_id)
        path = self.path_planner.plan_path(
            start, goal, robot_id=robot_id,
            priority=task.priority if task else 50
        )

        # 恢复原始障碍物状态
        self.path_planner.update_dynamic_obstacles(orig_obstacles)
        return path

    def get_corridor_for_position(self, pos):
        """返回坐标所在走廊 ID，不在走廊内返回 None。"""
        if not pos:
            return None
        x, y = pos
        for cid, info in self.corridor_zones.items():
            x_min, x_max, y_min, y_max = info['bbox']
            if x_min <= x <= x_max and y_min <= y <= y_max:
                return cid
        return None

    def get_robot_corridor_state(self, rid):
        """返回机器人走廊状态 (cid, direction_sign)。"""
        if rid not in self.robot_positions:
            return None, 0
        cid = self.get_corridor_for_position(self.robot_positions[rid])
        if cid is None:
            return None, 0

        path = self.robot_paths.get(rid) or []
        if not path:
            return cid, 0

        curr = self.robot_positions[rid]
        next_pt = path[0]
        dx = next_pt[0] - curr[0]
        dy = next_pt[1] - curr[1]
        if abs(dx) >= abs(dy):
            direction = 1 if dx >= 0 else -1
        else:
            direction = 1 if dy >= 0 else -1
        return cid, direction

    def cleanup_corridor_tokens(self):
        """清理过期令牌或离开走廊的持有者。"""
        now = time.time()
        for cid in list(self.corridor_tokens.keys()):
            token = self.corridor_tokens.get(cid, {})
            holder = token.get('holder')
            until = token.get('until', 0.0)
            if now >= until:
                self.corridor_token_release_count_total += 1
                self._corridor_log(
                    f"release:{cid}",
                    f"🚧 Corridor token released: {cid}, reason=expired, holder=R{holder}",
                    level='info'
                )
                del self.corridor_tokens[cid]
                continue
            if holder not in self.robot_positions:
                self.corridor_token_release_count_total += 1
                self._corridor_log(
                    f"release:{cid}",
                    f"🚧 Corridor token released: {cid}, reason=holder_missing, holder=R{holder}",
                    level='info'
                )
                del self.corridor_tokens[cid]
                continue
            holder_cid = self.get_corridor_for_position(self.robot_positions[holder])
            if holder_cid != cid:
                self.corridor_token_release_count_total += 1
                self._corridor_log(
                    f"release:{cid}",
                    f"🚧 Corridor token released: {cid}, reason=holder_left, holder=R{holder}",
                    level='info'
                )
                del self.corridor_tokens[cid]

    def _corridor_log(self, key, message, level='info'):
        """走廊令牌日志（带限频，避免刷屏）。"""
        now = time.time()
        if now - self.corridor_last_log_time.get(key, 0.0) < self.corridor_log_throttle_sec:
            return
        self.corridor_last_log_time[key] = now
        if level == 'warn':
            rospy.logwarn(message)
        else:
            rospy.loginfo(message)

    def corridor_priority_decision(self, r1, r2):
        """走廊单向令牌判定，返回 True 表示 r1 需要让路。"""
        if not self.enable_corridor_token:
            return None

        now = time.time()
        c1, d1 = self.get_robot_corridor_state(r1)
        c2, d2 = self.get_robot_corridor_state(r2)

        if c1 is None or c2 is None or c1 != c2:
            return None
        if d1 == 0 or d2 == 0:
            return None
        if d1 == d2:
            return None

        token = self.corridor_tokens.get(c1)
        if token and token.get('until', 0.0) > now:
            holder = token.get('holder')
            if holder == r1:
                self.corridor_token_reuse_count_total += 1
                token['until'] = now + self.corridor_token_ttl
                self._corridor_log(
                    f"reuse:{c1}:{holder}",
                    f"🚧 Corridor token reuse: {c1}, holder=R{holder}, pass=R{r1}, block=R{r2}",
                    level='info'
                )
                return False
            if holder == r2:
                self.corridor_token_reuse_count_total += 1
                token['until'] = now + self.corridor_token_ttl
                self._corridor_log(
                    f"reuse:{c1}:{holder}",
                    f"🚧 Corridor token reuse: {c1}, holder=R{holder}, pass=R{r2}, block=R{r1}",
                    level='info'
                )
                return True

        # 无有效令牌：按有效优先级决定持有人
        p1, _, _ = self.get_effective_priority(r1, peer_id=r2)
        p2, _, _ = self.get_effective_priority(r2, peer_id=r1)
        if p1 > p2:
            holder = r1
        elif p2 > p1:
            holder = r2
        else:
            holder = r1 if r1 < r2 else r2

        holder_dir = d1 if holder == r1 else d2
        self.corridor_tokens[c1] = {
            'holder': holder,
            'direction': holder_dir,
            'until': now + self.corridor_token_ttl,
        }
        self.corridor_token_grant_count_total += 1
        self._corridor_log(
            f"grant:{c1}",
            f"🚧 Corridor token grant: {c1}, holder=R{holder}, block=R{r2 if holder == r1 else r1}",
            level='warn'
        )
        return holder != r1

    # ============================================================
    #  ROS 回调函数
    # ============================================================

    def odom_callback(self, msg, robot_id):
        """
        @brief 里程计回调：更新位置、方向、速度并检测翻倒

        从 Odometry 消息提取位姿信息，计算 roll/pitch 判断
        是否翻倒（>30°），同步更新 A* 规划器的动态障碍物。

        @param msg:      ROS Odometry 消息
        @param robot_id: 机器人编号
        """
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation

        prev_pos = self.robot_last_position.get(robot_id)
        if prev_pos is not None:
            self.total_travel_distance += math.hypot(pos.x - prev_pos[0], pos.y - prev_pos[1])
        self.robot_last_position[robot_id] = (pos.x, pos.y)

        self.robot_positions[robot_id] = (pos.x, pos.y)
        self.robot_velocities[robot_id] = math.hypot(
            msg.twist.twist.linear.x, msg.twist.twist.linear.y)

        # 计算 yaw 角
        siny_cosp = 2.0 * (ori.w * ori.z + ori.x * ori.y)
        cosy_cosp = 1.0 - 2.0 * (ori.y * ori.y + ori.z * ori.z)
        self.robot_orientations[robot_id] = math.atan2(siny_cosp, cosy_cosp)

        # 翻倒检测状态机（倾角为主，高度异常为辅助）
        roll = math.atan2(2.0 * (ori.w * ori.x + ori.y * ori.z),
                          1.0 - 2.0 * (ori.x * ori.x + ori.y * ori.y))
        pitch_arg = 2.0 * (ori.w * ori.y - ori.z * ori.x)
        pitch_arg = max(-1.0, min(1.0, pitch_arg))
        pitch = math.asin(pitch_arg)

        self.update_upright_z_baseline(robot_id, pos.z, roll, pitch)
        is_flip_signal, is_severe_signal, reason, baseline_z = self.detect_flip_signal(
            robot_id, roll, pitch, pos.z
        )
        self.update_flip_state(
            robot_id,
            is_flip_signal,
            is_severe_signal,
            roll,
            pitch,
            pos.z,
            reason,
            baseline_z,
        )

        # 同步更新 A* 动态障碍物（过滤空闲机器人，减少末端任务被静态堵死）
        self.path_planner.update_dynamic_obstacles(self.get_planning_dynamic_obstacles())

    def get_planning_dynamic_obstacles(self):
        """
        @brief 生成用于路径规划的动态障碍物集合

        仅纳入非空闲机器人，避免空闲机器人长期停驻导致末端任务无路可走。
        """
        obs = {}
        for rid, pos in self.robot_positions.items():
            status = self.robot_status.get(rid, RobotStatus.IDLE)
            if status != RobotStatus.IDLE or self.robot_current_task.get(rid) is not None:
                obs[rid] = pos
        return obs

    def reset_robustness_trackers(self):
        """重置鲁棒性指标跟踪状态。"""
        self.freeze_duration_total = 0.0
        self.freeze_duration_samples.clear()
        self.persistent_stall_duration_total = 0.0
        self.persistent_stall_duration_samples.clear()
        self.robot_progress_timestamps.clear()
        self.recovery_trigger_count_total = 0
        self.recovery_trigger_timestamps.clear()
        self.recovery_success_timestamps.clear()
        self.last_progress_timestamp = self.system_start_time
        self.last_completed_task_count = len(self.completed_tasks)
        self.flow_window_last_tick = self.system_start_time
        self.flow_window_last_completed = len(self.completed_tasks)
        self.flow_positive_count_total = 0
        self.flow_total_window_count = 0
        self.flow_window_outcomes.clear()

    def update_upright_z_baseline(self, rid, pos_z, roll, pitch):
        """
        @brief 在“稳定直立”阶段更新高度基线（用于辅助判据）
        """
        state = self.robot_flip_state.get(rid, 'normal')
        speed = self.robot_velocities.get(rid, 0.0)
        is_stable_upright = (
            abs(roll) < 0.20
            and abs(pitch) < 0.20
            and speed < 0.08
            and state in ('normal', 'suspected')
        )
        if not is_stable_upright:
            return

        baseline = self.robot_upright_z_baseline.get(rid)
        if baseline is None:
            self.robot_upright_z_baseline[rid] = pos_z
        else:
            alpha = self.flip_z_baseline_alpha
            self.robot_upright_z_baseline[rid] = (1.0 - alpha) * baseline + alpha * pos_z
        self.robot_z_baseline_samples[rid] += 1

    def detect_flip_signal(self, rid, roll, pitch, pos_z):
        """
        @brief 生成翻倒信号：倾角主判据 + 高度下降辅助判据
        """
        tilt = max(abs(roll), abs(pitch))
        severe_tilt = tilt >= self.flip_tilt_severe_rad
        confirm_tilt = tilt >= self.flip_tilt_confirm_rad

        baseline_z = self.robot_upright_z_baseline.get(rid)
        z_drop = False
        if (
            baseline_z is not None
            and self.robot_z_baseline_samples[rid] >= self.flip_z_min_samples
        ):
            z_drop = pos_z < (baseline_z - self.flip_z_drop_threshold)

        # 高度单独异常不触发，必须伴随中等以上倾角
        z_tilt_combo = z_drop and tilt >= 0.65

        if severe_tilt:
            return True, True, 'severe_tilt', baseline_z
        if confirm_tilt:
            return True, False, 'tilt_confirm', baseline_z
        if z_tilt_combo:
            return True, False, 'z_tilt_combo', baseline_z
        return False, False, 'none', baseline_z

    def update_flip_state(self, rid, is_flip_signal, is_severe_signal,
                          roll, pitch, pos_z, reason, baseline_z):
        """
        @brief 翻倒状态机更新

        状态流转：
        normal -> suspected -> flipped -> recovering -> normal。
        suspected 需持续超过阈值时间，避免短时抖动误判。
        """
        now = time.time()
        state = self.robot_flip_state.get(rid, 'normal')

        if is_flip_signal:
            self.robot_flip_stable_since[rid] = None
            if state == 'normal':
                self.robot_flip_state[rid] = 'suspected'
                self.robot_flip_candidate_since[rid] = now
                return

            if state == 'suspected':
                started = self.robot_flip_candidate_since.get(rid) or now
                confirm_duration = 0.25 if is_severe_signal else self.flip_confirm_duration
                if now - started >= confirm_duration:
                    self.robot_flip_state[rid] = 'flipped'
                    self.robot_flip_detected[rid] = True
                    if now - self.robot_flip_last_confirm_time[rid] >= self.flip_repeat_suppress_duration:
                        self.robot_flip_count[rid] += 1
                        self.robot_flip_last_confirm_time[rid] = now
                    self.stop_robot(rid)
                    self.send_notification(
                        'warning',
                        f'机器人 {rid} 检测到翻倒，准备自动恢复'
                    )
                    baseline_text = 'N/A' if baseline_z is None else f'{baseline_z:.2f}'
                    rospy.logwarn(
                        f"⚠️ Robot {rid} flip confirmed: "
                        f"roll={roll:.2f}, pitch={pitch:.2f}, z={pos_z:.2f}, "
                        f"baseline_z={baseline_text}, reason={reason}, "
                        f"count={self.robot_flip_count[rid]}"
                    )
                return

            return

        if state == 'suspected':
            self.robot_flip_state[rid] = 'normal'
            self.robot_flip_candidate_since[rid] = None
            return

        if state == 'flipped' and rid not in self.robot_flip_recovering:
            stable_since = self.robot_flip_stable_since.get(rid)
            if stable_since is None:
                self.robot_flip_stable_since[rid] = now
                return

            tilt = max(abs(roll), abs(pitch))
            if tilt > self.flip_tilt_clear_rad:
                self.robot_flip_stable_since[rid] = None
                return

            if now - stable_since >= self.flip_clear_duration:
                self.robot_flip_state[rid] = 'normal'
                self.robot_flip_detected[rid] = False
                self.robot_flip_candidate_since[rid] = None
                self.robot_flip_stable_since[rid] = None

    def auto_recover_flipped_robots(self):
        """
        @brief 自动触发翻倒恢复（带冷却与并发保护）
        """
        now = time.time()
        for rid in range(self.num_robots):
            if self.robot_flip_state.get(rid) != 'flipped':
                continue
            if rid in self.robot_flip_recovering:
                continue
            if now - self.robot_flip_last_recover_time[rid] < self.flip_recover_cooldown:
                continue

            self.robot_flip_state[rid] = 'recovering'
            self.robot_flip_recovering.add(rid)
            self.robot_flip_last_recover_time[rid] = now
            self.publish_command_result(
                command='auto_recover',
                robot_id=rid,
                status='executing',
                message='检测到翻倒，开始自动恢复',
                source='auto_flip'
            )

            threading.Thread(
                target=self._auto_recover_worker,
                args=(rid,),
                daemon=True
            ).start()

    def _auto_recover_worker(self, rid):
        success, detail = self.recover_robot(rid, source='auto_flip')
        if success:
            self.publish_command_result(
                command='auto_recover',
                robot_id=rid,
                status='executed',
                message=detail,
                source='auto_flip'
            )
        else:
            self.publish_command_result(
                command='auto_recover',
                robot_id=rid,
                status='failed',
                message=detail,
                source='auto_flip'
            )
            self.robot_flip_state[rid] = 'flipped'
        self.robot_flip_recovering.discard(rid)

    def laser_callback(self, msg, robot_id):
        """
        @brief 激光雷达回调

        @param msg:      ROS LaserScan 消息
        @param robot_id: 机器人编号
        """
        self.robot_laser_data[robot_id] = msg.ranges
    
    # ============================================================
    #  导航控制与碰撞防护
    # ============================================================

    def send_navigation_goal(self, robot_id, target_pos):
        """
        @brief 导航控制：PID 角度跟踪 + 局部激光避障 + 三层防撞

        三层防护机制：
        1. 激光雷达局部避障（优先级最高）
        2. 全局距离防撞检测（动态限速/紧急后退）
        3. 硬安全距离禁止前进

        @param robot_id:   机器人编号
        @param target_pos: 目标位置 (x, y)
        """
        if robot_id not in self.robot_positions:
            return

        curr = self.robot_positions[robot_id]
        dx, dy = target_pos[0] - curr[0], target_pos[1] - curr[1]
        dist = math.hypot(dx, dy)

        if dist < 0.1:
            self.stop_robot(robot_id)
            return

        # 角度误差计算
        target_ang = math.atan2(dy, dx)
        ang_err = target_ang - self.robot_orientations.get(robot_id, 0.0)
        while ang_err > math.pi:
            ang_err -= 2 * math.pi
        while ang_err < -math.pi:
            ang_err += 2 * math.pi

        # 第一层：激光雷达局部避障
        has_laser, action = self.check_laser_obstacle(robot_id)
        if has_laser:
            cmd = Twist()
            if action == 'stop':
                cmd.linear.x = 0.0
            elif action == 'turn_left':
                cmd.linear.x, cmd.angular.z = -0.1, 1.0
            elif action == 'turn_right':
                cmd.linear.x, cmd.angular.z = -0.1, -1.0
            if self.is_linear_motion_toward_any_close_robot(robot_id, cmd.linear.x):
                cmd.linear.x = 0.0
            self.cmd_vel_pubs[robot_id].publish(cmd)
            return

        # 第二层：全局防撞检测
        has_coll, speed_fac, emg_stop = self.check_collision_nearby(robot_id)

        # 统计碰撞风险事件（仅在“无风险 -> 有风险”时计数，避免高频重复累计）
        if has_coll:
            if not self.robot_collision_active.get(robot_id, False):
                self.collision_event_count += 1
                self.collision_event_timestamps.append(time.time())
                self.robot_collision_active[robot_id] = True
        else:
            self.robot_collision_active[robot_id] = False

        if emg_stop:
            closest, _ = self.get_closest_robot(robot_id)
            cmd = self.build_emergency_escape_command(robot_id, closest)
            self.cmd_vel_pubs[robot_id].publish(cmd)
            rospy.sleep(1.0)
            self.stop_robot(robot_id)
            self.robot_paths[robot_id] = []
            return

        # 第三层：速度计算与安全距离限制
        max_v = 0.35
        if has_coll:
            # 动态限速：距离越近速度越慢
            min_d = min(
                [math.hypot(curr[0] - self.robot_positions[oid][0],
                             curr[1] - self.robot_positions[oid][1])
                 for oid in self.robot_positions if oid != robot_id],
                default=99
            )
            if min_d < 0.5:
                max_v = 0.15
            elif min_d < 1.0:
                max_v = 0.25

        # PID 速度输出
        lin = 0.08 * speed_fac if abs(ang_err) > 0.5 else min(max_v, dist * 0.4) * speed_fac
        ang = 1.5 * ang_err if abs(ang_err) > 0.5 else 1.0 * ang_err

        # 硬安全距离禁止前进
        if has_coll:
            min_d = 99.0
            closest = None
            for oid, opos in self.robot_positions.items():
                if oid == robot_id:
                    continue
                d = math.hypot(curr[0] - opos[0], curr[1] - opos[1])
                if d < min_d:
                    min_d = d
                    closest = oid
            if (
                min_d < self.hard_safety_distance
                and abs(lin) > 1e-6
                and closest is not None
                and self.is_linear_motion_toward_robot(robot_id, closest, lin)
            ):
                lin = 0.0

        cmd = Twist()
        cmd.linear.x = max(-max_v, min(max_v, lin))
        cmd.angular.z = max(-2.0, min(2.0, ang))
        self.cmd_vel_pubs[robot_id].publish(cmd)

    @staticmethod
    def normalize_angle(angle):
        """将角度归一化到 [-pi, pi]。"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def get_closest_robot(self, robot_id):
        """返回距离 robot_id 最近的机器人及距离。"""
        if robot_id not in self.robot_positions:
            return None, float('inf')

        my_pos = self.robot_positions[robot_id]
        min_d, closest = float('inf'), None
        for oid, opos in self.robot_positions.items():
            if oid == robot_id:
                continue
            d = math.hypot(my_pos[0] - opos[0], my_pos[1] - opos[1])
            if d < min_d:
                min_d, closest = d, oid
        return closest, min_d

    def get_relative_robot_sector(self, robot_id, other_id):
        """判断 other_id 位于 robot_id 车体前方、后方还是侧方。"""
        if robot_id not in self.robot_positions or other_id not in self.robot_positions:
            return 'unknown'

        my_pos = self.robot_positions[robot_id]
        other_pos = self.robot_positions[other_id]
        yaw = self.robot_orientations.get(robot_id, 0.0)
        bearing = math.atan2(other_pos[1] - my_pos[1], other_pos[0] - my_pos[0])
        rel = self.normalize_angle(bearing - yaw)
        abs_rel = abs(rel)

        if abs_rel <= math.radians(60):
            return 'front'
        if abs_rel >= math.radians(120):
            return 'back'
        return 'left' if rel > 0 else 'right'

    def is_linear_motion_toward_robot(self, robot_id, other_id, linear_x):
        """判断给定线速度是否在朝指定机器人运动。"""
        if abs(linear_x) < 1e-6:
            return False
        if robot_id not in self.robot_positions or other_id not in self.robot_positions:
            return False

        my_pos = self.robot_positions[robot_id]
        other_pos = self.robot_positions[other_id]
        vx = other_pos[0] - my_pos[0]
        vy = other_pos[1] - my_pos[1]
        norm = math.hypot(vx, vy)
        if norm < 1e-6:
            return True

        yaw = self.robot_orientations.get(robot_id, 0.0)
        direction = 1.0 if linear_x > 0 else -1.0
        mx = math.cos(yaw) * direction
        my = math.sin(yaw) * direction
        dot = mx * (vx / norm) + my * (vy / norm)
        return dot > 0.25

    def is_linear_motion_toward_any_close_robot(self, robot_id, linear_x, distance=None):
        """判断线速度是否会靠近任一近距离机器人。"""
        if distance is None:
            distance = self.hard_safety_distance
        for oid, opos in self.robot_positions.items():
            if oid == robot_id:
                continue
            my_pos = self.robot_positions.get(robot_id)
            if not my_pos:
                continue
            d = math.hypot(my_pos[0] - opos[0], my_pos[1] - opos[1])
            if d < distance and self.is_linear_motion_toward_robot(robot_id, oid, linear_x):
                return True
        return False

    def choose_escape_rotation(self, robot_id, distance=None):
        """当线性脱困方向都不安全时，按周围机器人分布选择原地转向方向。"""
        if distance is None:
            distance = self.collision_escape_block_distance

        my_pos = self.robot_positions.get(robot_id)
        if not my_pos:
            return 1.0

        yaw = self.robot_orientations.get(robot_id, 0.0)
        side_pressure = 0.0
        for oid, opos in self.robot_positions.items():
            if oid == robot_id:
                continue
            d = math.hypot(my_pos[0] - opos[0], my_pos[1] - opos[1])
            if d >= distance:
                continue
            bearing = math.atan2(opos[1] - my_pos[1], opos[0] - my_pos[0])
            rel = self.normalize_angle(bearing - yaw)
            weight = 1.0 / max(d, 0.05)
            side_pressure += math.sin(rel) * weight

        # 左侧压力大则右转；右侧压力大则左转；正前/正后拥堵时固定左转。
        if side_pressure > 0.05:
            return -1.0
        return 1.0

    def build_emergency_escape_command(self, robot_id, closest):
        """
        @brief 构造方向安全的紧急脱困指令

        旧逻辑无条件倒车。尾对尾时，对方位于本车后方，倒车会进一步
        缩小距离；此处按所有近距离机器人共同约束选择安全方向。
        """
        cmd = Twist()
        if closest is None:
            return cmd

        sector = self.get_relative_robot_sector(robot_id, closest)
        linear_candidates = []
        if sector == 'front':
            linear_candidates = [-0.16, 0.12]
        elif sector == 'back':
            linear_candidates = [0.16, -0.12]
        elif sector == 'left':
            linear_candidates = [-0.12, 0.12]
        elif sector == 'right':
            linear_candidates = [-0.12, 0.12]

        block_distance = max(
            self.hard_safety_distance,
            getattr(self, 'collision_escape_block_distance', 0.45)
        )
        for linear_x in linear_candidates:
            if not self.is_linear_motion_toward_any_close_robot(
                robot_id,
                linear_x,
                distance=block_distance
            ):
                cmd.linear.x = linear_x
                return cmd

        cmd.linear.x = 0.0
        cmd.angular.z = self.choose_escape_rotation(robot_id, distance=block_distance)
        return cmd

    def check_collision_nearby(self, robot_id):
        """
        @brief 检查周围碰撞风险

        三级判定：
        - 紧急后退距离 → 立即停止并后退
        - 硬安全距离 → 速度归零
        - 减速检测距离 → 按比例降速

        @param robot_id: 机器人编号
        @return: (has_collision, speed_factor, emergency_stop) 三元组
        """
        if robot_id not in self.robot_positions:
            return False, 1.0, False

        closest, min_d = self.get_closest_robot(robot_id)

        # 受保护机器人强制避让
        if closest in self.robot_protected and min_d < 0.4:
            return True, 0.0, True
        if min_d < self.critical_safety_distance:
            return True, 0.0, True
        if min_d < self.hard_safety_distance:
            # hard 区内仍保留低速脱困能力；最终速度会由方向安全检查
            # 截断所有“朝对方移动”的线速度。
            return True, 0.35, False
        if min_d < self.collision_check_distance:
            return True, max(0.3, min_d / self.collision_check_distance), False
        return False, 1.0, False

    def check_laser_obstacle(self, robot_id):
        """
        @brief 分析激光雷达数据判断局部障碍

        将激光扫描范围三等分（左/前/右），检测各区域最小距离。
        前方受阻时根据左右空间选择转向方向。

        @param robot_id: 机器人编号
        @return: (has_obstacle, action) 其中 action 为 'stop'/'turn_left'/'turn_right'/None
        """
        ranges = self.robot_laser_data.get(robot_id, [])
        if not ranges:
            return False, None

        n = len(ranges)
        l, r = n // 3, n * 2 // 3

        # 过滤无效数据（排除过近和过远值）
        def min_valid(arr):
            return min([x for x in arr if 0.04 < x < 5.0], default=5.0)

        front = min_valid(ranges[l:r])
        left = min_valid(ranges[0:l])
        right = min_valid(ranges[r:])

        if front < self.laser_obstacle_threshold:
            return True, 'turn_left' if left > right else 'turn_right'
        if left < 0.3:
            return True, 'turn_right'
        if right < 0.3:
            return True, 'turn_left'
        return False, None
    
    # ============================================================
    #  优先级管理与死锁检测
    # ============================================================

    def update_robot_priority(self, robot_id):
        """
        @brief 基于任务状态动态更新机器人优先级

        送货中（delivering）+20，装卸中（loading/unloading）+10。

        @param robot_id: 机器人编号
        """
        task = self.robot_current_task.get(robot_id)
        if not task:
            self.robot_priorities[robot_id] = 0
            return

        p = task.priority
        if task.status == "delivering":
            p += 20
        if task.status in ["loading", "unloading"]:
            p += 10
        self.robot_priorities[robot_id] = p

    def update_robot_wait_state(self, rid):
        """
        @brief 更新机器人等待状态（用于反饥饿优先级增益）

        MOVING 且存在路径但速度长期低于阈值时，累计等待时间；
        一旦恢复移动或路径清空则重置。
        """
        status = self.robot_status.get(rid)
        if status != RobotStatus.MOVING:
            self.robot_wait_since[rid] = None
            return

        path = self.robot_paths.get(rid)
        task = self.robot_current_task.get(rid)
        target = self.get_task_phase_target(task)
        if not path and (not task or target is None):
            self.robot_wait_since[rid] = None
            return

        speed = self.robot_velocities.get(rid, 0.0)
        now = time.time()
        if speed < self.wait_speed_threshold:
            if self.robot_wait_since.get(rid) is None:
                self.robot_wait_since[rid] = now
        else:
            self.robot_wait_since[rid] = None

    def get_wait_duration(self, rid):
        """返回机器人当前连续等待时长（秒）"""
        ts = self.robot_wait_since.get(rid)
        if ts is None:
            return 0.0
        return max(0.0, time.time() - ts)

    @staticmethod
    def get_task_phase_target(task):
        """返回任务当前阶段目标点。"""
        if not task:
            return None
        if task.status == "assigned":
            return task.source
        if task.status == "delivering":
            return task.destination
        return None

    def recover_stalled_robots(self):
        """
        @brief 单车长期零速自愈

        全局死锁扫描只处理近距离机器人对；若机器人已经接近任务点但被
        局部避障/安全距离压成 0 速，可能长期停在 MOVING。这里在等待
        超过阈值后，优先把近目标机器人交给到达处理，否则节流重规划。
        """
        now = time.time()
        for rid in range(self.num_robots):
            if self.robot_status.get(rid) != RobotStatus.MOVING:
                continue

            task = self.robot_current_task.get(rid)
            target = self.get_task_phase_target(task)
            if not task or target is None or rid not in self.robot_positions:
                continue

            if self.get_wait_duration(rid) < self.persistent_stall_horizon:
                continue

            curr = self.robot_positions[rid]
            dist_to_target = math.hypot(target[0] - curr[0], target[1] - curr[1])

            if dist_to_target <= self.stall_near_target_tolerance:
                rospy.logwarn(
                    f"⚠️ R{rid} stalled near target ({dist_to_target:.2f}m), forcing arrival handling"
                )
                self.clear_spacetime_reservation(rid)
                self.robot_paths[rid] = []
                self.robot_wait_since[rid] = None
                self.handle_arrival(rid)
                continue

            if now - self.robot_last_stall_replan_time[rid] < self.stall_replan_cooldown:
                continue

            self.robot_last_stall_replan_time[rid] = now
            repath = self.path_planner.plan_path(
                curr,
                target,
                robot_id=rid,
                priority=max(90, task.priority)
            )
            if repath and len(repath) >= 2:
                smooth = self.path_planner.smooth_path(repath)
                self.robot_paths[rid] = smooth if smooth else repath
                self.clear_spacetime_reservation(rid)
                self.robot_yielding.pop(rid, None)
                rospy.logwarn(
                    f"⚠️ R{rid} stalled for {self.get_wait_duration(rid):.1f}s, replanned path"
                )
            else:
                closest, min_d = self.get_closest_robot(rid)
                if closest is not None and min_d < self.collision_check_distance:
                    cmd = self.build_emergency_escape_command(rid, closest)
                    if rid in self.cmd_vel_pubs:
                        self.cmd_vel_pubs[rid].publish(cmd)
                    self.clear_spacetime_reservation(rid)
                    rospy.logwarn(
                        f"⚠️ R{rid} stalled for {self.get_wait_duration(rid):.1f}s, "
                        f"replan failed; applying local escape from R{closest} ({min_d:.2f}m)"
                    )

    def get_effective_priority(self, rid, peer_id=None):
        """
        @brief 计算有效优先级 = 基础优先级 + 等待增益 + 继承/保护加权

        @param rid:     当前机器人 ID
        @param peer_id: 对向机器人 ID（可选）
        @return: (effective_priority, base_priority, wait_boost)
        """
        self.update_robot_priority(rid)
        base_p = self.robot_priorities.get(rid, 0)

        wait_seconds = self.get_wait_duration(rid)
        wait_steps = int(wait_seconds / self.wait_boost_interval)
        wait_boost = min(self.max_wait_priority_boost, wait_steps * self.wait_boost_step)

        effective = base_p + wait_boost

        if rid in self.robot_protected:
            effective += self.protected_priority_bonus

        if peer_id is not None and peer_id in self.robot_yielding:
            target, until = self.robot_yielding[peer_id]
            if target == rid and time.time() < until:
                effective += self.priority_inheritance_bonus

        return effective, base_p, wait_boost

    def is_yielding_to(self, rid, target_id):
        """判断 rid 当前是否在主动让路给 target_id。"""
        info = self.robot_yielding.get(rid)
        if not info:
            return False
        target, until = info
        return target == target_id and time.time() < until

    @staticmethod
    def _pair_key(r1, r2):
        """返回机器人对的标准化键（小ID在前）。"""
        return (r1, r2) if r1 < r2 else (r2, r1)

    def global_deadlock_scan(self):
        """
        @brief 全局死锁扫描

        遍历所有机器人对，检测是否有两台机器人在 stuck_detection_window
        时间窗口内持续处于近距离状态。满足触发条件后调用强制解锁。
        """
        if not self.enable_deadlock_scan:
            return

        now = time.time()
        ids = list(self.robot_positions.keys())

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                r1, r2 = ids[i], ids[j]
                key = (r1, r2) if r1 < r2 else (r2, r1)

                s1 = self.robot_status.get(r1)
                s2 = self.robot_status.get(r2)
                navigable_states = [RobotStatus.MOVING, RobotStatus.MANUAL, RobotStatus.YIELDING]
                if s1 not in navigable_states and s2 not in navigable_states:
                    self.robot_pair_stuck_history.pop(key, None)
                    continue

                # pair 正在执行强制分离，暂不重复判死锁
                sep_until = self.pair_separation_active.get(key, 0.0)
                if now < sep_until:
                    continue
                if key in self.pair_separation_active and now >= sep_until:
                    del self.pair_separation_active[key]

                # 冷却期检查
                if key in self.deadlock_being_resolved:
                    if now < self.deadlock_being_resolved[key]:
                        continue
                    else:
                        del self.deadlock_being_resolved[key]

                # 距离检测
                p1, p2 = self.robot_positions[r1], self.robot_positions[r2]
                d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])

                # pair 已充分分离：清理累积重试，避免 retry 长期单调上升
                if d > self.deadlock_release_distance:
                    self.deadlock_pair_retry_count.pop(key, None)
                    self.deadlock_pair_last_time.pop(key, None)

                if d < self.stuck_distance_threshold:
                    rec = self.robot_pair_stuck_history.setdefault(
                        key, {'first': now, 'last': now, 'cnt': 0, 'min_d': d}
                    )
                    rec['last'] = now
                    rec['cnt'] += 1
                    rec['min_d'] = min(rec['min_d'], d)

                    # 判定为死锁
                    if (now - rec['first'] >= self.stuck_detection_window and
                            rec['cnt'] >= self.stuck_trigger_count):
                        last_t = self.deadlock_pair_last_time.get(key, 0.0)
                        if now - last_t > self.deadlock_retry_window:
                            self.deadlock_pair_retry_count[key] = 0
                        self.deadlock_pair_retry_count[key] += 1
                        retry_count = self.deadlock_pair_retry_count[key]
                        self.deadlock_pair_last_time[key] = now

                        rospy.logwarn(f"🔒 Deadlock: R{r1} <-> R{r2} (Dist: {d:.2f}m)")
                        self.deadlock_count_total += 1
                        self.deadlock_event_timestamps.append(now)
                        self.recovery_trigger_count_total += 1
                        self.recovery_trigger_timestamps.append(now)
                        cooldown = self.deadlock_resolve_cooldown + min(8.0, 1.5 * max(0, retry_count - 1))
                        self.deadlock_being_resolved[key] = now + cooldown
                        del self.robot_pair_stuck_history[key]
                        self.force_global_deadlock_resolution(r1, r2, retry_count)

                elif key in self.robot_pair_stuck_history:
                    del self.robot_pair_stuck_history[key]

    def force_global_deadlock_resolution(self, r1, r2, retry_count=1):
        """
        @brief 强制解决死锁：低优先级一方后退

        比较两机器人优先级，低优先级方执行 2 秒后退动作，
        然后清空路径等待重新规划。

        @param r1: 第一台机器人 ID
        @param r2: 第二台机器人 ID
        """
        if self.enable_fairness:
            p1, _, b1 = self.get_effective_priority(r1, peer_id=r2)
            p2, _, b2 = self.get_effective_priority(r2, peer_id=r1)
            if b1 > 0 or b2 > 0:
                self.starvation_prevent_count_total += 1
        else:
            p1 = self.robot_priorities.get(r1, 0)
            p2 = self.robot_priorities.get(r2, 0)

        # 走廊单向令牌优先，避免瓶颈区反复对向互卡
        corridor_decision = self.corridor_priority_decision(r1, r2)
        if corridor_decision is True:
            yielder, winner = r1, r2
        elif corridor_decision is False:
            yielder, winner = r2, r1
        else:
            # 决定让路方：有效优先级低的让路，优先级相同时 ID 大的让路
            if p1 < p2:
                yielder, winner = r1, r2
            elif p1 > p2:
                yielder, winner = r2, r1
            else:
                yielder, winner = (r1, r2) if r1 > r2 else (r2, r1)

        rospy.loginfo(f"🚨 Resolve: R{yielder} yields to R{winner} (retry={retry_count})")

        if self.enable_progressive_recovery and retry_count >= 6:
            self.trigger_pair_emergency_break(
                r1, r2,
                hold_sec=min(4.0, 2.5 + 0.2 * retry_count)
            )
            return

        # 重复死锁优先执行双机主动分离，避免单边hold造成互推僵局
        if self.enable_progressive_recovery and retry_count >= 2 and self.try_force_pair_separation(r1, r2, retry_count=retry_count):
            return

        def retreat():
            """优先侧移让路，失败则原地等待，不执行盲目后退"""
            hold_secs = min(14.0, 4.0 + 2.0 * max(0, retry_count - 1))
            lateral = [0.40, 0.55, 0.75] if retry_count >= 3 else [0.40]
            backward = [0.45, 0.65] if retry_count >= 3 else [0.45]

            safe_path = []
            if self.enable_progressive_recovery:
                safe_path = self.try_plan_safe_yield_path(
                    yielder,
                    avoid_rid=winner,
                    hold_seconds=hold_secs,
                    lateral_offsets=lateral,
                    backward_offsets=backward,
                )
            if safe_path:
                self.activate_yield_path(yielder, winner, safe_path, time.time() + hold_secs)
                self.robot_yield_count[yielder] += 1
                self.yield_count_total += 1
                self.collision_intervention_timestamps.append(time.time())
                rospy.loginfo(f"🚨 Deadlock resolve: R{yielder} safe-yield to R{winner}")
                return

            # 二次尝试：safe-yield失败后，改用双机主动分离
            if self.enable_progressive_recovery and self.try_force_pair_separation(yielder, winner, retry_count=retry_count):
                return

            self.stop_robot(yielder)
            self.robot_yielding[yielder] = (winner, time.time() + hold_secs)
            self.robot_yield_count[yielder] += 1
            self.yield_count_total += 1
            self.collision_intervention_timestamps.append(time.time())
            self.robot_paths[yielder] = []
            self.yield_fallback_count_total += 1
            self.deadlock_resolution_action_timestamps.append(time.time())
            self.recovery_success_timestamps.append(time.time())

            # 升级策略：多次失败后，强制重规划胜者路径，避免双方长期在原地互锁
            if self.enable_progressive_recovery and retry_count >= 3:
                task = self.robot_current_task.get(winner)
                if task and winner in self.robot_positions:
                    tgt = task.source if task.status == "assigned" else task.destination
                    repath = self.path_planner.plan_path(
                        self.robot_positions[winner],
                        tgt,
                        robot_id=winner,
                        priority=max(80, task.priority)
                    )
                    if repath and len(repath) >= 2:
                        smooth = self.path_planner.smooth_path(repath)
                        self.robot_paths[winner] = smooth if smooth else repath

            task = self.robot_current_task.get(yielder)
            if task and task.status in ("assigned", "delivering"):
                self.robot_status[yielder] = RobotStatus.MOVING
            rospy.logwarn(f"🚨 Deadlock resolve fallback: R{yielder} hold for safety")

        import threading
        threading.Thread(target=retreat, daemon=True).start()

    # ============================================================
    #  时空预约与冲突解决
    # ============================================================

    def reserve_spacetime(self, robot_id, path):
        """
        @brief 为机器人沿路径预约未来时空格子

        按当前速度估算到达每个路径点的时间，将 (grid_x, grid_y, t) 三元组
        存入 spacetime_reservations 供冲突检测使用。

        @param robot_id: 机器人编号
        @param path:     路径点列表 [(x, y), ...]
        """
        if not self.enable_spacetime_reservation:
            return

        if not path or len(path) < 2:
            return

        now = time.time()
        v = max(0.3, self.robot_velocities.get(robot_id, 0.3))
        node_res = []
        edge_res = []
        t_acc = 0.0

        first_gx = int(path[0][0] / self.reservation_grid_size)
        first_gy = int(path[0][1] / self.reservation_grid_size)
        node_res.append((first_gx, first_gy, now))

        for i in range(1, len(path)):
            prev_pt = path[i - 1]
            curr_pt = path[i]
            seg_dist = math.hypot(curr_pt[0] - prev_pt[0], curr_pt[1] - prev_pt[1])
            dt = seg_dist / v
            t0 = now + t_acc
            t_acc += dt
            t1 = now + t_acc

            if t_acc > self.reservation_horizon:
                break

            prev_gx = int(prev_pt[0] / self.reservation_grid_size)
            prev_gy = int(prev_pt[1] / self.reservation_grid_size)
            curr_gx = int(curr_pt[0] / self.reservation_grid_size)
            curr_gy = int(curr_pt[1] / self.reservation_grid_size)

            edge_res.append((prev_gx, prev_gy, curr_gx, curr_gy, t0, t1))
            node_res.append((curr_gx, curr_gy, t1))

        self.spacetime_reservations[robot_id] = {
            'nodes': node_res,
            'edges': edge_res,
        }

    def clear_spacetime_reservation(self, rid):
        """清理机器人时空预约，避免陈旧预约造成假冲突。"""
        self.spacetime_reservations.pop(rid, None)

    def _normalize_reservation_entry(self, entry):
        """
        @brief 兼容解析预约条目（新结构 dict 或旧结构 list）

        @param entry: 预约条目
        @return: (nodes, edges)
        """
        if isinstance(entry, dict):
            return entry.get('nodes', []), entry.get('edges', [])

        # 兼容旧格式：[(gx, gy, t), ...]
        nodes = entry if isinstance(entry, list) else []
        edges = []
        if len(nodes) >= 2:
            for i in range(1, len(nodes)):
                ax, ay, t0 = nodes[i - 1]
                bx, by, t1 = nodes[i]
                edges.append((ax, ay, bx, by, t0, t1))
        return nodes, edges

    @staticmethod
    def _time_overlap(t1_start, t1_end, t2_start, t2_end, tol=0.0):
        """判断两个时间区间是否重叠（含容忍窗口）"""
        return max(t1_start, t2_start) <= min(t1_end, t2_end) + tol

    def check_spacetime_conflict(self, robot_id):
        """
        @brief 检测当前机器人预约是否与其他机器人时空冲突

        两点在网格距离 ≤1 且时间差 <1s 视为冲突。

        @param robot_id: 机器人编号
        @return: (has_conflict, other_robot_id)
        """
        if not self.enable_spacetime_reservation:
            return False, None

        if robot_id not in self.spacetime_reservations:
            return False, None

        my_nodes, my_edges = self._normalize_reservation_entry(
            self.spacetime_reservations[robot_id]
        )
        now = time.time()
        tol = self.reservation_time_tolerance

        for oid, ores in self.spacetime_reservations.items():
            if oid == robot_id:
                continue

            other_nodes, other_edges = self._normalize_reservation_entry(ores)

            # 节点冲突：近网格 + 时间近邻
            for mx, my, mt in my_nodes:
                if mt < now:
                    continue
                for ox, oy, ot in other_nodes:
                    if ot < now:
                        continue
                    if abs(mx - ox) <= 1 and abs(my - oy) <= 1 and abs(mt - ot) < tol:
                        return True, oid

            # 边冲突1：对向换边（A->B 与 B->A）且时间重叠
            for ax, ay, bx, by, at0, at1 in my_edges:
                if at1 < now:
                    continue
                for ox, oy, px, py, ot0, ot1 in other_edges:
                    if ot1 < now:
                        continue
                    reverse_same = (ax == px and ay == py and bx == ox and by == oy)
                    if reverse_same and self._time_overlap(at0, at1, ot0, ot1, tol=tol * 0.5):
                        return True, oid

            # 边冲突2：同向同边重叠（同一边同时间占用）
            for ax, ay, bx, by, at0, at1 in my_edges:
                if at1 < now:
                    continue
                for ox, oy, px, py, ot0, ot1 in other_edges:
                    if ot1 < now:
                        continue
                    same_edge = (ax == ox and ay == oy and bx == px and by == py)
                    if same_edge and self._time_overlap(at0, at1, ot0, ot1, tol=tol * 0.5):
                        return True, oid

        return False, None

    def detect_conflict_type(self, r1, r2):
        """
        @brief 分析两机器人的冲突几何类型

        根据两机器人的朝向角度差和相对方位，分为：
        - following（同向跟随，角差 <60°）
        - perpendicular（垂直交叉，60°~120°）
        - opposite（对向行驶，150°~210°）
        - diagonal（斜向交叉，其他角度）

        @param r1: 第一台机器人 ID
        @param r2: 第二台机器人 ID
        @return: (conflict_type, angle_diff, relative_position)
        """
        if not (self.robot_paths.get(r1) and self.robot_paths.get(r2)):
            return 'none', 0, None

        p1, p2 = self.robot_positions[r1], self.robot_positions[r2]
        n1, n2 = self.robot_paths[r1][0], self.robot_paths[r2][0]

        # 计算两机器人的运动方向
        ang1 = math.atan2(n1[1] - p1[1], n1[0] - p1[0])
        ang2 = math.atan2(n2[1] - p2[1], n2[0] - p2[0])

        # 方向角差（归一化到 0~360°）
        diff = abs(math.degrees(math.atan2(
            math.sin(ang1 - ang2), math.cos(ang1 - ang2)
        )))

        # r2 相对于 r1 的方位
        rel_dir = math.degrees(
            math.atan2(p2[1] - p1[1], p2[0] - p1[0]) - ang1
        )
        rel_pos = 'front'
        if 45 < rel_dir <= 135:
            rel_pos = 'left'
        elif -135 <= rel_dir < -45:
            rel_pos = 'right'
        elif rel_dir > 135 or rel_dir < -135:
            rel_pos = 'back'

        # 按角度差归类
        if diff < 60:
            return 'following', diff, rel_pos
        if 60 <= diff < 120:
            return 'perpendicular', diff, rel_pos
        if 150 <= diff <= 210:
            return 'opposite', diff, rel_pos
        return 'diagonal', diff, rel_pos

    def resolve_conflict_by_priority(self, r1, r2):
        """
        @brief 基于冲突类型和优先级判断 r1 是否应让路

        对向冲突时距离目标近者优先；垂直/斜向冲突按优先级决定；
        同向跟随时后方让路（减速）。

        @param r1: 当前机器人 ID（被评估方）
        @param r2: 对方机器人 ID
        @return: True 表示 r1 应让路
        """
        # 若对方已在让路给我，则我不应再让路，避免双向振荡
        if self.is_yielding_to(r2, r1):
            return False
        # 若我当前已标记让路给对方，保持让路决策一致
        if self.is_yielding_to(r1, r2):
            return True

        if self.algorithm_mode in ('naive', 'path_only', 'path_reservation'):
            return r1 > r2

        # 走廊令牌优先（在狭窄区强制单向通行）
        corridor_decision = self.corridor_priority_decision(r1, r2)
        if corridor_decision is not None:
            return corridor_decision

        ctype, _, rel_pos = self.detect_conflict_type(r1, r2)

        # 确定优胜方（有效优先级：基础+等待增益+继承加权）
        p1, base1, boost1 = self.get_effective_priority(r1, peer_id=r2)
        p2, base2, boost2 = self.get_effective_priority(r2, peer_id=r1)
        winner = ('me' if p1 > p2
              else ('other' if p2 > p1
                else ('me' if r1 < r2 else 'other')))

        base_winner = ('me' if base1 > base2
                   else ('other' if base2 > base1
                     else ('me' if r1 < r2 else 'other')))
        if winner != base_winner and (boost1 > 0 or boost2 > 0):
            self.starvation_prevent_count_total += 1

        if ctype == 'opposite':
            # 对向：距离下一路径点更近的一方优先
            d1 = math.hypot(
                self.robot_paths[r1][0][0] - self.robot_positions[r1][0],
                self.robot_paths[r1][0][1] - self.robot_positions[r1][1]
            )
            d2 = math.hypot(
                self.robot_paths[r2][0][0] - self.robot_positions[r2][0],
                self.robot_paths[r2][0][1] - self.robot_positions[r2][1]
            )
            if d1 < d2 * 0.8:
                return False
            if d2 < d1 * 0.8:
                return True
            return winner != 'me'

        elif ctype in ('perpendicular', 'diagonal'):
            return winner != 'me'

        elif ctype == 'following':
            # 我在后面（对方在前），我减速让路
            return rel_pos == 'front' and winner != 'me'

        return winner != 'me'

    def is_position_safe_for_yield(self, rid, target_pos, min_dist=0.42):
        """
        @brief 检查让路目标点是否安全（边界、障碍、邻车距离）

        @param rid:        机器人编号
        @param target_pos: 目标坐标 (x, y)
        @param min_dist:   与其他机器人最小安全间距
        @return: True 表示可用于让路
        """
        if rid not in self.robot_positions:
            return False

        if not self.path_planner.is_valid(target_pos[0], target_pos[1], ignore_robot_id=rid):
            return False

        for oid, opos in self.robot_positions.items():
            if oid == rid:
                continue
            if math.hypot(target_pos[0] - opos[0], target_pos[1] - opos[1]) < min_dist:
                return False
        return True

    def try_plan_safe_yield_path(
        self,
        rid,
        avoid_rid=None,
        hold_seconds=4.0,
        lateral_offsets=None,
        backward_offsets=None,
    ):
        """
        @brief 为让路方生成安全让路路径（优先侧移，次选后移）

        @param rid:       让路方机器人 ID
        @param avoid_rid: 对向机器人 ID（可选）
        @return: 安全路径列表，失败返回 []
        """
        if rid not in self.robot_positions:
            return []

        curr = self.robot_positions[rid]
        yaw = self.robot_orientations.get(rid, 0.0)

        if lateral_offsets is None:
            lateral_offsets = [0.40]
        if backward_offsets is None:
            backward_offsets = [0.45]

        candidates = []
        for off in lateral_offsets:
            candidates.append((curr[0] - off * math.sin(yaw), curr[1] + off * math.cos(yaw)))
            candidates.append((curr[0] + off * math.sin(yaw), curr[1] - off * math.cos(yaw)))
        for off in backward_offsets:
            candidates.append((curr[0] - off * math.cos(yaw), curr[1] - off * math.sin(yaw)))

        for target in candidates:
            if not self.is_position_safe_for_yield(rid, target):
                continue

            path = self.path_planner.plan_path(curr, target, robot_id=rid, priority=100)
            if path and len(path) >= 2:
                smoothed = self.path_planner.smooth_path(path)
                if smoothed and len(smoothed) >= 2:
                    if avoid_rid is not None:
                        self.robot_yielding[rid] = (avoid_rid, time.time() + hold_seconds)
                    return smoothed

        return []

    def _plan_escape_path(self, rid, other_id, distance_candidates, side_candidates, min_dist=0.35):
        """为机器人规划远离 other_id 的临时脱困路径。"""
        if rid not in self.robot_positions or other_id not in self.robot_positions:
            return []

        curr = self.robot_positions[rid]
        other = self.robot_positions[other_id]
        vx = curr[0] - other[0]
        vy = curr[1] - other[1]
        norm = math.hypot(vx, vy)
        if norm < 1e-6:
            yaw = self.robot_orientations.get(rid, 0.0)
            vx, vy = math.cos(yaw), math.sin(yaw)
            norm = 1.0
        ux, uy = vx / norm, vy / norm
        px, py = -uy, ux

        for dist in distance_candidates:
            for side in side_candidates:
                tx = curr[0] + ux * dist + px * side
                ty = curr[1] + uy * dist + py * side
                target = (tx, ty)
                if not self.is_position_safe_for_yield(rid, target, min_dist=min_dist):
                    continue
                path = self.path_planner.plan_path(curr, target, robot_id=rid, priority=120)
                if path and len(path) >= 2:
                    smooth = self.path_planner.smooth_path(path)
                    if smooth and len(smooth) >= 2:
                        return smooth
        return []

    def activate_yield_path(self, rid, target_id, path, hold_until):
        """激活让路路径；空闲车进入 YIELDING，使主循环会实际导航它。"""
        self.robot_paths[rid] = path
        self.robot_yielding[rid] = (target_id, hold_until)

        task = self.robot_current_task.get(rid)
        if task and task.status in ("assigned", "delivering"):
            self.robot_status[rid] = RobotStatus.MOVING
            return

        if not task and self.robot_status.get(rid) in (RobotStatus.IDLE, RobotStatus.YIELDING):
            self.robot_status[rid] = RobotStatus.YIELDING

    def try_force_pair_separation(self, r1, r2, retry_count=1):
        """对死锁pair执行双机主动分离，成功返回 True。"""
        if r1 not in self.robot_positions or r2 not in self.robot_positions:
            return False

        key = self._pair_key(r1, r2)
        now = time.time()
        hold = min(14.0, self.pair_separation_hold_sec + 1.0 * max(0, retry_count - 1))
        dists = [0.65, 0.90, 1.15]
        sides = [0.0, 0.35, -0.35, 0.55, -0.55]

        p1 = self._plan_escape_path(r1, r2, dists, sides, min_dist=0.32)
        p2 = self._plan_escape_path(r2, r1, dists, sides, min_dist=0.32)

        if not p1 and not p2:
            return False

        if p1:
            self.activate_yield_path(r1, r2, p1, now + hold)
        if p2:
            self.activate_yield_path(r2, r1, p2, now + hold)

        self.clear_spacetime_reservation(r1)
        self.clear_spacetime_reservation(r2)
        self.pair_separation_active[key] = now + hold
        self.deadlock_being_resolved[key] = max(self.deadlock_being_resolved.get(key, 0.0), now + hold + 2.0)
        self.pair_forced_separation_count_total += 1
        self.deadlock_resolution_action_timestamps.append(now)
        self.collision_intervention_timestamps.append(now)
        self.recovery_success_timestamps.append(now)
        rospy.logwarn(
            f"🧯 Pair separation: R{r1}<->R{r2}, retry={retry_count}, "
            f"path1={'Y' if bool(p1) else 'N'}, path2={'Y' if bool(p2) else 'N'}"
        )
        return True

    def trigger_pair_emergency_break(self, r1, r2, hold_sec=2.5):
        """高重试兜底：双机短时刹停，清空预约并等待重新规划。"""
        now = time.time()
        key = self._pair_key(r1, r2)

        self.stop_robot(r1)
        self.stop_robot(r2)
        self.robot_paths[r1] = []
        self.robot_paths[r2] = []
        self.robot_yielding[r1] = (r2, now + hold_sec)
        self.robot_yielding[r2] = (r1, now + hold_sec)

        self.clear_spacetime_reservation(r1)
        self.clear_spacetime_reservation(r2)
        self.pair_separation_active[key] = now + hold_sec
        self.deadlock_being_resolved[key] = max(
            self.deadlock_being_resolved.get(key, 0.0),
            now + hold_sec + 2.0
        )
        self.pair_emergency_break_count_total += 1
        self.deadlock_resolution_action_timestamps.append(now)
        self.collision_intervention_timestamps.append(now)
        self.recovery_success_timestamps.append(now)
        rospy.logwarn(f"🛑 Emergency break pair: R{r1}<->R{r2}, hold={hold_sec:.1f}s")

    def execute_yield_action(self, r1, r2):
        """
        @brief 执行让路动作：低速后退 + 清空路径

        @param r1: 让路方机器人 ID
        @param r2: 优先方机器人 ID
        """
        now = time.time()
        last_peer = self.robot_last_yield_peer.get(r1)
        last_time = self.robot_last_yield_time.get(r1, 0.0)
        if last_peer == r2 and now - last_time <= self.yield_repeat_window:
            self.robot_consecutive_yield_count[r1] += 1
        else:
            self.robot_consecutive_yield_count[r1] = 1
        self.robot_last_yield_peer[r1] = r2
        self.robot_last_yield_time[r1] = now

        key = self._pair_key(r1, r2)
        self.yield_pair_cooldown[key] = now + self.yield_pair_cooldown_sec

        # 同一机器人连续对同一对象让路过多，升级为死锁级处理
        if self.robot_consecutive_yield_count[r1] >= self.max_consecutive_yield_same_peer:
            rospy.logwarn(
                f"🚨 Escalate repeated yield: R{r1} -> R{r2}, "
                f"count={self.robot_consecutive_yield_count[r1]}"
            )
            self.force_global_deadlock_resolution(
                r1, r2, retry_count=self.robot_consecutive_yield_count[r1]
            )
            return

        safe_path = []
        if self.enable_progressive_recovery:
            safe_path = self.try_plan_safe_yield_path(r1, avoid_rid=r2, hold_seconds=4.0)
        if safe_path:
            self.activate_yield_path(r1, r2, safe_path, time.time() + 4.0)
            self.robot_yield_count[r1] += 1
            self.yield_count_total += 1
            self.collision_intervention_timestamps.append(time.time())
            rospy.loginfo(f"🚦 R{r1} yields to R{r2}. Safe sidestep planned.")
            return

        # 普通让路失败，升级为双机主动分离
        if self.enable_progressive_recovery and self.try_force_pair_separation(r1, r2, retry_count=self.robot_consecutive_yield_count[r1]):
            return

        self.stop_robot(r1)
        self.robot_yielding[r1] = (r2, time.time() + 3.0)
        self.robot_yield_count[r1] += 1
        self.yield_count_total += 1
        self.collision_intervention_timestamps.append(time.time())
        self.robot_paths[r1] = []
        self.yield_fallback_count_total += 1
        self.deadlock_resolution_action_timestamps.append(time.time())
        self.recovery_success_timestamps.append(time.time())
        rospy.logwarn(f"🚦 R{r1} yield fallback: hold position for safety.")

    def is_robot_yielding(self, rid):
        """
        @brief 检查机器人是否处于让路冷却中

        让路超时后自动恢复路径规划。

        @param rid: 机器人编号
        @return: (is_yielding, can_move) 二元组
        """
        if rid not in self.robot_yielding:
            return False, True

        target, until = self.robot_yielding[rid]

        if time.time() >= until:
            # 让路结束，重新规划路径
            del self.robot_yielding[rid]
            task = self.robot_current_task.get(rid)
            if task and self.robot_status.get(rid) == RobotStatus.MOVING:
                tgt = task.source if task.status == "assigned" else task.destination
                if rid in self.robot_positions:
                    p = self.path_planner.plan_path(
                        self.robot_positions[rid], tgt,
                        robot_id=rid, priority=task.priority
                    )
                    if p and len(p) >= 2:
                        self.robot_paths[rid] = self.path_planner.smooth_path(p)
                    else:
                        self.robot_paths[rid] = []
                        self.stop_robot(rid)
                        self.send_notification('warning', f'机器人 {rid} 让路结束后重规划失败，等待重试')
            return False, True
        else:
            # 仍在让路窗口：若存在让路路径则允许执行移动，否则保持等待
            has_yield_path = bool(self.robot_paths.get(rid))
            return True, has_yield_path

    def pop_assignable_task(self, attempted_task_ids, now):
        """
        @brief 从队列中取出当前周期可尝试分配的任务

        队列末尾常出现“待办任务少、空闲机器人多”的状态。若同一任务在
        一个 10Hz 周期内被多台空闲机器人连续重试，临时路径拥堵会被快速
        放大成永久拒绝。这里跳过本周期已尝试和处于 backoff 的任务。
        """
        scan_count = len(self.pending_tasks)
        deferred = []

        for _ in range(scan_count):
            task = self.pending_tasks.popleft()
            if task.id in attempted_task_ids:
                deferred.append(task)
                continue

            next_time = getattr(task, 'next_assign_attempt_time', 0.0)
            if now < next_time:
                deferred.append(task)
                continue

            for item in reversed(deferred):
                self.pending_tasks.appendleft(item)
            return task

        for item in reversed(deferred):
            self.pending_tasks.appendleft(item)
        return None

    def get_assignment_retry_backoff(self, fail_count):
        """根据连续失败次数计算下一次分配尝试的退避时间。"""
        base = max(0.0, self.assignment_retry_backoff_base)
        max_backoff = max(0.0, self.assignment_retry_backoff_max)
        if base <= 0.0 or max_backoff <= 0.0:
            return 0.0

        level = 1 + min(7, max(0, fail_count - 1) // max(1, self.num_robots))
        return min(max_backoff, base * level)

    def record_assignment_failure(self, task, rid):
        """
        @brief 记录一次任务分配失败

        默认策略是不永久拒绝实验任务，避免最后几个任务因临时拥堵被统计为
        terminal/rejected。若确实需要旧行为，可设置 ALLOW_ASSIGNMENT_REJECTION=1。
        """
        now = time.time()
        self.assignment_reject_attempts_total += 1
        task.assign_fail_count += 1
        task.last_assign_attempt_time = now
        task.last_assign_attempt_robot = rid
        task.next_assign_attempt_time = now + self.get_assignment_retry_backoff(task.assign_fail_count)

        if self.allow_assignment_rejection and task.assign_fail_count > self.max_assignment_fail_retries:
            task.status = "rejected"
            task.completion_time = now
            self.rejected_task_count_total += 1
            self.send_notification(
                'warning',
                f'任务 {task.id} 多次分配失败，已拒绝（fail={task.assign_fail_count}）'
            )
            return True

        if (
            not self.allow_assignment_rejection
            and task.assign_fail_count == self.max_assignment_fail_retries + 1
        ):
            self.send_notification(
                'warning',
                f'任务 {task.id} 分配连续失败，将继续重试而不计入 rejected'
            )
        return False
    
    # ============================================================
    #  任务生成与分配
    # ============================================================

    def generate_tasks(self, mode='baseline'):
        """
        @brief 根据实验模式生成搬运任务队列

        支持四级压力模式（全部使用同一工厂场景，仅任务强度不同）：
        - minimal: 最简测试（19 个任务）
        - quick:   快速测试（40 个任务）
        - baseline: 基础测试（79 个任务）
        - stress:  压力测试（316 个任务）

        兼容模式别名：
        - monitor / s2_core / s2_congestion / s2_peak -> stress
        - baseline2 / s2_realtime -> baseline

        @param mode: 实验模式字符串
        """
        tid = 0
        mode_key = (mode or 'baseline').strip().lower()

        def add(type_enum, src_key, dst_key, prio, count):
            """辅助函数：批量创建同类型任务"""
            nonlocal tid
            srcs = self.locations[src_key]
            dsts = self.locations[dst_key]
            for i in range(count):
                self.pending_tasks.append(
                    Task(tid, type_enum, srcs[0], dsts[i % len(dsts)], prio)
                )
                tid += 1

        if mode_key == 'minimal':
            # 最简测试：19 个任务
            self.task_type_targets = {
                'empty_to_carding': 8,
                'green_to_drawing1': 8,
                'yellow_to_drawing2': 2,
                'red_to_completed': 1,
            }
        elif mode_key == 'quick':
            # 快速测试：40 个任务
            self.task_type_targets = {
                'empty_to_carding': 18,
                'green_to_drawing1': 18,
                'yellow_to_drawing2': 3,
                'red_to_completed': 1,
            }
        elif mode_key in ('baseline', 'baseline2', 's2_realtime'):
            # 基础测试：79 个任务
            self.task_type_targets = {
                'empty_to_carding': 36,
                'green_to_drawing1': 36,
                'yellow_to_drawing2': 6,
                'red_to_completed': 1,
            }
        elif mode_key in ('stress', 'stress2', 'monitor', 's2_core', 's2_congestion', 's2_peak'):
            # 压力测试：316 个任务
            self.task_type_targets = {
                'empty_to_carding': 144,
                'green_to_drawing1': 144,
                'yellow_to_drawing2': 24,
                'red_to_completed': 4,
            }
        else:
            # 未知模式兜底：基础测试（79）
            self.task_type_targets = {
                'empty_to_carding': 36,
                'green_to_drawing1': 36,
                'yellow_to_drawing2': 6,
                'red_to_completed': 1,
            }

        add(TaskType.EMPTY_TO_CARDING,    'empty_storage',  'carding_waiting',  65, self.task_type_targets['empty_to_carding'])
        add(TaskType.GREEN_TO_DRAWING1,   'green_storage',  'drawing1_waiting', 65, self.task_type_targets['green_to_drawing1'])
        add(TaskType.YELLOW_TO_DRAWING2,  'yellow_storage', 'drawing2_waiting', 75, self.task_type_targets['yellow_to_drawing2'])
        add(TaskType.RED_TO_COMPLETED,    'red_storage',    'completed',       100, self.task_type_targets['red_to_completed'])

        self.total_tasks = tid
        rospy.loginfo(f"📋 Generated {self.total_tasks} tasks for mode: {mode_key}")

    def assign_tasks(self):
        """
        @brief 将待办任务分配给空闲机器人

        仅在实验已启动时执行。对每台空闲机器人：
        1. 从队列取出一个任务
        2. 对源地点做区域分散优化
        3. 规划路径（优先使用区域避让版本）
        4. 激活任务并切换机器人为 MOVING 状态
        """
        if not self.experiment_started:
            return  # 等待实验启动

        idle = [
            i for i in range(self.num_robots)
            if self.robot_status[i] == RobotStatus.IDLE and i in self.robot_positions
        ]
        if not idle or not self.pending_tasks:
            return

        attempted_task_ids = set()
        for rid in idle:
            if not self.pending_tasks:
                break
            task = self.pop_assignable_task(attempted_task_ids, time.time())
            if not task:
                break
            attempted_task_ids.add(task.id)

            # 分散目标点优化：避免多台机器人扎堆
            goal = task.source
            reg = self.get_region_name_for_position(goal)
            if reg:
                new_goal = self.find_dispersed_goal_in_region(reg, goal)
                if new_goal != goal:
                    task.source = new_goal
                    goal = new_goal

            # 规划路径：优先使用区域避让版本
            path = self.plan_path_avoiding_region_robots(
                rid, self.robot_positions[rid], goal
            )
            if not path or len(path) < 2:
                # 备用：标准 A* 规划
                path = self.path_planner.plan_path(
                    self.robot_positions[rid], goal,
                    robot_id=rid, priority=task.priority
                )

            if not path or len(path) < 2:
                # 规划失败，任务放回队列
                rejected = self.record_assignment_failure(task, rid)
                if not rejected:
                    task.status = "pending"
                    self.pending_tasks.append(task)
                continue

            # 激活任务
            self.robot_paths[rid] = self.path_planner.smooth_path(path)
            task.assigned_robot = rid
            task.status = "assigned"
            task.start_time = time.time()
            task.assign_fail_count = 0
            task.next_assign_attempt_time = 0.0
            task.last_assign_attempt_robot = rid
            self.robot_current_task[rid] = task
            self.robot_status[rid] = RobotStatus.MOVING
            self.active_tasks[rid] = task
            rospy.loginfo(f"✅ Task {task.id} -> Robot {rid}")
    
    # ============================================================
    #  实验控制
    # ============================================================

    def handle_experiment_control(self, msg):
        """
        @brief 处理来自 Dashboard 的实验控制命令

        支持三种命令：
        - start: 按指定模式启动实验、生成任务
        - stop:  停止实验并停止所有机器人
        - reset: 重置调度器为初始状态

        @param msg: ROS String 消息（JSON 格式）
        """
        try:
            data = json.loads(msg.data)
            command = data.get('command')

            if command == 'start':
                mode = data.get('mode', 'baseline')
                if not self.experiment_started:
                    rospy.loginfo(f"🚀 Starting experiment - Mode: {mode}")
                    self.experiment_mode = mode
                    self.experiment_started = True
                    self.system_start_time = time.time()
                    self.reset_robustness_trackers()

                    # 按模式生成任务
                    self.generate_tasks(mode)

                    self.send_notification(
                        'success',
                        f'实验已启动 - {mode}模式 - {self.total_tasks}个任务'
                    )
                else:
                    rospy.logwarn("Experiment already started")

            elif command == 'stop':
                if self.experiment_started:
                    rospy.loginfo("⏹️ Stopping experiment...")
                    self.experiment_started = False
                    for rid in range(self.num_robots):
                        self.stop_robot(rid)
                    self.send_notification('warning', '实验已停止')

            elif command == 'reset':
                rospy.loginfo("🔄 Resetting scheduler...")
                self.experiment_started = False
                self.pending_tasks.clear()
                self.active_tasks.clear()
                self.completed_tasks.clear()
                self.total_tasks = 0
                self.task_type_targets = {
                    'empty_to_carding': 0,
                    'green_to_drawing1': 0,
                    'yellow_to_drawing2': 0,
                    'red_to_completed': 0,
                }

                # 重置运行期指标
                self.deadlock_count_total = 0
                self.yield_count_total = 0
                self.recovery_count_total = 0
                self.collision_event_count = 0
                self.starvation_prevent_count_total = 0
                self.yield_fallback_count_total = 0
                self.pair_forced_separation_count_total = 0
                self.pair_emergency_break_count_total = 0
                self.assignment_reject_attempts_total = 0
                self.rejected_task_count_total = 0
                self.task_completion_time_sum = 0.0
                self.total_travel_distance = 0.0
                self.robot_last_position.clear()
                self.computation_time_total = 0.0
                self.computation_time_max = 0.0
                self.computation_cycle_count = 0
                self.computation_cycle_lt_100ms_count = 0
                self.computation_cycle_timestamps.clear()
                self.notification_count_total = 0
                self.command_result_count_total = 0
                self.task_stats_publish_count_total = 0
                self.robot_status_publish_count_total = 0
                self.deadlock_event_timestamps.clear()
                self.deadlock_resolution_action_timestamps.clear()
                self.collision_event_timestamps.clear()
                self.collision_intervention_timestamps.clear()
                self.reset_robustness_trackers()
                self.robot_yield_count.clear()
                self.robot_pair_stuck_history.clear()
                self.deadlock_being_resolved.clear()
                self.deadlock_pair_retry_count.clear()
                self.deadlock_pair_last_time.clear()
                self.pair_separation_active.clear()
                self.yield_pair_cooldown.clear()
                self.robot_yielding.clear()
                self.spacetime_reservations.clear()
                self.arrival_crowded_cooldown.clear()
                self.arrival_crowded_retry.clear()
                self.robot_last_stall_replan_time.clear()
                self.robot_last_yield_peer.clear()
                self.robot_last_yield_time.clear()
                self.robot_consecutive_yield_count.clear()
                self.corridor_tokens.clear()
                self.corridor_token_grant_count_total = 0
                self.corridor_token_reuse_count_total = 0
                self.corridor_token_release_count_total = 0
                self.corridor_last_log_time.clear()

                for rid in range(self.num_robots):
                    self.robot_status[rid] = RobotStatus.IDLE
                    self.robot_current_task[rid] = None
                    self.robot_collision_active[rid] = False
                    self.stop_robot(rid)
                self.send_notification('info', '调度器已重置')

        except Exception as e:
            rospy.logerr(f"Failed to handle experiment control: {e}")
    # ============================================================
    #  路径导航与到达处理
    # ============================================================

    def navigate_along_path(self, rid):
        """
        @brief 沿路径逐点导航

        依次检查：人工模式等待、暂停状态、路径为空（到达判定）、
        让路冷却、时空冲突，最后对下一路径点执行导航。

        @param rid: 机器人编号
        """
        # 人工模式等待检查
        if self.robot_status[rid] == RobotStatus.MANUAL:
            info = self.manual_task_info.get(rid)
            if info and info['is_waiting']:
                return

        # 暂停状态：完全跳过导航和到达判定
        if self.robot_status[rid] == RobotStatus.PAUSED:
            self.clear_spacetime_reservation(rid)
            return

        # 让路状态检查（有让路路径则允许继续移动，无路径则等待）
        is_yield, can_move = self.is_robot_yielding(rid)
        yielding_mode = is_yield and can_move
        if is_yield and not can_move:
            self.clear_spacetime_reservation(rid)
            return

        # 路径为空 → 判定到达
        if not self.robot_paths.get(rid):
            self.clear_spacetime_reservation(rid)
            task = self.robot_current_task.get(rid)
            if not task:
                # 自愈：无任务时不应长期停留在非空闲状态
                if self.robot_status.get(rid) != RobotStatus.IDLE:
                    self.stop_robot(rid)
                    self.robot_status[rid] = RobotStatus.IDLE
                return
            if task and self.robot_status[rid] == RobotStatus.MOVING:
                # 空路径不等于已到达：先验证是否接近目标点，否则执行重规划
                target = None
                if task.status == "assigned":
                    target = task.source
                elif task.status == "delivering":
                    target = task.destination

                if target and rid in self.robot_positions:
                    d_tgt = math.hypot(
                        target[0] - self.robot_positions[rid][0],
                        target[1] - self.robot_positions[rid][1]
                    )
                    if d_tgt <= 0.45:
                        self.handle_arrival(rid)
                    else:
                        repath = self.path_planner.plan_path(
                            self.robot_positions[rid],
                            target,
                            robot_id=rid,
                            priority=task.priority
                        )
                        if repath and len(repath) >= 2:
                            smooth = self.path_planner.smooth_path(repath)
                            self.robot_paths[rid] = smooth if smooth else repath
                        else:
                            self.stop_robot(rid)
            return

        # 清除保护标记
        if rid in self.robot_protected:
            self.robot_protected.remove(rid)

        # 时空预约与冲突检测（让路执行阶段不触发新的让路判定，避免振荡）
        if not yielding_mode:
            self.reserve_spacetime(rid, self.robot_paths[rid])
            confl, other = self.check_spacetime_conflict(rid)
            if confl and other is not None:
                pkey = self._pair_key(rid, other)
                if time.time() < self.pair_separation_active.get(pkey, 0.0):
                    confl = False
            if confl and other is not None and self.is_yielding_to(other, rid):
                confl = False
            if confl and other is not None:
                pair_key = self._pair_key(rid, other)
                if time.time() < self.yield_pair_cooldown.get(pair_key, 0.0):
                    confl = False
            if confl and self.resolve_conflict_by_priority(rid, other):
                self.execute_yield_action(rid, other)
                return

        # 逐点前进（非递归，避免 path 变化导致越界）
        if rid not in self.robot_positions:
            return

        path = self.robot_paths.get(rid)
        if not path:
            task = self.robot_current_task.get(rid)
            if task and self.robot_status[rid] == RobotStatus.MOVING:
                self.handle_arrival(rid)
            return

        # 连续弹出已到达的近点，直到遇到下一个有效目标
        while path:
            next_pt = path[0]
            dist_to_next = math.hypot(
                next_pt[0] - self.robot_positions[rid][0],
                next_pt[1] - self.robot_positions[rid][1]
            )
            if dist_to_next >= 0.4:
                break
            path.pop(0)

        if not path:
            self.handle_arrival(rid)
            return

        self.send_navigation_goal(rid, path[0])

    def cleanup_runtime_navigation_states(self):
        """清理非导航状态下的陈旧预约与让路状态。"""
        now = time.time()
        for rid in range(self.num_robots):
            status = self.robot_status.get(rid)
            if status not in [RobotStatus.MOVING, RobotStatus.MANUAL, RobotStatus.YIELDING]:
                self.clear_spacetime_reservation(rid)

            yi = self.robot_yielding.get(rid)
            if yi:
                _, until = yi
                if now >= until and (not self.robot_paths.get(rid)):
                    self.robot_yielding.pop(rid, None)

    def handle_arrival(self, rid):
        """
        @brief 到达目的地后的处理逻辑

        先做拥挤安全检查：若周围太密集则尝试分散或后退。
        安全后切换状态：assigned→loading→delivery，delivering→unloading→complete。

        @param rid: 机器人编号
        """
        task = self.robot_current_task.get(rid)
        if not task:
            self.stop_robot(rid)
            self.robot_status[rid] = RobotStatus.IDLE
            return

        # 拥挤安全检查
        curr = self.robot_positions[rid]
        closest, min_d = self.get_closest_robot(rid)

        if min_d < 0.35:
            now = time.time()
            if now < self.arrival_crowded_cooldown.get(rid, 0.0):
                self.stop_robot(rid)
                return

            self.arrival_crowded_retry[rid] += 1
            self.arrival_crowded_cooldown[rid] = now + 1.8
            rospy.logwarn(f"⚠️ R{rid} arrived but crowded ({min_d:.2f}m). Relocating...")

            # 多次重试后，优先执行更激进的脱困让路轨迹
            if self.arrival_crowded_retry[rid] >= 4:
                nearest = None
                nearest_d = 99.0
                for oid, opos in self.robot_positions.items():
                    if oid == rid:
                        continue
                    d = math.hypot(curr[0] - opos[0], curr[1] - opos[1])
                    if d < nearest_d:
                        nearest_d = d
                        nearest = oid

                escape = self.try_plan_safe_yield_path(
                    rid,
                    avoid_rid=nearest,
                    hold_seconds=6.0,
                    lateral_offsets=[0.55, 0.80],
                    backward_offsets=[0.65, 0.90],
                )
                if escape:
                    self.robot_paths[rid] = escape
                    return

            # 尝试分散到附近空闲位置
            reg = self.get_region_name_for_position(
                task.source if task.status == "assigned" else task.destination
            )
            if reg:
                tgt = task.source if task.status == "assigned" else task.destination
                new_pt = self.find_dispersed_goal_in_region(reg, tgt)
                if math.hypot(new_pt[0] - curr[0], new_pt[1] - curr[1]) > 0.3:
                    p = self.plan_path_avoiding_region_robots(rid, curr, new_pt)
                    if p:
                        self.robot_paths[rid] = self.path_planner.smooth_path(p)
                        if task.status == "assigned":
                            task.source = new_pt
                        else:
                            task.destination = new_pt
                        return

            # 无法分散时按相对方位脱困，避免尾对尾时盲目倒车互撞
            cmd = self.build_emergency_escape_command(rid, closest)
            self.cmd_vel_pubs[rid].publish(cmd)
            rospy.sleep(1.0)
            self.stop_robot(rid)
            self.robot_paths[rid] = []
            return

        # 状态切换
        self.arrival_crowded_retry[rid] = 0
        if rid in self.arrival_crowded_cooldown:
            del self.arrival_crowded_cooldown[rid]
        self.stop_robot(rid)
        if task.status == "assigned":
            task.status = "loading"
            self.robot_status[rid] = RobotStatus.LOADING
            task_id = task.id
            rospy.Timer(
                rospy.Duration(1.5),
                lambda e, robot_id=rid, expected_task_id=task_id: self.start_delivery(
                    robot_id,
                    expected_task_id=expected_task_id
                ), oneshot=True
            )
        elif task.status == "delivering":
            task.status = "unloading"
            self.robot_status[rid] = RobotStatus.UNLOADING
            task_id = task.id
            rospy.Timer(
                rospy.Duration(1.5),
                lambda e, robot_id=rid, expected_task_id=task_id: self.complete_task(
                    robot_id,
                    expected_task_id=expected_task_id
                ), oneshot=True
            )

    # ============================================================
    #  任务状态流转
    # ============================================================

    def get_timer_bound_task(self, rid, expected_task_id, expected_status, action_name):
        """
        @brief 获取定时器绑定的当前任务，过滤过期回调

        装载/卸载使用 rospy.Timer 延迟触发。若期间机器人被恢复、
        人工接管或重新分配，仅凭 rid 会误操作新任务，因此必须同时
        校验任务 ID、任务状态和 active_tasks 绑定关系。
        """
        task = self.robot_current_task.get(rid)
        if not task:
            rospy.logwarn(f"⚠️ Ignore stale {action_name} timer for R{rid}: no current task")
            return None

        if expected_task_id is not None and task.id != expected_task_id:
            rospy.logwarn(
                f"⚠️ Ignore stale {action_name} timer for R{rid}: "
                f"expected Task {expected_task_id}, current Task {task.id}"
            )
            return None

        if task.status != expected_status:
            rospy.logwarn(
                f"⚠️ Ignore stale {action_name} timer for R{rid}: "
                f"Task {task.id} status={task.status}, expected={expected_status}"
            )
            return None

        if self.active_tasks.get(rid) is not task:
            rospy.logwarn(
                f"⚠️ Ignore stale {action_name} timer for R{rid}: "
                f"Task {task.id} is no longer active"
            )
            return None

        return task

    def start_delivery(self, rid, expected_task_id=None):
        """
        @brief 装载完成后开始送货阶段

        规划从当前位置到任务目的地的路径。

        @param rid: 机器人编号
        @param expected_task_id: Timer 创建时绑定的任务 ID，用于忽略过期回调
        """
        task = self.get_timer_bound_task(
            rid,
            expected_task_id,
            expected_status="loading",
            action_name="start_delivery"
        )
        if not task:
            return

        task.status = "delivering"
        self.robot_status[rid] = RobotStatus.MOVING

        p = self.path_planner.plan_path(
            self.robot_positions[rid], task.destination,
            robot_id=rid, priority=task.priority
        )
        if p and len(p) >= 2:
            self.robot_paths[rid] = self.path_planner.smooth_path(p)
        else:
            self.robot_paths[rid] = []
            self.robot_status[rid] = RobotStatus.MOVING
            self.send_notification('warning', f'机器人 {rid} 送货路径规划失败，等待下一周期重试')
        rospy.loginfo(f"🚚 R{rid} delivering Task {task.id}")

    def complete_task(self, rid, expected_task_id=None):
        """
        @brief 卸货完成，标记任务为 completed 并释放机器人

        更新统计计数、清空状态、发布最新统计数据。

        @param rid: 机器人编号
        @param expected_task_id: Timer 创建时绑定的任务 ID，用于忽略过期回调
        """
        task = self.get_timer_bound_task(
            rid,
            expected_task_id,
            expected_status="unloading",
            action_name="complete_task"
        )
        if not task:
            return

        task.status = "completed"
        task.completion_time = time.time()
        self.task_completion_counts[task.type.value] += 1
        self.completed_tasks.append(task)
        elapsed = 0.0
        if task.start_time is not None and task.completion_time is not None:
            elapsed = max(0.0, task.completion_time - task.start_time)
            self.task_completion_time_sum += elapsed

        rospy.loginfo(
            f"🏁 R{rid} finished Task {task.id}. "
            f"Time: {elapsed:.1f}s"
        )

        # 释放机器人
        self.robot_current_task[rid] = None
        self.robot_status[rid] = RobotStatus.IDLE
        self.robot_paths[rid] = []
        if rid in self.active_tasks:
            del self.active_tasks[rid]
        self.stop_robot(rid)
        self.publish_statistics()

    def stop_robot(self, rid):
        """
        @brief 发布零速指令使机器人立即停止

        @param rid: 机器人编号
        """
        self.cmd_vel_pubs[rid].publish(Twist())

    # ============================================================
    #  统计发布与通知
    # ============================================================

    def publish_statistics(self):
        """
        @brief 发布详细统计数据到 ROS Topic 供前端展示

        包含：总任务数、待办/进行中/已完成计数、平均时间、
        吞吐率、各类型完成计数、活跃任务详情、机器人状态。
        """
        # 构建活跃任务列表
        act = []
        for r, t in self.active_tasks.items():
            loc = "Moving"
            if self.robot_status[r] == RobotStatus.LOADING:
                loc = "Loading"
            elif self.robot_status[r] == RobotStatus.UNLOADING:
                loc = "Unloading"
            act.append({
                'robot_id': r, 'task_id': t.id,
                'type': t.type.value, 'status': t.status,
                'priority': t.priority, 'progress': loc
            })

        # 待办任务预览（前 5 条）
        pend = [
            {'task_id': t.id, 'type': t.type.value, 'priority': t.priority}
            for i, t in enumerate(self.pending_tasks) if i < 5
        ]

        # 统计指标
        elapsed_time = time.time() - self.system_start_time
        makespan = elapsed_time
        completed_count = len(self.completed_tasks)
        rejected_count = int(self.rejected_task_count_total)
        terminal_count = completed_count + rejected_count
        completion_rate = (
            (completed_count / self.total_tasks * 100.0)
            if self.total_tasks > 0 else 0
        )
        terminal_completion_rate = (
            (terminal_count / self.total_tasks * 100.0)
            if self.total_tasks > 0 else 0
        )
        task_completion_rate = completion_rate
        throughput_per_min = (
            (completed_count / (elapsed_time / 60.0))
            if elapsed_time > 0 else 0
        )
        total_completion_time = self.task_completion_time_sum
        avg_task_time = (
            (total_completion_time / len(self.completed_tasks))
            if self.completed_tasks else 0
        )

        tasks_by_robot = [0 for _ in range(self.num_robots)]
        for task in self.completed_tasks:
            if task.assigned_robot is not None and 0 <= task.assigned_robot < self.num_robots:
                tasks_by_robot[task.assigned_robot] += 1

        mean_load = (sum(tasks_by_robot) / self.num_robots) if self.num_robots > 0 else 0.0
        load_variance = (
            sum((value - mean_load) ** 2 for value in tasks_by_robot) / self.num_robots
            if self.num_robots > 0 else 0.0
        )
        load_balance_std = math.sqrt(load_variance)

        sorted_loads = sorted(tasks_by_robot)
        if sum(sorted_loads) > 0 and self.num_robots > 0:
            weighted_sum = 0.0
            for index, value in enumerate(sorted_loads, start=1):
                weighted_sum += index * value
            load_balance_gini = (
                (2.0 * weighted_sum) / (self.num_robots * sum(sorted_loads))
                - (self.num_robots + 1.0) / self.num_robots
            )
        else:
            load_balance_gini = 0.0

        deadlock_resolution_actions_total = len(self.deadlock_resolution_action_timestamps)
        if self.deadlock_count_total > 0:
            deadlock_resolved_count = min(self.deadlock_count_total, deadlock_resolution_actions_total)
            deadlock_resolution_ratio = deadlock_resolved_count / float(self.deadlock_count_total)
        else:
            deadlock_resolution_ratio = 1.0

        # 发布任务统计 Topic
        msg = String()
        robot_status_map = {
            str(i): self.robot_status[i].value for i in range(self.num_robots)
        }
        robot_control_state_map = {
            str(i): self.get_robot_display_state(i) for i in range(self.num_robots)
        }
        robot_flip_state_map = {
            str(i): self.robot_flip_state.get(i, 'normal') for i in range(self.num_robots)
        }
        msg.data = json.dumps({
            'timestamp':              time.time(),
            'test_id':               self.test_id,
            'experiment_mode':        self.experiment_mode or 'unknown',
            'algorithm_mode':         self.algorithm_mode_label,
            'algorithm_mode_canonical': self.algorithm_mode,
            'algorithm_family':       self.algorithm_family,
            'ablation_mode':          self.ablation_mode,
            'ablation_applied':       bool(self.ablation_applied),
            'total_tasks':            self.total_tasks,
            'pending_tasks':          len(self.pending_tasks),
            'in_progress_tasks':      len(self.active_tasks),
            'active_tasks':           len(self.active_tasks),
            'completed_tasks':        completed_count,
            'rejected_tasks':         rejected_count,
            'terminal_tasks':         terminal_count,
            'elapsed_time':           elapsed_time,
            'completion_rate':        completion_rate,
            'task_completion_rate':   task_completion_rate,
            'task_completion_rate_pct': task_completion_rate,
            'terminal_completion_rate_pct': terminal_completion_rate,
            'throughput_per_min':     throughput_per_min,
            'avg_task_time':          avg_task_time,
            'makespan':               makespan,
            'deadlock_resolution_ratio': deadlock_resolution_ratio,
            'total_travel_distance':  self.total_travel_distance,
            'load_balance_gini':      load_balance_gini,
            'tasks_completed_per_robot': {str(i): tasks_by_robot[i] for i in range(self.num_robots)},
            'scalability_robot_count': self.num_robots,
            'scalability_task_count': self.total_tasks,
            'task_type_targets':      dict(self.task_type_targets),
            'task_completion_counts': dict(self.task_completion_counts),
            'active_tasks_details':   act,
            'pending_tasks_preview':  pend,
            'deadlock_count':         self.deadlock_count_total,
            'yield_count':            self.yield_count_total,
            'recovery_count':         self.recovery_count_total,
            'collision_count':        self.collision_event_count,
            'starvation_prevent_count': self.starvation_prevent_count_total,
            'robot_status':           robot_status_map,
            'robot_control_state':    robot_control_state_map,
            'robot_flip_state':       robot_flip_state_map
        })
        self.task_stats_pub.publish(msg)
        self.task_stats_publish_count_total += 1

        # 发布每台机器人的独立状态
        for robot_id in range(self.num_robots):
            pos = self.robot_positions.get(robot_id, [0.0, 0.0])
            task = self.active_tasks.get(robot_id)

            robot_data = {
                'robot_id':        f'robot_{robot_id + 1}',
                'status':          self.robot_status[robot_id].value.upper(),
                'display_state':   self.get_robot_display_state(robot_id).upper(),
                'flip_state':      self.robot_flip_state.get(robot_id, 'normal').upper(),
                'position':        pos,
                'current_task':    task.id if task else None,
                'tasks_completed': sum(
                    1 for t in self.completed_tasks if t.assigned_robot == robot_id
                ),
                'distance':        0
            }

            robot_msg = String()
            robot_msg.data = json.dumps(robot_data)
            self.robot_status_pub.publish(robot_msg)
            self.robot_status_publish_count_total += 1

    def get_robot_display_state(self, rid):
        """
        @brief 获取前端展示用状态（优先反映翻倒/恢复中）
        """
        flip_state = self.robot_flip_state.get(rid, 'normal')
        if flip_state in ('flipped', 'recovering'):
            return flip_state
        return self.robot_status[rid].value

    def send_notification(self, level, message):
        """
        @brief 发送通知到前端 Dashboard

        @param level:   通知级别（success / warning / error / info）
        @param message: 通知内容（中文）
        """
        notification = {
            'type':      'notification',
            'level':     level,
            'message':   message,
            'timestamp': time.time()
        }
        msg = String()
        msg.data = json.dumps(notification)
        self.notification_pub.publish(msg)
        self.notification_count_total += 1

    def publish_command_result(self, command, status, message,
                               robot_id=None, source='web', reason=None, request_id=None):
        """
        @brief 发布结构化命令执行结果，供前端确认链路

        @param command:   命令名
        @param status:    accepted/rejected/executing/executed/failed
        @param message:   人类可读说明
        @param robot_id:  机器人编号（可选）
        @param source:    web/auto_flip/system
        @param reason:    机器可解析失败原因（可选）
        @param request_id:前端请求ID（可选）
        """
        payload = {
            'type': 'command_result',
            'timestamp': time.time(),
            'command': command,
            'status': status,
            'message': message,
            'source': source,
        }
        if robot_id is not None:
            payload['robot_id'] = int(robot_id)
        if reason:
            payload['reason'] = reason
        if request_id:
            payload['request_id'] = request_id

        msg = String()
        msg.data = json.dumps(payload)
        self.command_result_pub.publish(msg)
        self.command_result_count_total += 1
    
    # ============================================================
    #  完成检测与 Web 指令
    # ============================================================

    def check_completion(self):
        """
        @brief 检查所有任务是否已完成

        仅在实验已启动后才检查。所有任务完成时发送前端通知。

        @return: True 表示全部完成
        """
        if not self.experiment_started:
            return False

        # 自愈：无任务绑定的机器人应恢复 IDLE，避免完成判定被状态噪声阻塞
        for rid in range(self.num_robots):
            if self.robot_current_task.get(rid) is None and self.robot_status.get(rid) in (RobotStatus.MOVING, RobotStatus.LOADING, RobotStatus.UNLOADING):
                self.robot_status[rid] = RobotStatus.IDLE

        completed_count = len(self.completed_tasks)
        rejected_count = int(self.rejected_task_count_total)
        terminal_count = completed_count + rejected_count

        all_idle = all(
            s == RobotStatus.IDLE for s in self.robot_status.values()
        )
        if not self.active_tasks and not self.pending_tasks and all_idle and (
            self.total_tasks <= 0 or terminal_count >= self.total_tasks
        ):
            if self.total_tasks > 0:
                elapsed = (time.time() - self.system_start_time) / 60
                if rejected_count > 0:
                    rospy.logwarn(
                        f"⚠️ Experiment ended with terminal tasks {terminal_count}/{self.total_tasks} "
                        f"(completed={completed_count}, rejected={rejected_count}) in {elapsed:.1f} min"
                    )
                    self.send_notification(
                        'warning',
                        f'实验结束：完成{completed_count}，拒绝{rejected_count}，总计{self.total_tasks}，用时{elapsed:.1f}分钟'
                    )
                else:
                    rospy.loginfo(
                        f"🎉 All {self.total_tasks} tasks completed in {elapsed:.1f} min!"
                    )
                    self.send_notification(
                        'success',
                        f'实验完成！{self.total_tasks}个任务，用时{elapsed:.1f}分钟'
                    )
            return True
        return False

    def handle_web_command(self, msg):
        """
        @brief 处理来自 Web 控制面板的指令

        支持：manual_dispatch / recover_robot / stop_robot /
        resume_robot / recover_all。

        @param msg: ROS String 消息（JSON 格式）
        """
        try:
            d = json.loads(msg.data)
            cmd = d.get('command') or d.get('type')
            rid = d.get('robot_id')
            request_id = d.get('request_id')
            if rid is not None:
                rid = int(rid)

            commands_need_robot = {'manual_dispatch', 'recover_robot', 'stop_robot', 'resume_robot'}
            if cmd in commands_need_robot and rid is None:
                self.publish_command_result(
                    command=cmd,
                    robot_id=None,
                    status='rejected',
                    message=f'指令 {cmd} 缺少 robot_id 参数',
                    source='web',
                    reason='missing_robot_id',
                    request_id=request_id
                )
                self.send_notification('warning', f'指令 {cmd} 缺少 robot_id 参数')
                rospy.logwarn(f"Cmd dropped: {cmd} missing robot_id")
                return

            if cmd == 'manual_dispatch' and rid is not None:
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='accepted',
                    message='人工调度指令已接收，正在执行',
                    source='web',
                    request_id=request_id
                )
                tx = float(d.get('x'))
                ty = float(d.get('y'))
                duration = float(d.get('duration', 0))
                ok, detail = self.execute_manual_dispatch(
                    rid,
                    (tx, ty),
                    duration
                )
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='executed' if ok else 'failed',
                    message=detail,
                    source='web',
                    request_id=request_id
                )
            elif cmd == 'recover_robot' and rid is not None:
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='accepted',
                    message='恢复指令已接收，正在处理',
                    source='web',
                    request_id=request_id
                )
                ok, detail = self.recover_robot(rid, source='web')
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='executed' if ok else 'failed',
                    message=detail,
                    source='web',
                    request_id=request_id
                )
            elif cmd == 'stop_robot' and rid is not None:
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='accepted',
                    message='停止指令已接收，正在处理',
                    source='web',
                    request_id=request_id
                )
                ok, detail = self.pause_robot(rid)
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='executed' if ok else 'failed',
                    message=detail,
                    source='web',
                    request_id=request_id
                )
            elif cmd == 'resume_robot' and rid is not None:
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='accepted',
                    message='恢复运行指令已接收，正在处理',
                    source='web',
                    request_id=request_id
                )
                ok, detail = self.resume_robot(rid)
                self.publish_command_result(
                    command=cmd,
                    robot_id=rid,
                    status='executed' if ok else 'failed',
                    message=detail,
                    source='web',
                    request_id=request_id
                )
            elif cmd == 'recover_all':
                self.publish_command_result(
                    command=cmd,
                    status='accepted',
                    message='全部恢复指令已接收，开始执行',
                    source='web',
                    request_id=request_id
                )
                success_count = 0
                for i in range(self.num_robots):
                    ok, _ = self.recover_robot(i, source='web')
                    if ok:
                        success_count += 1
                self.publish_command_result(
                    command=cmd,
                    status='executed',
                    message=f'已完成批量恢复：{success_count}/{self.num_robots}',
                    source='web',
                    request_id=request_id
                )
            else:
                self.publish_command_result(
                    command=cmd or 'unknown',
                    status='rejected',
                    message=f'未知Web指令: {cmd}',
                    source='web',
                    reason='unknown_command',
                    request_id=request_id
                )
                self.send_notification('warning', f'未知Web指令: {cmd}')
                rospy.logwarn(f"Unknown web command: {cmd}")
        except Exception as e:
            self.publish_command_result(
                command='parse',
                status='failed',
                message=f'Web指令解析失败: {str(e)}',
                source='web',
                reason='parse_error'
            )
            self.send_notification('error', f'Web指令解析失败: {str(e)}')
            rospy.logerr(f"Cmd Error: {e}")

    # ============================================================
    #  暂停与恢复
    # ============================================================

    def pause_robot(self, rid):
        """
        @brief 暂停机器人运行（保留路径和任务状态）

        只有 MOVING / MANUAL 状态才可暂停。暂停后保存当前路径
        和任务快照，以便后续恢复时重新规划。

        @param rid: 机器人编号
        """
        if rid not in self.robot_status:
            return False, f'机器人 {rid} 不存在'

        current_status = self.robot_status[rid]

        # 仅 MOVING / MANUAL 可暂停
        if current_status not in [RobotStatus.MOVING, RobotStatus.MANUAL]:
            msg = f'机器人 {rid} 当前状态 [{current_status.value}] 无法暂停'
            self.send_notification('warning', msg)
            rospy.logwarn(
                f"⚠️ Cannot pause Robot {rid} - status: {current_status.value}"
            )
            return False, msg

        # 物理停止
        self.stop_robot(rid)

        # 保存暂停前快照
        task = self.robot_current_task.get(rid)
        self.robot_paused_state[rid] = {
            'previous_status': current_status,
            'path':   self.robot_paths.get(rid, []).copy(),
            'task':   task,
            'target': (task.destination if (task and task.status == "delivering")
                       else (task.source if task else None))
        }

        self.robot_status[rid] = RobotStatus.PAUSED
        msg = f'机器人 {rid} 已暂停'
        self.send_notification('success', msg)
        rospy.loginfo(f"⏸️ Robot {rid} Paused (path preserved)")
        return True, msg

    def resume_robot(self, rid):
        """
        @brief 恢复暂停的机器人（重新规划路径防止环境变化）

        从暂停快照中取出目标位置，重新规划路径后切换回 MOVING 状态。

        @param rid: 机器人编号
        """
        if rid not in self.robot_status:
            return False, f'机器人 {rid} 不存在'

        if self.robot_status[rid] != RobotStatus.PAUSED:
            msg = f'机器人 {rid} 未处于暂停状态'
            self.send_notification('warning', msg)
            rospy.logwarn(f"⚠️ Robot {rid} is not paused - cannot resume")
            return False, msg

        if rid not in self.robot_paused_state:
            # 安全回退
            self.robot_status[rid] = RobotStatus.IDLE
            msg = f'机器人 {rid} 暂停状态丢失，已设为空闲'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Robot {rid} paused state lost - set to IDLE")
            return False, msg

        paused_info = self.robot_paused_state[rid]
        task = paused_info['task']
        target = paused_info['target']

        if not task or not target or rid not in self.robot_positions:
            # 无任务或无位置信息
            self.robot_status[rid] = RobotStatus.IDLE
            self.robot_paths[rid] = []
            del self.robot_paused_state[rid]
            msg = f'机器人 {rid} 恢复失败（无任务），已设为空闲'
            self.send_notification('warning', msg)
            rospy.logwarn(f"⚠️ Robot {rid} resumed without task - set to IDLE")
            return False, msg

        # 强制重新规划路径
        current_pos = self.robot_positions[rid]
        new_path = self.path_planner.plan_path(
            current_pos, target, robot_id=rid, priority=task.priority
        )

        if not new_path or len(new_path) < 2:
            self.robot_status[rid] = RobotStatus.IDLE
            self.robot_paths[rid] = []
            msg = f'机器人 {rid} 恢复失败（路径规划失败）'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Robot {rid} resume failed - path planning failed")
            del self.robot_paused_state[rid]
            return False, msg

        # 更新路径并恢复运行
        self.robot_paths[rid] = self.path_planner.smooth_path(new_path)
        self.robot_status[rid] = RobotStatus.MOVING
        del self.robot_paused_state[rid]

        msg = f'机器人 {rid} 已恢复运行'
        self.send_notification('success', msg)
        rospy.loginfo(
            f"▶️ Robot {rid} Resumed "
            f"(path replanned: {len(self.robot_paths[rid])} waypoints)"
        )
        return True, msg
    
    # ============================================================
    #  人工调度与手动任务
    # ============================================================

    def execute_manual_dispatch(self, rid, target, duration):
        """
        @brief 执行人工调度：将机器人派往指定坐标

        若机器人正在执行自动任务，先将任务退回队列头部。
        到达目标后等待 duration 秒再恢复为 IDLE。

        @param rid:      机器人编号
        @param target:   目标坐标 (x, y)
        @param duration: 到达后等待时间（秒）
        """
        if rid < 0 or rid >= self.num_robots:
            msg = f'人工调度失败：机器人ID无效({rid})'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Manual dispatch failed: invalid robot id {rid}")
            return False, msg

        if rid not in self.robot_positions:
            msg = f'人工调度失败：机器人 {rid} 位置未就绪，请稍后重试'
            self.send_notification('warning', msg)
            rospy.logwarn(f"⚠️ Manual dispatch skipped: robot {rid} odom not ready")
            return False, msg

        tx, ty = target
        if not (math.isfinite(tx) and math.isfinite(ty)):
            msg = f'人工调度失败：目标坐标非法 ({target})'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Manual dispatch failed: invalid target {target}")
            return False, msg

        # 地图边界约束（与 A* is_valid 的边界逻辑对齐）
        margin = 0.1
        tx = max(margin, min(self.path_planner.map_width - margin, tx))
        ty = max(margin, min(self.path_planner.map_height - margin, ty))
        target = (tx, ty)

        duration = max(0.0, duration)

        ct = self.robot_current_task.get(rid)

        path = self.path_planner.plan_path(
            self.robot_positions[rid], target,
            robot_id=rid, priority=ct.priority if ct else 100
        )

        if not path or len(path) < 2:
            msg = f'人工调度失败：机器人 {rid} 路径规划失败'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Manual dispatch failed: no valid path for robot {rid} -> {target}")
            return False, msg

        # 路径规划成功后再执行任务接管，避免失败时破坏原状态
        if ct:
            ct.status = "pending"
            ct.assigned_robot = None
            ct.start_time = None
            self.pending_tasks.appendleft(ct)
            if rid in self.active_tasks:
                del self.active_tasks[rid]
        self.robot_current_task[rid] = None

        # 清理可能残留的让路/暂停状态
        if rid in self.robot_yielding:
            del self.robot_yielding[rid]
        if rid in self.robot_paused_state:
            del self.robot_paused_state[rid]

        self.robot_status[rid] = RobotStatus.MANUAL
        self.manual_task_info[rid] = {
            'duration':        duration,
            'is_waiting':      False,
            'start_wait_time': None
        }
        self.robot_paths[rid] = self.path_planner.smooth_path(path)
        msg = f'人工调度已生效：机器人 {rid} -> ({tx:.2f}, {ty:.2f})'
        self.send_notification('info', msg)
        rospy.loginfo(f"👮 Robot {rid} -> Manual Target")
        return True, msg

    def check_manual_tasks(self):
        """
        @brief 更新所有人工任务的等待状态

        到达目标后开始计时，等待时间结束后释放机器人。
        """
        for rid, info in list(self.manual_task_info.items()):
            if self.robot_status[rid] != RobotStatus.MANUAL:
                continue

            if not info['is_waiting']:
                # 检查是否已到达目标
                if not self.robot_paths.get(rid):
                    self.stop_robot(rid)
                    info['is_waiting'] = True
                    info['start_wait_time'] = time.time()
                    rospy.loginfo(
                        f"👮 Robot {rid} Waiting ({info['duration']}s)..."
                    )
            elif time.time() - info['start_wait_time'] >= info['duration']:
                # 等待结束，释放机器人
                self.robot_status[rid] = RobotStatus.IDLE
                del self.manual_task_info[rid]
                rospy.loginfo(f"👮 Robot {rid} Manual Task Done.")

    # ============================================================
    #  机器人复位（Gazebo 传送）
    # ============================================================

    def recover_robot(self, rid, source='manual'):
        """
        @brief 复位机器人到出生点

        三步流程：
        1. 零速预处理（消除惯性，0.5 秒）
        2. 调用 Gazebo set_model_state 传送到 spawn 位置
        3. 重置内部状态（任务退回队列、清空路径、3 秒保护期）

        @param rid: 机器人编号
        """
        if rid not in self.robot_spawn_positions:
            msg = f'机器人 {rid} 无spawn位置配置'
            self.send_notification('error', msg)
            return False, msg

        self.recovery_trigger_count_total += 1
        self.recovery_trigger_timestamps.append(time.time())

        try:
            # ========== 第一步：零速预处理 ==========
            rospy.loginfo(f"🔧 Robot {rid} recovery step 1/3: Zeroing velocity...")
            zero_cmd = Twist()
            start_time = rospy.Time.now()
            rate = rospy.Rate(20)
            while (rospy.Time.now() - start_time).to_sec() < 0.5:
                self.cmd_vel_pubs[rid].publish(zero_cmd)
                rate.sleep()

            # ========== 第二步：Gazebo 传送 ==========
            rospy.loginfo(f"🔧 Robot {rid} recovery step 2/3: Teleporting to spawn...")
            rospy.wait_for_service('/gazebo/set_model_state', timeout=2.0)
            from gazebo_msgs.srv import SetModelState
            from gazebo_msgs.msg import ModelState

            sp = self.robot_spawn_positions[rid]
            ms = ModelState()
            ms.model_name = f'robot_{rid}'

            # 位置（Z 轴略抬高防止卡地板）
            ms.pose.position.x = sp[0]
            ms.pose.position.y = sp[1]
            ms.pose.position.z = 0.25

            # 姿态归零
            ms.pose.orientation.w = 1.0

            # 速度归零（清除物理引擎残留速度）
            ms.twist = Twist()
            ms.reference_frame = 'world'

            set_state_service = rospy.ServiceProxy(
                '/gazebo/set_model_state', SetModelState
            )
            response = set_state_service(ms)

            if not response.success:
                raise Exception(
                    f"Gazebo service returned failure: {response.status_message}"
                )

            # ========== 第三步：重置内部状态 ==========
            rospy.loginfo(f"🔧 Robot {rid} recovery step 3/3: Resetting internal state...")

            # 当前任务退回队列头部
            task = self.robot_current_task.get(rid)
            if task:
                task.assigned_robot = None
                task.status = "pending"
                task.start_time = None
                self.pending_tasks.appendleft(task)
                if rid in self.active_tasks:
                    del self.active_tasks[rid]
                rospy.loginfo(
                    f"   ↩️ Task {task.id} returned to queue head "
                    f"(priority: {task.priority})"
                )

            # 清空所有状态
            self.robot_current_task[rid] = None
            self.robot_status[rid] = RobotStatus.IDLE
            self.robot_paths[rid] = []
            self.robot_flip_detected[rid] = False
            self.robot_flip_state[rid] = 'normal'
            self.robot_flip_candidate_since[rid] = None
            self.robot_flip_stable_since[rid] = None

            # 清除特殊状态
            if rid in self.robot_yielding:
                del self.robot_yielding[rid]
            if rid in self.robot_paused_state:
                del self.robot_paused_state[rid]
            if rid in self.manual_task_info:
                del self.manual_task_info[rid]

            # 强制更新位置（不等待 Odom 回调）
            self.robot_positions[rid] = (sp[0], sp[1])
            self.robot_orientations[rid] = 0.0
            self.robot_velocities[rid] = 0.0

            # 再次发送零速
            self.stop_robot(rid)

            # 添加 3 秒保护期
            self.robot_protected.add(rid)

            def remove_protection():
                """保护期结束后自动移除"""
                rospy.sleep(3.0)
                if rid in self.robot_protected:
                    self.robot_protected.discard(rid)
                    rospy.loginfo(f"   🛡️ Robot {rid} protection removed")

            import threading
            threading.Thread(target=remove_protection, daemon=True).start()

            self.recovery_count_total += 1
            self.recovery_success_timestamps.append(time.time())
            msg = f'机器人 {rid} 已成功重置到出生点'
            self.send_notification('success', msg)
            rospy.loginfo(
                f"✅ Robot {rid} fully recovered: "
                f"pos=({sp[0]:.2f}, {sp[1]:.2f}), status=IDLE, protected=3s"
            )
            return True, msg

        except rospy.ROSException as e:
            msg = f'机器人 {rid} 恢复失败: Gazebo服务超时'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Recovery failed for Robot {rid}: {e}")
            if source == 'auto_flip':
                self.robot_flip_state[rid] = 'flipped'
            return False, msg
        except Exception as e:
            msg = f'机器人 {rid} 恢复失败: {str(e)}'
            self.send_notification('error', msg)
            rospy.logerr(f"❌ Recovery failed for Robot {rid}: {e}")
            if source == 'auto_flip':
                self.robot_flip_state[rid] = 'flipped'
            return False, msg

    # ============================================================
    #  主循环
    # ============================================================

    def run(self):
        """
        @brief 调度器主循环（10 Hz）

        每帧依次执行：完成检测 → 任务分配 → 区域追踪 →
        死锁扫描 → 人工任务检查 → 导航 → 统计发布。
        """
        rate = rospy.Rate(10)
        rospy.loginfo("🚀 Scheduler Running...")

        while not rospy.is_shutdown():
            cycle_start = time.time()
            if self.check_completion():
                break

            if self.enable_corridor_token:
                self.cleanup_corridor_tokens()
            self.cleanup_runtime_navigation_states()
            self.assign_tasks()
            self.update_region_tracking()
            self.global_deadlock_scan()
            self.auto_recover_flipped_robots()
            self.check_manual_tasks()

            for i in range(self.num_robots):
                self.update_robot_wait_state(i)

            self.recover_stalled_robots()

            for i in range(self.num_robots):
                # MOVING 和 MANUAL 才执行导航（PAUSED 在 navigate 内部拦截）
                if self.robot_status.get(i) in [RobotStatus.MOVING, RobotStatus.MANUAL, RobotStatus.YIELDING]:
                    self.navigate_along_path(i)

            cycle_cost = time.time() - cycle_start
            cycle_end_ts = time.time()
            self.computation_cycle_count += 1
            self.computation_time_total += cycle_cost
            if cycle_cost < 0.1:
                self.computation_cycle_lt_100ms_count += 1
            self.computation_cycle_timestamps.append((cycle_end_ts, cycle_cost < 0.1))
            if cycle_cost > self.computation_time_max:
                self.computation_time_max = cycle_cost

            completed_now = len(self.completed_tasks)
            if completed_now > self.last_completed_task_count:
                self.last_progress_timestamp = cycle_end_ts
            self.last_completed_task_count = completed_now

            effective_robot_now = 0
            for rid in range(self.num_robots):
                task = self.robot_current_task.get(rid)
                if task is None:
                    continue
                status = self.robot_status.get(rid, RobotStatus.IDLE)
                speed = self.robot_velocities.get(rid, 0.0)
                has_progress = (status in (RobotStatus.LOADING, RobotStatus.UNLOADING)) or (speed > self.wait_speed_threshold)
                if has_progress:
                    effective_robot_now += 1
                    self.robot_progress_timestamps[rid].append(cycle_end_ts)

                if self.get_wait_duration(rid) >= self.persistent_stall_horizon:
                    self.persistent_stall_duration_total += cycle_cost
                    self.persistent_stall_duration_samples.append((cycle_end_ts, cycle_cost))

            unfinished = bool(self.pending_tasks or self.active_tasks)
            no_progress_for = cycle_end_ts - self.last_progress_timestamp
            if unfinished and no_progress_for >= self.freeze_detection_grace and effective_robot_now <= self.freeze_effective_robot_threshold:
                self.freeze_duration_total += cycle_cost
                self.freeze_duration_samples.append((cycle_end_ts, cycle_cost))

            while cycle_end_ts - self.flow_window_last_tick >= self.flow_window_seconds:
                positive = 1 if completed_now > self.flow_window_last_completed else 0
                self.flow_total_window_count += 1
                if positive > 0:
                    self.flow_positive_count_total += 1
                self.flow_window_last_tick += self.flow_window_seconds
                self.flow_window_last_completed = completed_now
                self.flow_window_outcomes.append((self.flow_window_last_tick, positive))

            self.publish_statistics()
            rate.sleep()


# ================================================================
#  入口
# ================================================================
if __name__ == '__main__':
    try:
        CleanTaskScheduler(num_robots=10).run()
    except rospy.ROSInterruptException:
        pass
