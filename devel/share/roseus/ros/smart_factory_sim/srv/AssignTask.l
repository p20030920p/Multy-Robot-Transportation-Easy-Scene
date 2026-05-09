;; Auto-generated. Do not edit!


(when (boundp 'smart_factory_sim::AssignTask)
  (if (not (find-package "SMART_FACTORY_SIM"))
    (make-package "SMART_FACTORY_SIM"))
  (shadow 'AssignTask (find-package "SMART_FACTORY_SIM")))
(unless (find-package "SMART_FACTORY_SIM::ASSIGNTASK")
  (make-package "SMART_FACTORY_SIM::ASSIGNTASK"))
(unless (find-package "SMART_FACTORY_SIM::ASSIGNTASKREQUEST")
  (make-package "SMART_FACTORY_SIM::ASSIGNTASKREQUEST"))
(unless (find-package "SMART_FACTORY_SIM::ASSIGNTASKRESPONSE")
  (make-package "SMART_FACTORY_SIM::ASSIGNTASKRESPONSE"))

(in-package "ROS")





(defclass smart_factory_sim::AssignTaskRequest
  :super ros::object
  :slots (_task_id _robot_id ))

(defmethod smart_factory_sim::AssignTaskRequest
  (:init
   (&key
    ((:task_id __task_id) 0)
    ((:robot_id __robot_id) 0)
    )
   (send-super :init)
   (setq _task_id (round __task_id))
   (setq _robot_id (round __robot_id))
   self)
  (:task_id
   (&optional __task_id)
   (if __task_id (setq _task_id __task_id)) _task_id)
  (:robot_id
   (&optional __robot_id)
   (if __robot_id (setq _robot_id __robot_id)) _robot_id)
  (:serialization-length
   ()
   (+
    ;; int32 _task_id
    4
    ;; int32 _robot_id
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _task_id
       (write-long _task_id s)
     ;; int32 _robot_id
       (write-long _robot_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _task_id
     (setq _task_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int32 _robot_id
     (setq _robot_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(defclass smart_factory_sim::AssignTaskResponse
  :super ros::object
  :slots (_success _message ))

(defmethod smart_factory_sim::AssignTaskResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:message __message) "")
    )
   (send-super :init)
   (setq _success __success)
   (setq _message (string __message))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:message
   (&optional __message)
   (if __message (setq _message __message)) _message)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _message
    4 (length _message)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _message
       (write-long (length _message) s) (princ _message s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass smart_factory_sim::AssignTask
  :super ros::object
  :slots ())

(setf (get smart_factory_sim::AssignTask :md5sum-) "3450a2182eb013df5d30a3ff5215b470")
(setf (get smart_factory_sim::AssignTask :datatype-) "smart_factory_sim/AssignTask")
(setf (get smart_factory_sim::AssignTask :request) smart_factory_sim::AssignTaskRequest)
(setf (get smart_factory_sim::AssignTask :response) smart_factory_sim::AssignTaskResponse)

(defmethod smart_factory_sim::AssignTaskRequest
  (:response () (instance smart_factory_sim::AssignTaskResponse :init)))

(setf (get smart_factory_sim::AssignTaskRequest :md5sum-) "3450a2182eb013df5d30a3ff5215b470")
(setf (get smart_factory_sim::AssignTaskRequest :datatype-) "smart_factory_sim/AssignTaskRequest")
(setf (get smart_factory_sim::AssignTaskRequest :definition-)
      "# 任务分配服务请求
int32 task_id
int32 robot_id
---
# 任务分配服务响应
bool success
string message

")

(setf (get smart_factory_sim::AssignTaskResponse :md5sum-) "3450a2182eb013df5d30a3ff5215b470")
(setf (get smart_factory_sim::AssignTaskResponse :datatype-) "smart_factory_sim/AssignTaskResponse")
(setf (get smart_factory_sim::AssignTaskResponse :definition-)
      "# 任务分配服务请求
int32 task_id
int32 robot_id
---
# 任务分配服务响应
bool success
string message

")



(provide :smart_factory_sim/AssignTask "3450a2182eb013df5d30a3ff5215b470")


