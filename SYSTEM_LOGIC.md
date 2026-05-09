# Smart Factory Multi-Robot Scheduling System — Full Logic Doc (Launch-Ordered, Function-Level)

> **Scope**: Entire codebase.  
> **Reading order**: Follows launch_system.py startup order; architecture overview first, then per-module function-level breakdown.  
> **Chinese version**: `SYSTEM_LOGIC_CN.md` (kept in sync). Please refer to CN version for the most detailed content with Mermaid diagrams.

---

## 0. Architecture Overview

```
launch_system.py (Orchestrator)
  ├─ 1→ roscore
  ├─ 2→ Gazebo (10 differential-drive AGVs)
  ├─ 3→ ROS Bridge (WebSocket :9090)
  ├─ 4→ task_scheduler_ros_clean.py (Core scheduler + astar_planner.py)
  ├─ 5→ experiment_monitor_dashboard.py (Flask :5001)
  ├─ 6→ matplotlib_ros_stream.py (MJPEG :5000)
  └─ 7→ python3 -m http.server (:8000)

Environment variable chain:
  EXPERIMENT_MODE → scheduler + dashboard
  ALGORITHM_MODE → scheduler
  ABLATION_MODE → scheduler
  TEST_ID → scheduler
```

---

## 1. Module 1: launch_system.py (Launcher)

**Class**: `SmartFactorySystem` | **~500 lines**

### Utility Methods
- `log(msg, level)`, `check_port(port)`, `kill_port(port)`, `check_process(name)`, `launch_service_command(...)`, `kill_process(name)`, `cleanup_old_processes()`

### Service Starters
- `start_roscore()` — 15s timeout; `start_gazebo()` — 15s warmup; `start_rosbridge()` — auto-detect or manual; `start_task_scheduler_with_mode(mode, algorithm, test_id, ablation_mode)` — env vars; `start_dashboard(experiment_mode, algorithm_mode)`; `start_map_visualization()`; `start_web_server()`

### Lifecycle
- `open_web_pages()`, `verify_system()`, `cleanup(signum, frame)`, `run(...)` — menu→cleanup→launch 7 services→verify→browser→monitor loop

---

## 2. Module 2: task_scheduler_ros_clean.py (Core Scheduler)

**Class**: `CleanTaskScheduler` | **~2200 lines**

### Key Parameters
- Collision: 1.5m check / 0.25m hard / 0.15m critical / 0.5m laser threshold
- Deadlock: 2.5s window / 0.33m threshold / 12 trigger count / 12s cooldown
- Spacetime reservation: 8.0s horizon / 0.6m grid / 0.8s tolerance
- Priority: 2.0s wait step / +6 per step / max +36 / +15 inheritance / +8 protected
- Flip: 0.95rad confirm / 1.20rad severe / 1.0s confirm duration / 8s recovery cooldown

### Algorithm Modes
| Mode | Alias | Features Enabled |
|------|-------|------------------|
| naive / rule_greedy | Rule-based (Greedy) | Basic greedy |
| path_only / auction_based | Auction-based | + path planning |
| path_reservation / cbs_based | CBS-based | + spacetime reservation |
| full / proposed | Proposed | All: reservation+deadlock scan+fairness+corridor token+progressive recovery |

### Ablation Modes (Proposed only)
A1=no reservation, A2=no deadlock scan, A3=no fairness, A4=no progressive recovery

### Main Loop run() — 10Hz Order
```
1. check_completion()
2. cleanup_corridor_tokens()
3. cleanup_runtime_navigation_states()
4. assign_tasks()
5. update_region_tracking()
6. global_deadlock_scan()
7. auto_recover_flipped_robots()
8. check_manual_tasks()
9. update_robot_wait_state() ×10
10. recover_stalled_robots()
11. navigate_along_path() for MOVING/MANUAL/YIELDING
12. update_cycle_metrics()
13. publish_statistics()
```

### Key Subsystems
- **Region & Dispersion**: `update_region_tracking()`, `find_dispersed_goal_in_region()`, `plan_path_avoiding_region_robots()`
- **Corridor Tokens**: `corridor_priority_decision(r1, r2)` — one-way passage in narrow zones
- **Flip Detection FSM**: normal→suspected→flipped→recovering→normal
- **Navigation 3-Layer Safety**: Laser avoidance → Dynamic speed cap → Hard safety stop
- **Effective Priority**: `P_eff = P_base + wait_boost + protected_bonus + inheritance_bonus`
- **Deadlock Escalation**: retry≥6→emergency break, retry≥2→pair separation, retry=1→safe yield
- **Spacetime Reservation**: node (gx,gy,t) + edge conflicts detection
- **Task Lifecycle**: pending→assigned→loading→delivering→unloading→completed

---

## 3. Module 3: astar_planner.py (Path Planning)

**Classes**: `Node`, `AStarPlanner` | **~380 lines**

- 8-direction A* (cardinal cost 1.0, diagonal 1.414), max 3000 iterations
- 3-layer `is_valid()`: boundary→static obstacles→dynamic (safe_dist=8×radius)
- `smooth_path()`: line-of-sight simplification
- `find_nearest_valid_point()`: concentric search 0.1~0.5m, 32 angles
- Thread-safe dynamic obstacle updates

---

## 4. Module 4: experiment_monitor_dashboard.py (Dashboard Backend)

**Framework**: Flask+CORS | **Port**: 5001 | **~380 lines**

- Subscribes: /factory/task_statistics, /factory/robot_status, /factory/notifications
- Routes: GET `/api/data`, GET `/api/report/status`, POST `/api/report/generate`
- Auto-triggers report generation on experiment completion
- ROS thread with 60s connection retry

---

## 5. Module 5: templates/monitor_dashboard.html

**~700 lines** | 2s AJAX refresh | Displays all metrics, robot cards, events, report controls

---

## 6. Module 6: matplotlib_ros_stream.py

**Framework**: Matplotlib+Flask | **Port**: 5000 | **~750 lines**

- 31 factory zones, 10 robots with trails (maxlen=150), status indicators
- MJPEG output at ~10 FPS via `/video_feed`
- `/api/stats` JSON endpoint

---

## 7. Module 7: gazebo_control_with_tasks.html

**~500 lines** | WebSocket→rosbridge:9090

Left panel (370px): stats, task list, robot grid, manual dispatch panel  
Right panel: 2D map stream + control buttons

---

## 8-10. Tools

- **tools/run_experiments.py**: `ExperimentRecorder` records real-time data, exports CSV+summary.json+plots
- **tools/analyze_experiments.py**: `ExperimentAnalyzer` — permutation test (5000 iters), significance analysis, comparison charts
- **tools/generate_paper_materials.py**: `PaperMaterialGenerator` — Tables 1/2/3, Figures 1/2/3, LaTeX, summary report

---

## 11. Topic & API Summary

**ROS topics** (publisher→subscriber):
- /factory/task_statistics: scheduler→dashboard/map/control
- /factory/robot_status: scheduler→dashboard
- /factory/notifications: scheduler→dashboard/control
- /factory/command: control→scheduler
- /factory/command_result: scheduler→control
- /robot_X/odom: gazebo→scheduler/map/control
- /robot_X/scan: gazebo→scheduler
- /robot_X/cmd_vel: scheduler→gazebo

**HTTP**: :5001→`/api/data`, `/api/report/status`, `/api/report/generate` | :5000→`/video_feed`, `/api/stats` | :8000→`/gazebo_control_with_tasks.html`

---

## 12. Quick Commands

```bash
# Interactive start
cd ~/graduate/catkin_ws && python3 launch_system.py

# CLI mode
python3 launch_system.py --mode baseline --algorithm proposed --yes --no-browser

# Ablation experiment
python3 launch_system.py --mode baseline --algorithm proposed --ablation A1 --yes

# Syntax check
python3 -m py_compile launch_system.py task_scheduler_ros_clean.py

# Port check
ss -lntp | grep -E ':5000|:5001|:8000|:9090'

# Analysis
python3 tools/analyze_experiments.py --action all

# Paper materials
python3 tools/generate_paper_materials.py
```

---

*Doc version: v2.0 | Generated: 2026-05-05 | For full Mermaid diagrams see SYSTEM_LOGIC_CN.md*

