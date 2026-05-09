#!/usr/bin/env python3
"""
Gazebo机器人控制节点
接收仿真系统的指令，控制Gazebo中的机器人移动
"""

import rospy
import json
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import math

class GazeboRobotController:
    def __init__(self, robot_id):
        self.robot_id = robot_id
        self.namespace = f'/robot_{robot_id}'
        
        # 当前位置和目标位置
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        
        self.target_x = 0.0
        self.target_y = 0.0
        self.has_target = False
        
        # 控制参数
        self.linear_speed = 0.5  # m/s
        self.angular_speed = 1.0  # rad/s
        self.position_tolerance = 0.1  # 米
        
        # 发布器：控制机器人速度
        self.cmd_vel_pub = rospy.Publisher(
            f'{self.namespace}/cmd_vel', 
            Twist, 
            queue_size=10
        )
        
        # 订阅器：获取机器人位置
        self.odom_sub = rospy.Subscriber(
            f'{self.namespace}/odom',
            Odometry,
            self.odom_callback
        )
        
        # 订阅器：接收目标位置指令
        self.target_sub = rospy.Subscriber(
            f'{self.namespace}/target_position',
            String,
            self.target_callback
        )
        
        rospy.loginfo(f"✅ 机器人 {robot_id} 控制器已启动")
    
    def odom_callback(self, msg):
        """里程计回调：更新当前位置"""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # 从四元数计算yaw角
        orientation = msg.pose.pose.orientation
        siny_cosp = 2 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy_cosp = 1 - 2 * (orientation.y * orientation.y + orientation.z * orientation.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)
    
    def target_callback(self, msg):
        """目标位置回调：接收新目标"""
        try:
            data = json.loads(msg.data)
            self.target_x = data['x']
            self.target_y = data['y']
            self.has_target = True
            rospy.loginfo(f"🎯 机器人{self.robot_id} 收到新目标: ({self.target_x:.2f}, {self.target_y:.2f})")
        except Exception as e:
            rospy.logerr(f"❌ 解析目标位置失败: {e}")
    
    def calculate_distance(self):
        """计算到目标的距离"""
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        return math.sqrt(dx*dx + dy*dy)
    
    def calculate_angle_to_target(self):
        """计算到目标的角度"""
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        return math.atan2(dy, dx)
    
    def normalize_angle(self, angle):
        """归一化角度到[-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
    
    def control_loop(self):
        """主控制循环"""
        rate = rospy.Rate(10)  # 10 Hz
        
        while not rospy.is_shutdown():
            if not self.has_target:
                # 没有目标，停止
                self.stop_robot()
                rate.sleep()
                continue
            
            distance = self.calculate_distance()
            
            if distance < self.position_tolerance:
                # 到达目标
                self.stop_robot()
                self.has_target = False
                rospy.loginfo(f"✅ 机器人{self.robot_id} 到达目标")
                rate.sleep()
                continue
            
            # 计算需要转向的角度
            target_angle = self.calculate_angle_to_target()
            angle_diff = self.normalize_angle(target_angle - self.current_yaw)
            
            # 创建速度命令
            cmd = Twist()
            
            # 如果角度偏差较大，先转向
            if abs(angle_diff) > 0.1:
                cmd.linear.x = 0.0
                cmd.angular.z = self.angular_speed if angle_diff > 0 else -self.angular_speed
            else:
                # 角度接近，直线前进
                cmd.linear.x = min(self.linear_speed, distance)
                cmd.angular.z = 0.5 * angle_diff  # 微调方向
            
            self.cmd_vel_pub.publish(cmd)
            rate.sleep()
    
    def stop_robot(self):
        """停止机器人"""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)

def main():
    rospy.init_node('gazebo_robot_controller')
    
    # 从参数服务器获取机器人ID
    robot_id = rospy.get_param('~robot_id', 0)
    
    controller = GazeboRobotController(robot_id)
    
    try:
        controller.control_loop()
    except rospy.ROSInterruptException:
        rospy.loginfo(f"机器人{robot_id}控制器关闭")

if __name__ == '__main__':
    main()
