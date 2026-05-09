;; Auto-generated. Do not edit!


(when (boundp 'smart_factory_sim::ProcessMaterial)
  (if (not (find-package "SMART_FACTORY_SIM"))
    (make-package "SMART_FACTORY_SIM"))
  (shadow 'ProcessMaterial (find-package "SMART_FACTORY_SIM")))
(unless (find-package "SMART_FACTORY_SIM::PROCESSMATERIAL")
  (make-package "SMART_FACTORY_SIM::PROCESSMATERIAL"))
(unless (find-package "SMART_FACTORY_SIM::PROCESSMATERIALREQUEST")
  (make-package "SMART_FACTORY_SIM::PROCESSMATERIALREQUEST"))
(unless (find-package "SMART_FACTORY_SIM::PROCESSMATERIALRESPONSE")
  (make-package "SMART_FACTORY_SIM::PROCESSMATERIALRESPONSE"))

(in-package "ROS")





(defclass smart_factory_sim::ProcessMaterialRequest
  :super ros::object
  :slots (_machine_id _material_ids ))

(defmethod smart_factory_sim::ProcessMaterialRequest
  (:init
   (&key
    ((:machine_id __machine_id) 0)
    ((:material_ids __material_ids) (make-array 0 :initial-element 0 :element-type :integer))
    )
   (send-super :init)
   (setq _machine_id (round __machine_id))
   (setq _material_ids __material_ids)
   self)
  (:machine_id
   (&optional __machine_id)
   (if __machine_id (setq _machine_id __machine_id)) _machine_id)
  (:material_ids
   (&optional __material_ids)
   (if __material_ids (setq _material_ids __material_ids)) _material_ids)
  (:serialization-length
   ()
   (+
    ;; int32 _machine_id
    4
    ;; int32[] _material_ids
    (* 4    (length _material_ids)) 4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _machine_id
       (write-long _machine_id s)
     ;; int32[] _material_ids
     (write-long (length _material_ids) s)
     (dotimes (i (length _material_ids))
       (write-long (elt _material_ids i) s)
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _machine_id
     (setq _machine_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int32[] _material_ids
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _material_ids (instantiate integer-vector n))
     (dotimes (i n)
     (setf (elt _material_ids i) (sys::peek buf ptr- :integer)) (incf ptr- 4)
     ))
   ;;
   self)
  )

(defclass smart_factory_sim::ProcessMaterialResponse
  :super ros::object
  :slots (_success _message _processed_count ))

(defmethod smart_factory_sim::ProcessMaterialResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:message __message) "")
    ((:processed_count __processed_count) 0)
    )
   (send-super :init)
   (setq _success __success)
   (setq _message (string __message))
   (setq _processed_count (round __processed_count))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:message
   (&optional __message)
   (if __message (setq _message __message)) _message)
  (:processed_count
   (&optional __processed_count)
   (if __processed_count (setq _processed_count __processed_count)) _processed_count)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _message
    4 (length _message)
    ;; int32 _processed_count
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _message
       (write-long (length _message) s) (princ _message s)
     ;; int32 _processed_count
       (write-long _processed_count s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int32 _processed_count
     (setq _processed_count (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(defclass smart_factory_sim::ProcessMaterial
  :super ros::object
  :slots ())

(setf (get smart_factory_sim::ProcessMaterial :md5sum-) "4208032b26373306627bcd16215de808")
(setf (get smart_factory_sim::ProcessMaterial :datatype-) "smart_factory_sim/ProcessMaterial")
(setf (get smart_factory_sim::ProcessMaterial :request) smart_factory_sim::ProcessMaterialRequest)
(setf (get smart_factory_sim::ProcessMaterial :response) smart_factory_sim::ProcessMaterialResponse)

(defmethod smart_factory_sim::ProcessMaterialRequest
  (:response () (instance smart_factory_sim::ProcessMaterialResponse :init)))

(setf (get smart_factory_sim::ProcessMaterialRequest :md5sum-) "4208032b26373306627bcd16215de808")
(setf (get smart_factory_sim::ProcessMaterialRequest :datatype-) "smart_factory_sim/ProcessMaterialRequest")
(setf (get smart_factory_sim::ProcessMaterialRequest :definition-)
      "# 物料处理服务请求
int32 machine_id
int32[] material_ids
---
# 物料处理服务响应
bool success
string message
int32 processed_count

")

(setf (get smart_factory_sim::ProcessMaterialResponse :md5sum-) "4208032b26373306627bcd16215de808")
(setf (get smart_factory_sim::ProcessMaterialResponse :datatype-) "smart_factory_sim/ProcessMaterialResponse")
(setf (get smart_factory_sim::ProcessMaterialResponse :definition-)
      "# 物料处理服务请求
int32 machine_id
int32[] material_ids
---
# 物料处理服务响应
bool success
string message
int32 processed_count

")



(provide :smart_factory_sim/ProcessMaterial "4208032b26373306627bcd16215de808")


