; Auto-generated. Do not edit!


(cl:in-package smart_factory_sim-msg)


;//! \htmlinclude MachineState.msg.html

(cl:defclass <MachineState> (roslisp-msg-protocol:ros-message)
  ((machine_id
    :reader machine_id
    :initarg :machine_id
    :type cl:integer
    :initform 0)
   (machine_type
    :reader machine_type
    :initarg :machine_type
    :type cl:string
    :initform "")
   (status
    :reader status
    :initarg :status
    :type cl:string
    :initform "")
   (position
    :reader position
    :initarg :position
    :type geometry_msgs-msg:Point
    :initform (cl:make-instance 'geometry_msgs-msg:Point))
   (materials_count
    :reader materials_count
    :initarg :materials_count
    :type cl:integer
    :initform 0)
   (efficiency
    :reader efficiency
    :initarg :efficiency
    :type cl:float
    :initform 0.0))
)

(cl:defclass MachineState (<MachineState>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <MachineState>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'MachineState)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name smart_factory_sim-msg:<MachineState> is deprecated: use smart_factory_sim-msg:MachineState instead.")))

(cl:ensure-generic-function 'machine_id-val :lambda-list '(m))
(cl:defmethod machine_id-val ((m <MachineState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:machine_id-val is deprecated.  Use smart_factory_sim-msg:machine_id instead.")
  (machine_id m))

(cl:ensure-generic-function 'machine_type-val :lambda-list '(m))
(cl:defmethod machine_type-val ((m <MachineState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:machine_type-val is deprecated.  Use smart_factory_sim-msg:machine_type instead.")
  (machine_type m))

(cl:ensure-generic-function 'status-val :lambda-list '(m))
(cl:defmethod status-val ((m <MachineState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:status-val is deprecated.  Use smart_factory_sim-msg:status instead.")
  (status m))

(cl:ensure-generic-function 'position-val :lambda-list '(m))
(cl:defmethod position-val ((m <MachineState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:position-val is deprecated.  Use smart_factory_sim-msg:position instead.")
  (position m))

(cl:ensure-generic-function 'materials_count-val :lambda-list '(m))
(cl:defmethod materials_count-val ((m <MachineState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:materials_count-val is deprecated.  Use smart_factory_sim-msg:materials_count instead.")
  (materials_count m))

(cl:ensure-generic-function 'efficiency-val :lambda-list '(m))
(cl:defmethod efficiency-val ((m <MachineState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:efficiency-val is deprecated.  Use smart_factory_sim-msg:efficiency instead.")
  (efficiency m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <MachineState>) ostream)
  "Serializes a message object of type '<MachineState>"
  (cl:let* ((signed (cl:slot-value msg 'machine_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'machine_type))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'machine_type))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'status))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'status))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'position) ostream)
  (cl:let* ((signed (cl:slot-value msg 'materials_count)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'efficiency))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <MachineState>) istream)
  "Deserializes a message object of type '<MachineState>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'machine_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'machine_type) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'machine_type) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'status) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'status) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'position) istream)
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'materials_count) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'efficiency) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<MachineState>)))
  "Returns string type for a message object of type '<MachineState>"
  "smart_factory_sim/MachineState")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'MachineState)))
  "Returns string type for a message object of type 'MachineState"
  "smart_factory_sim/MachineState")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<MachineState>)))
  "Returns md5sum for a message object of type '<MachineState>"
  "83c455b2e59b8c116d67ec85f20c9dc2")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'MachineState)))
  "Returns md5sum for a message object of type 'MachineState"
  "83c455b2e59b8c116d67ec85f20c9dc2")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<MachineState>)))
  "Returns full string definition for message of type '<MachineState>"
  (cl:format cl:nil "# 机器状态消息~%int32 machine_id~%string machine_type  # carding, drawing1, drawing2, roving~%string status  # idle, processing, waiting, blocked~%geometry_msgs/Point position~%int32 materials_count~%float32 efficiency~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'MachineState)))
  "Returns full string definition for message of type 'MachineState"
  (cl:format cl:nil "# 机器状态消息~%int32 machine_id~%string machine_type  # carding, drawing1, drawing2, roving~%string status  # idle, processing, waiting, blocked~%geometry_msgs/Point position~%int32 materials_count~%float32 efficiency~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <MachineState>))
  (cl:+ 0
     4
     4 (cl:length (cl:slot-value msg 'machine_type))
     4 (cl:length (cl:slot-value msg 'status))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'position))
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <MachineState>))
  "Converts a ROS message object to a list"
  (cl:list 'MachineState
    (cl:cons ':machine_id (machine_id msg))
    (cl:cons ':machine_type (machine_type msg))
    (cl:cons ':status (status msg))
    (cl:cons ':position (position msg))
    (cl:cons ':materials_count (materials_count msg))
    (cl:cons ':efficiency (efficiency msg))
))
