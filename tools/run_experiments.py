#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验自动化运行脚本 - 智能工厂多机器人任务调度系统
用于自动执行实验、收集数据、生成报告
"""

import rospy
from std_msgs.msg import String
from nav_msgs.msg import Odometry
import json
import time
import csv
import os
import sys
import argparse
from datetime import datetime
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 无GUI后端
import matplotlib.pyplot as plt
import pandas as pd


EXPERIMENT_MODE_NORMALIZATION = {
    'minimal': 'minimal',
    'quick': 'quick',
    'baseline': 'baseline',
    'stress': 'stress',
    'baseline2': 'baseline',
    'stress2': 'stress',
    'monitor': 'stress',
    's2_core': 'stress',
    's2_realtime': 'baseline',
    's2_congestion': 'stress',
    's2_peak': 'stress',
}

ALGORITHM_MODE_NORMALIZATION = {
    'rule_greedy': 'naive',
    'cbs_based': 'path_reservation',
    'auction_based': 'path_only',
    'proposed': 'full',
}

ALGORITHM_FAMILY_LABEL = {
    'naive': 'Rule-based (Greedy)',
    'rule_greedy': 'Rule-based (Greedy)',
    'path_only': 'Auction-based',
    'auction_based': 'Auction-based',
    'path_reservation': 'CBS-based',
    'cbs_based': 'CBS-based',
    'full': 'Proposed',
    'proposed': 'Proposed',
}

# 论文 4.2.1 指标白名单（仅这 8 项用于量化对比）
METRIC_WHITELIST_421 = [
    'task_completion_rate_pct',
    'makespan_s',
    'throughput_tasks_per_min',
    'deadlock_count',
    'deadlock_resolution_ratio',
    'collision_count',
    'total_travel_distance_m',
    'load_balance_gini',
]


def normalize_experiment_mode(mode):
    mode_key = (mode or 'unknown').strip().lower()
    return EXPERIMENT_MODE_NORMALIZATION.get(mode_key, mode_key)


def normalize_algorithm_mode(mode):
    mode_key = (mode or 'unknown').strip().lower()
    return ALGORITHM_MODE_NORMALIZATION.get(mode_key, mode_key)


def infer_algorithm_family(mode):
    mode_key = (mode or 'unknown').strip().lower()
    normalized = normalize_algorithm_mode(mode_key)
    return ALGORITHM_FAMILY_LABEL.get(mode_key, ALGORITHM_FAMILY_LABEL.get(normalized, 'Unknown'))


def build_proposed_test_id(experiment_mode):
    """生成 proposed 压力实验编号。"""
    mode_norm = normalize_experiment_mode(experiment_mode)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"proposed-{mode_norm}-{ts}"


def build_metric_whitelist_row(summary):
    """按 4.2.1 指标白名单构建单行导出数据。"""
    exp_mode = summary.get('experiment_mode', 'unknown')
    algo_mode = summary.get('algorithm_mode', 'unknown')
    exp_mode_norm = normalize_experiment_mode(exp_mode)
    algo_mode_norm = normalize_algorithm_mode(algo_mode)

    total_tasks = int(summary.get('total_tasks', 0) or 0)
    completed_tasks = int(summary.get('completed_tasks', 0) or 0)
    if total_tasks > 0:
        completion_rate_pct = float(summary.get('task_completion_rate_pct', (completed_tasks / total_tasks) * 100.0) or 0.0)
    else:
        completion_rate_pct = float(summary.get('task_completion_rate_pct', 0.0) or 0.0)

    completion_time = float(summary.get('completion_time', 0.0) or 0.0)
    throughput = float(summary.get('throughput_per_min', 0.0) or 0.0)
    if throughput <= 0 and completion_time > 1e-9:
        throughput = completed_tasks / (completion_time / 60.0)

    row = {
        'experiment_name': summary.get('experiment_name', 'unknown'),
        'test_id': (summary.get('test_id') or '').strip(),
        'experiment_mode': exp_mode,
        'experiment_mode_normalized': exp_mode_norm,
        'algorithm_mode': algo_mode,
        'algorithm_mode_normalized': algo_mode_norm,
        'algorithm_family': infer_algorithm_family(algo_mode),
        'task_completion_rate_pct': round(completion_rate_pct, 3),
        'makespan_s': round(float(summary.get('makespan', completion_time) or 0.0), 3),
        'throughput_tasks_per_min': round(throughput, 6),
        'deadlock_count': int(summary.get('deadlock_count', 0) or 0),
        'deadlock_resolution_ratio': round(float(summary.get('deadlock_resolution_ratio', 1.0) or 0.0), 6),
        'collision_count': int(summary.get('collision_count', 0) or 0),
        'total_travel_distance_m': round(float(summary.get('total_travel_distance', summary.get('total_distance', 0.0)) or 0.0), 3),
        'load_balance_gini': round(float(summary.get('load_balance_gini', 0.0) or 0.0), 6),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
    }
    return row


def append_algorithm_comparison_row(summary, report_dir, comparison_filename="algorithm_comparison_summary.csv"):
    """将单次实验关键指标追加到算法对比汇总CSV。"""
    os.makedirs(report_dir, exist_ok=True)
    output_file = os.path.join(report_dir, comparison_filename)

    row = build_metric_whitelist_row(summary)
    row['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df_new = pd.DataFrame([row])
    if os.path.exists(output_file):
        df_old = pd.read_csv(output_file)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(output_file, index=False, encoding='utf-8-sig')
    return output_file


class ExperimentRecorder:
    """实验数据记录器"""
    
    def __init__(self, experiment_name, output_dir="experiment_results", report_dir="paper_materials"):
        self.experiment_name = experiment_name
        self.output_dir = output_dir
        self.report_dir = report_dir
        self.start_time = time.time()

        algo_env = normalize_algorithm_mode(os.environ.get('ALGORITHM_MODE', 'unknown'))
        mode_env = normalize_experiment_mode(os.environ.get('EXPERIMENT_MODE', 'unknown'))
        env_test_id = (os.environ.get('TEST_ID', '') or '').strip()
        if env_test_id:
            self.test_id = env_test_id
        elif algo_env == 'full':
            self.test_id = build_proposed_test_id(mode_env)
        else:
            self.test_id = ''
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.exp_dir = os.path.join(output_dir, f"{experiment_name}_{timestamp}")
        os.makedirs(self.exp_dir, exist_ok=True)
        
        # 数据存储
        self.task_stats_history = []
        self.robot_positions_history = defaultdict(list)
        self.event_log = []
        self.performance_metrics = {
            'experiment_name': experiment_name,
            'test_id': self.test_id,
            'experiment_mode': 'unknown',
            'algorithm_mode': 'unknown',
            'algorithm_mode_canonical': 'unknown',
            'algorithm_family': 'Unknown',
            'total_tasks': 0,
            'completed_tasks': 0,
            'pending_tasks': 0,
            'active_tasks': 0,
            'task_completion_rate_pct': 0,
            'completion_time': 0,
            'deadlock_count': 0,
            'deadlock_resolution_ratio': 0,
            'yield_count': 0,
            'collision_count': 0,
            'recovery_count': 0,
            'starvation_prevent_count': 0,
            'total_distance': 0,
            'avg_task_time': 0,
            'makespan': 0,
            'total_travel_distance': 0,
            'load_balance_gini': 0,
            'throughput_per_min': 0,
            'scalability_robot_count': 0,
            'scalability_task_count': 0,
            'robot_utilization': {},
            'task_completion_distribution': {}
        }
        
        # ROS订阅
        rospy.init_node('experiment_recorder', anonymous=True)
        rospy.Subscriber('/factory/task_statistics', String, self.stats_callback)
        rospy.Subscriber('/factory/notifications', String, self.notification_callback)
        
        # 订阅机器人位置
        self.num_robots = 10
        for i in range(self.num_robots):
            rospy.Subscriber(f'/robot_{i}/odom', Odometry, self.odom_callback, callback_args=i)
        
        # 性能计时器
        self.timing_data = defaultdict(list)
        
        print(f"✅ Experiment recorder started: {self.experiment_name}")
        if self.test_id:
            print(f"🧪 Test ID: {self.test_id}")
        print(f"📁 Output directory: {self.exp_dir}")
    
    def stats_callback(self, msg):
        """任务统计回调"""
        try:
            data = json.loads(msg.data)
            data['elapsed_time'] = time.time() - self.start_time
            self.task_stats_history.append(data)
            
            # 更新性能指标
            self.performance_metrics['total_tasks'] = data.get('pending_tasks', 0) + \
                                                      data.get('active_tasks', 0) + \
                                                      data.get('completed_tasks', 0)
            self.performance_metrics['experiment_mode'] = data.get('experiment_mode', self.performance_metrics['experiment_mode'])
            self.performance_metrics['algorithm_mode'] = data.get('algorithm_mode', self.performance_metrics['algorithm_mode'])
            self.performance_metrics['algorithm_mode_canonical'] = data.get('algorithm_mode_canonical', self.performance_metrics['algorithm_mode_canonical'])
            self.performance_metrics['algorithm_family'] = data.get('algorithm_family', self.performance_metrics['algorithm_family'])
            self.performance_metrics['test_id'] = data.get('test_id', self.performance_metrics.get('test_id', ''))
            self.performance_metrics['completed_tasks'] = data.get('completed_tasks', 0)
            self.performance_metrics['pending_tasks'] = data.get('pending_tasks', 0)
            self.performance_metrics['active_tasks'] = data.get('active_tasks', 0)
            self.performance_metrics['task_completion_rate_pct'] = data.get('task_completion_rate_pct', self.performance_metrics['task_completion_rate_pct'])
            self.performance_metrics['deadlock_count'] = data.get('deadlock_count', 0)
            self.performance_metrics['deadlock_resolution_ratio'] = data.get('deadlock_resolution_ratio', self.performance_metrics['deadlock_resolution_ratio'])
            self.performance_metrics['yield_count'] = data.get('yield_count', 0)
            self.performance_metrics['recovery_count'] = data.get('recovery_count', 0)
            self.performance_metrics['collision_count'] = data.get('collision_count', 0)
            self.performance_metrics['starvation_prevent_count'] = data.get('starvation_prevent_count', 0)

            extra_fields = [
                'makespan', 'throughput_per_min', 'avg_task_time', 'total_travel_distance',
                'load_balance_gini', 'scalability_robot_count', 'scalability_task_count'
            ]
            for field in extra_fields:
                if field in data:
                    self.performance_metrics[field] = data.get(field)
            
            # 任务完成分布
            if 'task_completion_counts' in data:
                self.performance_metrics['task_completion_distribution'] = data['task_completion_counts']
            
            # 打印进度
            if len(self.task_stats_history) % 50 == 0:
                    print(f"📊 [{data['elapsed_time']:.1f}s] Completed: {data.get('completed_tasks', 0)}, "
                        f"Active: {data.get('active_tasks', 0)}, Pending: {data.get('pending_tasks', 0)}")
        
        except Exception as e:
            print(f"❌ Stats callback error: {e}")
    
    def notification_callback(self, msg):
        """通知回调（记录事件）"""
        try:
            data = json.loads(msg.data)
            event = {
                'time': time.time() - self.start_time,
                'type': data.get('type'),
                'level': data.get('level'),
                'message': data.get('message')
            }
            self.event_log.append(event)
            
            # 统计主指标统一来自 /factory/task_statistics，避免与通知重复计数
        
        except Exception as e:
            print(f"❌ Notification callback error: {e}")
    
    def odom_callback(self, msg, robot_id):
        """里程计回调（记录位置）"""
        pos = msg.pose.pose.position
        self.robot_positions_history[robot_id].append({
            'time': time.time() - self.start_time,
            'x': pos.x,
            'y': pos.y,
            'z': pos.z
        })
    
    def calculate_total_distance(self):
        """计算所有机器人的总移动距离"""
        total_dist = 0
        for robot_id in range(self.num_robots):
            positions = self.robot_positions_history[robot_id]
            if len(positions) < 2:
                continue
            
            dist = 0
            for i in range(1, len(positions)):
                prev = positions[i-1]
                curr = positions[i]
                dx = curr['x'] - prev['x']
                dy = curr['y'] - prev['y']
                dist += np.sqrt(dx**2 + dy**2)
            
            total_dist += dist
        
        return total_dist
    
    def save_raw_data(self):
        """保存原始数据到CSV"""
        print("\n💾 Saving raw data...")
        
        # 1. 任务统计历史
        if self.task_stats_history:
            df_stats = pd.DataFrame(self.task_stats_history)
            stats_file = os.path.join(self.exp_dir, "task_statistics.csv")
            df_stats.to_csv(stats_file, index=False)
            print(f"   ✓ Task statistics: {stats_file}")
        
        # 2. 事件日志
        if self.event_log:
            df_events = pd.DataFrame(self.event_log)
            events_file = os.path.join(self.exp_dir, "event_log.csv")
            df_events.to_csv(events_file, index=False)
            print(f"   ✓ Event log: {events_file}")
        
        # 3. 机器人轨迹
        for robot_id in range(self.num_robots):
            if self.robot_positions_history[robot_id]:
                df_traj = pd.DataFrame(self.robot_positions_history[robot_id])
                traj_file = os.path.join(self.exp_dir, f"robot_{robot_id}_trajectory.csv")
                df_traj.to_csv(traj_file, index=False)
        print(f"   ✓ Robot trajectories: {self.num_robots} files")
    
    def generate_summary(self):
        """生成实验摘要"""
        print("\n📊 Generating experiment summary...")
        
        # 计算总距离
        self.performance_metrics['total_distance'] = self.calculate_total_distance()
        
        # 计算完成时间
        if self.task_stats_history:
            self.performance_metrics['completion_time'] = self.task_stats_history[-1]['elapsed_time']
        
        # 计算平均任务时间
        if self.performance_metrics['completed_tasks'] > 0:
            total_completion_time = float(self.performance_metrics.get('total_completion_time', 0.0) or 0.0)
            if total_completion_time > 0:
                self.performance_metrics['avg_task_time'] = \
                    total_completion_time / self.performance_metrics['completed_tasks']
            else:
                self.performance_metrics['avg_task_time'] = \
                    self.performance_metrics['completion_time'] / self.performance_metrics['completed_tasks']
        
        # 计算机器人利用率（简化版）
        for robot_id in range(self.num_robots):
            positions = self.robot_positions_history[robot_id]
            if len(positions) > 1:
                # 统计移动时间占比
                moving_time = 0
                for i in range(1, len(positions)):
                    prev = positions[i-1]
                    curr = positions[i]
                    dx = curr['x'] - prev['x']
                    dy = curr['y'] - prev['y']
                    if np.sqrt(dx**2 + dy**2) > 0.01:  # 移动阈值
                        moving_time += curr['time'] - prev['time']
                
                total_time = positions[-1]['time'] - positions[0]['time']
                utilization = (moving_time / total_time * 100) if total_time > 0 else 0
                self.performance_metrics['robot_utilization'][f'robot_{robot_id}'] = round(utilization, 2)
        
        # 保存摘要到JSON
        summary_file = os.path.join(self.exp_dir, "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.performance_metrics, f, indent=4, ensure_ascii=False)

        # 保存单次指标CSV（可直接用于论文与对比）
        single_csv_file = os.path.join(self.exp_dir, "single_run_metrics.csv")
        single_row = build_metric_whitelist_row(self.performance_metrics)
        single_row['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pd.DataFrame([single_row]).to_csv(single_csv_file, index=False, encoding='utf-8-sig')

        # 追加到全局对比CSV
        comparison_file = append_algorithm_comparison_row(self.performance_metrics, self.report_dir)
        
        print(f"   ✓ Summary file: {summary_file}")
        print(f"   ✓ Single-run metrics: {single_csv_file}")
        print(f"   ✓ Comparison aggregate: {comparison_file}")
        return self.performance_metrics
    
    def plot_results(self):
        """生成可视化图表"""
        print("\n📈 Generating visualization plots...")
        
        if not self.task_stats_history:
            print("   ⚠️  No data available for plotting")
            return
        
        df = pd.DataFrame(self.task_stats_history)
        
        # 创建多子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Experiment Results - {self.experiment_name}', fontsize=16)

        total_tasks = max(int(self.performance_metrics.get('total_tasks', 0) or 0), 0)
        completed_tasks = max(int(self.performance_metrics.get('completed_tasks', 0) or 0), 0)
        completion_time = float(self.performance_metrics.get('completion_time', 0.0) or 0.0)
        total_distance = float(self.performance_metrics.get('total_distance', 0.0) or 0.0)
        completion_pct = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0
        throughput = (completed_tasks / (completion_time / 60.0)) if completion_time > 1e-9 else 0.0
        avg_distance_per_task = (total_distance / completed_tasks) if completed_tasks > 0 else 0.0
        avg_robot_util = (
            np.mean(list(self.performance_metrics['robot_utilization'].values()))
            if self.performance_metrics['robot_utilization'] else 0.0
        )
        
        # 1. 任务完成进度曲线
        ax1 = axes[0, 0]
        ax1.plot(df['elapsed_time'] / 60, df['completed_tasks'], label='Completed', linewidth=2)
        ax1.plot(df['elapsed_time'] / 60, df['active_tasks'], label='Active', linewidth=2)
        ax1.plot(df['elapsed_time'] / 60, df['pending_tasks'], label='Pending', linewidth=2)
        ax1.set_xlabel('Time (min)')
        ax1.set_ylabel('Task count')
        ax1.set_title('Task Progress')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 任务类型分布（饼图）
        ax2 = axes[0, 1]
        if self.performance_metrics['task_completion_distribution']:
            labels = list(self.performance_metrics['task_completion_distribution'].keys())
            sizes = list(self.performance_metrics['task_completion_distribution'].values())
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Task Type Distribution')
        
        # 3. 机器人利用率（柱状图）
        ax3 = axes[1, 0]
        if self.performance_metrics['robot_utilization']:
            robots = list(self.performance_metrics['robot_utilization'].keys())
            utils = list(self.performance_metrics['robot_utilization'].values())
            ax3.bar(range(len(robots)), utils, color='steelblue')
            ax3.set_xlabel('Robot ID')
            ax3.set_ylabel('Utilization (%)')
            ax3.set_title('Robot Utilization')
            ax3.set_xticks(range(len(robots)))
            ax3.set_xticklabels([r.split('_')[1] for r in robots])
            ax3.grid(True, alpha=0.3, axis='y')
            ax3.axhline(y=np.mean(utils), color='r', linestyle='--', label=f'Average: {np.mean(utils):.1f}%')
            ax3.legend()
        
        # 4. 关键指标汇总（文本）
        ax4 = axes[1, 1]
        ax4.axis('off')
        summary_text = f"""
        Experiment: {self.experiment_name}
        Test ID: {self.performance_metrics.get('test_id', '') or 'N/A'}
        
        ======================
        Core Metrics
        ======================
        Total tasks: {total_tasks}
        Completed tasks: {completed_tasks}
        Completion rate: {completion_pct:.1f}%
        
        Makespan: {completion_time/60:.1f} min
        Avg task time: {self.performance_metrics['avg_task_time']:.1f} s
        Throughput: {throughput:.2f} tasks/min
        
        ======================
        Conflict Governance
        ======================
        Deadlock count: {self.performance_metrics['deadlock_count']}
        Deadlock resolution ratio: {self.performance_metrics.get('deadlock_resolution_ratio', 0) * 100.0:.2f}%
        Collision-risk events: {self.performance_metrics.get('collision_count', 0)}
        
        ======================
        Efficiency
        ======================
        Total travel distance: {self.performance_metrics.get('total_travel_distance', total_distance):.1f} m
        Avg distance per task: {avg_distance_per_task:.2f} m/task
        Avg robot utilization: {avg_robot_util:.1f}%
        Load-balance Gini: {self.performance_metrics.get('load_balance_gini', 0):.4f}
        """
        ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
                fontsize=11, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plot_file = os.path.join(self.exp_dir, "results_plot.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   ✓ Result plot: {plot_file}")
    
    def print_summary(self):
        """打印实验摘要到终端"""
        total_tasks = max(int(self.performance_metrics.get('total_tasks', 0) or 0), 0)
        completed_tasks = max(int(self.performance_metrics.get('completed_tasks', 0) or 0), 0)
        completion_time = float(self.performance_metrics.get('completion_time', 0.0) or 0.0)
        total_distance = float(self.performance_metrics.get('total_distance', 0.0) or 0.0)
        completion_pct = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0
        throughput = (completed_tasks / (completion_time / 60.0)) if completion_time > 1e-9 else 0.0
        avg_distance_per_task = (total_distance / completed_tasks) if completed_tasks > 0 else 0.0

        print("\n" + "="*60)
        print(f"📊 Experiment Summary - {self.experiment_name}")
        print(f"🧪 Test ID: {self.performance_metrics.get('test_id', '') or 'N/A'}")
        print("="*60)
        print(f"\n✅ Completion:")
        print(f"   Total tasks: {total_tasks}")
        print(f"   Completed tasks: {completed_tasks}")
        print(f"   Completion rate: {completion_pct:.1f}%")
        
        print(f"\n⏱️  Time Metrics:")
        print(f"   Makespan: {completion_time/60:.1f} min")
        print(f"   Avg task time: {self.performance_metrics['avg_task_time']:.1f} s")
        print(f"   Throughput: {throughput:.2f} tasks/min")
        
        print(f"\n🚧 Conflict Governance Metrics:")
        print(f"   Deadlock count: {self.performance_metrics['deadlock_count']}")
        print(f"   Deadlock resolution ratio: {self.performance_metrics.get('deadlock_resolution_ratio', 0) * 100.0:.2f}%")
        print(f"   Collision-risk events: {self.performance_metrics.get('collision_count', 0)}")
        
        print(f"\n📏 Efficiency Metrics:")
        print(f"   Total travel distance: {self.performance_metrics.get('total_travel_distance', total_distance):.1f} m")
        print(f"   Avg distance per task: {avg_distance_per_task:.2f} m/task")
        print(f"   Load-balance Gini: {self.performance_metrics.get('load_balance_gini', 0):.4f}")
        if self.performance_metrics['robot_utilization']:
            avg_util = np.mean(list(self.performance_metrics['robot_utilization'].values()))
            print(f"   Avg robot utilization: {avg_util:.1f}%")

        print(f"\n🧪 Section 4.2.1 Metric Set:")
        print(f"   Completion Rate: {completion_pct:.2f}%")
        print(f"   Makespan: {self.performance_metrics.get('makespan', 0):.2f}s")
        print(f"   Throughput: {throughput:.2f} tasks/min")
        print(f"   Deadlock Count: {self.performance_metrics.get('deadlock_count', 0)}")
        print(f"   Deadlock Resolution Ratio: {self.performance_metrics.get('deadlock_resolution_ratio', 0):.4f}")
        print(f"   Collision Count: {self.performance_metrics.get('collision_count', 0)}")
        print(f"   Total Travel Distance: {self.performance_metrics.get('total_travel_distance', 0):.2f}m")
        print(f"   Load-Balance Gini: {self.performance_metrics.get('load_balance_gini', 0):.4f}")
        
        print("\n" + "="*60)


class ExperimentRunner:
    """实验自动化运行器"""
    
    def __init__(self):
        self.experiments = {
            'baseline': self.run_baseline_experiment,
            'load_test': self.run_load_test,
            'robustness': self.run_robustness_test,
            'pause_resume': self.run_pause_resume_test,
            'comparison': self.run_comparison_experiment,
            'realtime': self.run_realtime_monitoring
        }
    
    def run_baseline_experiment(self, repeat=3):
        """实验一：基准性能测试"""
        print("\n🔬 Starting Experiment 1: Baseline Performance Test")
        print(f"   Repeat count: {repeat}")
        
        results = []
        for i in range(repeat):
            print(f"\n━━━━━━ Run {i+1}/{repeat} ━━━━━━")
            recorder = ExperimentRecorder(f"baseline_run{i+1}")
            
            # 等待系统就绪
            rospy.sleep(5)
            
            # 监控直到完成（或超时）
            timeout = 3600 * 2  # 2小时超时
            start = time.time()
            rate = rospy.Rate(0.2)  # 5秒检查一次
            
            while not rospy.is_shutdown():
                elapsed = time.time() - start
                if elapsed > timeout:
                    print(f"⚠️  Timeout ({timeout/60} min), stopping recorder")
                    break
                
                # 检查是否完成
                if recorder.performance_metrics['completed_tasks'] >= recorder.performance_metrics['total_tasks'] > 0:
                    print(f"✅ All tasks completed!")
                    rospy.sleep(10)  # 等待10秒确保数据保存
                    break
                
                rate.sleep()
            
            # 保存数据
            recorder.save_raw_data()
            summary = recorder.generate_summary()
            recorder.plot_results()
            recorder.print_summary()
            
            results.append(summary)
        
        # 生成汇总对比
        self.generate_multi_run_comparison(results, "baseline")
        return results
    
    def run_load_test(self):
        """实验二：负载压力测试"""
        print("\n🔬 Starting Experiment 2: Load Stress Test")
        print("   You may need to manually adjust task counts in task_scheduler_ros_clean.py")
        print("   Run different load levels according to the experiment design")
        
        # 提示用户
        input("   Press Enter to continue after configuration...")
        
        # 运行单次实验
        recorder = ExperimentRecorder("load_test")
        # ... 类似baseline的监控逻辑
    
    def run_robustness_test(self):
        """实验三：鲁棒性测试"""
        print("\n🔬 Starting Experiment 3: Robustness Test")
        print("   This test requires manual interventions (obstacles, forced disturbances, etc.)")
        print("   Please prepare the Web control panel")
    
    def run_pause_resume_test(self):
        """实验四：暂停/恢复测试"""
        print("\n🔬 Starting Experiment 4: Pause/Resume Test")
    
    def run_comparison_experiment(self):
        """实验五：算法对比"""
        print("\n🔬 Starting Experiment 5: Algorithm Comparison")
        print("   This requires switching among different scheduling algorithm modes")
    
    def run_realtime_monitoring(self):
        """实验六：实时性能监控"""
        print("\n🔬 Starting Experiment 6: Real-time Performance Monitoring")
    
    def generate_multi_run_comparison(self, results, exp_name):
        """生成多次运行的对比报告"""
        print(f"\n📊 Generating multi-run comparison report...")
        
        # 提取关键指标
        metrics = [
            'task_completion_rate_pct',
            'makespan',
            'throughput_per_min',
            'deadlock_count',
            'deadlock_resolution_ratio',
            'collision_count',
            'total_travel_distance',
            'load_balance_gini',
        ]
        
        comparison = {}
        for metric in metrics:
            values = [r[metric] for r in results if metric in r]
            if values:
                comparison[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'values': values
                }
        
        # 保存对比结果
        output_dir = "experiment_results"
        comparison_file = os.path.join(output_dir, f"{exp_name}_comparison.json")
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=4)
        
        print(f"   ✓ Comparison report: {comparison_file}")
        
        # 打印统计摘要
        print(f"\n📈 {exp_name.upper()} - Multi-run Statistics Summary:")
        for metric, stats in comparison.items():
            print(f"\n   {metric}:")
            print(f"      Mean: {stats['mean']:.2f}")
            print(f"      Std: {stats['std']:.2f}")
            print(f"      Range: [{stats['min']:.2f}, {stats['max']:.2f}]")


def main():
    parser = argparse.ArgumentParser(description='Smart Factory Experiment Automation Runner')
    parser.add_argument('--experiment', type=str, choices=['baseline', 'load_test', 'robustness', 
                                                            'pause_resume', 'comparison', 'realtime', 'all'],
                        default='baseline', help='Experiment type')
    parser.add_argument('--repeat', type=int, default=3, help='Repeat count (for baseline, etc.)')
    parser.add_argument('--monitor-only', action='store_true', help='Monitor-only mode (no system control)')
    parser.add_argument('--experiment-name', type=str, default='monitor_session', help='Experiment name tag (recommended: include algorithm and mode)')
    parser.add_argument('--output-dir', type=str, default='experiment_results', help='Raw output directory')
    parser.add_argument('--report-dir', type=str, default='paper_materials', help='Comparison summary output directory')
    parser.add_argument('--auto-stop-on-complete', action='store_true', help='In monitor mode, auto-stop and save when tasks complete')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔬 Smart Factory Experiment Automation System")
    print("="*60)
    print(f"Experiment type: {args.experiment}")
    print(f"Repeat count: {args.repeat}")
    print("="*60)
    
    if args.monitor_only:
        # 仅监控模式
        print("\n📡 Starting monitor mode...")
        recorder = ExperimentRecorder(
            args.experiment_name,
            output_dir=args.output_dir,
            report_dir=args.report_dir,
        )
        try:
            if args.auto_stop_on_complete:
                rate = rospy.Rate(0.2)
                while not rospy.is_shutdown():
                    total_tasks = recorder.performance_metrics.get('total_tasks', 0)
                    done_tasks = recorder.performance_metrics.get('completed_tasks', 0)
                    if total_tasks > 0 and done_tasks >= total_tasks:
                        print("\n✅ Monitor detected task completion, auto-stopping and generating reports")
                        break
                    rate.sleep()
            else:
                rospy.spin()
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitor stopped")
        finally:
            recorder.save_raw_data()
            recorder.generate_summary()
            recorder.plot_results()
            recorder.print_summary()
    else:
        # 运行实验
        runner = ExperimentRunner()
        
        if args.experiment == 'all':
            print("\n⚠️  Running the full experiment suite takes a long time (~30 hours)")
            confirm = input("Confirm to continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled")
                return
            
            # 依次运行所有实验
            for exp_name, exp_func in runner.experiments.items():
                exp_func()
        else:
            # 运行单个实验
            if args.experiment in runner.experiments:
                runner.experiments[args.experiment](repeat=args.repeat if args.experiment == 'baseline' else 1)
            else:
                print(f"❌ Unknown experiment type: {args.experiment}")


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        print("\n❌ ROS interrupted")
    except KeyboardInterrupt:
        print("\n\n⏹️  Experiment interrupted by user")
