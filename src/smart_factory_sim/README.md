# 智能工厂ROS仿真系统

## 🎯 项目简介

将原Windows下的Python 2D仿真系统迁移到**Ubuntu 20.04 + ROS1 Noetic + Gazebo 11**的3D仿真环境。

### 系统特点
- ✅ 10个AGV机器人协同搬运
- ✅ 真实3D物理仿真（Gazebo）
- ✅ ROS导航栈（替代自定义A*）
- ✅ 多机器人任务调度
- ✅ Rviz 3D可视化

---

## 📦 环境要求

### 必需软件
- Ubuntu 20.04 LTS
- ROS Noetic Ninjemys
- Gazebo 11
- Python 3.8+

### 检查ROS安装
```bash
rosversion -d  # 应输出 noetic
gazebo --version  # 应输出 Gazebo 11.x
```

---

## 🚀 快速开始

### 方法一：一键启动（推荐）

```bash
cd ~/graduate/catkin_ws/src/smart_factory_sim/scripts
./setup_and_run.sh
```

### 方法二：手动启动

```bash
# 1. 编译工作空间
cd ~/graduate/catkin_ws
catkin_make
source devel/setup.bash

# 2. 启动仿真
roslaunch smart_factory_sim factory.launch
```

### 方法三：分步启动（调试用）

```bash
# 终端1：启动Gazebo世界
roslaunch smart_factory_sim gazebo_world.launch

# 终端2：启动机器人
roslaunch smart_factory_sim spawn_robots.launch

# 终端3：启动任务调度
rosrun smart_factory_sim task_scheduler_node.py

# 终端4：启动Rviz可视化
rviz -d ~/graduate/catkin_ws/src/smart_factory_sim/rviz/factory_view.rviz
```

---

## 📊 系统架构

```
ROS Master
├── Gazebo (3D仿真环境)
│   ├── 10个AGV机器人
│   ├── 10台机器（梳棉/拉伸/粗纱）
│   └── 500个物料桶
│
├── factory_manager_node (工厂主控)
│   ├── 生成搬运任务
│   └── 监控生产进度
│
├── task_scheduler_node (任务调度)
│   ├── 优先级队列
│   └── 任务分配
│
├── robot_controller_node x10 (机器人控制)
│   ├── move_base导航
│   └── 物料装卸
│
└── Rviz (3D可视化)
```

---

## 🛠️ 安装依赖

### ROS基础包
```bash
sudo apt-get update
sudo apt-get install -y \
    ros-noetic-gazebo-ros-pkgs \
    ros-noetic-gazebo-ros-control \
    ros-noetic-navigation \
    ros-noetic-move-base \
    ros-noetic-amcl \
    ros-noetic-map-server \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-rviz \
    ros-noetic-rqt \
    ros-noetic-rqt-common-plugins
```

### Python依赖
```bash
pip3 install numpy scipy
```

---

## 📖 使用指南

### 查看话题列表
```bash
rostopic list
```

**主要话题**：
- `/factory/tasks` - 任务发布
- `/robot_0/cmd_vel` - 机器人速度控制
- `/robot_0/odom` - 里程计数据
- `/robot_0/scan` - 激光雷达数据

### 查看节点状态
```bash
rosnode list
rosnode info /factory_manager
```

### 查看TF树
```bash
rosrun rqt_tf_tree rqt_tf_tree
```

### 手动发布任务
```bash
# 发布搬运任务：优先级100，从(1,1)到(5,5)，物料类型empty
rostopic pub /factory/task_request std_msgs/String "data: '100:1.0,1.0:5.0,5.0:empty'"
```

---

## 🔧 参数配置

### launch文件参数

在`factory.launch`中可以修改：

```xml
<arg name="num_robots" default="10"/>    <!-- 机器人数量 -->
<arg name="batch_size" default="6"/>     <!-- 批次大小 -->
<arg name="use_rviz" default="true"/>    <!-- 是否启动Rviz -->
<arg name="use_gui" default="true"/>     <!-- 是否显示Gazebo GUI -->
```

启动时覆盖参数：
```bash
roslaunch smart_factory_sim factory.launch num_robots:=5 use_gui:=false
```

### 导航参数

编辑配置文件：
- `config/base_local_planner_params.yaml` - 路径规划器参数
- `config/costmap_common.yaml` - 代价地图参数
- `config/global_costmap.yaml` - 全局地图参数
- `config/local_costmap.yaml` - 局部地图参数

---

## 🐛 故障排查

### 问题1：Gazebo启动很慢
**原因**：首次启动下载模型  
**解决**：
```bash
# 设置本地模型路径
export GAZEBO_MODEL_PATH=/usr/share/gazebo-11/models:$GAZEBO_MODEL_PATH
```

### 问题2：机器人导航失败
**原因**：代价地图参数不合适  
**解决**：调整`costmap_common.yaml`中的`robot_radius`

### 问题3：编译错误
```bash
cd ~/graduate/catkin_ws
catkin_make clean
catkin_make
```

### 问题4：Python节点无法执行
```bash
chmod +x ~/graduate/catkin_ws/src/smart_factory_sim/scripts/*.py
```

### 问题5：找不到功能包
```bash
source ~/graduate/catkin_ws/devel/setup.bash
rospack profile
```

---

## 📝 开发指南

### 添加新的机器人

1. 修改`launch/factory.launch`，增加新的robot group
2. 调整机器人初始位置
3. 更新`num_robots`参数

### 修改机器人模型

编辑`urdf/agv_robot.urdf.xacro`：
- 调整尺寸：修改`base_width`、`base_length`
- 添加传感器：增加新的link和joint
- 修改物理属性：调整mass、inertia

### 自定义任务类型

1. 在`task_scheduler_node.py`中添加新的任务类型
2. 在`robot_controller_node.py`中实现对应的执行逻辑
3. 更新任务请求格式

---

## 📊 性能指标

| 指标 | 原Python系统 | ROS+Gazebo系统 |
|------|-------------|----------------|
| 仿真维度 | 2D平面 | 3D空间 |
| 物理引擎 | 无 | Gazebo ODE |
| 路径规划 | 自定义A* | ROS navigation |
| 碰撞检测 | 简单半径 | 真实碰撞体 |
| 可视化 | HTML Canvas | Rviz 3D |
| 实时性 | 130x | 1x (实时) |

---

## 🎓 相关文档

- [ROS官方教程](http://wiki.ros.org/ROS/Tutorials)
- [Gazebo教程](http://gazebosim.org/tutorials)
- [navigation包文档](http://wiki.ros.org/navigation)
- [move_base参数说明](http://wiki.ros.org/move_base)

---

## 📞 技术支持

遇到问题？查看以下资源：
1. 查看日志：`rosrun rqt_console rqt_console`
2. 检查TF：`rosrun tf view_frames`
3. 调试节点：`rosnode info <node_name>`
4. 查看参数：`rosparam list`

---

## 📄 许可证

MIT License

---

## 🙏 致谢

本项目从Windows Python仿真系统迁移而来，感谢原系统的设计与实现。

**版本**：v1.0.0  
**更新日期**：2025年11月19日
