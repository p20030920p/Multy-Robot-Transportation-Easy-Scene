#!/bin/bash
# 智能工厂ROS仿真系统 - 一键启动脚本

echo "=========================================="
echo "  智能工厂ROS仿真系统"
echo "  Ubuntu 20.04 + ROS Noetic + Gazebo 11"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步骤1：检查ROS安装
echo -e "${YELLOW}[1/6] 检查ROS环境...${NC}"
if [ -f "/opt/ros/noetic/setup.bash" ]; then
    source /opt/ros/noetic/setup.bash
    echo -e "${GREEN}✓ ROS Noetic已安装${NC}"
else
    echo -e "${RED}✗ 未找到ROS Noetic，请先安装！${NC}"
    exit 1
fi

# 步骤2：检查工作空间
echo -e "${YELLOW}[2/6] 检查catkin工作空间...${NC}"
WORKSPACE_PATH="$HOME/graduate/catkin_ws"
if [ -d "$WORKSPACE_PATH" ]; then
    echo -e "${GREEN}✓ 工作空间存在: $WORKSPACE_PATH${NC}"
else
    echo -e "${RED}✗ 工作空间不存在，请先创建！${NC}"
    exit 1
fi

# 步骤3：编译工作空间
echo -e "${YELLOW}[3/6] 编译catkin工作空间...${NC}"
cd "$WORKSPACE_PATH"
catkin_make

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 编译成功${NC}"
else
    echo -e "${RED}✗ 编译失败，请检查错误信息${NC}"
    exit 1
fi

# 步骤4：设置环境变量
echo -e "${YELLOW}[4/6] 设置环境变量...${NC}"
source "$WORKSPACE_PATH/devel/setup.bash"
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$WORKSPACE_PATH/src/smart_factory_sim/models
echo -e "${GREEN}✓ 环境变量已设置${NC}"

# 步骤5：检查依赖
echo -e "${YELLOW}[5/6] 检查ROS依赖包...${NC}"
MISSING_DEPS=0

# 检查必要的包
for pkg in gazebo_ros move_base map_server amcl robot_state_publisher; do
    if ! rospack find $pkg &> /dev/null; then
        echo -e "${RED}✗ 缺少包: $pkg${NC}"
        MISSING_DEPS=1
    fi
done

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${YELLOW}提示：运行以下命令安装缺失的包：${NC}"
    echo "sudo apt-get install ros-noetic-gazebo-ros-pkgs ros-noetic-navigation"
    read -p "是否现在安装？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            ros-noetic-gazebo-ros-pkgs \
            ros-noetic-gazebo-ros-control \
            ros-noetic-navigation \
            ros-noetic-robot-state-publisher \
            ros-noetic-joint-state-publisher
    else
        exit 1
    fi
fi

echo -e "${GREEN}✓ 依赖检查完成${NC}"

# 步骤6：启动仿真
echo -e "${YELLOW}[6/6] 启动ROS仿真系统...${NC}"
echo ""
echo "=========================================="
echo "  系统即将启动，请稍候..."
echo "  - Gazebo将在新窗口打开"
echo "  - 10个机器人将自动生成"
echo "  - Rviz可视化将启动"
echo "=========================================="
echo ""

sleep 2

# 启动launch文件
roslaunch smart_factory_sim factory.launch

# 捕获Ctrl+C
trap "echo -e '\n${YELLOW}正在关闭仿真系统...${NC}'; killall -9 gazebo gzserver gzclient; exit 0" SIGINT

echo -e "${GREEN}✓ 仿真系统已启动！${NC}"
