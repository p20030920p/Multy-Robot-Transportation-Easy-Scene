#!/usr/bin/env python3
"""
任务调度节点 - 迁移自scheduling.py的TaskScheduler类
负责：
1. 接收工厂管理节点的任务请求
2. 根据机器人状态分配任务
3. 维护任务优先级队列
4. 监控任务执行进度
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Point
from collections import deque
import heapq

class Task:
    """任务类"""
    def __init__(self, task_id, task_type, priority, source, destination, material_type):
        self.task_id = task_id
        self.task_type = task_type
        self.priority = priority
        self.source = source  # (x, y)
        self.destination = destination  # (x, y)
        self.material_type = material_type
        self.status = 'pending'
        self.assigned_robot = None
    
    def __lt__(self, other):
        # 优先级越高，数值越小（用于heapq）
        return self.priority < other.priority

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        rospy.init_node('task_scheduler', anonymous=False)
        rospy.loginfo("📋 任务调度节点启动中...")
        
        # ========== 参数 ==========
        self.num_robots = rospy.get_param('~num_robots', 10)
        
        # ========== 任务队列 ==========
        self.task_queue = []  # 优先级队列（heapq）
        self.active_tasks = {}  # {task_id: Task}
        self.completed_tasks = []
        self.next_task_id = 0
        
        # ========== 机器人状态追踪 ==========
        self.robot_states = {}  # {robot_id: {'status': 'idle', 'position': (x,y)}}
        for i in range(self.num_robots):
            self.robot_states[i] = {'status': 'idle', 'position': (0, 0)}
        
        # ========== ROS发布器 ==========
        # 为每个机器人创建任务发布器
        self.robot_task_pubs = {}
        for i in range(self.num_robots):
            self.robot_task_pubs[i] = rospy.Publisher(
                f'/robot_{i}/task', 
                String, 
                queue_size=10
            )
        
        # ========== ROS订阅器 ==========
        # 订阅工厂管理节点的任务请求
        rospy.Subscriber('/factory/task_request', String, self.task_request_callback)
        
        # 订阅机器人状态
        for i in range(self.num_robots):
            rospy.Subscriber(
                f'/robot_{i}/status', 
                String, 
                lambda msg, robot_id=i: self.robot_status_callback(msg, robot_id)
            )
        
        # ========== 定时器 ==========
        # 任务分配定时器 - 2Hz
        rospy.Timer(rospy.Duration(0.5), self.assign_tasks_callback)
        
        # 统计输出定时器 - 0.1Hz (每10秒)
        rospy.Timer(rospy.Duration(10.0), self.print_statistics)
        
        rospy.loginfo("✅ 任务调度节点启动完成！")
    
    def task_request_callback(self, msg):
        """接收任务请求"""
        # 解析任务请求 "priority:src_x,src_y:dst_x,dst_y:material_type"
        try:
            parts = msg.data.split(':')
            if len(parts) < 4:
                rospy.logwarn(f"任务请求格式错误: {msg.data}")
                return
            
            priority = int(parts[0])
            source = tuple(map(float, parts[1].split(',')))
            destination = tuple(map(float, parts[2].split(',')))
            material_type = parts[3]
            
            # 创建任务
            task = Task(
                task_id=self.next_task_id,
                task_type='TRANSPORT',
                priority=priority,
                source=source,
                destination=destination,
                material_type=material_type
            )
            self.next_task_id += 1
            
            # 加入优先级队列
            heapq.heappush(self.task_queue, (task.priority, task))
            rospy.loginfo(f"接收任务{task.task_id}: 优先级{priority}, {material_type}")
            
        except Exception as e:
            rospy.logerr(f"任务请求解析失败: {e}")
    
    def robot_status_callback(self, msg, robot_id):
        """更新机器人状态"""
        # 解析状态 "status:carrying_count:completed_tasks"
        try:
            parts = msg.data.split(':')
            if len(parts) >= 1:
                self.robot_states[robot_id]['status'] = parts[0]
        except Exception as e:
            rospy.logdebug(f"机器人{robot_id}状态解析失败: {e}")
    
    def assign_tasks_callback(self, event):
        """定期尝试分配任务"""
        if not self.task_queue:
            return
        
        # 找到空闲的机器人
        idle_robots = [
            robot_id for robot_id, state in self.robot_states.items()
            if state['status'] == 'idle'
        ]
        
        if not idle_robots:
            return
        
        # 分配任务给空闲机器人
        assigned_count = 0
        while self.task_queue and idle_robots:
            # 取出优先级最高的任务
            _, task = heapq.heappop(self.task_queue)
            
            # 选择最近的机器人
            robot_id = self.find_nearest_robot(idle_robots, task.source)
            
            # 发布任务
            task_msg = String()
            task_msg.data = (f"TRANSPORT:{task.source[0]},{task.source[1]}:"
                           f"{task.destination[0]},{task.destination[1]}:"
                           f"{task.material_type}")
            
            self.robot_task_pubs[robot_id].publish(task_msg)
            
            # 更新状态
            task.status = 'assigned'
            task.assigned_robot = robot_id
            self.active_tasks[task.task_id] = task
            self.robot_states[robot_id]['status'] = 'assigned'
            idle_robots.remove(robot_id)
            
            assigned_count += 1
            rospy.loginfo(f"分配任务{task.task_id}给机器人{robot_id}")
        
        if assigned_count > 0:
            rospy.loginfo(f"本轮分配了{assigned_count}个任务")
    
    def find_nearest_robot(self, robot_ids, target_position):
        """找到距离目标最近的机器人"""
        min_dist = float('inf')
        nearest_robot = robot_ids[0]
        
        for robot_id in robot_ids:
            pos = self.robot_states[robot_id]['position']
            dist = ((pos[0] - target_position[0])**2 + 
                   (pos[1] - target_position[1])**2)**0.5
            
            if dist < min_dist:
                min_dist = dist
                nearest_robot = robot_id
        
        return nearest_robot
    
    def print_statistics(self, event):
        """输出统计信息"""
        idle_count = sum(1 for s in self.robot_states.values() if s['status'] == 'idle')
        rospy.loginfo(f"📊 任务统计: 队列={len(self.task_queue)}, "
                     f"活跃={len(self.active_tasks)}, "
                     f"已完成={len(self.completed_tasks)}, "
                     f"空闲机器人={idle_count}/{self.num_robots}")

if __name__ == '__main__':
    try:
        scheduler = TaskScheduler()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("任务调度节点关闭")
