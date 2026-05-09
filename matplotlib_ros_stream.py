#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@brief 2D 实时地图可视化服务器（Matplotlib + Flask）

该模块订阅 ROS 话题获取机器人位姿与任务统计数据，
使用 Matplotlib 渲染 2D 工厂地图，并通过 Flask 以
MJPEG 视频流的形式提供给浏览器实时显示。

主要功能：
    - 订阅 /robot_X/odom：获取 10 个机器人的实时位姿
    - 订阅 /factory/task_statistics：获取任务进度统计
    - Matplotlib 绘制工厂区域、机器人位置、运动轨迹
    - Flask 视频流（端口 5000，约 10 FPS）
    - /api/stats 接口提供任务统计 JSON 数据
"""

import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from flask import Flask, Response
import matplotlib
matplotlib.use('Agg')                   # 无头渲染模式
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow
import matplotlib.patches as mpatches
import numpy as np
import io
import threading
import time
import math
from collections import deque
import json
import sys



# ============================================================
#  Flask 应用初始化
# ============================================================

app = Flask(__name__)

# ============================================================
#  全局状态数据
# ============================================================

robot_positions = {}                    # 机器人位置 {id: (x, y)}
robot_velocities = {}                   # 机器人线速度 {id: float}
robot_angles = {}                       # 机器人朝向角 {id: float}（弧度）
robot_paths = {}                        # 机器人运动轨迹 {id: deque[(x, y)]}
robot_status = {}                       # 机器人状态 {id: str}
robot_carrying = {}                     # 机器人负载信息 {id: str/None}
last_update_time = {}                   # 最后更新时间戳 {id: float}

data_received_count = 0                 # 累计接收消息数
ros_initialized = False                 # ROS 初始化标志

# 实验统计数据（由 /factory/task_statistics 回调更新）
experiment_stats = {
    'task_stats': {
        'total_tasks': 0,
        'completed_tasks': 0,
        'pending_tasks': 0,
        'in_progress_tasks': 0,
        'elapsed_time': 0,
        'completion_rate': 0,
        'avg_task_time': 0
    },
    'experiment_mode': 'unknown',       # 实验模式
    'last_update': None                 # 最后更新时间
}

# ============================================================
#  可视化参数配置
# ============================================================

# 机器人绘制尺寸（1/4 缩放）
ROBOT_RADIUS = 0.0625                   # 机器人圆形半径
ROBOT_ARROW_LENGTH = 0.08               # 方向箭头长度
ROBOT_ARROW_WIDTH = 0.015               # 箭头杆宽度
ROBOT_ARROW_HEAD_WIDTH = 0.0375         # 箭头头部宽度
ROBOT_ARROW_HEAD_LENGTH = 0.025         # 箭头头部长度
ROBOT_STATUS_INDICATOR_RADIUS = 0.0175  # 状态指示灯半径
ROBOT_STATUS_INDICATOR_OFFSET = 0.045   # 指示灯相对机器人中心偏移

# 机器人颜色方案（10 台机器人）
ROBOT_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788'
]

# 状态对应颜色
STATUS_COLORS = {
    'IDLE': '#2196F3',                  # 空闲 → 蓝色
    'MOVING': '#4CAF50',                # 移动中 → 绿色
    'LOADING': '#FFC107',               # 装载中 → 黄色
    'UNLOADING': '#FF9800',             # 卸载中 → 橙色
    'BLOCKED': '#F44336',               # 阻塞 → 红色
    'UNKNOWN': '#9E9E9E'                # 未知 → 灰色
}

# 工厂区域定义（与 smart_factory_10robots.world 对齐）
# radius 单位为米，显示与 detect 逻辑共用。
AREAS = {
    'empty_storage':    {'center': (2.0, 2.0),   'radius': 0.9,  'color': '#90A4AE', 'name': 'Empty'},
    'green_storage':    {'center': (2.0, 8.0),   'radius': 0.9,  'color': '#66CC66', 'name': 'Green'},
    'yellow_storage':   {'center': (14.0, 2.0),  'radius': 0.9,  'color': '#FBC02D', 'name': 'Yellow'},
    'red_storage':      {'center': (14.0, 8.0),  'radius': 0.9,  'color': '#E53935', 'name': 'Red'},
    'completed':        {'center': (14.0, 5.0),  'radius': 0.8,  'color': '#43A047', 'name': 'Done'},
    'carding_wait_0':   {'center': (5.0, 1.5),   'radius': 0.35, 'color': '#64B5F6', 'name': 'CW0'},
    'carding_wait_1':   {'center': (5.0, 3.5),   'radius': 0.35, 'color': '#64B5F6', 'name': 'CW1'},
    'carding_wait_2':   {'center': (5.0, 5.5),   'radius': 0.35, 'color': '#64B5F6', 'name': 'CW2'},
    'carding_wait_3':   {'center': (5.0, 7.5),   'radius': 0.35, 'color': '#64B5F6', 'name': 'CW3'},
    'carding_machine_0': {'center': (6.0, 1.5),  'radius': 0.3,  'color': '#4F83FF', 'name': 'C0'},
    'carding_machine_1': {'center': (6.0, 3.5),  'radius': 0.3,  'color': '#4F83FF', 'name': 'C1'},
    'carding_machine_2': {'center': (6.0, 5.5),  'radius': 0.3,  'color': '#4F83FF', 'name': 'C2'},
    'carding_machine_3': {'center': (6.0, 7.5),  'radius': 0.3,  'color': '#4F83FF', 'name': 'C3'},
    'carding_finish_0': {'center': (7.0, 1.5),   'radius': 0.35, 'color': '#283593', 'name': 'CF0'},
    'carding_finish_1': {'center': (7.0, 3.5),   'radius': 0.35, 'color': '#283593', 'name': 'CF1'},
    'carding_finish_2': {'center': (7.0, 5.5),   'radius': 0.35, 'color': '#283593', 'name': 'CF2'},
    'carding_finish_3': {'center': (7.0, 7.5),   'radius': 0.35, 'color': '#283593', 'name': 'CF3'},
    'drawing1_wait_0':  {'center': (8.0, 2.5),   'radius': 0.35, 'color': '#81C784', 'name': 'D1W0'},
    'drawing1_wait_1':  {'center': (8.0, 6.5),   'radius': 0.35, 'color': '#81C784', 'name': 'D1W1'},
    'drawing1_machine_0': {'center': (9.0, 2.5), 'radius': 0.3,  'color': '#66CC66', 'name': 'D1M0'},
    'drawing1_machine_1': {'center': (9.0, 6.5), 'radius': 0.3,  'color': '#66CC66', 'name': 'D1M1'},
    'drawing1_finish_0': {'center': (10.0, 2.5), 'radius': 0.35, 'color': '#1B5E20', 'name': 'D1F0'},
    'drawing1_finish_1': {'center': (10.0, 6.5), 'radius': 0.35, 'color': '#1B5E20', 'name': 'D1F1'},
    'drawing2_wait_0':  {'center': (10.8, 2.5),  'radius': 0.35, 'color': '#FFCC80', 'name': 'D2W0'},
    'drawing2_wait_1':  {'center': (10.8, 6.5),  'radius': 0.35, 'color': '#FFCC80', 'name': 'D2W1'},
    'drawing2_machine_0': {'center': (11.8, 2.5),'radius': 0.3,  'color': '#FFB74D', 'name': 'D2M0'},
    'drawing2_machine_1': {'center': (11.8, 6.5),'radius': 0.3,  'color': '#FFB74D', 'name': 'D2M1'},
    'drawing2_finish_0': {'center': (12.8, 2.5), 'radius': 0.35, 'color': '#E65100', 'name': 'D2F0'},
    'drawing2_finish_1': {'center': (12.8, 6.5), 'radius': 0.35, 'color': '#E65100', 'name': 'D2F1'},
}


def pick_contrast_text_color(hex_color):
    """
    @brief 根据背景色选择黑/白文本颜色，保证区域标签清晰可读

    @param hex_color: 颜色字符串（#RRGGBB）
    @return: '#111111' 或 '#FFFFFF'
    """
    color = hex_color.lstrip('#')
    if len(color) != 6:
        return '#111111'
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    return '#111111' if luma > 150 else '#FFFFFF'

# ============================================================
#  辅助工具函数
# ============================================================

def quaternion_to_euler(q):
    """
    @brief 四元数转欧拉角（仅提取 yaw）

    @param q: ROS Quaternion 消息
    @return: yaw 角度（弧度）
    """
    return math.atan2(2 * (q.w * q.z + q.x * q.y),
                      1 - 2 * (q.y * q.y + q.z * q.z))


def detect_robot_area(x, y):
    """
    @brief 检测机器人所在的工厂区域

    @param x: 机器人 X 坐标（米）
    @param y: 机器人 Y 坐标（米）
    @return: 区域名称字符串，不在任何区域内则返回 'Free Area'
    """
    candidates = []
    for _, info in AREAS.items():
        cx, cy = info['center']
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        radius = max(info['radius'], 1e-6)
        if dist <= radius:
            candidates.append((dist / radius, dist, info['name']))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]
    return 'Free Area'


# ============================================================
#  ROS 回调函数
# ============================================================

def odom_callback(msg, robot_id):
    """
    @brief 里程计话题回调

    从 /robot_X/odom 消息中提取位置、朝向和速度，
    更新全局状态并追加到运动轨迹队列。

    @param msg:      ROS Odometry 消息
    @param robot_id: 机器人编号（0~9）
    """
    global data_received_count
    data_received_count += 1

    pos = msg.pose.pose.position
    vel = msg.twist.twist.linear

    robot_positions[robot_id] = (pos.x, pos.y)
    robot_angles[robot_id] = quaternion_to_euler(msg.pose.pose.orientation)
    robot_velocities[robot_id] = np.sqrt(vel.x ** 2 + vel.y ** 2)
    last_update_time[robot_id] = time.time()

    # 追加到运动轨迹（保留最近 150 个点）
    if robot_id not in robot_paths:
        robot_paths[robot_id] = deque(maxlen=150)
    robot_paths[robot_id].append((pos.x, pos.y))


def status_callback(msg, robot_id):
    """
    @brief 机器人状态话题回调

    @param msg:      ROS String 消息，JSON 格式
    @param robot_id: 机器人编号（0~9）
    """
    try:
        d = json.loads(msg.data)
        robot_status[robot_id] = d.get('status', 'IDLE')
        robot_carrying[robot_id] = d.get('carrying', None)
    except Exception:
        robot_status[robot_id] = 'UNKNOWN'


def task_stats_callback(msg):
    """
    @brief 任务统计话题回调

    从 /factory/task_statistics 消息中更新实验统计数据。

    @param msg: ROS String 消息，JSON 格式的任务统计
    """
    global experiment_stats
    try:
        data = json.loads(msg.data)
        experiment_stats['task_stats'].update(data)
        from datetime import datetime
        experiment_stats['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"⚠️ Failed to parse task statistics: {e}")

# ============================================================
#  ROS 初始化与数据流监控
# ============================================================

def start_ros_subscribers():
    """
    @brief 初始化 ROS 节点并订阅所有话题

    订阅 10 个机器人的 odom 和 status 话题，以及任务统计话题。
    初始化完成后启动数据流监控线程。
    """
    global ros_initialized, experiment_stats
    try:
        rospy.init_node('matplotlib_visualizer', anonymous=True)
        print(">>> Initializing visualization node...")

        # 订阅每个机器人的里程计和状态话题
        for i in range(10):
            rospy.Subscriber(f'/robot_{i}/odom', Odometry, odom_callback, callback_args=i)
            rospy.Subscriber(f'/robot_{i}/status', String, status_callback, callback_args=i)

        # 订阅任务统计话题
        rospy.Subscriber('/factory/task_statistics', String, task_stats_callback)

        # 获取实验模式（从环境变量）
        import os
        experiment_stats['experiment_mode'] = os.environ.get('EXPERIMENT_MODE', 'unknown')

        ros_initialized = True
        print(f"✅ Subscribed robot topics for 10 robots")
        print(f"✅ Subscribed task statistics topic")
        print(f"📊 Experiment mode: {experiment_stats['experiment_mode']}")

        # 启动数据流监控线程
        threading.Thread(target=monitor_data_flow, daemon=True).start()

    except Exception as e:
        print(f"❌ ROS initialization failed: {e}")
        sys.exit(1)


def monitor_data_flow():
    """
    @brief 数据流监控线程

    每 5 秒打印一次在线机器人数量和消息接收速率，
    用于调试和运行状态确认。
    """
    last_cnt = 0
    while True:
        time.sleep(5)
        curr_cnt = data_received_count
        diff = curr_cnt - last_cnt
        last_cnt = curr_cnt
        online = len(robot_positions)
        print(f"📊 Data flow: online robots {online}/10 | received {diff} messages in 5 seconds")

# ============================================================
#  Matplotlib 地图渲染
# ============================================================

def generate_factory_map():
    """
    @brief 生成工厂地图帧的生成器函数

    持续渲染 Matplotlib 图像帧，输出为 MJPEG 格式的字节流。
    每帧包含：工厂区域、机器人位置/方向/轨迹、状态指示灯、速度文本。
    渲染频率约 10 FPS。

    @yield: MJPEG 帧数据（bytes）
    """
    frame_cnt = 0

    # 等待 ROS 初始化和首批数据到达
    while not ros_initialized:
        time.sleep(0.5)
    while not robot_positions:
        time.sleep(0.5)

    print("🎬 Starting map stream generation...")

    while True:
        try:
            frame_cnt += 1
            if frame_cnt % 50 == 0:
                print(f"🖼️  Generated {frame_cnt} frames | total messages: {data_received_count}")

            # 创建画布
            fig, ax = plt.subplots(figsize=(16, 10), dpi=100)
            ax.set_xlim(0, 16)
            ax.set_ylim(0, 10)
            ax.set_aspect('equal')
            ax.set_facecolor('#FFFFFF')
            ax.grid(True, color='#CFD8DC', linestyle='--', linewidth=0.8, alpha=0.7)

            # ---------- 绘制工厂区域 ----------
            for _, info in AREAS.items():
                cx, cy = info['center']
                r = info['radius']
                ax.add_patch(Circle(
                    (cx, cy), r,
                    facecolor=info['color'], edgecolor='#1F2937', linewidth=1.2, alpha=0.82, zorder=1
                ))
                label_color = pick_contrast_text_color(info['color'])
                ax.text(cx, cy, info['name'],
                        ha='center', va='center', fontsize=6, fontweight='bold',
                        color=label_color, zorder=2)

            # ---------- 绘制机器人 ----------
            active_cnt = 0
            for rid in range(10):
                if rid not in robot_positions:
                    continue

                x, y = robot_positions[rid]
                angle = robot_angles.get(rid, 0)
                vel = robot_velocities.get(rid, 0)
                stat = robot_status.get(rid, 'IDLE')
                path = robot_paths.get(rid, deque())
                col = ROBOT_COLORS[rid]

                if vel > 0.01:
                    active_cnt += 1

                # 运动轨迹
                if len(path) > 1:
                    p = np.array(path)
                    ax.plot(p[:, 0], p[:, 1], color=col, alpha=0.55, linewidth=2.0, zorder=2.5)

                # 机器人本体（圆形）
                ax.add_patch(Circle(
                    (x, y), ROBOT_RADIUS,
                    facecolor=col, edgecolor='black', alpha=0.9, zorder=3
                ))

                # 方向箭头
                dx = ROBOT_ARROW_LENGTH * math.cos(angle)
                dy = ROBOT_ARROW_LENGTH * math.sin(angle)
                ax.add_patch(FancyArrow(
                    x, y, dx, dy,
                    width=ROBOT_ARROW_WIDTH,
                    head_width=ROBOT_ARROW_HEAD_WIDTH,
                    head_length=ROBOT_ARROW_HEAD_LENGTH,
                    fc='white', ec='black', zorder=4
                ))

                # 机器人编号
                ax.text(x, y, str(rid),
                        ha='center', va='center', fontsize=9,
                        fontweight='bold', color='white', zorder=5)

                # 状态指示灯
                status_color = STATUS_COLORS.get(stat, '#999999')
                ax.add_patch(Circle(
                    (x + ROBOT_STATUS_INDICATOR_OFFSET,
                     y + ROBOT_STATUS_INDICATOR_OFFSET),
                    ROBOT_STATUS_INDICATOR_RADIUS,
                    facecolor=status_color, zorder=6
                ))

                # 速度文本
                ax.text(x, y + 0.11, f'{vel:.2f}m/s',
                    ha='center', va='bottom', fontsize=6, fontweight='bold', color='#263238')

                # 负载信息标签
                carry = robot_carrying.get(rid)
                if carry:
                    txt = carry[0] if isinstance(carry, str) else str(carry)
                    ax.text(x + 0.085, y + 0.085, f'[{txt}]',
                            ha='left', va='bottom', fontsize=5,
                            color='#E91E63', fontweight='bold')

            # ---------- 标题与底部信息 ----------
            t_str = time.strftime("%H:%M:%S")
            ax.set_title(
                f"Factory Map (1/4 Scale) | Robots: {len(robot_positions)}/10 | Active: {active_cnt}",
                fontsize=14, fontweight='bold', color='#1565C0', pad=15
            )
            ax.text(8, -0.5, f'Update: {t_str} | Frame: {frame_cnt}',
                    ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE082', edgecolor='#FB8C00', alpha=0.9))

            # ---------- 图例 ----------
            legs = [mpatches.Patch(color=c, label=l) for l, c in STATUS_COLORS.items()]
            ax.legend(handles=legs, loc='upper left', fontsize=8, framealpha=0.9)

            # ---------- 输出图像帧 ----------
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)

            yield (b'--frame\r\nContent-Type: image/png\r\n\r\n' + buf.read() + b'\r\n')
            time.sleep(0.1)             # 约 10 FPS

        except Exception as e:
            print(f"❌ Rendering error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)

# ============================================================
#  Flask 路由
# ============================================================

@app.route('/video_feed')
def video_feed():
    """
    @brief 地图视频流路由

    以 MJPEG 格式持续输出 Matplotlib 渲染的地图帧。

    @return: Flask Response（multipart 流式响应）
    """
    return Response(generate_factory_map(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/stats')
def api_stats():
    """
    @brief 任务统计数据 API

    返回当前实验的任务统计信息（JSON 格式）。

    @return: JSON 格式的 experiment_stats
    """
    from flask import jsonify
    return jsonify(experiment_stats)


@app.route('/')
def index():
    """
    @brief 根路由（后端服务说明）

    不再提供独立 2D 动画页面，避免与控制面板重复展示。
    地图画面应通过 8000 控制面板内嵌使用 /video_feed。

    @return: HTML 说明页面字符串
    """
    return """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #1f2937;
                color: #f9fafb;
                font-family: Arial, sans-serif;
            }}
            .card {
                width: min(860px, 92vw);
                background: #111827;
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 24px;
                line-height: 1.7;
            }}
            h1 {
                margin: 0 0 10px 0;
                font-size: 22px;
                color: #93c5fd;
            }}
            .code {
                display: inline-block;
                font-family: monospace;
                background: #0b1220;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 2px 8px;
                color: #bfdbfe;
                margin: 2px 4px 2px 0;
            }}
            a {
                color: #93c5fd;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🧩 2D Map Stream Backend (5000)</h1>
            <p>This port only provides embedded map stream APIs and does not host a standalone animation page.</p>
            <p>Open the control panel to view the map:</p>
            <p><a href="http://localhost:8000/gazebo_control_with_tasks.html" target="_blank">http://localhost:8000/gazebo_control_with_tasks.html</a></p>
            <p>Available endpoints:</p>
            <div class="code">/video_feed</div>
            <div class="code">/api/stats</div>
        </div>
    </body>
    </html>
    """

# ============================================================
#  主函数
# ============================================================

if __name__ == '__main__':
    start_ros_subscribers()
    print(">>> Starting Web server (port 5000)...")
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServer stopped")