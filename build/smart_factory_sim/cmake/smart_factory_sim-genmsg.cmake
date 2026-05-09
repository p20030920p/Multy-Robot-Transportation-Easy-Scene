# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "smart_factory_sim: 3 messages, 2 services")

set(MSG_I_FLAGS "-Ismart_factory_sim:/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg;-Iactionlib_msgs:/opt/ros/noetic/share/actionlib_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(smart_factory_sim_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" NAME_WE)
add_custom_target(_smart_factory_sim_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "smart_factory_sim" "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" NAME_WE)
add_custom_target(_smart_factory_sim_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "smart_factory_sim" "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" NAME_WE)
add_custom_target(_smart_factory_sim_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "smart_factory_sim" "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" NAME_WE)
add_custom_target(_smart_factory_sim_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "smart_factory_sim" "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" ""
)

get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" NAME_WE)
add_custom_target(_smart_factory_sim_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "smart_factory_sim" "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" ""
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_cpp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_cpp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
)

### Generating Services
_generate_srv_cpp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
)
_generate_srv_cpp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
)

### Generating Module File
_generate_module_cpp(smart_factory_sim
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(smart_factory_sim_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(smart_factory_sim_generate_messages smart_factory_sim_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_cpp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_cpp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_cpp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_cpp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_cpp _smart_factory_sim_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(smart_factory_sim_gencpp)
add_dependencies(smart_factory_sim_gencpp smart_factory_sim_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS smart_factory_sim_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_eus(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_eus(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
)

### Generating Services
_generate_srv_eus(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
)
_generate_srv_eus(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
)

### Generating Module File
_generate_module_eus(smart_factory_sim
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(smart_factory_sim_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(smart_factory_sim_generate_messages smart_factory_sim_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_eus _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_eus _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_eus _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_eus _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_eus _smart_factory_sim_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(smart_factory_sim_geneus)
add_dependencies(smart_factory_sim_geneus smart_factory_sim_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS smart_factory_sim_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_lisp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_lisp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
)

### Generating Services
_generate_srv_lisp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
)
_generate_srv_lisp(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
)

### Generating Module File
_generate_module_lisp(smart_factory_sim
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(smart_factory_sim_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(smart_factory_sim_generate_messages smart_factory_sim_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_lisp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_lisp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_lisp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_lisp _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_lisp _smart_factory_sim_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(smart_factory_sim_genlisp)
add_dependencies(smart_factory_sim_genlisp smart_factory_sim_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS smart_factory_sim_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_nodejs(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_nodejs(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
)

### Generating Services
_generate_srv_nodejs(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
)
_generate_srv_nodejs(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
)

### Generating Module File
_generate_module_nodejs(smart_factory_sim
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(smart_factory_sim_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(smart_factory_sim_generate_messages smart_factory_sim_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_nodejs _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_nodejs _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_nodejs _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_nodejs _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_nodejs _smart_factory_sim_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(smart_factory_sim_gennodejs)
add_dependencies(smart_factory_sim_gennodejs smart_factory_sim_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS smart_factory_sim_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_py(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
)
_generate_msg_py(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
)

### Generating Services
_generate_srv_py(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
)
_generate_srv_py(smart_factory_sim
  "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
)

### Generating Module File
_generate_module_py(smart_factory_sim
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(smart_factory_sim_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(smart_factory_sim_generate_messages smart_factory_sim_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MaterialInfo.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_py _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/TaskStatus.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_py _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/msg/MachineState.msg" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_py _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/AssignTask.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_py _smart_factory_sim_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/qzl/graduate/catkin_ws/src/smart_factory_sim/srv/ProcessMaterial.srv" NAME_WE)
add_dependencies(smart_factory_sim_generate_messages_py _smart_factory_sim_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(smart_factory_sim_genpy)
add_dependencies(smart_factory_sim_genpy smart_factory_sim_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS smart_factory_sim_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/smart_factory_sim
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(smart_factory_sim_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(smart_factory_sim_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()
if(TARGET actionlib_msgs_generate_messages_cpp)
  add_dependencies(smart_factory_sim_generate_messages_cpp actionlib_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/smart_factory_sim
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(smart_factory_sim_generate_messages_eus std_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(smart_factory_sim_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()
if(TARGET actionlib_msgs_generate_messages_eus)
  add_dependencies(smart_factory_sim_generate_messages_eus actionlib_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/smart_factory_sim
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(smart_factory_sim_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(smart_factory_sim_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()
if(TARGET actionlib_msgs_generate_messages_lisp)
  add_dependencies(smart_factory_sim_generate_messages_lisp actionlib_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/smart_factory_sim
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(smart_factory_sim_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(smart_factory_sim_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()
if(TARGET actionlib_msgs_generate_messages_nodejs)
  add_dependencies(smart_factory_sim_generate_messages_nodejs actionlib_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim)
  install(CODE "execute_process(COMMAND \"/usr/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/smart_factory_sim
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(smart_factory_sim_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(smart_factory_sim_generate_messages_py geometry_msgs_generate_messages_py)
endif()
if(TARGET actionlib_msgs_generate_messages_py)
  add_dependencies(smart_factory_sim_generate_messages_py actionlib_msgs_generate_messages_py)
endif()
