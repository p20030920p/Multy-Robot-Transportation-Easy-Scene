# 任务状态消息
int32 task_id
string task_type  # TRANSPORT, PROCESS
int32 priority
geometry_msgs/Point source
geometry_msgs/Point destination
string material_type
string status  # pending, assigned, in_progress, completed, failed
int32 assigned_robot_id
