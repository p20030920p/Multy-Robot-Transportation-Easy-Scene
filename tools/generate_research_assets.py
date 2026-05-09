#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def draw_box(ax, x, y, w, h, title, lines, fc="#F5F7FA", ec="#2F3B52"):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.04, title, ha="center", va="top", fontsize=10, weight="bold")
    text = "\n".join(lines)
    ax.text(x + 0.02, y + h - 0.09, text, ha="left", va="top", fontsize=8.5)


def generate_figure(output_dir: Path):
    fig = plt.figure(figsize=(14, 7), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1.0], wspace=0.18)

    # ---------------------------
    # Left panel: framework chart
    # ---------------------------
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)
    ax0.axis("off")

    ax0.set_title("(a) Hierarchical Scheduling Framework", fontsize=12, weight="bold", pad=10)

    draw_box(
        ax0, 0.04, 0.73, 0.40, 0.22,
        "System Orchestration",
        [
            "launch_system.py",
            "- Start 7 services in sequence",
            "- Mode via EXPERIMENT_MODE",
            "- Health check and cleanup",
        ],
        fc="#EAF2FF"
    )

    draw_box(
        ax0, 0.52, 0.73, 0.44, 0.22,
        "Scheduler Core (10 Hz loop)",
        [
            "assign_tasks -> update_region_tracking",
            "global_deadlock_scan -> navigate_along_path",
            "publish_statistics",
            "task_scheduler_ros_clean.py",
        ],
        fc="#EAFBF1"
    )

    draw_box(
        ax0, 0.04, 0.42, 0.40, 0.24,
        "Conflict Handling L1-L4",
        [
            "L1: safety distance + laser",
            "L2: node/edge/time reservation",
            "L3: corridor token arbitration",
            "L4: deadlock escalation",
            "    yield -> pair separation -> emergency break",
        ],
        fc="#FFF4E5"
    )

    draw_box(
        ax0, 0.52, 0.42, 0.44, 0.24,
        "Planning and Navigation",
        [
            "astar_planner.py",
            "- 8-neighbor A* + smoothing",
            "- dynamic obstacle avoidance",
            "- empty-path recheck and replanning",
        ],
        fc="#F3ECFF"
    )

    draw_box(
        ax0, 0.04, 0.08, 0.92, 0.25,
        "Observability and Research Outputs",
        [
            "Topics: /factory/task_statistics, /factory/robot_status, /factory/notifications",
            "Dashboard: experiment_monitor_dashboard.py  |  Map stream: matplotlib_ros_stream.py",
            "Tools: run_experiments.py / analyze_experiments.py / generate_paper_materials.py",
            "Metrics: deadlock, yield, fallback, forced_separation, emergency_break, starvation_prevent",
        ],
        fc="#F8FAFC"
    )

    arrows = [
        ((0.44, 0.84), (0.52, 0.84)),
        ((0.24, 0.73), (0.24, 0.66)),
        ((0.74, 0.73), (0.74, 0.66)),
        ((0.24, 0.42), (0.24, 0.33)),
        ((0.74, 0.42), (0.74, 0.33)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax0.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.5))

    # ---------------------------
    # Right panel: mode scale chart
    # ---------------------------
    ax1 = fig.add_subplot(gs[0, 1])
    ax1.set_title("(b) Task Scale and Preserved Type Ratio", fontsize=12, weight="bold", pad=10)

    modes = ["quick", "baseline2", "baseline", "stress2", "stress"]
    empty_to_carding = [36, 108, 144, 216, 288]
    green_to_drawing1 = [36, 108, 144, 216, 288]
    yellow_to_drawing2 = [6, 18, 24, 36, 48]
    red_to_completed = [1, 3, 4, 6, 8]

    bottoms = [0] * len(modes)
    colors = ["#4F81BD", "#9BBB59", "#F2C811", "#C0504D"]
    labels = [
        "empty_to_carding",
        "green_to_drawing1",
        "yellow_to_drawing2",
        "red_to_completed",
    ]
    stacks = [empty_to_carding, green_to_drawing1, yellow_to_drawing2, red_to_completed]

    for values, c, label in zip(stacks, colors, labels):
        ax1.bar(modes, values, bottom=bottoms, color=c, label=label, edgecolor="white", linewidth=0.5)
        bottoms = [b + v for b, v in zip(bottoms, values)]

    for i, total in enumerate(bottoms):
        ax1.text(i, total + 8, f"{total}", ha="center", va="bottom", fontsize=9, weight="bold")

    ax1.set_ylabel("Number of tasks")
    ax1.set_ylim(0, max(bottoms) * 1.18)
    ax1.grid(axis="y", alpha=0.25)
    ax1.legend(loc="upper left", fontsize=8)

    ax1.text(
        0.02,
        0.02,
        "Type ratio is preserved across modes: 36:36:6:1",
        transform=ax1.transAxes,
        fontsize=8.5,
        color="#333333",
        bbox=dict(boxstyle="round,pad=0.25", fc="#F9F9F9", ec="#DDDDDD"),
    )

    fig.suptitle("Smart Factory Multi-AGV System: Architecture and Experimental Scale", fontsize=14, weight="bold", y=0.99)

    png_path = output_dir / "fig_research_framework_and_modes.png"
    pdf_path = output_dir / "fig_research_framework_and_modes.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path


def generate_markdown(output_dir: Path, png_name: str):
    md_path = output_dir / "research_figure_notes.md"
    content = f"""# Research Figure Notes (Paper-ready)

## Figure

![Smart Factory Framework and Modes](./{png_name})

**Figure X.** Smart factory multi-AGV architecture and experiment-scale design. Panel (a) illustrates the end-to-end control stack: system orchestration, scheduler loop, hierarchical conflict handling (L1-L4), and observability pipeline. Panel (b) reports task scale across five representative modes while preserving the task-type ratio (36:36:6:1), which supports fair trend comparison across workload levels.

---

## Recommended paper text (can be used directly)

### 中文图注（可直接用于论文）
图 X 展示了智能工厂多 AGV 调度系统的总体技术路径与实验规模设计。子图 (a) 给出了从系统编排、调度主循环、分层冲突治理（L1-L4）到监控分析输出的完整闭环；子图 (b) 给出了不同实验模式下的任务规模，并保持任务类型比例恒定（36:36:6:1），用于保证不同负载对比的公平性。

### Method description paragraph
We implement a hierarchical multi-AGV scheduling framework in ROS/Gazebo. The runtime loop executes task assignment, region-aware navigation, deadlock scanning, and statistics publication at 10 Hz. Conflict resolution is organized into four layers: safety control (L1), spatiotemporal reservation with priority arbitration (L2), corridor token control for bottlenecks (L3), and deadlock escalation (L4), where the strategy upgrades from safe yielding to pair separation and finally emergency pair braking.

### Experimental design paragraph
To evaluate scalability under controlled workload growth, we define five operating modes (quick, baseline2, baseline, stress2, stress). The composition of task types is kept constant at 36:36:6:1, so that changes in performance metrics primarily reflect workload intensity rather than distribution shift.

---

## LaTeX insertion template

```tex
\\begin{{figure*}}[t]
  \\centering
  \\includegraphics[width=0.98\\textwidth]{{fig_research_framework_and_modes.png}}
  \\caption{{Smart factory multi-AGV architecture and experiment-scale design.}}
  \\label{{fig:framework_modes}}
\\end{{figure*}}
```

---

## Reproducibility command

```bash
cd /home/qzl/graduate/catkin_ws
python3 tools/generate_research_assets.py
```
"""
    md_path.write_text(content, encoding="utf-8")
    return md_path


def main():
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "paper_materials"
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path, pdf_path = generate_figure(output_dir)
    md_path = generate_markdown(output_dir, png_path.name)

    print(f"Generated: {png_path}")
    print(f"Generated: {pdf_path}")
    print(f"Generated: {md_path}")


if __name__ == "__main__":
    main()
