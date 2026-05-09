#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@brief A* 路径规划算法（线程安全版本）

该模块实现了基于 A* 搜索的路径规划功能，包含路径平滑与动态障碍物规避。
支持8方向网格搜索，并通过线程锁保证多机器人并发规划时的数据一致性。

主要功能：
    - A* 全局路径搜索（8方向，带对角代价）
    - 路径平滑（基于可视性的线段简化）
    - 动态障碍物（其他机器人）实时规避
    - 起点不合法时的最近合法点搜索
"""

import math
import heapq
from collections import defaultdict
import threading


# ============================================================
#  Node - A* 搜索节点
# ============================================================

class Node:
    """
    @brief A* 搜索中的网格节点

    使用 __slots__ 优化内存占用，每个节点保存网格坐标、
    代价值（g/h/f）和父节点指针用于路径回溯。
    """
    __slots__ = ('x', 'y', 'g', 'h', 'f', 'parent')

    def __init__(self, x, y, g=0, h=0, parent=None):
        """
        @brief 初始化搜索节点

        @param x:      网格 X 坐标
        @param y:      网格 Y 坐标
        @param g:      从起点到当前节点的实际代价
        @param h:      从当前节点到目标的启发式估计代价
        @param parent: 父节点引用，用于回溯路径
        """
        self.x = x
        self.y = y
        self.g = g
        self.h = h
        self.f = g + h          # 总代价 f = g + h
        self.parent = parent

    def __lt__(self, other):
        """优先队列比较：f 值小的优先"""
        return self.f < other.f

    def __eq__(self, other):
        """节点相等判定：仅比较网格坐标"""
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """哈希值：基于坐标元组，用于 closed_set 去重"""
        return hash((self.x, self.y))


# ============================================================
#  AStarPlanner - A* 路径规划器
# ============================================================

class AStarPlanner:
    """
    @brief A* 路径规划器

    基于栅格地图的 A* 路径搜索器，支持静态障碍物和动态障碍物
    （其他机器人位置）的实时规避。内部使用线程锁保证多线程安全。
    """

    def __init__(self, grid_size=0.1, robot_radius=0.0625):
        """
        @brief 初始化路径规划器

        @param grid_size:    栅格分辨率（米），默认 0.1m
        @param robot_radius: 机器人碰撞半径（米），默认 0.0625m
        """
        self.grid_size = grid_size          # 栅格分辨率
        self.robot_radius = robot_radius    # 碰撞半径
        self.map_width = 16.0               # 地图宽度（米）
        self.map_height = 10.0              # 地图高度（米）

        self.obstacles = []                 # 静态障碍物列表 [(x, y, radius), ...]
        self.dynamic_obstacles = {}         # 动态障碍物（其他机器人） {id: (x, y)}
        self.lock = threading.Lock()        # 线程锁，保护动态障碍物数据

        # 8方向移动向量：上下左右 + 四个对角方向
        self.directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),      # 直线方向
            (1, 1), (1, -1), (-1, -1), (-1, 1)      # 对角方向
        ]
        # 对应移动代价：直线 1.0，对角 √2 ≈ 1.414
        self.direction_costs = [1.0, 1.0, 1.0, 1.0, 1.414, 1.414, 1.414, 1.414]

        print(f"✅ A* Planner Init: Grid={grid_size}m, Radius={robot_radius}m, "
              f"Map={self.map_width}x{self.map_height}m")

    def set_obstacles(self, obstacles):
        """
        @brief 设置静态障碍物列表

        @param obstacles: 障碍物列表，每项为 (x, y, radius)
        """
        self.obstacles = obstacles

    def update_dynamic_obstacles(self, robot_positions):
        """
        @brief 更新动态障碍物（其他机器人位置）

        线程安全地替换当前动态障碍物字典。

        @param robot_positions: 机器人位置字典 {robot_id: (x, y)}
        """
        with self.lock:
            self.dynamic_obstacles = robot_positions.copy()

    # ============================================================
    #  核心工具方法
    # ============================================================

    def heuristic(self, node, goal):
        """
        @brief 计算启发式估计代价（欧氏距离）

        @param node: 当前节点
        @param goal: 目标节点
        @return: 两节点间的欧氏距离
        """
        return math.hypot(node.x - goal.x, node.y - goal.y)

    def is_valid(self, x, y, ignore_robot_id=None):
        """
        @brief 检查世界坐标点是否合法（可通行）

        依次进行三层检查：
        1. 地图边界检查（含安全边距 0.1m）
        2. 静态障碍物碰撞检查
        3. 动态障碍物（其他机器人）安全距离检查

        @param x:               世界坐标 X（米）
        @param y:               世界坐标 Y（米）
        @param ignore_robot_id: 需要忽略的机器人 ID（规划时忽略自身）
        @return: True 表示可通行，False 表示被阻挡
        """
        # 第一层：边界检查（0.1m 安全边距）
        margin = 0.1
        if x < margin or x > self.map_width - margin or y < margin or y > self.map_height - margin:
            return False

        # 第二层：静态障碍物碰撞检查
        for ox, oy, orad in self.obstacles:
            if math.hypot(x - ox, y - oy) < (orad + self.robot_radius):
                return False

        # 第三层：动态障碍物（其他机器人）安全距离检查
        with self.lock:
            dyn_obs = dict(self.dynamic_obstacles)

        safe_dist = self.robot_radius * 8   # 膨胀 8 倍作为安全距离
        for rid, (rx, ry) in dyn_obs.items():
            if rid == ignore_robot_id:
                continue
            if math.hypot(x - rx, y - ry) < safe_dist:
                return False

        return True

    # ============================================================
    #  坐标转换
    # ============================================================

    def world_to_grid(self, x, y):
        """
        @brief 世界坐标 → 栅格坐标

        @param x: 世界坐标 X（米）
        @param y: 世界坐标 Y（米）
        @return: (gx, gy) 栅格坐标元组
        """
        return int(x / self.grid_size), int(y / self.grid_size)

    def grid_to_world(self, gx, gy):
        """
        @brief 栅格坐标 → 世界坐标

        @param gx: 栅格 X 坐标
        @param gy: 栅格 Y 坐标
        @return: (wx, wy) 世界坐标元组（米）
        """
        return gx * self.grid_size, gy * self.grid_size

    # ============================================================
    #  A* 核心搜索
    # ============================================================

    def plan_path(self, start, goal, robot_id=0, priority=50):
        """
        @brief A* 路径搜索主函数

        从起点到终点执行 A* 搜索，返回世界坐标路径点列表。
        若起点不合法，自动搜索最近合法点。搜索上限 3000 次迭代。
        到达目标允许 2 格容差。若搜索失败，返回起终点直线。

        @param start:    起点世界坐标 (x, y)
        @param goal:     终点世界坐标 (x, y)
        @param robot_id: 当前机器人 ID，用于忽略自身的动态障碍物
        @param priority: 任务优先级（预留，暂未使用）
        @return: 路径点列表 [(x1, y1), (x2, y2), ...]
        """
        # 起点不合法时，搜索最近合法点
        if not self.is_valid(start[0], start[1], robot_id):
            start = self.find_nearest_valid_point(start, robot_id)

        # 坐标转换：世界坐标 → 栅格坐标
        sg = self.world_to_grid(*start)
        gg = self.world_to_grid(*goal)

        start_node = Node(sg[0], sg[1])
        goal_node = Node(gg[0], gg[1])

        # 初始化 open_list（优先队列）和 closed_set
        open_list = []
        heapq.heappush(open_list, start_node)
        closed_set = set()

        # g 值记录表，默认无穷大
        g_scores = defaultdict(lambda: float('inf'))
        g_scores[start_node] = 0

        iters = 0
        max_iters = 3000    # 最大迭代次数，防止无限循环

        while open_list and iters < max_iters:
            iters += 1
            curr = heapq.heappop(open_list)

            # 到达目标附近（2 格容差）
            if abs(curr.x - goal_node.x) <= 2 and abs(curr.y - goal_node.y) <= 2:
                path = self.reconstruct_path(curr)
                w_path = [self.grid_to_world(x, y) for x, y in path]
                w_path.append(goal)    # 追加精确目标点
                return w_path

            closed_set.add(curr)

            # 展开 8 个邻居节点
            for i, (dx, dy) in enumerate(self.directions):
                nx, ny = curr.x + dx, curr.y + dy
                wx, wy = self.grid_to_world(nx, ny)

                if not self.is_valid(wx, wy, robot_id):
                    continue

                neighbor = Node(nx, ny)
                if neighbor in closed_set:
                    continue

                tentative_g = curr.g + self.direction_costs[i]
                if tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    neighbor.g = tentative_g
                    neighbor.h = self.heuristic(neighbor, goal_node)
                    neighbor.f = neighbor.g + neighbor.h
                    neighbor.parent = curr
                    heapq.heappush(open_list, neighbor)

        # 搜索失败：返回空路径，由上层调度器决定安全回退策略
        return []

    def reconstruct_path(self, node):
        """
        @brief 从目标节点回溯重建路径

        沿 parent 指针从目标回溯到起点，然后翻转得到正序路径。

        @param node: 目标节点（搜索到达的节点）
        @return: 栅格坐标路径列表 [(gx1, gy1), ...]
        """
        path = []
        while node:
            path.append((node.x, node.y))
            node = node.parent
        return path[::-1]               # 翻转：起点 → 终点

    def find_nearest_valid_point(self, point, robot_id):
        """
        @brief 搜索距离指定点最近的合法位置

        以 0.1m 步长向外扩圈搜索，最远搜索 0.5m。
        每圈均匀采样 32 个方向。

        @param point:    原始坐标 (x, y)
        @param robot_id: 当前机器人 ID，用于忽略自身
        @return: 最近合法点 (x, y)，若全部不合法则返回原点
        """
        step = 0.1
        for r in [step * i for i in range(1, 6)]:      # 搜索半径 0.1m ~ 0.5m
            for ang in [i * math.pi / 16 for i in range(32)]:   # 32 个方向均匀采样
                nx = point[0] + r * math.cos(ang)
                ny = point[1] + r * math.sin(ang)
                if self.is_valid(nx, ny, robot_id):
                    return (nx, ny)
        return point                    # 全部不合法时返回原点（保底）

    # ============================================================
    #  路径平滑
    # ============================================================

    def smooth_path(self, path):
        """
        @brief 路径平滑：基于可视性的线段简化

        从路径起点开始，尽可能跳过中间点直接连接远端可视点，
        以减少不必要的折线，使路径更平滑高效。

        @param path: 原始路径点列表 [(x1, y1), ...]
        @return: 平滑后的路径点列表
        """
        if len(path) <= 2:
            return path

        smoothed = [path[0]]
        i = 0
        while i < len(path) - 1:
            # 从最远点开始尝试，找到第一个可视的远端点
            for j in range(len(path) - 1, i, -1):
                if self.is_line_clear(path[i], path[j]):
                    smoothed.append(path[j])
                    i = j
                    break
            else:
                # 无可视远端点，逐步前进
                i += 1
                if i < len(path):
                    smoothed.append(path[i])
        return smoothed

    def is_line_clear(self, p1, p2):
        """
        @brief 检查两点间直线是否无障碍

        沿 p1→p2 的直线等间距采样，逐点检查合法性。
        采样间距等于栅格分辨率。

        @param p1: 起点 (x, y)
        @param p2: 终点 (x, y)
        @return: True 表示通畅，False 表示被阻挡
        """
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        steps = int(dist / self.grid_size) + 1
        for i in range(steps + 1):
            t = i / max(steps, 1)
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            if not self.is_valid(x, y):
                return False
        return True


# ============================================================
#  测试入口
# ============================================================

if __name__ == '__main__':
    print(">>> Testing A* Planner...")
    planner = AStarPlanner()

    # 测试基础路径规划
    p = planner.plan_path((0.5, 0.5), (9.0, 7.5))
    print(f"Path found: {len(p)} points")

    # 测试路径平滑
    s_p = planner.smooth_path(p)
    print(f"Smoothed: {len(s_p)} points")