# 机器状态消息
int32 machine_id
string machine_type  # carding, drawing1, drawing2, roving
string status  # idle, processing, waiting, blocked
geometry_msgs/Point position
int32 materials_count
float32 efficiency
