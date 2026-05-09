; Auto-generated. Do not edit!


(cl:in-package smart_factory_sim-srv)


;//! \htmlinclude ProcessMaterial-request.msg.html

(cl:defclass <ProcessMaterial-request> (roslisp-msg-protocol:ros-message)
  ((machine_id
    :reader machine_id
    :initarg :machine_id
    :type cl:integer
    :initform 0)
   (material_ids
    :reader material_ids
    :initarg :material_ids
    :type (cl:vector cl:integer)
   :initform (cl:make-array 0 :element-type 'cl:integer :initial-element 0)))
)

(cl:defclass ProcessMaterial-request (<ProcessMaterial-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ProcessMaterial-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ProcessMaterial-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name smart_factory_sim-srv:<ProcessMaterial-request> is deprecated: use smart_factory_sim-srv:ProcessMaterial-request instead.")))

(cl:ensure-generic-function 'machine_id-val :lambda-list '(m))
(cl:defmethod machine_id-val ((m <ProcessMaterial-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:machine_id-val is deprecated.  Use smart_factory_sim-srv:machine_id instead.")
  (machine_id m))

(cl:ensure-generic-function 'material_ids-val :lambda-list '(m))
(cl:defmethod material_ids-val ((m <ProcessMaterial-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:material_ids-val is deprecated.  Use smart_factory_sim-srv:material_ids instead.")
  (material_ids m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ProcessMaterial-request>) ostream)
  "Serializes a message object of type '<ProcessMaterial-request>"
  (cl:let* ((signed (cl:slot-value msg 'machine_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'material_ids))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let* ((signed ele) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    ))
   (cl:slot-value msg 'material_ids))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ProcessMaterial-request>) istream)
  "Deserializes a message object of type '<ProcessMaterial-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'machine_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'material_ids) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'material_ids)))
    (cl:dotimes (i __ros_arr_len)
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:aref vals i) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296)))))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ProcessMaterial-request>)))
  "Returns string type for a service object of type '<ProcessMaterial-request>"
  "smart_factory_sim/ProcessMaterialRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ProcessMaterial-request)))
  "Returns string type for a service object of type 'ProcessMaterial-request"
  "smart_factory_sim/ProcessMaterialRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ProcessMaterial-request>)))
  "Returns md5sum for a message object of type '<ProcessMaterial-request>"
  "4208032b26373306627bcd16215de808")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ProcessMaterial-request)))
  "Returns md5sum for a message object of type 'ProcessMaterial-request"
  "4208032b26373306627bcd16215de808")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ProcessMaterial-request>)))
  "Returns full string definition for message of type '<ProcessMaterial-request>"
  (cl:format cl:nil "# 物料处理服务请求~%int32 machine_id~%int32[] material_ids~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ProcessMaterial-request)))
  "Returns full string definition for message of type 'ProcessMaterial-request"
  (cl:format cl:nil "# 物料处理服务请求~%int32 machine_id~%int32[] material_ids~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ProcessMaterial-request>))
  (cl:+ 0
     4
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'material_ids) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 4)))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ProcessMaterial-request>))
  "Converts a ROS message object to a list"
  (cl:list 'ProcessMaterial-request
    (cl:cons ':machine_id (machine_id msg))
    (cl:cons ':material_ids (material_ids msg))
))
;//! \htmlinclude ProcessMaterial-response.msg.html

(cl:defclass <ProcessMaterial-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (message
    :reader message
    :initarg :message
    :type cl:string
    :initform "")
   (processed_count
    :reader processed_count
    :initarg :processed_count
    :type cl:integer
    :initform 0))
)

(cl:defclass ProcessMaterial-response (<ProcessMaterial-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ProcessMaterial-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ProcessMaterial-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name smart_factory_sim-srv:<ProcessMaterial-response> is deprecated: use smart_factory_sim-srv:ProcessMaterial-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <ProcessMaterial-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:success-val is deprecated.  Use smart_factory_sim-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'message-val :lambda-list '(m))
(cl:defmethod message-val ((m <ProcessMaterial-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:message-val is deprecated.  Use smart_factory_sim-srv:message instead.")
  (message m))

(cl:ensure-generic-function 'processed_count-val :lambda-list '(m))
(cl:defmethod processed_count-val ((m <ProcessMaterial-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader smart_factory_sim-srv:processed_count-val is deprecated.  Use smart_factory_sim-srv:processed_count instead.")
  (processed_count m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ProcessMaterial-response>) ostream)
  "Serializes a message object of type '<ProcessMaterial-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'message))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'message))
  (cl:let* ((signed (cl:slot-value msg 'processed_count)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ProcessMaterial-response>) istream)
  "Deserializes a message object of type '<ProcessMaterial-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'message) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'message) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'processed_count) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ProcessMaterial-response>)))
  "Returns string type for a service object of type '<ProcessMaterial-response>"
  "smart_factory_sim/ProcessMaterialResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ProcessMaterial-response)))
  "Returns string type for a service object of type 'ProcessMaterial-response"
  "smart_factory_sim/ProcessMaterialResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ProcessMaterial-response>)))
  "Returns md5sum for a message object of type '<ProcessMaterial-response>"
  "4208032b26373306627bcd16215de808")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ProcessMaterial-response)))
  "Returns md5sum for a message object of type 'ProcessMaterial-response"
  "4208032b26373306627bcd16215de808")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ProcessMaterial-response>)))
  "Returns full string definition for message of type '<ProcessMaterial-response>"
  (cl:format cl:nil "# 物料处理服务响应~%bool success~%string message~%int32 processed_count~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ProcessMaterial-response)))
  "Returns full string definition for message of type 'ProcessMaterial-response"
  (cl:format cl:nil "# 物料处理服务响应~%bool success~%string message~%int32 processed_count~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ProcessMaterial-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'message))
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ProcessMaterial-response>))
  "Converts a ROS message object to a list"
  (cl:list 'ProcessMaterial-response
    (cl:cons ':success (success msg))
    (cl:cons ':message (message msg))
    (cl:cons ':processed_count (processed_count msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'ProcessMaterial)))
  'ProcessMaterial-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'ProcessMaterial)))
  'ProcessMaterial-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ProcessMaterial)))
  "Returns string type for a service object of type '<ProcessMaterial>"
  "smart_factory_sim/ProcessMaterial")