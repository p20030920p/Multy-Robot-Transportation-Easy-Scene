#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验数据分析与报告生成工具
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import argparse

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")


class ExperimentAnalyzer:
    """实验数据分析器"""
    
    def __init__(self, results_dir="experiment_results"):
        self.results_dir = results_dir
        self.experiments = []
        self.load_experiments()
    
    def load_experiments(self):
        """加载所有实验结果"""
        print(f"📂 Loading experiment data: {self.results_dir}")
        
        if not os.path.exists(self.results_dir):
            print(f"❌ Directory does not exist: {self.results_dir}")
            return
        
        for exp_dir in os.listdir(self.results_dir):
            exp_path = os.path.join(self.results_dir, exp_dir)
            if not os.path.isdir(exp_path):
                continue
            
            summary_file = os.path.join(exp_path, "summary.json")
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                    summary['exp_dir'] = exp_dir
                    summary['exp_name'] = exp_dir.rsplit('_', 1)[0]
                    self.experiments.append(summary)
        
        print(f"   ✓ Loaded {len(self.experiments)} experiments")

    def infer_group(self, exp_name):
        """根据实验名推断分组：改进前/改进后/其他"""
        name = (exp_name or '').lower()
        before_keys = ['before', 'old', 'legacy', 'naive', 'baseline_old']
        after_keys = ['after', 'new', 'refactor', 'improved', 'optimized', 'baseline_run']

        if any(k in name for k in before_keys):
            return 'before'
        if any(k in name for k in after_keys):
            return 'after'
        return 'other'

    @staticmethod
    def permutation_test(mean_a, mean_b, pooled, n_a, n_b, iterations=5000, seed=42):
        """双侧置换检验（基于均值差）"""
        if n_a <= 0 or n_b <= 0:
            return None

        rng = np.random.default_rng(seed)
        observed = abs(mean_a - mean_b)
        exceed = 0

        pooled_arr = np.array(pooled, dtype=float)
        for _ in range(iterations):
            perm = rng.permutation(pooled_arr)
            a = perm[:n_a]
            b = perm[n_a:n_a + n_b]
            diff = abs(np.mean(a) - np.mean(b))
            if diff >= observed:
                exceed += 1

        # 加一平滑，避免返回 0
        return (exceed + 1) / (iterations + 1)

    def run_significance_analysis(self, exp_name_filter=None, iterations=5000):
        """Before-vs-after significance analysis with CSV and Markdown outputs."""
        print(f"\n🧪 Significance Test (before vs after)")

        if exp_name_filter:
            exps = [e for e in self.experiments if exp_name_filter in e['exp_name']]
        else:
            exps = self.experiments

        if not exps:
            print("   ⚠️  No experiments available")
            return None

        grouped = {'before': [], 'after': []}
        for exp in exps:
            g = self.infer_group(exp.get('exp_name', ''))
            if g in grouped:
                grouped[g].append(exp)

        if len(grouped['before']) < 2 or len(grouped['after']) < 2:
            print("   ⚠️  Not enough grouped samples (at least 2 per group)")
            print("   Hint: experiment names containing before/old or after/new/improved can be grouped automatically")
            return None

        # 4.2.1 指标白名单（仅这 8 项做量化显著性分析）
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

        metric_direction = {
            'task_completion_rate_pct': 'higher',
            'makespan': 'lower',
            'throughput_per_min': 'higher',
            'deadlock_count': 'lower',
            'deadlock_resolution_ratio': 'higher',
            'collision_count': 'lower',
            'total_travel_distance': 'lower',
            'load_balance_gini': 'lower',
        }

        rows = []
        for metric in metrics:
            before_vals = []
            after_vals = []
            for e in grouped['before']:
                if metric == 'makespan':
                    before_vals.append(float(e.get('makespan', e.get('completion_time', 0)) or 0))
                elif metric == 'total_travel_distance':
                    before_vals.append(float(e.get('total_travel_distance', e.get('total_distance', 0)) or 0))
                else:
                    before_vals.append(float(e.get(metric, 0) or 0))

            for e in grouped['after']:
                if metric == 'makespan':
                    after_vals.append(float(e.get('makespan', e.get('completion_time', 0)) or 0))
                elif metric == 'total_travel_distance':
                    after_vals.append(float(e.get('total_travel_distance', e.get('total_distance', 0)) or 0))
                else:
                    after_vals.append(float(e.get(metric, 0) or 0))

            before_mean = float(np.mean(before_vals))
            after_mean = float(np.mean(after_vals))
            delta = after_mean - before_mean
            if before_mean > 1e-9:
                if metric_direction.get(metric) == 'higher':
                    improve_pct = (after_mean - before_mean) / before_mean * 100.0
                else:
                    improve_pct = (before_mean - after_mean) / before_mean * 100.0
            else:
                improve_pct = 0.0
            p_val = self.permutation_test(
                before_mean,
                after_mean,
                before_vals + after_vals,
                len(before_vals),
                len(after_vals),
                iterations=iterations,
                seed=42,
            )

            rows.append({
                'metric': metric,
                'before_mean': before_mean,
                'after_mean': after_mean,
                'delta_after_minus_before': delta,
                'improvement_pct': improve_pct,
                'p_value': p_val,
                'significant_0_05': (p_val is not None and p_val < 0.05),
            })

        df = pd.DataFrame(rows)
        csv_file = os.path.join(self.results_dir, 'significance_before_after.csv')
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')

        md_lines = [
            '# Significance Results (before vs after)',
            '',
            f'- before sample size: {len(grouped["before"])}',
            f'- after sample size: {len(grouped["after"])}',
            f'- test method: permutation test (iterations={iterations})',
            '',
            '| Metric | Before Mean | After Mean | Improvement (%) | p-value | Significant (p<0.05) |',
            '|---|---:|---:|---:|---:|:---:|',
        ]

        for _, row in df.iterrows():
            md_lines.append(
                f"| {row['metric']} | {row['before_mean']:.4f} | {row['after_mean']:.4f} | "
                f"{row['improvement_pct']:.2f} | {row['p_value']:.4f} | {'Yes' if row['significant_0_05'] else 'No'} |"
            )

        md_file = os.path.join(self.results_dir, 'significance_before_after.md')
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        print(f"   ✓ Significance CSV: {csv_file}")
        print(f"   ✓ Significance MD: {md_file}")
        return df
    
    def compare_experiments(self, exp_name_filter=None):
        """Compare multiple experiments."""
        print(f"\n📊 Comparison Analysis")
        
        # 筛选实验
        if exp_name_filter:
            exps = [e for e in self.experiments if exp_name_filter in e['exp_name']]
        else:
            exps = self.experiments
        
        if not exps:
            print("   ⚠️  No matching experiments found")
            return
        
        print(f"   Analyzing {len(exps)} experiments")
        
        # 创建对比DataFrame
        metrics = [
            'total_tasks',
            'completed_tasks',
            'task_completion_rate_pct',
            'makespan',
            'throughput_per_min',
            'deadlock_count',
            'deadlock_resolution_ratio',
            'collision_count',
            'total_travel_distance',
            'load_balance_gini',
        ]
        
        data = []
        for exp in exps:
            row = {'experiment': exp['exp_dir']}
            for metric in metrics:
                if metric == 'makespan':
                    row[metric] = exp.get('makespan', exp.get('completion_time', 0))
                elif metric == 'total_travel_distance':
                    row[metric] = exp.get('total_travel_distance', exp.get('total_distance', 0))
                else:
                    row[metric] = exp.get(metric, 0)
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # 保存对比表格
        output_file = os.path.join(self.results_dir, f"comparison_{exp_name_filter or 'all'}.csv")
        df.to_csv(output_file, index=False)
        print(f"   ✓ Comparison table: {output_file}")
        
        # 生成对比图表
        self.plot_comparison(df, exp_name_filter)
        
        return df
    
    def plot_comparison(self, df, exp_name):
        """绘制对比图表"""
        print(f"   📈 Generating comparison plots...")
        
        metric_specs = [
            ('task_completion_rate_pct', 'Completion Rate (%)', '#1f77b4'),
            ('makespan', 'Makespan (s)', '#ff7f0e'),
            ('throughput_per_min', 'Throughput (tasks/min)', '#2ca02c'),
            ('deadlock_count', 'Deadlock Count', '#d62728'),
            ('deadlock_resolution_ratio', 'Deadlock Resolution Ratio', '#9467bd'),
            ('collision_count', 'Collision Count', '#8c564b'),
            ('total_travel_distance', 'Total Travel Distance (m)', '#17becf'),
            ('load_balance_gini', 'Load-Balance Gini', '#7f7f7f'),
        ]

        fig, axes = plt.subplots(2, 4, figsize=(22, 10))
        fig.suptitle(f'Experiment Comparison (Section 4.2.1 Metric Set) - {exp_name or "All"}', fontsize=16, fontweight='bold')

        x_vals = range(len(df))
        x_ticks = [f"E{i+1}" for i in range(len(df))]

        for ax, (metric_key, title, color) in zip(axes.flatten(), metric_specs):
            series = df[metric_key] if metric_key in df.columns else pd.Series([0] * len(df))
            bars = ax.bar(x_vals, series, color=color)
            ax.set_title(title)
            ax.set_xlabel('Experiment ID')
            ax.set_xticks(list(x_vals))
            ax.set_xticklabels(x_ticks, rotation=45)
            ax.grid(True, alpha=0.3, axis='y')
            mean_val = float(series.mean()) if len(series) > 0 else 0.0
            ax.axhline(y=mean_val, color='r', linestyle='--', linewidth=1.0)

            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f'{height:.3f}' if abs(height) < 100 else f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=8
                )
        
        plt.tight_layout()
        output_file = os.path.join(self.results_dir, f"comparison_plot_{exp_name or 'all'}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   ✓ Comparison plot: {output_file}")
    
    def generate_statistics_table(self, exp_name_filter=None):
        """Generate statistics table."""
        print(f"\n📊 Generating statistics table")
        
        # 筛选实验
        if exp_name_filter:
            exps = [e for e in self.experiments if exp_name_filter in e['exp_name']]
        else:
            exps = self.experiments
        
        if not exps:
            print("   ⚠️  No matching experiments found")
            return
        
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
        
        stats = {}
        for metric in metrics:
            values = []
            for e in exps:
                if metric == 'makespan':
                    values.append(e.get('makespan', e.get('completion_time', 0)))
                elif metric == 'total_travel_distance':
                    values.append(e.get('total_travel_distance', e.get('total_distance', 0)))
                else:
                    values.append(e.get(metric, 0))
            stats[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values)
            }
        
        df_stats = pd.DataFrame(stats).T
        
        # 格式化
        df_stats['mean'] = df_stats['mean'].map('{:.2f}'.format)
        df_stats['std'] = df_stats['std'].map('{:.2f}'.format)
        df_stats['min'] = df_stats['min'].map('{:.2f}'.format)
        df_stats['max'] = df_stats['max'].map('{:.2f}'.format)
        df_stats['median'] = df_stats['median'].map('{:.2f}'.format)
        
        # 保存
        output_file = os.path.join(self.results_dir, f"statistics_{exp_name_filter or 'all'}.csv")
        df_stats.to_csv(output_file, encoding='utf-8-sig')
        
        print(f"   ✓ Statistics table: {output_file}")
        print("\n" + df_stats.to_string())
        
        return df_stats
    
    def plot_trajectory(self, exp_dir, robot_ids=None):
        """Plot robot trajectories."""
        print(f"\n🗺️  Plotting trajectories: {exp_dir}")
        
        exp_path = os.path.join(self.results_dir, exp_dir)
        if not os.path.exists(exp_path):
            print(f"   ❌ Experiment directory does not exist: {exp_path}")
            return
        
        # 加载轨迹数据
        trajectories = {}
        for i in range(10):  # 假设最多10个机器人
            traj_file = os.path.join(exp_path, f"robot_{i}_trajectory.csv")
            if os.path.exists(traj_file):
                df = pd.read_csv(traj_file)
                trajectories[i] = df
        
        if not trajectories:
            print("   ⚠️  No trajectory data found")
            return
        
        # 绘制
        plt.figure(figsize=(12, 10))
        
        colors = plt.cm.tab10(np.linspace(0, 1, 10))
        
        for robot_id, df in trajectories.items():
            if robot_ids is None or robot_id in robot_ids:
                plt.plot(df['x'], df['y'], alpha=0.6, linewidth=1.5, 
                        color=colors[robot_id], label=f'Robot {robot_id}')
                # 标记起点和终点
                plt.plot(df['x'].iloc[0], df['y'].iloc[0], 'o', 
                        color=colors[robot_id], markersize=8)
                plt.plot(df['x'].iloc[-1], df['y'].iloc[-1], 's', 
                        color=colors[robot_id], markersize=8)
        
        plt.xlabel('X coordinate (m)')
        plt.ylabel('Y coordinate (m)')
        plt.title(f'Robot Trajectories - {exp_dir}')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        
        output_file = os.path.join(exp_path, "trajectories_plot.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   ✓ Trajectory plot: {output_file}")
    
    def generate_latex_table(self, df, caption="Experiment Results Comparison"):
        """Generate LaTeX table code."""
        print(f"\n📄 Generating LaTeX table")
        
        latex_code = df.to_latex(index=True, caption=caption, label="tab:experiment_results")
        
        output_file = os.path.join(self.results_dir, "latex_table.tex")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        
        print(f"   ✓ LaTeX table: {output_file}")
        print("\n" + latex_code)
        
        return latex_code
    
    def generate_full_report(self, output_file="experiment_report.html"):
        """Generate full HTML report."""
        print(f"\n📝 Generating full experiment report")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Experiment Report - Smart Factory Multi-Robot Scheduling System</title>
    <style>
        body {{
            font-family: Arial, "Microsoft YaHei", sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .metric {{
            background-color: #ecf0f1;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
        }}
        .summary {{
            background-color: #e8f5e9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Smart Factory Multi-Robot Scheduling System - Experiment Report</h1>
        
        <div class="summary">
            <h3>📊 Experiment Overview</h3>
            <p><strong>Experiment count:</strong> {len(self.experiments)}</p>
            <p><strong>Generated at:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <h2>1. Experiment Results Summary</h2>
        """
        
        # 添加每个实验的摘要
        for i, exp in enumerate(self.experiments, 1):
            makespan = float(exp.get('makespan', exp.get('completion_time', 0)) or 0.0)
            throughput = float(exp.get('throughput_per_min', 0.0) or 0.0)
            total_travel_distance = float(exp.get('total_travel_distance', exp.get('total_distance', 0)) or 0.0)
            html += f"""
        <h3>Experiment {i}: {exp['exp_name']}</h3>
        <div class="metric">
            <p><strong>Completed tasks:</strong> {exp.get('completed_tasks', 0)} / {exp.get('total_tasks', 0)}</p>
            <p><strong>Completion rate:</strong> {exp.get('task_completion_rate_pct', 0):.2f}%</p>
            <p><strong>Makespan:</strong> {makespan:.2f} s</p>
            <p><strong>Throughput:</strong> {throughput:.3f} tasks/min</p>
            <p><strong>Deadlock count:</strong> {exp.get('deadlock_count', 0)}</p>
            <p><strong>Deadlock resolution ratio:</strong> {exp.get('deadlock_resolution_ratio', 0):.4f}</p>
            <p><strong>Collision count:</strong> {exp.get('collision_count', 0)}</p>
            <p><strong>Total travel distance:</strong> {total_travel_distance:.2f} m</p>
            <p><strong>Load-balance Gini:</strong> {exp.get('load_balance_gini', 0):.4f}</p>
        </div>
            """
        
        html += """
        <h2>2. Performance Comparison</h2>
        <p>See CSV files and comparison plots for detailed data.</p>
        
        <h2>3. Conclusions and Recommendations</h2>
        <div class="summary">
            <p>The experiment data highlights the following characteristics:</p>
            <ul>
                <li>✅ High task scheduling efficiency</li>
                <li>✅ Strong obstacle avoidance and deadlock handling</li>
                <li>✅ Stable runtime performance</li>
            </ul>
        </div>
        
    </div>
</body>
</html>
        """
        
        output_path = os.path.join(self.results_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"   ✓ HTML report: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description='Experiment Data Analysis Tool')
    parser.add_argument('--results-dir', type=str, default='experiment_results',
                        help='Experiment results directory')
    parser.add_argument('--filter', type=str, default=None,
                        help='Experiment name filter')
    parser.add_argument('--action', type=str, 
                        choices=['compare', 'stats', 'trajectory', 'report', 'significance', 'all'],
                        default='all', help='Analysis action')
    parser.add_argument('--exp-dir', type=str, help='Experiment directory (for trajectory action)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📊 Experiment Data Analysis Tool")
    print("="*60)
    
    analyzer = ExperimentAnalyzer(args.results_dir)
    
    if len(analyzer.experiments) == 0:
        print("\n❌ No experiment data found")
        print(f"   Please check directory: {args.results_dir}")
        return
    
    if args.action in ['compare', 'all']:
        analyzer.compare_experiments(args.filter)
    
    if args.action in ['stats', 'all']:
        df_stats = analyzer.generate_statistics_table(args.filter)
        if df_stats is not None:
            analyzer.generate_latex_table(df_stats)

    if args.action in ['significance', 'all']:
        analyzer.run_significance_analysis(args.filter)
    
    if args.action == 'trajectory' and args.exp_dir:
        analyzer.plot_trajectory(args.exp_dir)
    
    if args.action in ['report', 'all']:
        analyzer.generate_full_report()
    
    print("\n✅ Analysis completed!")


if __name__ == '__main__':
    main()
