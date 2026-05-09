
#!/usr/bin/env python3
"""
机器人控制节点 - 迁移自robots.py的Robot类
负责：
1. 接收任务指令
2. 使用move_base导航到目标
3. 执行物料装卸动作
4. 上报机器人状态
"""

import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Int32
import tf
from enum import Enum

class RobotStatus(Enum):
    """机器人状态枚举"""
    IDLE = "idle"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    WAITING = "waiting"
    BLOCKED = "blocked"

class RobotController:
    """机器人控制器 - 替代原robots.py的Robot类"""
    
    def __init__(self):
        rospy.init_node('robot_controller', anonymous=False)
        
        # 获取机器人ID
        self.robot_id = rospy.get_param('~robot_id', 0)
        rospy.loginfo(f"🤖 机器人{self.robot_id}控制节点启动中...")
        
        # ========== 状态变量 ==========
        self.status = RobotStatus.IDLE
        self.current_pose = None
        self.current_task = None
        self.carrying_materials = []
        self.completed_tasks = 0
        
        # ========== move_base动作客户端 ==========
        self.move_client = actionlib.SimpleActionClient(
            f'/robot_{self.robot_id}/move_base', 
            MoveBaseAction
        )
        
        rospy.loginfo(f"机器人{self.robot_id}等待move_base服务器...")
        if not self.move_client.wait_for_server(rospy.Duration(10.0)):
            rospy.logerr(f"机器人{self.robot_id}无法连接到move_base服务器！")
            return
        
        rospy.loginfo(f"机器人{self.robot_id}已连接到move_base")
        
        # ========== 发布器 ==========
        self.status_pub = rospy.Publisher(
            f'/robot_{self.robot_id}/status', 
            String, 
            queue_size=10
        )
        
        self.pose_pub = rospy.Publisher(
            f'/robot_{self.robot_id}/current_pose', 
            PoseStamped, 
            queue_size=10
        )
        
        # ========== 订阅器 ==========
        # 订阅任务指令
        rospy.Subscriber(
            f'/robot_{self.robot_id}/task', 
            String, 
            self.task_callback
        )
        
        # 订阅里程计
        rospy.Subscriber(
            f'/robot_{self.robot_id}/odom', 
            Odometry, 
            self.odom_callback
        )
        
        # ========== TF监听器 ==========
        self.tf_listener = tf.TransformListener()
        
        # ========== 定时器 ==========
        # 状态发布定时器 - 1Hz
        rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        rospy.loginfo(f"✅ 机器人{self.robot_id}控制节点启动完成！")
    
    def task_callback(self, msg):
        """接收新任务"""
        task_str = msg.data
        rospy.loginfo(f"机器人{self.robot_id}接收任务: {task_str}")
        
        # 解析任务字符串 "TRANSPORT:source_x,source_y:dest_x,dest_y:material_type"
        try:
            parts = task_str.split(':')
            if len(parts) < 4:
                rospy.logwarn(f"任务格式错误: {task_str}")
                return
            
            task_type = parts[0]
            source_coords = parts[1].split(',')
            dest_coords = parts[2].split(',')
            material_type = parts[3]
            
            if task_type == "TRANSPORT":
                self.execute_transport_task(
                    float(source_coords[0]), 
                    float(source_coords[1]),
                    float(dest_coords[0]), 
                    float(dest_coords[1]),
                    material_type
                )
        except Exception as e:
            rospy.logerr(f"任务解析失败: {e}")
    
    def execute_transport_task(self, src_x, src_y, dst_x, dst_y, material_type):
        """执行搬运任务（替代原Robot.execute_task）"""
        rospy.loginfo(f"机器人{self.robot_id}开始执行搬运任务: "
                     f"从({src_x},{src_y})到({dst_x},{dst_y})")
        
        # 1. 移动到物料源
        self.status = RobotStatus.MOVING
        if not self.move_to_position(src_x, src_y):
            rospy.logwarn(f"机器人{self.robot_id}无法到达物料源")
            self.status = RobotStatus.IDLE
            return
        
        # 2. 装载物料
        self.status = RobotStatus.LOADING
        rospy.loginfo(f"机器人{self.robot_id}装载{material_type}物料...")
        rospy.sleep(2.0)  # 模拟装载时间
        self.carrying_materials.append(material_type)
        
        # 3. 移动到目标
        self.status = RobotStatus.MOVING
        if not self.move_to_position(dst_x, dst_y):
            rospy.logwarn(f"机器人{self.robot_id}无法到达目标")
            self.status = RobotStatus.IDLE
            return
        
        # 4. 卸载物料
        self.status = RobotStatus.UNLOADING
        rospy.loginfo(f"机器人{self.robot_id}卸载物料...")
        rospy.sleep(2.0)  # 模拟卸载时间
        if self.carrying_materials:
            self.carrying_materials.pop()
        
        # 5. 任务完成
        self.status = RobotStatus.IDLE
        self.completed_tasks += 1
        rospy.loginfo(f"✅ 机器人{self.robot_id}完成任务（总计{self.completed_tasks}个）")
    
    def move_to_position(self, x, y):
        """移动到指定位置（使用move_base）"""
        rospy.loginfo(f"机器人{self.robot_id}导航到: ({x:.2f}, {y:.2f})")
        
        # 创建目标
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = x
        goal.target_pose.pose.position.y = y
        goal.target_pose.pose.position.z = 0.0
        
        # 朝向（四元数，朝向目标方向）
        goal.target_pose.pose.orientation.x = 0.0
        goal.target_pose.pose.orientation.y = 0.0
        goal.target_pose.pose.orientation.z = 0.0
        goal.target_pose.pose.orientation.w = 1.0
        
        # 发送目标
        self.move_client.send_goal(goal)
        
        # 等待结果（超时30秒）
        success = self.move_client.wait_for_result(rospy.Duration(30.0))
        
        if not success:
            rospy.logwarn(f"机器人{self.robot_id}导航超时")
            self.move_client.cancel_goal()
            return False
        
        state = self.move_client.get_state()
        if state == actionlib.GoalStatus.SUCCEEDED:
            rospy.loginfo(f"机器人{self.robot_id}到达目标")
            return True
        else:
            rospy.logwarn(f"机器人{self.robot_id}导航失败，状态码: {state}")
            return False
    
    def odom_callback(self, msg):
        """里程计回调（更新当前位置）"""
        self.current_pose = msg.pose.pose
    
    def publish_status(self, event):
        """发布机器人状态"""
        status_msg = String()
        status_msg.data = f"{self.status.value}:{len(self.carrying_materials)}:{self.completed_tasks}"
        self.status_pub.publish(status_msg)
        
        # 发布当前位置
        if self.current_pose:
            pose_msg = PoseStamped()
            pose_msg.header.stamp = rospy.Time.now()
            pose_msg.header.frame_id = "map"
            pose_msg.pose = self.current_pose
            self.pose_pub.publish(pose_msg)
    
    def emergency_stop(self):
        """紧急停止"""
        rospy.logwarn(f"机器人{self.robot_id}紧急停止！")
        self.move_client.cancel_all_goals()
        self.status = RobotStatus.BLOCKED

if __name__ == '__main__':
    try:
        controller = RobotController()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo(f"机器人控制节点关闭")
