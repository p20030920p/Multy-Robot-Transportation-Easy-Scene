;; Auto-generated. Do not edit!


(when (boundp 'smart_factory_sim::MaterialInfo)
  (if (not (find-package "SMART_FACTORY_SIM"))
    (make-package "SMART_FACTORY_SIM"))
  (shadow 'MaterialInfo (find-package "SMART_FACTORY_SIM")))
(unless (find-package "SMART_FACTORY_SIM::MATERIALINFO")
  (make-package "SMART_FACTORY_SIM::MATERIALINFO"))

(in-package "ROS")
;;//! \htmlinclude MaterialInfo.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))


(defclass smart_factory_sim::MaterialInfo
  :super ros::object
  :slots (_id _type _position _location _batch_id ))

(defmethod smart_factory_sim::MaterialInfo
  (:init
   (&key
    ((:id __id) 0)
    ((:type __type) "")
    ((:position __position) (instance geometry_msgs::Point :init))
    ((:location __location) "")
    ((:batch_id __batch_id) 0)
    )
   (send-super :init)
   (setq _id (round __id))
   (setq _type (string __type))
   (setq _position __position)
   (setq _location (string __location))
   (setq _batch_id (round __batch_id))
   self)
  (:id
   (&optional __id)
   (if __id (setq _id __id)) _id)
  (:type
   (&optional __type)
   (if __type (setq _type __type)) _type)
  (:position
   (&rest __position)
   (if (keywordp (car __position))
       (send* _position __position)
     (progn
       (if __position (setq _position (car __position)))
       _position)))
  (:location
   (&optional __location)
   (if __location (setq _location __location)) _location)
  (:batch_id
   (&optional __batch_id)
   (if __batch_id (setq _batch_id __batch_id)) _batch_id)
  (:serialization-length
   ()
   (+
    ;; int32 _id
    4
    ;; string _type
    4 (length _type)
    ;; geometry_msgs/Point _position
    (send _position :serialization-length)
    ;; string _location
    4 (length _location)
    ;; int32 _batch_id
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _id
       (write-long _id s)
     ;; string _type
       (write-long (length _type) s) (princ _type s)
     ;; geometry_msgs/Point _position
       (send _position :serialize s)
     ;; string _location
       (write-long (length _location) s) (princ _location s)
     ;; int32 _batch_id
       (write-long _batch_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _id
     (setq _id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; string _type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; geometry_msgs/Point _position
     (send _position :deserialize buf ptr-) (incf ptr- (send _position :serialization-length))
   ;; string _location
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _location (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int32 _batch_id
     (setq _batch_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get smart_factory_sim::MaterialInfo :md5sum-) "7b98b1aedcf605a3fb21632bdda789d0")
(setf (get smart_factory_sim::MaterialInfo :datatype-) "smart_factory_sim/MaterialInfo")
(setf (get smart_factory_sim::MaterialInfo :definition-)
      "# 物料信息消息
int32 id
string type  # empty, green, yellow, red
geometry_msgs/Point position
string location  # 物料所在位置
int32 batch_id

================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

")



(provide :smart_factory_sim/MaterialInfo "7b98b1aedcf605a3fb21632bdda789d0")


