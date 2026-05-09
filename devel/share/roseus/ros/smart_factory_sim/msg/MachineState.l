;; Auto-generated. Do not edit!


(when (boundp 'smart_factory_sim::MachineState)
  (if (not (find-package "SMART_FACTORY_SIM"))
    (make-package "SMART_FACTORY_SIM"))
  (shadow 'MachineState (find-package "SMART_FACTORY_SIM")))
(unless (find-package "SMART_FACTORY_SIM::MACHINESTATE")
  (make-package "SMART_FACTORY_SIM::MACHINESTATE"))

(in-package "ROS")
;;//! \htmlinclude MachineState.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))


(defclass smart_factory_sim::MachineState
  :super ros::object
  :slots (_machine_id _machine_type _status _position _materials_count _efficiency ))

(defmethod smart_factory_sim::MachineState
  (:init
   (&key
    ((:machine_id __machine_id) 0)
    ((:machine_type __machine_type) "")
    ((:status __status) "")
    ((:position __position) (instance geometry_msgs::Point :init))
    ((:materials_count __materials_count) 0)
    ((:efficiency __efficiency) 0.0)
    )
   (send-super :init)
   (setq _machine_id (round __machine_id))
   (setq _machine_type (string __machine_type))
   (setq _status (string __status))
   (setq _position __position)
   (setq _materials_count (round __materials_count))
   (setq _efficiency (float __efficiency))
   self)
  (:machine_id
   (&optional __machine_id)
   (if __machine_id (setq _machine_id __machine_id)) _machine_id)
  (:machine_type
   (&optional __machine_type)
   (if __machine_type (setq _machine_type __machine_type)) _machine_type)
  (:status
   (&optional __status)
   (if __status (setq _status __status)) _status)
  (:position
   (&rest __position)
   (if (keywordp (car __position))
       (send* _position __position)
     (progn
       (if __position (setq _position (car __position)))
       _position)))
  (:materials_count
   (&optional __materials_count)
   (if __materials_count (setq _materials_count __materials_count)) _materials_count)
  (:efficiency
   (&optional __efficiency)
   (if __efficiency (setq _efficiency __efficiency)) _efficiency)
  (:serialization-length
   ()
   (+
    ;; int32 _machine_id
    4
    ;; string _machine_type
    4 (length _machine_type)
    ;; string _status
    4 (length _status)
    ;; geometry_msgs/Point _position
    (send _position :serialization-length)
    ;; int32 _materials_count
    4
    ;; float32 _efficiency
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _machine_id
       (write-long _machine_id s)
     ;; string _machine_type
       (write-long (length _machine_type) s) (princ _machine_type s)
     ;; string _status
       (write-long (length _status) s) (princ _status s)
     ;; geometry_msgs/Point _position
       (send _position :serialize s)
     ;; int32 _materials_count
       (write-long _materials_count s)
     ;; float32 _efficiency
       (sys::poke _efficiency (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _machine_id
     (setq _machine_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; string _machine_type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _machine_type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _status
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _status (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; geometry_msgs/Point _position
     (send _position :deserialize buf ptr-) (incf ptr- (send _position :serialization-length))
   ;; int32 _materials_count
     (setq _materials_count (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; float32 _efficiency
     (setq _efficiency (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get smart_factory_sim::MachineState :md5sum-) "83c455b2e59b8c116d67ec85f20c9dc2")
(setf (get smart_factory_sim::MachineState :datatype-) "smart_factory_sim/MachineState")
(setf (get smart_factory_sim::MachineState :definition-)
      "# 机器状态消息
int32 machine_id
string machine_type  # carding, drawing1, drawing2, roving
string status  # idle, processing, waiting, blocked
geometry_msgs/Point position
int32 materials_count
float32 efficiency

================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

")



(provide :smart_factory_sim/MachineState "83c455b2e59b8c116d67ec85f20c9dc2")


