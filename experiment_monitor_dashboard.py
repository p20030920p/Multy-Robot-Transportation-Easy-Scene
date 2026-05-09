#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@brief 实验监控 Dashboard

该模块启动一个 Flask Web 服务器（端口 5001），订阅 ROS 话题以实时接收
任务统计、机器人状态和系统通知，通过 RESTful API 提供给前端页面展示。

主要功能：
    - 订阅 /factory/task_statistics：任务进度与统计
    - 订阅 /factory/robot_status：各机器人实时状态
    - 订阅 /factory/notifications：系统事件通知
    - 提供 /api/data 接口返回全部监控数据
    - 提供 /api/report/generate 接口触发报告生成
"""

import rospy
from std_msgs.msg import String
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import threading
import time
import subprocess
import os
from datetime import datetime
import copy

# ============================================================
#  Flask 应用初始化
# ============================================================

app = Flask(__name__)
CORS(app)                               # 启用跨域支持


# ============================================================
#  全局数据存储
# ============================================================

dashboard_data = {
    'task_stats': {                      # 任务统计数据
        'total_tasks': 0,
        'completed_tasks': 0,
        'pending_tasks': 0,
        'in_progress_tasks': 0,
        'elapsed_time': 0,
        'completion_rate': 0,
        'task_completion_rate_pct': 0,
        'avg_task_time': 0,
        'throughput_per_min': 0,
        'algorithm_mode': os.environ.get('ALGORITHM_MODE', 'unknown'),
        'makespan': 0,
        'deadlock_resolution_ratio': 1,
        'total_travel_distance': 0,
        'load_balance_gini': 0,
        'deadlock_count': 0,
        'yield_count': 0,
        'recovery_count': 0,
        'collision_count': 0,
        'scalability_robot_count': 0,
        'scalability_task_count': 0
    },
    'robot_stats': {},                   # 各机器人状态 {robot_id: {...}}
    'events': [],                        # 系统事件列表（最新在前）
    'system_status': 'INITIALIZING',     # 系统状态字符串
    'last_update': None,                 # 最后更新时间
    'experiment_mode': os.environ.get('EXPERIMENT_MODE', 'unknown'),  # 实验模式
    'algorithm_mode': os.environ.get('ALGORITHM_MODE', 'unknown'),    # 算法模式
    'report_status': {
        'generating': False,
        'generated': False,
        'generated_at': None,
        'duration_sec': None,
        'trigger_source': None,
        'auto_triggered': False,
        'message': 'Report has not been generated yet'
    }
}

ros_connected = False                    # ROS 连接状态标志
data_lock = threading.Lock()             # 数据访问锁
report_lock = threading.Lock()           # 报告生成锁


def is_experiment_completed_unlocked():
    """在已持有 data_lock 的上下文中判断实验是否完成。"""
    stats = dashboard_data.get('task_stats', {})
    total = int(stats.get('total_tasks', 0) or 0)
    completed = int(stats.get('completed_tasks', 0) or 0)
    rejected = int(stats.get('rejected_tasks', 0) or 0)
    terminal = int(stats.get('terminal_tasks', completed + rejected) or 0)
    pending = int(stats.get('pending_tasks', 0) or 0)
    in_progress = int(stats.get('in_progress_tasks', stats.get('active_tasks', 0)) or 0)
    return total > 0 and terminal >= total and pending <= 0 and in_progress <= 0


def run_report_generation(trigger_source='manual'):
    """后台执行报告生成，并更新 report_status。"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(base_dir, 'tools', 'generate_paper_materials.py')
    start_ts = time.time()

    if not os.path.exists(script):
        with data_lock:
            dashboard_data['report_status'].update({
                'generating': False,
                'generated': False,
                'duration_sec': round(time.time() - start_ts, 2),
                'trigger_source': trigger_source,
                'message': 'Report generator script not found'
            })
        return

    try:
        proc = subprocess.Popen(
            ['python3', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=base_dir
        )
        try:
            stdout_data, stderr_data = proc.communicate(timeout=180)
            success = proc.returncode == 0
            err_msg = stderr_data.decode(errors='ignore').strip()
            if success:
                message = 'Report generated successfully. Files were updated in paper_materials/'
            else:
                message = f'Report generation failed: {err_msg[:200]}' if err_msg else 'Report generation failed'
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            success = False
            message = 'Report generation timed out (>180s). Please check data scale or script state'

        with data_lock:
            dashboard_data['report_status'].update({
                'generating': False,
                'generated': success,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if success else None,
                'duration_sec': round(time.time() - start_ts, 2),
                'trigger_source': trigger_source,
                'message': message
            })
    except Exception as e:
        with data_lock:
            dashboard_data['report_status'].update({
                'generating': False,
                'generated': False,
                'duration_sec': round(time.time() - start_ts, 2),
                'trigger_source': trigger_source,
                'message': f'Report generation exception: {str(e)}'
            })


def start_report_generation(trigger_source='manual'):
    """尝试启动一次报告生成任务（异步）。"""
    with report_lock:
        with data_lock:
            if dashboard_data['report_status'].get('generating', False):
                return False, 'Report generation is in progress, please wait'

            dashboard_data['report_status'].update({
                'generating': True,
                'trigger_source': trigger_source,
                'message': 'Generating report...'
            })

        thread = threading.Thread(
            target=run_report_generation,
            args=(trigger_source,),
            daemon=True
        )
        thread.start()
        return True, 'Report generation task started'


# ============================================================
#  ROS 回调函数
# ============================================================

def task_statistics_callback(msg):
    """
    @brief 任务统计话题回调

    解析 /factory/task_statistics 消息，更新全局任务统计数据。

    @param msg: ROS String 消息，data 字段为 JSON 格式的任务统计
    """
    global dashboard_data
    try:
        data = json.loads(msg.data)
        should_trigger_auto = False
        with data_lock:
            dashboard_data['task_stats'].update(data)
            dashboard_data['algorithm_mode'] = data.get('algorithm_mode', dashboard_data.get('algorithm_mode', 'unknown'))
            dashboard_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dashboard_data['system_status'] = 'RUNNING'

            if (is_experiment_completed_unlocked()
                    and not dashboard_data['report_status'].get('auto_triggered', False)
                    and not dashboard_data['report_status'].get('generating', False)
                    and not dashboard_data['report_status'].get('generated', False)):
                dashboard_data['report_status']['auto_triggered'] = True
                should_trigger_auto = True

        print(f"📊 Stats update: completed={data.get('completed_tasks', 0)}/{data.get('total_tasks', 0)}")

        if should_trigger_auto:
            print("📄 Experiment completion detected, auto-triggering report generation...")
            start_report_generation('auto')
    except Exception as e:
        print(f"⚠️ Failed to parse task statistics: {e}")


def robot_status_callback(msg):
    """
    @brief 机器人状态话题回调

    解析 /factory/robot_status 消息，更新对应机器人的实时状态。

    @param msg: ROS String 消息，data 字段为 JSON 格式的单个机器人状态
    """
    global dashboard_data
    try:
        data = json.loads(msg.data)
        robot_id = data.get('robot_id', 'unknown')
        with data_lock:
            dashboard_data['robot_stats'][robot_id] = {
                'status': data.get('status', 'UNKNOWN'),
                'position': data.get('position', [0, 0]),
                'current_task': data.get('current_task', None),
                'tasks_completed': data.get('tasks_completed', 0),
                'distance': data.get('distance', 0)
            }
    except Exception as e:
        print(f"⚠️ Failed to parse robot status: {e}")


def notification_callback(msg):
    """
    @brief 系统通知话题回调

    解析 /factory/notifications 消息，将事件插入全局事件列表头部。
    最多保留 50 条事件记录。

    @param msg: ROS String 消息，data 字段为 JSON 格式的通知信息
    """
    global dashboard_data
    try:
        data = json.loads(msg.data)
        event = {
            'timestamp': data.get('timestamp', time.time()),
            'level': data.get('level', 'info'),
            'message': data.get('message', ''),
            'time_str': datetime.now().strftime('%H:%M:%S')
        }
        with data_lock:
            dashboard_data['events'].insert(0, event)
            dashboard_data['events'] = dashboard_data['events'][:50]    # 最多保留 50 条
    except Exception as e:
        print(f"⚠️ Failed to parse notification: {e}")


# ============================================================
#  ROS 监听线程
# ============================================================

def ros_thread_func():
    """
    @brief ROS 监听线程函数

    在独立线程中初始化 ROS 节点、订阅话题，并以 10Hz 频率循环
    保持活跃。使用 rate.sleep() 而非 rospy.spin()，避免阻塞
    Flask 主线程。连接超时上限为 60 秒。
    """
    global ros_connected, dashboard_data

    print("🔄 Waiting for ROS Master connection...")
    dashboard_data['system_status'] = 'WAITING_ROS'

    # 尝试连接 ROS Master（最多重试 60 次，每次间隔 1 秒）
    connected = False
    for i in range(60):
        try:
            rospy.init_node('experiment_monitor_dashboard',
                            anonymous=True,
                            disable_signals=True)   # 不接管信号，避免与 Flask 冲突
            connected = True
            break
        except Exception:
            print(f"   Trying ROS connection ({i + 1}/60)...")
            time.sleep(1)

    if not connected:
        print("❌ Unable to connect to ROS Master")
        dashboard_data['system_status'] = 'ERROR'
        return

    print("Connected to ROS Master")
    ros_connected = True

    # 订阅三个核心话题
    rospy.Subscriber('/factory/task_statistics', String, task_statistics_callback)
    rospy.Subscriber('/factory/robot_status', String, robot_status_callback)
    rospy.Subscriber('/factory/notifications', String, notification_callback)

    print("Subscribed ROS topics:")
    print("   - /factory/task_statistics")
    print("   - /factory/robot_status")
    print("   - /factory/notifications")

    dashboard_data['system_status'] = 'RUNNING'
    print("✅ Dashboard ROS listener is ready")

    # 以 10Hz 循环保持线程活跃（替代 rospy.spin()）
    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        try:
            rate.sleep()
        except Exception:
            break


# ============================================================
#  Flask 路由
# ============================================================

@app.route('/')
def index():
    """
    @brief 主页面路由

    渲染 monitor_dashboard.html 模板。

    @return: 渲染后的 HTML 页面
    """
    return render_template('monitor_dashboard.html')


@app.route('/api/data')
def get_data():
    """
    @brief 获取全部监控数据的 API

    返回包含任务统计、机器人状态、系统事件等全部数据的 JSON。

    @return: JSON 格式的 dashboard_data
    """
    with data_lock:
        return jsonify(copy.deepcopy(dashboard_data))


@app.route('/api/report/status')
def report_status():
    """获取报告生成状态。"""
    with data_lock:
        stats = dashboard_data.get('task_stats', {})
        total = int(stats.get('total_tasks', 0) or 0)
        completed = int(stats.get('completed_tasks', 0) or 0)
        rejected = int(stats.get('rejected_tasks', 0) or 0)
        terminal = int(stats.get('terminal_tasks', completed + rejected) or 0)
        completed_flag = is_experiment_completed_unlocked()
        payload = {
            'experiment_completed': completed_flag,
            'progress': {
                'completed_tasks': completed,
                'rejected_tasks': rejected,
                'terminal_tasks': terminal,
                'total_tasks': total
            },
            'report_status': copy.deepcopy(dashboard_data.get('report_status', {}))
        }
    return jsonify(payload)


@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    """
    @brief 触发报告生成的 API

    调用 tools/generate_paper_materials.py 脚本生成实验报告。
    超时上限 60 秒。

    @return: JSON 格式的执行结果 {success, message}
    """
    with data_lock:
        stats = dashboard_data.get('task_stats', {})
        total = int(stats.get('total_tasks', 0) or 0)
        completed = int(stats.get('completed_tasks', 0) or 0)
        rejected = int(stats.get('rejected_tasks', 0) or 0)
        terminal = int(stats.get('terminal_tasks', completed + rejected) or 0)
        done = is_experiment_completed_unlocked()

    if not done:
        return jsonify({
            'success': False,
            'message': f'Experiment not completed: terminal {terminal}/{total} (completed={completed}, rejected={rejected}). The system will auto-generate report after completion.'
        })

    ok, message = start_report_generation('manual')
    return jsonify({
        'success': ok,
        'message': message
    })


# ============================================================
#  主函数
# ============================================================

def main():
    """
    @brief Dashboard 主函数

    依次执行：
    1. 启动 ROS 监听线程（后台守护线程）
    2. 等待 ROS 连接建立
    3. 启动 Flask Web 服务器（端口 5001）
    """
    print("=" * 60)
    print("🏭 Starting experiment monitoring dashboard...")
    print(f"📊 Experiment mode: {dashboard_data['experiment_mode']}")
    print("=" * 60)

    # 启动 ROS 监听线程（守护线程，随主进程退出）
    ros_thread = threading.Thread(target=ros_thread_func, daemon=True)
    ros_thread.start()

    # 等待 ROS 连接
    print("⏳ Waiting for ROS connection...")
    time.sleep(3)

    # 启动 Flask Web 服务器
    print("🌐 Starting Web server (http://0.0.0.0:5001)")
    print("=" * 60)

    try:
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == '__main__':
    main()
