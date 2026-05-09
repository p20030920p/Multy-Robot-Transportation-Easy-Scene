; Auto-generated. Do not edit!


(cl:in-package smart_factory_sim-srv)


;//! \htmlinclude AssignTask-request.msg.html

(cl:defclass <AssignTask-request> (roslisp-msg-protocol:ros-message)
  ((task_id
    :reader task_id
    :initarg :task_id
    :type cl:integer
    :initform 0)
   (robot_id
    :reader robot_id
    :initarg :robot_id
    :type cl:integer
    :initform 0))
)

(cl:defclass AssignTask-request (<AssignTask-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <AssignTask-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'AssignTask-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name smart_factory_sim-srv:<AssignTask-request> is deprecated: use smart_factory_sim-srv:AssignTask-request instead.")))

(cl:ensure-generic-function 'task_id-val :lambda-list '(m))
(cl:defmethod task_id-val ((m <AssignTask-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:task_id-val is deprecated.  Use smart_factory_sim-srv:task_id instead.")
  (task_id m))

(cl:ensure-generic-function 'robot_id-val :lambda-list '(m))
(cl:defmethod robot_id-val ((m <AssignTask-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:robot_id-val is deprecated.  Use smart_factory_sim-srv:robot_id instead.")
  (robot_id m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <AssignTask-request>) ostream)
  "Serializes a message object of type '<AssignTask-request>"
  (cl:let* ((signed (cl:slot-value msg 'task_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'robot_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <AssignTask-request>) istream)
  "Deserializes a message object of type '<AssignTask-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'task_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'robot_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<AssignTask-request>)))
  "Returns string type for a service object of type '<AssignTask-request>"
  "smart_factory_sim/AssignTaskRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'AssignTask-request)))
  "Returns string type for a service object of type 'AssignTask-request"
  "smart_factory_sim/AssignTaskRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<AssignTask-request>)))
  "Returns md5sum for a message object of type '<AssignTask-request>"
  "3450a2182eb013df5d30a3ff5215b470")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'AssignTask-request)))
  "Returns md5sum for a message object of type 'AssignTask-request"
  "3450a2182eb013df5d30a3ff5215b470")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<AssignTask-request>)))
  "Returns full string definition for message of type '<AssignTask-request>"
  (cl:format cl:nil "# 任务分配服务请求~%int32 task_id~%int32 robot_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'AssignTask-request)))
  "Returns full string definition for message of type 'AssignTask-request"
  (cl:format cl:nil "# 任务分配服务请求~%int32 task_id~%int32 robot_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <AssignTask-request>))
  (cl:+ 0
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <AssignTask-request>))
  "Converts a ROS message object to a list"
  (cl:list 'AssignTask-request
    (cl:cons ':task_id (task_id msg))
    (cl:cons ':robot_id (robot_id msg))
))
;//! \htmlinclude AssignTask-response.msg.html

(cl:defclass <AssignTask-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (message
    :reader message
    :initarg :message
    :type cl:string
    :initform ""))
)

(cl:defclass AssignTask-response (<AssignTask-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <AssignTask-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'AssignTask-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name smart_factory_sim-srv:<AssignTask-response> is deprecated: use smart_factory_sim-srv:AssignTask-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <AssignTask-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:success-val is deprecated.  Use smart_factory_sim-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'message-val :lambda-list '(m))
(cl:defmethod message-val ((m <AssignTask-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:message-val is deprecated.  Use smart_factory_sim-srv:message instead.")
  (message m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <AssignTask-response>) ostream)
  "Serializes a message object of type '<AssignTask-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'message))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'message))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <AssignTask-response>) istream)
  "Deserializes a message object of type '<AssignTask-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'message) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'message) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<AssignTask-response>)))
  "Returns string type for a service object of type '<AssignTask-response>"
  "smart_factory_sim/AssignTaskResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'AssignTask-response)))
  "Returns string type for a service object of type 'AssignTask-response"
  "smart_factory_sim/AssignTaskResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<AssignTask-response>)))
  "Returns md5sum for a message object of type '<AssignTask-response>"
  "3450a2182eb013df5d30a3ff5215b470")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'AssignTask-response)))
  "Returns md5sum for a message object of type 'AssignTask-response"
  "3450a2182eb013df5d30a3ff5215b470")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<AssignTask-response>)))
  "Returns full string definition for message of type '<AssignTask-response>"
  (cl:format cl:nil "# 任务分配服务响应~%bool success~%string message~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'AssignTask-response)))
  "Returns full string definition for message of type 'AssignTask-response"
  (cl:format cl:nil "# 任务分配服务响应~%bool success~%string message~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <AssignTask-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'message))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <AssignTask-response>))
  "Converts a ROS message object to a list"
  (cl:list 'AssignTask-response
    (cl:cons ':success (success msg))
    (cl:cons ':message (message msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'AssignTask)))
  'AssignTask-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'AssignTask)))
  'AssignTask-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'AssignTask)))
  "Returns string type for a service object of type '<AssignTask>"
  "smart_factory_sim/AssignTask")