#!/usr/bin/env python3
"""
工厂管理ROS节点 - 适配原Python仿真系统
"""
import rospy
import sys
import os

# 添加原项目路径
sys.path.insert(0, '/home/qzl/graduate')

from run import SmartFactory
from geometry_msgs.msg import Pose, Point, Quaternion, Twist
from std_msgs.msg import String, Int32, Float32
from sensor_msgs.msg import JointState
import json

class FactoryManagerNode:
    def __init__(self):
        rospy.init_node('factory_manager', anonymous=False)
        
        # 初始化原Python仿真系统
        self.factory = SmartFactory(num_robots=10, batch_size=6)
        
        # ROS发布器
        self.state_pub = rospy.Publisher('/factory/state', String, queue_size=10)
        self.robot_poses_pub = rospy.Publisher('/factory/robot_poses', String, queue_size=10)
        
        # 订阅控制命令
        rospy.Subscriber('/factory/command', String, self.command_callback)
        
        # 定时器：10Hz更新
        self.timer = rospy.Timer(rospy.Duration(0.1), self.update_callback)
        
        self.is_running = False
        rospy.loginfo("✅ 工厂管理节点启动成功")
    
    def update_callback(self, event):
        """主更新循环"""
        if self.is_running and not self.factory.system_completed:
            # 执行仿真步骤
            self.factory.update()
            
            # 每10步发布一次状态
            if self.factory.current_time % 10 == 0:
                self.publish_state()
    
    def publish_state(self):
        """发布系统状态到ROS"""
        state_data = {
            'time': self.factory.current_time,
            'robots': [
                {
                    'id': r.id,
                    'x': float(r.position.x),
                    'y': float(r.position.y),
                    'status': r.status.value
                }
                for r in self.factory.robots
            ],
            'machines': [
                {
                    'id': m.id,
                    'type': m.type.value,
                    'x': float(m.position.x),
                    'y': float(m.position.y),
                    'materials_count': len(m.materials)
                }
                for m in self.factory.machines
            ],
            'statistics': {
                'completed_red': self.factory.process_monitor.material_counts['completed_red'],
                'total_materials': len(self.factory.materials)
            }
        }
        
        self.state_pub.publish(json.dumps(state_data))
    
    def command_callback(self, msg):
        """处理控制命令"""
        try:
            cmd = json.loads(msg.data)
            action = cmd.get('action')
            
            if action == 'start':
                self.is_running = True
                rospy.loginfo("▶️ 仿真开始")
            elif action == 'pause':
                self.is_running = False
                rospy.loginfo("⏸️ 仿真暂停")
            elif action == 'stop':
                self.is_running = False
                rospy.loginfo("⏹️ 仿真停止")
            elif action == 'reset':
                self.factory = SmartFactory(num_robots=10, batch_size=6)
                self.is_running = False
                rospy.loginfo("🔄 系统重置")
                
        except Exception as e:
            rospy.logerr(f"命令处理错误: {e}")

if __name__ == '__main__':
    try:
        node = FactoryManagerNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
