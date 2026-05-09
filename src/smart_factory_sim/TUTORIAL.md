# 🎯 ROS智能工厂仿真系统 - 实战使用指南

## 📋 前置检查清单

在开始之前，确认以下内容：
- ✅ Ubuntu 20.04 系统
- ✅ ROS Noetic 已安装
- ✅ 工作空间已编译（catkin_make成功）
- ✅ 所有依赖包已安装

---

## 🚀 第一次使用（新手推荐）

### 步骤1：打开终端并设置环境

```bash
# 进入工作空间
cd ~/graduate/catkin_ws

# 加载ROS环境
source /opt/ros/noetic/setup.bash
source devel/setup.bash

# 验证功能包
rospack find smart_factory_sim
# 如果输出路径，说明功能包正常
```

### 步骤2：启动Gazebo测试（最简单）

这个测试会启动Gazebo 3D仿真环境，显示工厂车间和一个测试机器人。

```bash
roslaunch smart_factory_sim test_gazebo_only.launch
```

**你将看到**：
1. 终端输出启动日志
2. Gazebo窗口自动打开（需要等待10-30秒）
3. 一个10m×10m的灰色工厂地面
4. 四周有灰色围墙
5. 一个蓝色的AGV机器人在地面上

**操作技巧**：
- 🖱️ **鼠标左键拖拽**：旋转视角
- 🖱️ **鼠标滚轮**：缩放
- 🖱️ **Shift+鼠标左键**：平移视角
- ⏸️ **底部播放按钮**：暂停/继续仿真

**如果Gazebo启动很慢**：
```bash
# 首次启动会下载模型，可以在新终端查看下载进度
tail -f ~/.gazebo/server.log
```

---

### 步骤3：查看ROS话题（验证系统运行）

**在新终端**执行以下命令（保持Gazebo运行）：

```bash
# 终端1：保持Gazebo运行
# 不要关闭上一个终端！

# 打开新终端2
cd ~/graduate/catkin_ws
source devel/setup.bash

# 查看所有话题
rostopic list

# 你应该看到类似输出：
# /test_robot_0/cmd_vel       # 机器人速度控制
# /test_robot_0/odom          # 机器人里程计
# /test_robot_0/scan          # 激光雷达数据
# /gazebo/model_states        # Gazebo中所有模型状态
```

**查看机器人位置**：
```bash
rostopic echo /test_robot_0/odom
```

你会看到实时更新的位置数据：
```yaml
position: 
  x: 1.0
  y: 1.0
  z: 0.1
```

**停止查看**：按 `Ctrl+C`

---

### 步骤4：手动控制机器人移动

让我们手动发送指令让机器人移动：

```bash
# 在终端2中执行
rostopic pub -1 /test_robot_0/cmd_vel geometry_msgs/Twist "linear:
  x: 0.5
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.5"
```

**观察Gazebo窗口**：机器人应该开始移动并旋转！

**停止机器人**：
```bash
rostopic pub -1 /test_robot_0/cmd_vel geometry_msgs/Twist "linear:
  x: 0.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0"
```

---

## 🏭 第二次使用（启动完整工厂）

现在你已经熟悉了基础操作，让我们启动完整的工厂系统。

### 步骤1：关闭之前的测试

```bash
# 在运行Gazebo的终端按 Ctrl+C
# 或者在新终端执行：
rosnode kill -a
killall -9 gzserver gzclient
```

### 步骤2：启动完整工厂（包含10个机器人）

```bash
cd ~/graduate/catkin_ws
source devel/setup.bash

# 启动完整工厂仿真
roslaunch smart_factory_sim factory.launch
```

**注意**：如果出现错误"找不到地图文件"，这是正常的，我们稍后会创建。

**你将看到**：
- Gazebo窗口打开
- 10个蓝色AGV机器人
- 10台机器（圆柱形，不同颜色）
- 5个存储区域（不同颜色的方块）

---

### 步骤3：启动工厂管理节点

**在新终端3**执行：

```bash
cd ~/graduate/catkin_ws
source devel/setup.bash

# 启动工厂主控节点
rosrun smart_factory_sim factory_manager_node.py
```

**你将看到**：
```
🏭 工厂管理节点启动中...
正在初始化工厂布局...
创建区域: empty_storage at (1.0, 1.0)
创建区域: green_storage at (1.0, 3.0)
...
✅ 工厂布局初始化完成
✅ 工厂管理节点启动完成！
```

---

### 步骤4：启动任务调度器

**在新终端4**执行：

```bash
cd ~/graduate/catkin_ws
source devel/setup.bash

# 启动任务调度节点
rosrun smart_factory_sim task_scheduler_node.py
```

**你将看到**：
```
📋 任务调度节点启动中...
✅ 任务调度节点启动完成！
```

---

### 步骤5：发布测试任务

让我们手动发布一个搬运任务：

**在新终端5**执行：

```bash
cd ~/graduate/catkin_ws
source devel/setup.bash

# 发布一个搬运任务
# 格式：优先级:起点x,起点y:终点x,终点y:物料类型
rostopic pub -1 /factory/task_request std_msgs/String "data: '100:1.0,1.0:5.0,5.0:empty'"
```

**观察**：
- 终端3（工厂管理器）应该显示任务已接收
- 终端4（调度器）应该显示任务已分配给某个机器人
- Gazebo中某个机器人开始移动！

---

## 📊 查看系统状态

### 查看所有ROS节点
```bash
rosnode list
# 输出：
# /factory_manager
# /task_scheduler
# /robot_0/robot_controller
# /robot_1/robot_controller
# ...
```

### 查看所有话题
```bash
rostopic list | grep factory
# 输出：
# /factory/tasks
# /factory/statistics
# /factory/progress
# /factory/task_request
```

### 实时监控机器人状态
```bash
rostopic echo /robot_0/status
```

### 查看TF树（坐标变换关系）
```bash
rosrun rqt_tf_tree rqt_tf_tree
# 会打开一个图形界面显示坐标系关系
```

---

## 🎮 使用Rviz可视化

Rviz是ROS的3D可视化工具，比Gazebo更适合调试。

```bash
# 在新终端启动Rviz
rviz
```

**配置Rviz**：

1. **左下角"Add"按钮** → 添加显示项
2. **添加"RobotModel"** → 显示机器人模型
3. **添加"LaserScan"** → 显示激光雷达
   - Topic: `/robot_0/scan`
4. **添加"TF"** → 显示坐标变换
5. **添加"Map"** → 显示地图（需要先创建地图）

**保存配置**：
- File → Save Config As → 保存到 `rviz/factory_view.rviz`

**下次直接加载**：
```bash
rviz -d ~/graduate/catkin_ws/src/smart_factory_sim/rviz/factory_view.rviz
```

---

## 🐛 常见问题解决

### 问题1：Gazebo启动失败

**症状**：终端显示`[gazebo-1] process has died`

**解决**：
```bash
# 杀死残留进程
killall -9 gzserver gzclient

# 清理Gazebo缓存
rm -rf ~/.gazebo/log/*

# 重新启动
roslaunch smart_factory_sim test_gazebo_only.launch
```

---

### 问题2：找不到功能包

**症状**：`[rospack] Error: package 'smart_factory_sim' not found`

**解决**：
```bash
cd ~/graduate/catkin_ws
catkin_make
source devel/setup.bash
rospack profile  # 刷新包索引
```

---

### 问题3：Python节点无法执行

**症状**：`Permission denied`

**解决**：
```bash
chmod +x ~/graduate/catkin_ws/src/smart_factory_sim/scripts/*.py
```

---

### 问题4：机器人不动

**检查清单**：

1. **检查机器人是否收到速度指令**：
   ```bash
   rostopic echo /robot_0/cmd_vel
   ```

2. **检查导航节点是否启动**：
   ```bash
   rosnode list | grep move_base
   ```

3. **查看日志**：
   ```bash
   rosrun rqt_console rqt_console
   ```

---

## 🎯 快速参考

### 一键启动脚本（推荐）

创建一个启动脚本 `start_all.sh`：

```bash
#!/bin/bash
# 保存到 ~/graduate/catkin_ws/start_all.sh

echo "🚀 启动智能工厂ROS仿真系统"

# 设置环境
cd ~/graduate/catkin_ws
source /opt/ros/noetic/setup.bash
source devel/setup.bash

# 启动Gazebo（后台）
gnome-terminal -- bash -c "roslaunch smart_factory_sim test_gazebo_only.launch; exec bash"

sleep 5

# 启动工厂管理器
gnome-terminal -- bash -c "source devel/setup.bash && rosrun smart_factory_sim factory_manager_node.py; exec bash"

sleep 2

# 启动任务调度器
gnome-terminal -- bash -c "source devel/setup.bash && rosrun smart_factory_sim task_scheduler_node.py; exec bash"

echo "✅ 系统启动完成！"
```

**使用**：
```bash
chmod +x ~/graduate/catkin_ws/start_all.sh
~/graduate/catkin_ws/start_all.sh
```

---

## 📚 进阶功能

### 录制和回放

**录制仿真数据**：
```bash
rosbag record -a -O factory_sim.bag
```

**回放**：
```bash
rosbag play factory_sim.bag
```

### 性能分析

**查看消息频率**：
```bash
rostopic hz /robot_0/odom
```

**查看消息内容**：
```bash
rostopic echo /factory/statistics
```

---

## 💡 下一步学习

1. ✅ 修改机器人URDF模型（`urdf/agv_robot.urdf.xacro`）
2. ✅ 调整导航参数（`config/base_local_planner_params.yaml`）
3. ✅ 添加新的任务类型（修改`task_scheduler_node.py`）
4. ✅ 创建自定义Gazebo模型（`models/`目录）
5. ✅ 实现多机器人协同避障

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`rosrun rqt_console rqt_console`
2. 检查话题：`rostopic list`
3. 检查节点：`rosnode list`
4. 查看TF：`rosrun tf view_frames`
5. 阅读README：`~/graduate/catkin_ws/src/smart_factory_sim/README.md`

**版本**：v1.0  
**最后更新**：2025-11-19
