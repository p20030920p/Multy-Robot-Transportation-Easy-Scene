;; Auto-generated. Do not edit!


(when (boundp 'smart_factory_sim::TaskStatus)
  (if (not (find-package "SMART_FACTORY_SIM"))
    (make-package "SMART_FACTORY_SIM"))
  (shadow 'TaskStatus (find-package "SMART_FACTORY_SIM")))
(unless (find-package "SMART_FACTORY_SIM::TASKSTATUS")
  (make-package "SMART_FACTORY_SIM::TASKSTATUS"))

(in-package "ROS")
;;//! \htmlinclude TaskStatus.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))


(defclass smart_factory_sim::TaskStatus
  :super ros::object
  :slots (_task_id _task_type _priority _source _destination _material_type _status _assigned_robot_id ))

(defmethod smart_factory_sim::TaskStatus
  (:init
   (&key
    ((:task_id __task_id) 0)
    ((:task_type __task_type) "")
    ((:priority __priority) 0)
    ((:source __source) (instance geometry_msgs::Point :init))
    ((:destination __destination) (instance geometry_msgs::Point :init))
    ((:material_type __material_type) "")
    ((:status __status) "")
    ((:assigned_robot_id __assigned_robot_id) 0)
    )
   (send-super :init)
   (setq _task_id (round __task_id))
   (setq _task_type (string __task_type))
   (setq _priority (round __priority))
   (setq _source __source)
   (setq _destination __destination)
   (setq _material_type (string __material_type))
   (setq _status (string __status))
   (setq _assigned_robot_id (round __assigned_robot_id))
   self)
  (:task_id
   (&optional __task_id)
   (if __task_id (setq _task_id __task_id)) _task_id)
  (:task_type
   (&optional __task_type)
   (if __task_type (setq _task_type __task_type)) _task_type)
  (:priority
   (&optional __priority)
   (if __priority (setq _priority __priority)) _priority)
  (:source
   (&rest __source)
   (if (keywordp (car __source))
       (send* _source __source)
     (progn
       (if __source (setq _source (car __source)))
       _source)))
  (:destination
   (&rest __destination)
   (if (keywordp (car __destination))
       (send* _destination __destination)
     (progn
       (if __destination (setq _destination (car __destination)))
       _destination)))
  (:material_type
   (&optional __material_type)
   (if __material_type (setq _material_type __material_type)) _material_type)
  (:status
   (&optional __status)
   (if __status (setq _status __status)) _status)
  (:assigned_robot_id
   (&optional __assigned_robot_id)
   (if __assigned_robot_id (setq _assigned_robot_id __assigned_robot_id)) _assigned_robot_id)
  (:serialization-length
   ()
   (+
    ;; int32 _task_id
    4
    ;; string _task_type
    4 (length _task_type)
    ;; int32 _priority
    4
    ;; geometry_msgs/Point _source
    (send _source :serialization-length)
    ;; geometry_msgs/Point _destination
    (send _destination :serialization-length)
    ;; string _material_type
    4 (length _material_type)
    ;; string _status
    4 (length _status)
    ;; int32 _assigned_robot_id
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _task_id
       (write-long _task_id s)
     ;; string _task_type
       (write-long (length _task_type) s) (princ _task_type s)
     ;; int32 _priority
       (write-long _priority s)
     ;; geometry_msgs/Point _source
       (send _source :serialize s)
     ;; geometry_msgs/Point _destination
       (send _destination :serialize s)
     ;; string _material_type
       (write-long (length _material_type) s) (princ _material_type s)
     ;; string _status
       (write-long (length _status) s) (princ _status s)
     ;; int32 _assigned_robot_id
       (write-long _assigned_robot_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _task_id
     (setq _task_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; string _task_type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _task_type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int32 _priority
     (setq _priority (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; geometry_msgs/Point _source
     (send _source :deserialize buf ptr-) (incf ptr- (send _source :serialization-length))
   ;; geometry_msgs/Point _destination
     (send _destination :deserialize buf ptr-) (incf ptr- (send _destination :serialization-length))
   ;; string _material_type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _material_type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _status
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _status (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int32 _assigned_robot_id
     (setq _assigned_robot_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get smart_factory_sim::TaskStatus :md5sum-) "b60bd2ab3a7887e34ec8035f0abf6774")
(setf (get smart_factory_sim::TaskStatus :datatype-) "smart_factory_sim/TaskStatus")
(setf (get smart_factory_sim::TaskStatus :definition-)
      "# 任务状态消息
int32 task_id
string task_type  # TRANSPORT, PROCESS
int32 priority
geometry_msgs/Point source
geometry_msgs/Point destination
string material_type
string status  # pending, assigned, in_progress, completed, failed
int32 assigned_robot_id

================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

")



(provide :smart_factory_sim/TaskStatus "b60bd2ab3a7887e34ec8035f0abf6774")


