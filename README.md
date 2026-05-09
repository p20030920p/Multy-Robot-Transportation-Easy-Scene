# 智能工厂多机器人调度系统技术文档（细化版）

本文件是仓库当前唯一系统级功能文档，目标是按“代码注释级颗粒度”解释：
- 每个模块做什么
- 每个模块输入/输出什么
- 每个模块内部按什么步骤运行
- 仿真工具中的机器人参数、工厂参数、物理参数如何设置

---

## 1. 文档范围与阅读方式

### 1.1 面向对象
- 调试系统运行问题（死锁、拥堵、吞吐下降）
- 需要写论文方法与实验章节
- 需要做参数复现实验

### 1.2 参数来源文件（权威）
- 启动链路：`launch_system.py`
- 调度逻辑：`task_scheduler_ros_clean.py`
- 路径规划：`astar_planner.py`
- 机器人模型：`src/smart_factory_sim/urdf/agv_robot.urdf.xacro`
- 工厂场景：`src/smart_factory_sim/worlds/smart_factory_10robots.world`
- 10 机器人启动：`src/smart_factory_sim/launch/smart_factory_10_robots.launch`
- 代价地图：`src/smart_factory_sim/config/*.yaml`

---

## 2. 总体架构（运行链路）

统一入口：`launch_system.py`

顺序拉起 7 个组件：
1. ROS Master（`roscore`）
2. Gazebo（`smart_factory_10_robots.launch`）
3. ROS Bridge（`rosbridge_websocket`, 9090）
4. 调度器（`task_scheduler_ros_clean.py`）
5. Dashboard（`experiment_monitor_dashboard.py`, 5001）
6. 2D 地图流（`matplotlib_ros_stream.py`, 5000）
7. Web 静态服务（`python3 -m http.server`, 8000）

模式通过 `EXPERIMENT_MODE` 传递给调度器和 Dashboard。

---

## 3. 启动模块细化：`launch_system.py`

### 3.1 模块职责
负责“一键编排 + 服务生命周期管理”：
- 清理旧进程
- 端口占用检测与释放
- 按依赖顺序启动服务
- 启动后健康检查
- 统一 Ctrl+C 清理退出

### 3.2 输入/输出
- 输入：CLI 参数 `--mode/--yes/--headless/--no-browser`
- 输出：运行中的系统服务 + 两个可访问页面

### 3.3 关键执行步骤（按代码流程）
1. 解析参数并确定实验模式
2. 检测 `gnome-terminal`，不可用则自动切换 `headless`
3. 清理旧脚本进程与端口（5000/5001/8000/9090）
4. 按 `ROS→Gazebo→Bridge→Scheduler→Dashboard→Map→Web` 启动
5. 调用 `verify_system()` 检查各服务状态
6. 可选自动打开页面
7. 进入监控循环，若 ROS Master 挂掉则触发清理

### 3.4 启动模式
- `quick`: 79
- `baseline`: 316
- `baseline2`: 237
- `stress`: 632
- `stress2`: 474
- `monitor`: 316
- `s2_core`: 316（S2核心对比，同工厂场景）
- `s2_realtime`: 237（S2实时性对比，同工厂场景）
- `s2_congestion`: 474（S2拥堵对比，同工厂场景）
- `s2_peak`: 632（S2峰值压力对比，同工厂场景）

### 3.5 算法模式
- `naive` / `rule_greedy`：Rule-based (Greedy)
- `path_only` / `auction_based`：Auction-based
- `path_reservation` / `cbs_based`：CBS-based
- `full` / `proposed`：Proposed

---

## 4. 调度核心模块细化：`task_scheduler_ros_clean.py`

### 4.1 模块职责
`CleanTaskScheduler` 负责多机器人任务闭环：
- 任务生成、任务分配
- 路径导航、冲突检测、死锁恢复
- 手动干预（暂停/恢复/人工调度/复位）
- 指标发布（供 Dashboard 与分析工具）

### 4.2 关键状态容器（核心数据结构）
- `robot_positions`：机器人位置
- `robot_paths`：机器人当前路径
- `robot_current_task`：当前任务对象
- `pending_tasks` / `active_tasks` / `completed_tasks`
- `spacetime_reservations`：时空预约（节点+边）
- `robot_yielding`：让路状态
- `deadlock_*`：死锁检测与处置状态
- `corridor_tokens`：走廊单向通行令牌

### 4.3 任务生成（`generate_tasks`）
按模式写入 `task_type_targets`：
- 类型比例固定 `36:36:6:1`
- `baseline2` 与 `stress2` 保持原比例缩放

任务类型：
- `empty_to_carding`
- `green_to_drawing1`
- `yellow_to_drawing2`
- `red_to_completed`

### 4.4 任务分配（`assign_tasks`）逐步逻辑
1. 仅在 `experiment_started=True` 下执行
2. 找出 `IDLE` 且有位置的机器人
3. 从队列弹出任务
4. 尝试区域分散目标（避免扎堆）
5. 优先使用 `plan_path_avoiding_region_robots` 规划
6. 失败时回退标准 A*
7. 成功则激活任务，机器人状态切到 `MOVING`

### 4.5 导航执行（`navigate_along_path`）逐步逻辑
1. 若 `PAUSED`：直接跳过导航
2. 若让路中且无让路路径：保持等待
3. 若路径为空：先测距目标，再决定“到达”或“重规划”
4. 非让路阶段执行时空预约
5. 检查时空冲突并调用优先级裁决
6. 需要让路则执行 `execute_yield_action`
7. 滚动弹出已到达的路径点，向下一点发导航控制

### 4.6 到达处理（`handle_arrival`）逐步逻辑
1. 先检查到达点拥挤程度
2. 拥挤时尝试：更激进让路轨迹 → 区域分散重定位 → 后退等待
3. 安全后推进任务状态：
	 - `assigned -> loading -> delivering`
	 - `delivering -> unloading -> completed`

### 4.7 死锁治理（四层）

#### L1 安全层
- 激光 + 邻距保护
- 参数：`critical_safety_distance`、`hard_safety_distance`

#### L2 冲突层（预约+优先级）
- 预约结构：`nodes + edges`
- 冲突检测：节点冲突、对向换边、同边重叠
- 裁决函数：`resolve_conflict_by_priority`

有效优先级：
$$
P_i^{eff}=P_i^{base}+B_i^{wait}+B_i^{inherit}+B_i^{protect}
$$

#### L3 瓶颈层（走廊令牌）
- 函数：`corridor_priority_decision`
- 机制：狭窄区单向通行 + TTL 回收

#### L4 死锁升级层
1. `global_deadlock_scan`：持续近距计数触发死锁
2. `force_global_deadlock_resolution`：统一处置入口
3. `try_force_pair_separation`：双机主动分离
4. `trigger_pair_emergency_break`：高重试短时急停

### 4.8 去抖与反活锁
- `yield_pair_cooldown`
- `robot_consecutive_yield_count`
- `pair_separation_active`

### 4.9 人工控制链
- 暂停：`pause_robot`
- 恢复：`resume_robot`（会重规划）
- 手动派单：`execute_manual_dispatch`
- 复位：`recover_robot`（Gazebo 传送 + 状态回收）

### 4.10 主循环（`run`）精确顺序
1. 完成检测
2. 走廊令牌清理
3. 运行态清理
4. 任务分配
5. 区域追踪
6. 死锁扫描
7. 翻倒恢复
8. 手动任务检查
9. 每台机器人等待态更新与导航
10. 发布统计

---

## 5. 路径规划模块细化：`astar_planner.py`

### 5.1 模块职责
- 8 邻域 A* 搜索
- 动态障碍规避
- 路径平滑

### 5.2 关键参数
- `grid_size = 0.1`
- `robot_radius = 0.0625`
- 地图尺寸：`map_width = 16.0`、`map_height = 10.0`
- 最大迭代：`3000`

### 5.3 `plan_path` 步骤
1. 检查起点合法性，不合法则找最近合法点
2. 世界坐标转栅格
3. 初始化 open/closed 集
4. 扩展 8 邻域（直线/对角不同代价）
5. 到达目标附近则回溯路径
6. 返回平滑前路径给调度器继续处理
7. 搜索失败返回空路径（由上层决定重规划策略）

---

## 6. Dashboard 模块细化：`experiment_monitor_dashboard.py`

### 6.1 模块职责
- 订阅 ROS 统计与通知
- 聚合成 Web API 数据
- 触发报告生成

### 6.2 输入/输出
- 输入 topic：
	- `/factory/task_statistics`
	- `/factory/robot_status`
	- `/factory/notifications`
- 输出 API：
	- `GET /api/data`
	- `GET /api/report/status`
	- `POST /api/report/generate`

### 6.3 关键步骤
1. 启动 ROS 监听线程
2. 回调更新全局 `dashboard_data`
3. 完成检测后可自动触发报告生成
4. Flask 提供前端拉取接口

---

## 7. 地图流模块细化：`matplotlib_ros_stream.py`

### 7.1 模块职责
- 订阅机器人 odom 与任务统计
- Matplotlib 绘制工厂 2D 态势
- Flask 输出视频流与统计

### 7.2 关键参数
- 轨迹缓存：最近 150 点
- 激光/状态数据由 ROS topic 实时驱动
- 视频输出端口：5000

### 7.3 关键接口
- `GET /video_feed`
- `GET /api/stats`

---

## 8. 实验工具链模块细化（`tools/`）

### 8.1 `run_experiments.py`
步骤：
1. 订阅统计、通知、机器人 odom
2. 记录时间序列与轨迹
3. 生成 `summary.json` + 图表 + 终端摘要

### 8.2 `analyze_experiments.py`
步骤：
1. 读取 `experiment_results/*/summary.json`
2. 聚合指标（均值/方差/分布）
3. 生成对比图、统计表、显著性结果

### 8.3 `generate_paper_materials.py`
步骤：
1. 聚合基准实验与对比实验数据
2. 生成 `paper_materials/` 下 CSV/PNG/LaTeX
3. 输出可直接粘贴论文的表格代码

---

## 9. 仿真参数总表（机器人 + 工厂 + 启动）

## 9.1 启动参数（`smart_factory_10_robots.launch`）

### Gazebo 启动参数
- `world_name = smart_factory_10robots.world`
- `paused = false`
- `use_sim_time = true`
- `gui = true`
- `headless = false`
- `debug = false`
- `verbose = false`

### 机器人出生点（10 台）
- `R0 (3.5, 1.5, 0.15)`
- `R1 (3.5, 3.0, 0.15)`
- `R2 (1.0, 3.5, 0.15)`
- `R3 (3.5, 7.0, 0.15)`
- `R4 (3.5, 8.5, 0.15)`
- `R5 (1.0, 6.5, 0.15)`
- `R6 (13.0, 1.5, 0.15)`
- `R7 (13.0, 3.0, 0.15)`
- `R8 (13.0, 7.0, 0.15)`
- `R9 (13.0, 8.5, 0.15)`

### 通信参数
- rosbridge 端口：`9090`

## 9.2 机器人参数（`agv_robot.urdf.xacro`）

### 几何与质量
- `base_width = 0.075`
- `base_length = 0.0875`
- `base_height = 0.0375`
- `wheel_radius = 0.02`
- `wheel_width = 0.01`
- `wheel_separation = 0.075`
- `base_link mass = 2.0`

### 差速驱动插件参数
- `updateRate = 30`
- `wheelTorque = 2.0`
- `wheelAcceleration = 0.6`
- `odometrySource = world`

### 激光雷达参数
- `update_rate = 10`
- 水平角：`[-1.57, 1.57]`
- `samples = 180`
- 距离范围：`min=0.04`，`max=5.0`
- 噪声：高斯 `stddev = 0.002`

### 接触/摩擦参数
- `base_link`: `mu1=0.2`, `mu2=0.2`, `kp=250000`, `kd=40`
- `left_wheel/right_wheel`: `mu1=0.8`, `mu2=0.8`, `kp=250000`, `kd=40`
- `caster_wheel`: `mu1=0.05`, `mu2=0.05`, `kp=1000000`, `kd=10`

## 9.3 工厂场景参数（`smart_factory_10robots.world`）

### 物理引擎参数（ODE）
- `max_step_size = 0.003`
- `real_time_factor = 1`
- `real_time_update_rate = 333.33`
- `solver iters = 50`
- `erp = 0.2`
- `contact_surface_layer = 0.001`

### 地面与边界
- 地面 plane：`18 x 12`
- 工厂边界可视盒：`16 x 10`

### 存储区坐标（中心）
- 空桶：`(2.0, 2.0)`，半径 `1.0`
- 绿桶：`(2.0, 8.0)`，半径 `1.0`
- 黄桶：`(14.0, 2.0)`，半径 `1.0`
- 红桶：`(14.0, 8.0)`，半径 `1.0`
- 完成区：`(15.0, 5.0)`，半径 `0.8`

### 工位参数（关键）
- 梳棉等待区：`(5.0, 1.5/3.5/5.5/8.5)`
- 梳棉机台：`(6.0, 1.5/3.5/5.5/8.5)`
- 梳棉完成区：`(7.0, 1.5/3.5/5.5/8.5)`
- 拉伸1等待：`(9.0, 2.5/6.5)`
- 拉伸1机台：`(10.0, 2.5/6.5)`
- 拉伸1完成：`(11.0, 2.5/6.5)`
- 拉伸2等待：`(11.5, 2.5/6.5)`
- 拉伸2机台：`(12.5, 2.5/6.5)`
- 拉伸2完成：`(13.5, 2.5/6.5)`

### Gazebo 相机参数
- 视角位姿：`(8.0, -2.0, 20.0, 0, 1.5, 1.57)`

## 9.4 导航代价地图参数（`config/*.yaml`）

### 通用代价地图
- `robot_radius = 0.15`
- `obstacle_range = 2.5`
- `raytrace_range = 3.0`
- `inflation_radius = 0.3`
- `cost_scaling_factor = 10.0`

### 全局代价地图
- `width = 10.0`, `height = 10.0`, `resolution = 0.05`
- `update_frequency = 2.0`

### 局部代价地图
- `width = 4.0`, `height = 4.0`, `resolution = 0.05`
- `update_frequency = 5.0`

### 局部规划器（TrajectoryPlannerROS）
- `max_vel_x = 0.5`
- `min_vel_x = 0.1`
- `max_vel_theta = 1.0`
- `acc_lim_x = 2.5`
- `xy_goal_tolerance = 0.1`
- `sim_time = 1.7`

> 说明：当前主调度路径控制以自定义调度器与 A* 为主；上述导航参数主要用于 ROS 导航栈配置参考。

---

## 10. 指标体系与数据接口

## 10.1 统计 topic（调度器发布）
- Topic：`/factory/task_statistics`
- 核心字段：
	- 任务：`total/pending/in_progress/completed`
	- 时间：`elapsed_time/avg_task_time`
	- 效率：`completion_rate/throughput_per_min`
	- 冻结窗口：`freeze_window_seconds/freeze_window_elapsed/frz_window_active`
	- 比率指标：`time_efficiency_ratio/task_completion_ratio/deadlock_resolution_ratio/zero_collision_maintenance_ratio/realtime_cycle_ratio_lt_100ms/load_balance_quality_ratio`
	- 冲突：`deadlock_count/yield_count/collision_count`
	- 死锁恢复：`yield_fallback_count/pair_forced_separation_count/pair_emergency_break_count`
	- 公平性：`starvation_prevent_count`
	- 走廊：`corridor_token_active/grant/reuse/release`

### 10.1.1 1800s 统一窗口约定（FRZ-1800）
- 默认冻结窗口：`1800s`（可通过环境变量 `FREEZE_WINDOW_SECONDS` 覆盖）
- `time_efficiency_ratio = min(window / makespan, 1)`
- `task_completion_ratio = completed_tasks / total_tasks`
- `deadlock_resolution_ratio = resolved_deadlocks / deadlock_count`（无死锁时记为 1）
- `zero_collision_maintenance_ratio = 1 - collision_count / collision_risk_interventions`（无风险干预时记为 1）
- `realtime_cycle_ratio_lt_100ms = computation_cycle_lt_100ms_count / computation_cycle_count`
- `load_balance_quality_ratio = 1 - load_balance_gini`

## 10.2 Dashboard API
- `GET /api/data`
- `GET /api/report/status`
- `POST /api/report/generate`

## 10.3 地图流 API
- `GET /video_feed`
- `GET /api/stats`

---

## 11. 运行命令与回归流程

### 11.1 语法检查
```bash
cd /home/qzl/graduate/catkin_ws
/home/qzl/graduate/catkin_ws/.venv/bin/python -m py_compile launch_system.py task_scheduler_ros_clean.py
```

### 11.2 推荐回归顺序
```bash
python3 launch_system.py --mode quick --yes
python3 launch_system.py --mode baseline2 --yes
python3 launch_system.py --mode stress2 --yes
```

### 11.3 关键日志
- `🔒 Deadlock`
- `🧯 Pair separation`
- `🛑 Emergency break pair`
- `🚦 ... yield fallback`

---

## 12. 论文写作映射（直接可用）

### 12.1 方法章节建议
1. 分层冲突治理（L1-L4）
2. 节点-边-时间预约机制
3. 动态优先级 + 反饥饿
4. 双机分离与紧急刹停升级链

### 12.2 实验章节建议
1. 仿真平台与参数表（第9章直接引用）
2. 模式规模设计（第4章）
3. 指标定义（第10章）
4. 显著性分析（置换检验，`tools/analyze_experiments.py`）

### 12.3 统计建议
- 每组重复次数建议 $n \ge 5$
- 报告 `mean/std/p-value`

---

## 13. 常见问题排查

### 13.1 页面打不开
```bash
ss -lntp | grep -E ':5000|:5001|:8000|:9090'
```

### 13.2 ROS Master 异常
```bash
pgrep -af rosmaster
source /opt/ros/noetic/setup.bash
roscore
```

### 13.3 服务存活
```bash
pgrep -af gzserver
pgrep -af rosbridge_websocket
pgrep -af task_scheduler_ros_clean.py
pgrep -af experiment_monitor_dashboard.py
pgrep -af matplotlib_ros_stream.py
```

---

## 14. 已知边界与后续优化方向

1. 阈值参数仍主要依赖经验调参
2. 动态障碍场景仍偏机器人-机器人交互
3. 走廊令牌为几何区域法，可扩展为拓扑瓶颈识别
4. 可考虑学习式优先级或自适应阈值调优

---

## 15. 快速索引

- 启动器：`launch_system.py`
- 调度器：`task_scheduler_ros_clean.py`
- A*：`astar_planner.py`
- Dashboard：`experiment_monitor_dashboard.py`
- 地图流：`matplotlib_ros_stream.py`
- 工厂 world：`src/smart_factory_sim/worlds/smart_factory_10robots.world`
- 机器人 URDF：`src/smart_factory_sim/urdf/agv_robot.urdf.xacro`
- 10 机器人 launch：`src/smart_factory_sim/launch/smart_factory_10_robots.launch`
- 分析工具：`tools/run_experiments.py`、`tools/analyze_experiments.py`、`tools/generate_paper_materials.py`
