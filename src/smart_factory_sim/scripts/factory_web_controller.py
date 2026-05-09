#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能工厂Web控制器节点 - 优化版
功能：
1. 订阅10个机器人的odom和状态信息
2. 发布机器人目标点控制指令（简化版运动控制）
3. 通过rosbridge提供Web接口
4. 精确的区域检测和状态报告
5. 目标到达检测
"""

import rospy
import math
from geometry_msgs.msg import Twist, PoseStamped, Point
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Int32
import json

class FactoryWebController:
    def __init__(self):
        rospy.init_node('factory_web_controller', anonymous=False)
        
        # 工厂区域定义 (对应2D项目的区域，比例1:100，单位：米)
        self.areas = {
            # 存储区
            'empty_storage': {'center': (1.0, 1.0), 'radius': 0.4, 'name': '空桶存储区', 'type': 'storage'},
            'green_storage': {'center': (1.0, 3.0), 'radius': 0.4, 'name': '绿桶存储区', 'type': 'storage'},
            'yellow_storage': {'center': (1.0, 5.0), 'radius': 0.4, 'name': '黄桶存储区', 'type': 'storage'},
            'red_storage': {'center': (1.0, 7.0), 'radius': 0.4, 'name': '红桶存储区', 'type': 'storage'},
            'completed': {'center': (9.5, 4.0), 'radius': 0.5, 'name': '完成区', 'type': 'storage'},
            
            # 梳棉机区域
            'carding_waiting_0': {'center': (2.5, 1.5), 'radius': 0.35, 'name': '梳棉机0等待区', 'type': 'waiting'},
            'carding_machine_0': {'center': (3.25, 1.5), 'radius': 0.3, 'name': '梳棉机0', 'type': 'machine'},
            'carding_finished_0': {'center': (4.0, 1.5), 'radius': 0.35, 'name': '梳棉机0完成区', 'type': 'finished'},
            
            'carding_waiting_1': {'center': (2.5, 3.5), 'radius': 0.35, 'name': '梳棉机1等待区', 'type': 'waiting'},
            'carding_machine_1': {'center': (3.25, 3.5), 'radius': 0.3, 'name': '梳棉机1', 'type': 'machine'},
            'carding_finished_1': {'center': (4.0, 3.5), 'radius': 0.35, 'name': '梳棉机1完成区', 'type': 'finished'},
            
            'carding_waiting_2': {'center': (2.5, 5.5), 'radius': 0.35, 'name': '梳棉机2等待区', 'type': 'waiting'},
            'carding_machine_2': {'center': (3.25, 5.5), 'radius': 0.3, 'name': '梳棉机2', 'type': 'machine'},
            'carding_finished_2': {'center': (4.0, 5.5), 'radius': 0.35, 'name': '梳棉机2完成区', 'type': 'finished'},
            
            'carding_waiting_3': {'center': (2.5, 7.5), 'radius': 0.35, 'name': '梳棉机3等待区', 'type': 'waiting'},
            'carding_machine_3': {'center': (3.25, 7.5), 'radius': 0.3, 'name': '梳棉机3', 'type': 'machine'},
            'carding_finished_3': {'center': (4.0, 7.5), 'radius': 0.35, 'name': '梳棉机3完成区', 'type': 'finished'},
            
            # 拉伸机1区域
            'drawing1_waiting_0': {'center': (5.0, 2.0), 'radius': 0.35, 'name': '拉伸机1-0等待区', 'type': 'waiting'},
            'drawing1_machine_0': {'center': (5.75, 2.0), 'radius': 0.3, 'name': '拉伸机1-0', 'type': 'machine'},
            'drawing1_finished_0': {'center': (6.5, 2.0), 'radius': 0.35, 'name': '拉伸机1-0完成区', 'type': 'finished'},
            
            'drawing1_waiting_1': {'center': (5.0, 5.0), 'radius': 0.35, 'name': '拉伸机1-1等待区', 'type': 'waiting'},
            'drawing1_machine_1': {'center': (5.75, 5.0), 'radius': 0.3, 'name': '拉伸机1-1', 'type': 'machine'},
            'drawing1_finished_1': {'center': (6.5, 5.0), 'radius': 0.35, 'name': '拉伸机1-1完成区', 'type': 'finished'},
            
            # 拉伸机2区域
            'drawing2_waiting_0': {'center': (7.0, 2.0), 'radius': 0.35, 'name': '拉伸机2-0等待区', 'type': 'waiting'},
            'drawing2_machine_0': {'center': (7.75, 2.0), 'radius': 0.3, 'name': '拉伸机2-0', 'type': 'machine'},
            'drawing2_finished_0': {'center': (8.5, 2.0), 'radius': 0.35, 'name': '拉伸机2-0完成区', 'type': 'finished'},
            
            'drawing2_waiting_1': {'center': (7.0, 5.0), 'radius': 0.35, 'name': '拉伸机2-1等待区', 'type': 'waiting'},
            'drawing2_machine_1': {'center': (7.75, 5.0), 'radius': 0.3, 'name': '拉伸机2-1', 'type': 'machine'},
            'drawing2_finished_1': {'center': (8.5, 5.0), 'radius': 0.35, 'name': '拉伸机2-1完成区', 'type': 'finished'},
        }
        
        # 机器人状态存储
        self.robot_states = {}
        self.robot_goals = {}
        
        for i in range(10):
            self.robot_states[i] = {
                'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0},
                'velocity': {'linear': 0.0, 'angular': 0.0},
                'current_area': '自由区域',
                'goal_position': None,
                'goal_reached': True,
                'distance_to_goal': 0.0,
                'status': 'idle',
                'last_update': rospy.Time.now().to_sec()
            }
            self.robot_goals[i] = None
        
        # 订阅和发布
        self.odom_subscribers = []
        for i in range(10):
            sub = rospy.Subscriber(f'/robot_{i}/odom', Odometry, 
                                   self.odom_callback, callback_args=i)
            self.odom_subscribers.append(sub)
        
        self.cmd_vel_publishers = []
        for i in range(10):
            pub = rospy.Publisher(f'/robot_{i}/cmd_vel', Twist, queue_size=10)
            self.cmd_vel_publishers.append(pub)
        
        self.status_pub = rospy.Publisher('/factory/status', String, queue_size=10)
        self.cmd_sub = rospy.Subscriber('/factory/command', String, self.command_callback)
        
        self.status_timer = rospy.Timer(rospy.Duration(0.1), self.publish_status)
        self.control_timer = rospy.Timer(rospy.Duration(0.05), self.control_update)
        
        rospy.loginfo("=" * 50)
        rospy.loginfo("✅ 智能工厂Web控制器已启动")
        rospy.loginfo("=" * 50)
        
    def odom_callback(self, msg, robot_id):
        pos = msg.pose.pose.position
        orient = msg.pose.pose.orientation
        vel = msg.twist.twist
        
        self.robot_states[robot_id]['position'] = {'x': pos.x, 'y': pos.y, 'z': pos.z}
        self.robot_states[robot_id]['orientation'] = {'x': orient.x, 'y': orient.y, 'z': orient.z, 'w': orient.w}
        
        linear_vel = math.sqrt(vel.linear.x**2 + vel.linear.y**2)
        self.robot_states[robot_id]['velocity'] = {'linear': linear_vel, 'angular': vel.angular.z}
        self.robot_states[robot_id]['current_area'] = self.detect_area(pos.x, pos.y)
        
        if self.robot_goals[robot_id] is not None:
            goal_x, goal_y = self.robot_goals[robot_id]
            distance = math.sqrt((pos.x - goal_x)**2 + (pos.y - goal_y)**2)
            self.robot_states[robot_id]['distance_to_goal'] = distance
            
            if distance < 0.15:
                if not self.robot_states[robot_id]['goal_reached']:
                    self.robot_states[robot_id]['goal_reached'] = True
                    self.robot_states[robot_id]['status'] = 'idle'
                    rospy.loginfo(f"✅ 机器人{robot_id}已到达目标")
            else:
                self.robot_states[robot_id]['goal_reached'] = False
        
        if linear_vel > 0.02:
            self.robot_states[robot_id]['status'] = 'moving'
        elif not self.robot_states[robot_id]['goal_reached'] and self.robot_goals[robot_id]:
            self.robot_states[robot_id]['status'] = 'waiting'
        else:
            self.robot_states[robot_id]['status'] = 'idle'
    
    def detect_area(self, x, y):
        min_distance = float('inf')
        closest_area = '自由区域'
        
        for area_id, area_info in self.areas.items():
            cx, cy = area_info['center']
            radius = area_info['radius']
            distance = math.sqrt((x - cx)**2 + (y - cy)**2)
            
            if distance <= radius and distance < min_distance:
                min_distance = distance
                closest_area = area_info['name']
        
        return closest_area
    
    def command_callback(self, msg):
        try:
            command = json.loads(msg.data)
            cmd_type = command.get('type', '')
            
            if cmd_type == 'set_goal':
                robot_id = command.get('robot_id', 0)
                x = command.get('x', 0.0)
                y = command.get('y', 0.0)
                self.set_robot_goal(robot_id, x, y)
            elif cmd_type == 'stop_robot':
                robot_id = command.get('robot_id', 0)
                self.stop_robot(robot_id)
            elif cmd_type == 'stop_all':
                for i in range(10):
                    self.stop_robot(i)
            elif cmd_type == 'go_to_area':
                robot_id = command.get('robot_id', 0)
                area_id = command.get('area_id', '')
                self.go_to_area(robot_id, area_id)
        except Exception as e:
            rospy.logerr(f"❌ 指令执行错误: {e}")
    
    def set_robot_goal(self, robot_id, x, y):
        if 0 <= robot_id < 10:
            self.robot_goals[robot_id] = (x, y)
            self.robot_states[robot_id]['goal_position'] = {'x': x, 'y': y}
            self.robot_states[robot_id]['goal_reached'] = False
            self.robot_states[robot_id]['status'] = 'moving'
            rospy.loginfo(f"🎯 机器人{robot_id}设置目标: ({x:.2f}, {y:.2f})")
    
    def go_to_area(self, robot_id, area_id):
        if area_id in self.areas:
            cx, cy = self.areas[area_id]['center']
            self.set_robot_goal(robot_id, cx, cy)
    
    def stop_robot(self, robot_id):
        if 0 <= robot_id < 10:
            cmd = Twist()
            self.cmd_vel_publishers[robot_id].publish(cmd)
            self.robot_goals[robot_id] = None
            self.robot_states[robot_id]['goal_reached'] = True
            self.robot_states[robot_id]['status'] = 'idle'
    
    def control_update(self, event):
        for robot_id in range(10):
            if self.robot_goals[robot_id] is None or self.robot_states[robot_id]['goal_reached']:
                continue
            
            target_x, target_y = self.robot_goals[robot_id]
            pos = self.robot_states[robot_id]['position']
            orient = self.robot_states[robot_id]['orientation']
            
            dx = target_x - pos['x']
            dy = target_y - pos['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 0.15:
                self.stop_robot(robot_id)
                continue
            
            target_angle = math.atan2(dy, dx)
            qw = orient['w']
            qz = orient['z']
            current_yaw = math.atan2(2.0 * qw * qz, 1.0 - 2.0 * qz * qz)
            
            angle_diff = target_angle - current_yaw
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            cmd = Twist()
            if abs(angle_diff) > 0.3:
                cmd.linear.x = 0.1
                cmd.angular.z = 1.5 * angle_diff
            else:
                cmd.linear.x = min(0.5, distance * 1.0)
                cmd.angular.z = 1.0 * angle_diff
            
            cmd.linear.x = max(-0.5, min(0.5, cmd.linear.x))
            cmd.angular.z = max(-2.0, min(2.0, cmd.angular.z))
            
            self.cmd_vel_publishers[robot_id].publish(cmd)
    
    def publish_status(self, event):
        status_data = {
            'timestamp': rospy.Time.now().to_sec(),
            'robots': [],
            'areas': self.get_area_list()
        }
        
        for robot_id, state in self.robot_states.items():
            robot_info = {
                'id': robot_id,
                'position': state['position'],
                'velocity': state['velocity'],
                'current_area': state['current_area'],
                'goal_position': state.get('goal_position'),
                'distance_to_goal': state.get('distance_to_goal', 0.0),
                'goal_reached': state.get('goal_reached', True),
                'status': state['status']
            }
            status_data['robots'].append(robot_info)
        
        status_msg = String()
        status_msg.data = json.dumps(status_data)
        self.status_pub.publish(status_msg)
    
    def get_area_list(self):
        area_list = []
        for area_id, area_info in self.areas.items():
            area_list.append({
                'id': area_id,
                'name': area_info['name'],
                'center': area_info['center'],
                'radius': area_info['radius'],
                'type': area_info['type']
            })
        return area_list
    
    def run(self):
        rospy.spin()

if __name__ == '__main__':
    try:
        controller = FactoryWebController()
        controller.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("工厂Web控制器节点已关闭")
