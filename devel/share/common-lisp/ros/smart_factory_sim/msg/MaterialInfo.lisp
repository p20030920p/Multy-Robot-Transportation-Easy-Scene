; Auto-generated. Do not edit!


(cl:in-package smart_factory_sim-msg)


;//! \htmlinclude MaterialInfo.msg.html

(cl:defclass <MaterialInfo> (roslisp-msg-protocol:ros-message)
  ((id
    :reader id
    :initarg :id
    :type cl:integer
    :initform 0)
   (type
    :reader type
    :initarg :type
    :type cl:string
    :initform "")
   (position
    :reader position
    :initarg :position
    :type geometry_msgs-msg:Point
    :initform (cl:make-instance 'geometry_msgs-msg:Point))
   (location
    :reader location
    :initarg :location
    :type cl:string
    :initform "")
   (batch_id
    :reader batch_id
    :initarg :batch_id
    :type cl:integer
    :initform 0))
)

(cl:defclass MaterialInfo (<MaterialInfo>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <MaterialInfo>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'MaterialInfo)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name smart_factory_sim-msg:<MaterialInfo> is deprecated: use smart_factory_sim-msg:MaterialInfo instead.")))

(cl:ensure-generic-function 'id-val :lambda-list '(m))
(cl:defmethod id-val ((m <MaterialInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:id-val is deprecated.  Use smart_factory_sim-msg:id instead.")
  (id m))

(cl:ensure-generic-function 'type-val :lambda-list '(m))
(cl:defmethod type-val ((m <MaterialInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:type-val is deprecated.  Use smart_factory_sim-msg:type instead.")
  (type m))

(cl:ensure-generic-function 'position-val :lambda-list '(m))
(cl:defmethod position-val ((m <MaterialInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:position-val is deprecated.  Use smart_factory_sim-msg:position instead.")
  (position m))

(cl:ensure-generic-function 'location-val :lambda-list '(m))
(cl:defmethod location-val ((m <MaterialInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:location-val is deprecated.  Use smart_factory_sim-msg:location instead.")
  (location m))

(cl:ensure-generic-function 'batch_id-val :lambda-list '(m))
(cl:defmethod batch_id-val ((m <MaterialInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-msg:batch_id-val is deprecated.  Use smart_factory_sim-msg:batch_id instead.")
  (batch_id m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <MaterialInfo>) ostream)
  "Serializes a message object of type '<MaterialInfo>"
  (cl:let* ((signed (cl:slot-value msg 'id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'type))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'type))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'position) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'location))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'location))
  (cl:let* ((signed (cl:slot-value msg 'batch_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <MaterialInfo>) istream)
  "Deserializes a message object of type '<MaterialInfo>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'type) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'type) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'position) istream)
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'location) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'location) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'batch_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<MaterialInfo>)))
  "Returns string type for a message object of type '<MaterialInfo>"
  "smart_factory_sim/MaterialInfo")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'MaterialInfo)))
  "Returns string type for a message object of type 'MaterialInfo"
  "smart_factory_sim/MaterialInfo")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<MaterialInfo>)))
  "Returns md5sum for a message object of type '<MaterialInfo>"
  "7b98b1aedcf605a3fb21632bdda789d0")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'MaterialInfo)))
  "Returns md5sum for a message object of type 'MaterialInfo"
  "7b98b1aedcf605a3fb21632bdda789d0")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<MaterialInfo>)))
  "Returns full string definition for message of type '<MaterialInfo>"
  (cl:format cl:nil "# 物料信息消息~%int32 id~%string type  # empty, green, yellow, red~%geometry_msgs/Point position~%string location  # 物料所在位置~%int32 batch_id~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'MaterialInfo)))
  "Returns full string definition for message of type 'MaterialInfo"
  (cl:format cl:nil "# 物料信息消息~%int32 id~%string type  # empty, green, yellow, red~%geometry_msgs/Point position~%string location  # 物料所在位置~%int32 batch_id~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <MaterialInfo>))
  (cl:+ 0
     4
     4 (cl:length (cl:slot-value msg 'type))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'position))
     4 (cl:length (cl:slot-value msg 'location))
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <MaterialInfo>))
  "Converts a ROS message object to a list"
  (cl:list 'MaterialInfo
    (cl:cons ':id (id msg))
    (cl:cons ':type (type msg))
    (cl:cons ':position (position msg))
    (cl:cons ':location (location msg))
    (cl:cons ':batch_id (batch_id msg))
))
