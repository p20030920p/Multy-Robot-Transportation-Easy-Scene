cmake_minimum_required(VERSION 3.0.2)
project(smart_factory_sim)

## 查找catkin和其他依赖包
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  nav_msgs
  sensor_msgs
  tf
  tf2_ros
  gazebo_ros
  gazebo_msgs
  move_base_msgs
  actionlib
  actionlib_msgs
  message_generation
)

## 声明自定义消息文件
add_message_files(
  FILES
  MaterialInfo.msg
  TaskStatus.msg
  MachineState.msg
)

## 声明自定义服务文件
add_service_files(
  FILES
  AssignTask.srv
  ProcessMaterial.srv
)

## 生成消息
generate_messages(
  DEPENDENCIES
  std_msgs
  geometry_msgs
  actionlib_msgs
)

## catkin配置
catkin_package(
  CATKIN_DEPENDS
    rospy
    std_msgs
    geometry_msgs
    nav_msgs
    sensor_msgs
    tf
    gazebo_ros
    move_base_msgs
    actionlib
    message_runtime
)

## 安装Python脚本
catkin_install_python(PROGRAMS
  scripts/factory_manager_node.py
  scripts/robot_controller_node.py
  scripts/task_scheduler_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## 安装launch文件
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
  FILES_MATCHING PATTERN "*.launch"
)

## 安装配置文件
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
  FILES_MATCHING PATTERN "*.yaml"
)

## 安装世界文件
install(DIRECTORY worlds/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/worlds
  FILES_MATCHING PATTERN "*.world"
)

## 安装URDF文件
install(DIRECTORY urdf/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/urdf
  FILES_MATCHING PATTERN "*.urdf" PATTERN "*.xacro"
)

## 安装模型文件
install(DIRECTORY models/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/models
)

## 安装Rviz配置
install(DIRECTORY rviz/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/rviz
  FILES_MATCHING PATTERN "*.rviz"
)
