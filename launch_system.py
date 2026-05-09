#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@brief 智能工厂完整系统启动器

该脚本是整个仿真系统的统一入口，负责按顺序启动以下 7 项服务：
    1. ROS Master (roscore)
    2. Gazebo 仿真环境 (10 台机器人)
    3. ROS Bridge (WebSocket 桥接)
    4. 任务调度器 (task_scheduler_ros_clean.py)
    5. 实验监控 Dashboard (端口 5001)
    6. 2D 地图可视化 (端口 5000)
    7. Web 控制面板静态服务器 (端口 8000)

启动前提供实验模式选择菜单（快速测试/基准实验/压力测试/监控模式），
通过环境变量 EXPERIMENT_MODE 传递给调度器和 Dashboard。
"""

import subprocess
import time
import os
import webbrowser
import signal
import sys
import socket
import psutil
import argparse
import shutil


# ============================================================
#  SmartFactorySystem - 系统启动器
# ============================================================

class SmartFactorySystem:
    """
    @brief 智能工厂系统启动器

    封装了所有服务的启动、监控、清理逻辑。
    支持端口冲突检测、进程存活检查和优雅退出。
    """

    def __init__(self):
        """
        @brief 初始化启动器

        设置工作目录和进程跟踪列表。
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_dir = os.path.expanduser("~/graduate/catkin_ws")
        self.base_dir = (
            script_dir
            if os.path.exists(os.path.join(script_dir, 'task_scheduler_ros_clean.py'))
            else default_dir
        )
        self.processes = []     # 后台进程列表 [(name, Popen)]
        self.terminals = []     # 终端窗口列表 [(name, Popen)]
        self.headless = False   # 无图形终端模式

    # ============================================================
    #  通用工具方法
    # ============================================================

    def log(self, message, level="INFO"):
        """
        @brief 统一日志输出

        根据级别添加不同的 emoji 前缀。

        @param message: 日志内容字符串
        @param level:   日志级别（INFO/WARN/ERROR/STEP）
        """
        prefix = {
            "INFO": "✅",
            "WARN": "⚠️ ",
            "ERROR": "❌",
            "STEP": "📍"
        }.get(level, "  ")
        print(f"{prefix} {message}")

    def check_port(self, port):
        """
        @brief 检查端口是否被占用

        @param port: 端口号
        @return: True 表示端口已被占用
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0

    def kill_port(self, port):
        """
        @brief 终止占用指定端口的进程

        优先使用 psutil 精确查找，失败时使用 lsof 备用方案。

        @param port: 需要释放的端口号
        @return: True 表示成功终止
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == port:
                            self.log(f"Cleaning port {port} (PID: {proc.pid})")
                            proc.terminate()
                            proc.wait(timeout=2)
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            # 备用方案：使用 lsof + kill
            subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
                           shell=True, capture_output=True)
        time.sleep(1)
        return False

    def check_process(self, name):
        """
        @brief 检查指定名称的进程是否正在运行

        @param name: 进程名称（支持模糊匹配）
        @return: True 表示进程存在
        """
        try:
            result = subprocess.run(['pgrep', '-f', name],
                                    capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False

    def launch_service_command(self, service_name, title, shell_cmd):
        """
        @brief 启动服务命令（支持终端模式与 headless 模式）

        @param service_name: 服务显示名
        @param title:        终端标题（仅终端模式使用）
        @param shell_cmd:    实际执行的 shell 命令
        @return: Popen 对象
        """
        if self.headless:
            proc = subprocess.Popen(
                ['bash', '-lc', shell_cmd],
                cwd=self.base_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.processes.append((service_name, proc))
            return proc

        cmd = [
            'gnome-terminal', '--tab', f'--title={title}', '--',
            'bash', '-c', f'{shell_cmd}; exec bash'
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.terminals.append((service_name, proc))
        return proc

    def kill_process(self, name):
        """
        @brief 终止指定名称的进程

        先发送 SIGTERM，等待 1 秒后强制 SIGKILL。

        @param name: 进程名称（支持模糊匹配）
        """
        if self.check_process(name):
            self.log(f"Cleaning process: {name}")
            subprocess.run(['pkill', '-f', name], capture_output=True)
            time.sleep(1)
            subprocess.run(['pkill', '-9', '-f', name], capture_output=True)
            time.sleep(1)
    
    def cleanup_old_processes(self):
        """
        @brief 清理旧的进程和端口

        终止可能残留的 Python 脚本进程，并释放 5000/5001/8000/9090 端口。
        """
        self.log("Cleaning old processes and ports...", "STEP")

        # 需要清理的 Python 脚本进程
        processes = [
            'matplotlib_ros_stream.py',
            'task_scheduler_ros.py',
            'task_scheduler_ros_clean.py',
            'experiment_monitor_dashboard.py',
            'experiment_dashboard_enhanced.py',
            'realtime_web_dashboard.py'
        ]
        for proc in processes:
            self.kill_process(proc)

        # 需要释放的端口
        ports = [5000, 5001, 8000, 9090]
        for port in ports:
            if self.check_port(port):
                self.log(f"Releasing port: {port}")
                self.kill_port(port)

        self.log("Cleanup completed")
    
    # ============================================================
    #  服务启动方法
    # ============================================================

    def start_roscore(self):
        """
        @brief 启动 ROS Master

        在 gnome-terminal 中执行 roscore。若已运行则跳过。
        等待最多 15 秒确认 rosmaster 进程存在。

        @return: True 表示启动成功
        """
        if self.check_process('rosmaster'):
            self.log("ROS Master is already running")
            return True

        self.log("Starting ROS Master...", "STEP")

        self.launch_service_command(
            'ROS Master',
            'ROS Master',
            'source /opt/ros/noetic/setup.bash && roscore'
        )

        # 等待 rosmaster 进程出现
        for i in range(15):
            time.sleep(1)
            if self.check_process('rosmaster'):
                self.log("ROS Master started")
                return True

            self.log("ROS Master startup timeout", "ERROR")
        return False

    def start_gazebo(self):
        """
        @brief 启动 Gazebo 仿真环境

        加载 smart_factory_10_robots.launch，包含工厂模型和 10 台机器人。
        等待约 15 秒让 Gazebo 完成加载。

        @return: True 表示启动成功（或可能未完全启动但继续执行）
        """
        if self.check_process('gzserver'):
            self.log("Gazebo is already running")
            return True

        self.log("Starting Gazebo simulation (10 robots)...", "STEP")

        self.launch_service_command(
            'Gazebo',
            'Gazebo 10 Robots',
            f'source /opt/ros/noetic/setup.bash && '
            f'source {self.base_dir}/devel/setup.bash && '
            f'roslaunch smart_factory_sim smart_factory_10_robots.launch'
        )

        self.log("Waiting for Gazebo to load...")
        time.sleep(15)

        if self.check_process('gzserver'):
            self.log("Gazebo started")
            return True
        else:
            self.log("Gazebo may not be fully started", "WARN")
            return True             # 继续执行，不阻塞后续步骤

    def start_rosbridge(self):
        """
        @brief 启动 ROS Bridge WebSocket 服务

        为 Web 前端提供 ROS 话题的 WebSocket 桥接（端口 9090）。

        @return: True 表示启动成功
        """
        if self.check_process('rosbridge_websocket') or self.check_port(9090):
            self.log("ROS Bridge is already running")
            return True

        # Gazebo launch 文件中可能已包含 rosbridge，先等待一段时间避免重复拉起
        self.log("Checking whether ROS Bridge is auto-started by Gazebo...")
        for _ in range(8):
            time.sleep(1)
            if self.check_process('rosbridge_websocket') or self.check_port(9090):
                self.log("ROS Bridge is ready (auto-started by launch file)")
                return True

        self.log("Starting ROS Bridge...", "STEP")

        self.launch_service_command(
            'ROS Bridge',
            'ROS Bridge',
            f'source /opt/ros/noetic/setup.bash && '
            f'source {self.base_dir}/devel/setup.bash && '
            f'roslaunch rosbridge_server rosbridge_websocket.launch'
        )

        # 等待端口就绪
        for _ in range(10):
            time.sleep(1)
            if self.check_port(9090):
                self.log("ROS Bridge started")
                return True

        self.log("ROS Bridge startup timeout", "WARN")
        return False

    def start_task_scheduler_with_mode(self, mode, algorithm='full', test_id=None, ablation_mode='A0'):
        """
        @brief 启动任务调度器（带实验模式与算法模式）

        通过环境变量 EXPERIMENT_MODE 与 ALGORITHM_MODE 将模式传递给调度器脚本。

        @param mode: 实验模式字符串（minimal/quick/baseline/stress/monitor）
        @param algorithm: 算法模式字符串（naive/path_only/path_reservation/full 及 rule_greedy/cbs_based/auction_based/proposed）
        @param test_id: 实验编号（为空时，proposed/full 自动生成）
        @param ablation_mode: 消融模式（A0/A1/A2/A3/A4，默认 A0）
        @return: True 表示启动成功
        """
        if self.check_process('task_scheduler_ros_clean.py'):
            self.log("Task scheduler is already running")
            return True

        algorithm_key = (algorithm or '').strip().lower()
        is_proposed = algorithm_key in ('full', 'proposed')
        resolved_ablation_mode = (ablation_mode or 'A0').strip().upper()
        if resolved_ablation_mode in ('NONE', 'OFF', 'DISABLED', 'FALSE', '0'):
            resolved_ablation_mode = 'A0'
        if resolved_ablation_mode not in {'A0', 'A1', 'A2', 'A3', 'A4'}:
            self.log(f"Unknown ablation mode {ablation_mode}, fallback to A0", "WARN")
            resolved_ablation_mode = 'A0'

        if resolved_ablation_mode != 'A0' and not is_proposed:
            self.log(
                f"Ablation {resolved_ablation_mode} requires Proposed. Auto-switched algorithm from {algorithm} to proposed",
                "WARN"
            )
            algorithm = 'proposed'
            algorithm_key = 'proposed'
            is_proposed = True

        resolved_test_id = (test_id or '').strip()
        if is_proposed and not resolved_test_id:
            resolved_test_id = f"proposed-{mode}-{time.strftime('%Y%m%d_%H%M%S')}"

        self.log(
            f"Starting task scheduler (mode: {mode}, algorithm: {algorithm}, ablation: {resolved_ablation_mode})...",
            "STEP"
        )
        if resolved_test_id:
            self.log(f"Using test ID: {resolved_test_id}")

        self.launch_service_command(
            'Task Scheduler',
            'Task Scheduler',
            f'source /opt/ros/noetic/setup.bash && '
            f'source {self.base_dir}/devel/setup.bash && '
            f'cd {self.base_dir} && '
            f'echo ">>> Task scheduler start - mode: {mode}, algorithm: {algorithm}" && '
            f'export EXPERIMENT_MODE={mode} && '
            f'export ALGORITHM_MODE={algorithm} && '
            f'export ABLATION_MODE={resolved_ablation_mode} && '
            +
            (f'export TEST_ID={resolved_test_id} && ' if resolved_test_id else '') +
            f'python3 task_scheduler_ros_clean.py'
        )

        time.sleep(3)
        self.log("Task scheduler started")
        return True

    def start_task_scheduler(self):
        """
        @brief 启动任务调度器（无实验模式）

        用于不需要指定实验模式的场景。

        @return: True 表示启动成功
        """
        if self.check_process('task_scheduler_ros_clean.py'):
            self.log("Task scheduler is already running")
            return True

        self.log("Starting task scheduler...", "STEP")

        self.launch_service_command(
            'Task Scheduler',
            'Task Scheduler',
            f'source /opt/ros/noetic/setup.bash && '
            f'source {self.base_dir}/devel/setup.bash && '
            f'cd {self.base_dir} && '
            f'echo ">>> Task scheduler running..." && '
            f'python3 task_scheduler_ros_clean.py'
        )

        time.sleep(3)
        self.log("Task scheduler started")
        return True

    def start_dashboard(self, experiment_mode, algorithm_mode='full'):
        """
        @brief 启动实验监控 Dashboard

        以后台进程方式启动 Flask Dashboard（端口 5001），
        通过环境变量传递实验模式。等待最多 15 秒确认端口可用。

        @param experiment_mode: 实验模式字符串
        @param algorithm_mode: 算法模式字符串
        @return: True 表示启动成功
        """
        # 端口冲突检查与清理
        if self.check_port(5001):
            self.log("Port 5001 is occupied, cleaning it...")
            self.kill_port(5001)

        self.log("Starting experiment monitoring dashboard (port 5001)...", "STEP")

        dashboard_script = os.path.join(self.base_dir, 'experiment_monitor_dashboard.py')

        # 设置环境变量
        env = os.environ.copy()
        env['EXPERIMENT_MODE'] = experiment_mode
        env['ALGORITHM_MODE'] = algorithm_mode

        proc = subprocess.Popen(
            ['python3', dashboard_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=self.base_dir,
            env=env
        )
        self.processes.append(('Dashboard', proc))

        # 等待 Dashboard 端口就绪
        self.log("Waiting for dashboard startup...")
        for i in range(15):
            time.sleep(1)
            if self.check_port(5001):
                self.log("Dashboard started (http://localhost:5001)")
                return True

            self.log("Dashboard startup timeout", "WARN")
        return False

    def start_map_visualization(self):
        """
        @brief 启动 2D 地图可视化服务

        在 gnome-terminal 中启动 matplotlib_ros_stream.py（端口 5000）。

        @return: True 表示启动成功
        """
        # 端口冲突检查与清理
        if self.check_port(5000):
            self.log("Port 5000 is occupied, cleaning it...")
            self.kill_port(5000)

        self.log("Starting 2D map stream (port 5000)...", "STEP")

        map_script = os.path.join(self.base_dir, 'matplotlib_ros_stream.py')
        if not os.path.exists(map_script):
            self.log("Map visualization script not found", "WARN")
            return False

        self.launch_service_command(
            'Map Visualization',
            'Matplotlib Stream',
            f'source /opt/ros/noetic/setup.bash && '
            f'source {self.base_dir}/devel/setup.bash && '
            f'cd {self.base_dir} && '
            f'echo ">>> Map visualization running..." && '
            f'python3 matplotlib_ros_stream.py'
        )

        # 等待端口就绪
        for i in range(10):
            time.sleep(1)
            if self.check_port(5000):
                self.log("Map visualization started (http://localhost:5000)")
                return True

            self.log("Map visualization startup timeout", "WARN")
        return False

    def start_web_server(self):
        """
        @brief 启动 Web 静态文件服务器

        使用 Python 内置 http.server 模块（端口 8000），
        用于提供 gazebo_control_with_tasks.html 等静态文件。

        @return: True 表示启动成功
        """
        # 端口冲突检查与清理
        if self.check_port(8000):
            self.log("Port 8000 is occupied, cleaning it...")
            self.kill_port(8000)

        self.log("Starting Web control server (port 8000)...", "STEP")

        self.launch_service_command(
            'Web Server',
            'Web Server',
            f'cd {self.base_dir} && '
            f'echo ">>> Web server running..." && '
            f'python3 -m http.server 8000'
        )

        # 等待端口就绪
        for i in range(5):
            time.sleep(1)
            if self.check_port(8000):
                self.log("Web server started (http://localhost:8000)")
                return True

            self.log("Web server startup timeout", "WARN")
        return False
    
    # ============================================================
    #  系统验证与浏览器打开
    # ============================================================

    def open_web_pages(self):
        """
        @brief 自动打开 Web 页面（仅两个页面）

        依次在默认浏览器中打开 Dashboard 与控制面板。
        2D 地图由控制面板内嵌显示（流服务端口 5000）。
        """
        self.log("Opening web pages...", "STEP")
        time.sleep(3)

        urls = [
            ('http://localhost:5001', 'Experiment Dashboard'),
            (f"http://localhost:8000/gazebo_control_with_tasks.html?v={int(time.time())}", 'Web Control Panel (embedded 2D map)'),
        ]

        for url, name in urls:
            try:
                self.log(f"Opening {name}: {url}")
                opened = webbrowser.open(url)
                if not opened:
                    self.log(f"Default browser API did not open {name}, trying xdg-open...", "WARN")
                    if shutil.which('xdg-open'):
                        ret = subprocess.run(
                            ['xdg-open', url],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        if ret.returncode != 0:
                            self.log(f"xdg-open failed for: {name}", "WARN")
                            self.log(f"Please open manually: {url}")
                    else:
                        self.log("xdg-open not found; cannot auto-open browser", "WARN")
                        self.log(f"Please open manually: {url}")
                time.sleep(2)
            except Exception as e:
                self.log(f"Failed to auto-open {name}: {e}", "WARN")
                self.log(f"Please open manually: {url}")

    def verify_system(self):
        """
        @brief 验证所有服务的运行状态

        逐项检查 ROS Master、Gazebo、各端口服务是否正常。

        @return: True 表示所有服务均正常运行
        """
        self.log("Verifying system status...", "STEP")

        checks = [
            ('ROS Master',          lambda: self.check_process('rosmaster')),
            ('Gazebo',              lambda: self.check_process('gzserver')),
            ('ROS Bridge',          lambda: self.check_process('rosbridge')),
            ('Task Scheduler',      lambda: self.check_process('task_scheduler_ros_clean.py')),
            ('Dashboard (5001)',    lambda: self.check_port(5001)),
            ('Map Stream (5000)',   lambda: self.check_port(5000)),
            ('Web Server (8000)',   lambda: self.check_port(8000)),
        ]

        all_ok = True
        for name, check_func in checks:
            ok = check_func()
            status = "✅" if ok else "❌"
            print(f"  {status} {name}")
            if not ok:
                all_ok = False

        return all_ok
    
    # ============================================================
    #  清理与退出
    # ============================================================

    def cleanup(self, signum=None, frame=None):
        """
        @brief 优雅停止所有服务并退出

        作为 SIGINT/SIGTERM 信号处理器注册。依次终止后台进程和脚本进程。

        @param signum: 信号编号（由信号处理器传入，可为 None）
        @param frame:  栈帧（由信号处理器传入，可为 None）
        """
        print("\n\n" + "=" * 70)
        self.log("Stopping all services...", "STEP")

        # 停止由 Popen 启动的后台进程
        for name, proc in reversed(self.processes):
            try:
                self.log(f"Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception:
                pass

        # 清理特定 Python 脚本进程
        processes_to_kill = [
            'matplotlib_ros_stream.py',
            'task_scheduler_ros_clean.py',
            'experiment_monitor_dashboard.py',
            'experiment_dashboard_enhanced.py'
        ]
        for proc_name in processes_to_kill:
            self.kill_process(proc_name)

        self.log("All services stopped")
        print("=" * 70)
        sys.exit(0)
    
    # ============================================================
    #  主运行流程
    # ============================================================

    def run(self, preset_mode=None, preset_algorithm=None, preset_ablation=None, auto_yes=False, open_browser=True, headless=False):
        """
        @brief 系统主运行函数

        执行流程：
        1. 显示实验模式选择菜单（1~5）
        2. 清理旧进程和端口
        3. 按顺序启动 7 项服务
        4. 验证系统状态
        5. 自动打开浏览器页面
        6. 进入监控循环，等待 Ctrl+C 退出
        """
        print("\n" + "=" * 70)
        print("🏭 Smart Factory Full System Launcher v2.1")
        print("=" * 70)
        
        # 注册信号处理器（Ctrl+C / kill）
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

        self.headless = headless
        if not self.headless and shutil.which('gnome-terminal') is None:
            self.log("gnome-terminal not detected, switched to headless mode", "WARN")
            self.headless = True

        mode_map = {
            'minimal': 'Minimal Test',
            'quick': 'Quick Test',
            'baseline': 'Baseline Test',
            'stress': 'Stress Test',
            'monitor': 'Monitoring Mode',
            's2_core': 'S2 Core Comparison (same factory)',
            # 兼容旧模式名
            'baseline2': 'Baseline Test (legacy alias)',
            'stress2': 'Stress Test (legacy alias)',
            's2_realtime': 'Baseline Test (legacy alias)',
            's2_congestion': 'Stress Test (legacy alias)',
            's2_peak': 'Stress Test (legacy alias)',
        }
        algorithm_map = {
            'naive': 'Naive',
            'path_only': 'Path Only',
            'path_reservation': 'Path+Reservation',
            'full': 'Full System',
            'rule_greedy': 'Rule-based (Greedy)',
            'cbs_based': 'CBS-based',
            'auction_based': 'Auction-based',
            'proposed': 'Proposed',
        }

        if preset_mode:
            experiment_mode = preset_mode
            mode_name = mode_map[experiment_mode]
            self.log(f"Using CLI experiment mode: {mode_name} ({experiment_mode})")
        else:
            # ---------- 实验模式选择菜单 ----------
            print("\nSelect experiment mode:")
            print("  1. 🧪 Minimal Test (19 tasks, ~5 min, Proposed only)")
            print("  2. ⚡ Quick Test (40 tasks, ~10 min, Proposed only)")
            print("  3. 📊 Baseline Test (79 tasks, ~15 min, Proposed only)")
            print("  4. 💪 Stress Test (316 tasks, ~60 min, Proposed only)")
            print("  5. 👁️  Monitoring Mode (316 tasks, continuous)")
            print("  6. 🧪 S2 Core Comparison (316 tasks, cross-algorithm)")
            print("  7. ❌ Cancel")

            while True:
                choice = input("\nEnter option (1-7): ").strip()
                if choice == '1':
                    experiment_mode = 'minimal'
                    mode_name = 'Minimal Test'
                    break
                elif choice == '2':
                    experiment_mode = 'quick'
                    mode_name = 'Quick Test'
                    break
                elif choice == '3':
                    experiment_mode = 'baseline'
                    mode_name = 'Baseline Test'
                    break
                elif choice == '4':
                    experiment_mode = 'stress'
                    mode_name = 'Stress Test'
                    break
                elif choice == '5':
                    experiment_mode = 'monitor'
                    mode_name = 'Monitoring Mode'
                    break
                elif choice == '6':
                    experiment_mode = 's2_core'
                    mode_name = 'S2 Core Comparison (same factory)'
                    break
                elif choice == '7':
                    print("Startup canceled")
                    return False
                else:
                    print("Invalid option, please try again")

        if preset_algorithm:
            algorithm_mode = preset_algorithm
            algorithm_name = algorithm_map[algorithm_mode]
            self.log(f"Using CLI algorithm mode: {algorithm_name} ({algorithm_mode})")
        else:
            print("\nSelect algorithm mode:")
            print("  1. 🟥 Naive")
            print("  2. 🟧 Path Only")
            print("  3. 🟨 Path+Reservation")
            print("  4. 🟩 Full System")
            print("  5. 📐 Rule-based (Greedy)")
            print("  6. 🧠 CBS-based")
            print("  7. 💰 Auction-based")
            print("  8. 🏆 Proposed")

            while True:
                choice = input("\nEnter algorithm option (1-8): ").strip()
                if choice == '1':
                    algorithm_mode = 'naive'
                    algorithm_name = 'Naive'
                    break
                elif choice == '2':
                    algorithm_mode = 'path_only'
                    algorithm_name = 'Path Only'
                    break
                elif choice == '3':
                    algorithm_mode = 'path_reservation'
                    algorithm_name = 'Path+Reservation'
                    break
                elif choice == '4':
                    algorithm_mode = 'full'
                    algorithm_name = 'Full System'
                    break
                elif choice == '5':
                    algorithm_mode = 'rule_greedy'
                    algorithm_name = 'Rule-based (Greedy)'
                    break
                elif choice == '6':
                    algorithm_mode = 'cbs_based'
                    algorithm_name = 'CBS-based'
                    break
                elif choice == '7':
                    algorithm_mode = 'auction_based'
                    algorithm_name = 'Auction-based'
                    break
                elif choice == '8':
                    algorithm_mode = 'proposed'
                    algorithm_name = 'Proposed'
                    break
                else:
                    print("Invalid option, please try again")

        proposed_family = algorithm_mode in ('full', 'proposed')
        ablation_prompt_allowed = proposed_family

        if preset_ablation:
            ablation_mode = str(preset_ablation).strip().upper()
            if ablation_mode in ('NONE', 'OFF', 'DISABLED', 'FALSE', '0'):
                ablation_mode = 'A0'
            if ablation_mode not in {'A0', 'A1', 'A2', 'A3', 'A4'}:
                self.log(f"Unknown --ablation={preset_ablation}, fallback to A0", "WARN")
                ablation_mode = 'A0'
            if not proposed_family and ablation_mode != 'A0':
                self.log(
                    f"Ablation {ablation_mode} is only available for Proposed/Full. Ignored for {algorithm_mode} (use A0).",
                    "WARN"
                )
                ablation_mode = 'A0'
        else:
            if ablation_prompt_allowed:
                print("\nSelect ablation mode:")
                print("  1. A0 - Full proposed stack")
                print("  2. A1 - No spacetime reservation")
                print("  3. A2 - No deadlock-governance scan")
                print("  4. A3 - No fairness compensation")
                print("  5. A4 - No progressive recovery")

                while True:
                    choice = input("\nEnter ablation option (1-5): ").strip()
                    if choice == '1':
                        ablation_mode = 'A0'
                        break
                    elif choice == '2':
                        ablation_mode = 'A1'
                        break
                    elif choice == '3':
                        ablation_mode = 'A2'
                        break
                    elif choice == '4':
                        ablation_mode = 'A3'
                        break
                    elif choice == '5':
                        ablation_mode = 'A4'
                        break
                    else:
                        print("Invalid option, please try again")
            else:
                ablation_mode = 'A0'

        if proposed_family:
            print(f"\nSelected: {mode_name} | Algorithm: {algorithm_name} | Ablation: {ablation_mode}")
        else:
            print(f"\nSelected: {mode_name} | Algorithm: {algorithm_name}")

        # ---------- 检测并清理旧服务 ----------
        if self.check_process('rosmaster'):
            print("\nExisting ROS process detected")
            if auto_yes:
                choice = 'y'
                self.log("--yes enabled, auto-restarting all services")
            else:
                choice = input("Restart all services? (y/N): ").strip().lower()
            if choice == 'y':
                self.log("Cleaning all existing services...")
                subprocess.run("killall -9 rosmaster roscore gzserver gzclient 2>/dev/null",
                               shell=True, capture_output=True)
                time.sleep(3)
        
        # 清理旧进程和端口
        self.cleanup_old_processes()
        time.sleep(2)

        # ---------- 按顺序启动 7 项服务 ----------
        print("\n" + "=" * 70)
        print(f"Starting all services - mode: {mode_name} | algorithm: {algorithm_name}")
        print("=" * 70 + "\n")
        
        # 按步骤启动各服务
        steps = [
            ("1/7", "ROS Master",                    self.start_roscore),
            ("2/7", "Gazebo Simulation",             self.start_gazebo),
            ("3/7", "ROS Bridge",                    self.start_rosbridge),
            ("4/7", f"Task Scheduler ({mode_name}, {algorithm_name}, {ablation_mode})", lambda: self.start_task_scheduler_with_mode(experiment_mode, algorithm_mode, ablation_mode=ablation_mode)),
            ("5/7", "Experiment Dashboard",           lambda: self.start_dashboard(experiment_mode, algorithm_mode)),
            ("6/7", "2D Map Stream",                 self.start_map_visualization),
            ("7/7", "Web Control Server",            self.start_web_server),
        ]

        for step_num, step_name, step_func in steps:
            print(f"\n[{step_num}] {step_name}")
            print("-" * 70)
            if not step_func():
                self.log(f"{step_name} failed to start, continuing...", "WARN")
            time.sleep(1)

        # ---------- 等待服务稳定并验证 ----------
        print("\n" + "=" * 70)
        self.log("Waiting for all services to stabilize...", "STEP")
        time.sleep(5)

        print("\n" + "=" * 70)
        self.verify_system()

        # ---------- 打开浏览器页面 ----------
        if open_browser:
            print("\n" + "=" * 70)
            print("[Final] Open Web UI")
            print("-" * 70)
            self.open_web_pages()
        else:
            self.log("--no-browser set, skipping auto-open")
        
        # ---------- 启动完成，打印使用说明 ----------
        print("\n" + "=" * 70)
        print(f"System startup completed - mode: {mode_name} | algorithm: {algorithm_name} | ablation: {ablation_mode}")
        print("=" * 70 + "\n")

        print("Available pages (2):")
        print("   1. Experiment Dashboard: http://localhost:5001")
        print(f"      - Current mode: {mode_name}")
        print(f"      - Current algorithm: {algorithm_name}")
        print(f"      - Ablation mode: {ablation_mode}")
        print("      - Real-time task progress, robot states, and metrics")
        print("      - Click 'Generate Experiment Report'")
        print()
        print("   2. Web Control Panel: http://localhost:8000/gazebo_control_with_tasks.html")
        print("      - Manual robot control + embedded 2D map")
        print("      - Map stream: http://localhost:5000/video_feed (backend endpoint)")
        print()

        print("Notes:")
        print(f"   - Experiment auto-started ({mode_name})")
        print(f"   - Ablation mode: {ablation_mode}")
        print(f"   - Startup mode: {'headless (background processes)' if self.headless else 'terminal (multi-window)'}")
        print(f"   - Auto-open browser: {'yes' if open_browser else 'no'}")
        print("   - Tasks are being assigned automatically")
        print("   - Dashboard refreshes every 2 seconds")
        print("   - Click 'Generate Experiment Report' after completion")
        print("   - Reports are generated in paper_materials/")
        print("   - Press Ctrl+C to stop all services")
        print()
        print("System is running. Press Ctrl+C to stop all services...")
        print("=" * 70 + "\n")

        # ---------- 监控循环 ----------
        try:
            while True:
                time.sleep(5)
                # 周期性检查 ROS Master 是否存活
                if not self.check_process('rosmaster'):
                    self.log("ROS Master has stopped", "WARN")
                    break
        except KeyboardInterrupt:
            pass

        self.cleanup()


# ============================================================
#  入口函数
# ============================================================

def main():
    """
    @brief 程序入口

    创建 SmartFactorySystem 实例并执行主运行流程。
    """
    try:
        parser = argparse.ArgumentParser(description='Smart Factory Full System Launcher')
        parser.add_argument(
            '--mode',
            choices=['minimal', 'quick', 'baseline', 'baseline2', 'stress', 'stress2', 'monitor',
                     's2_core', 's2_realtime', 's2_congestion', 's2_peak'],
            help='Experiment mode. If set, interactive menu is skipped.'
        )
        parser.add_argument(
            '--algorithm',
            choices=['naive', 'path_only', 'path_reservation', 'full',
                     'rule_greedy', 'cbs_based', 'auction_based', 'proposed'],
            help='Algorithm mode. If set, interactive menu is skipped.'
        )
        parser.add_argument(
            '--ablation',
            choices=['A0', 'A1', 'A2', 'A3', 'A4'],
            default=None,
            help='Ablation mode for proposed/full runs: A0(full), A1(no reservation), A2(no deadlock scan), A3(no fairness), A4(no progressive recovery).'
        )
        parser.add_argument(
            '--no-browser',
            action='store_true',
            help='Do not auto-open browser pages after startup.'
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Auto-confirm restart when existing services are detected.'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run all services in background mode without gnome-terminal.'
        )
        args = parser.parse_args()

        system = SmartFactorySystem()
        system.run(
            preset_mode=args.mode,
            preset_algorithm=args.algorithm,
            preset_ablation=args.ablation,
            auto_yes=args.yes,
            open_browser=not args.no_browser,
            headless=args.headless
        )
    except Exception as e:
        print(f"\n❌ System startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
