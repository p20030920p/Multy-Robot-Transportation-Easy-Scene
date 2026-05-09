// Auto-generated. Do not edit!

// (in-package smart_factory_sim.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let geometry_msgs = _finder('geometry_msgs');

//-----------------------------------------------------------

class TaskStatus {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.task_id = null;
      this.task_type = null;
      this.priority = null;
      this.source = null;
      this.destination = null;
      this.material_type = null;
      this.status = null;
      this.assigned_robot_id = null;
    }
    else {
      if (initObj.hasOwnProperty('task_id')) {
        this.task_id = initObj.task_id
      }
      else {
        this.task_id = 0;
      }
      if (initObj.hasOwnProperty('task_type')) {
        this.task_type = initObj.task_type
      }
      else {
        this.task_type = '';
      }
      if (initObj.hasOwnProperty('priority')) {
        this.priority = initObj.priority
      }
      else {
        this.priority = 0;
      }
      if (initObj.hasOwnProperty('source')) {
        this.source = initObj.source
      }
      else {
        this.source = new geometry_msgs.msg.Point();
      }
      if (initObj.hasOwnProperty('destination')) {
        this.destination = initObj.destination
      }
      else {
        this.destination = new geometry_msgs.msg.Point();
      }
      if (initObj.hasOwnProperty('material_type')) {
        this.material_type = initObj.material_type
      }
      else {
        this.material_type = '';
      }
      if (initObj.hasOwnProperty('status')) {
        this.status = initObj.status
      }
      else {
        this.status = '';
      }
      if (initObj.hasOwnProperty('assigned_robot_id')) {
        this.assigned_robot_id = initObj.assigned_robot_id
      }
      else {
        this.assigned_robot_id = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type TaskStatus
    // Serialize message field [task_id]
    bufferOffset = _serializer.int32(obj.task_id, buffer, bufferOffset);
    // Serialize message field [task_type]
    bufferOffset = _serializer.string(obj.task_type, buffer, bufferOffset);
    // Serialize message field [priority]
    bufferOffset = _serializer.int32(obj.priority, buffer, bufferOffset);
    // Serialize message field [source]
    bufferOffset = geometry_msgs.msg.Point.serialize(obj.source, buffer, bufferOffset);
    // Serialize message field [destination]
    bufferOffset = geometry_msgs.msg.Point.serialize(obj.destination, buffer, bufferOffset);
    // Serialize message field [material_type]
    bufferOffset = _serializer.string(obj.material_type, buffer, bufferOffset);
    // Serialize message field [status]
    bufferOffset = _serializer.string(obj.status, buffer, bufferOffset);
    // Serialize message field [assigned_robot_id]
    bufferOffset = _serializer.int32(obj.assigned_robot_id, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type TaskStatus
    let len;
    let data = new TaskStatus(null);
    // Deserialize message field [task_id]
    data.task_id = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [task_type]
    data.task_type = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [priority]
    data.priority = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [source]
    data.source = geometry_msgs.msg.Point.deserialize(buffer, bufferOffset);
    // Deserialize message field [destination]
    data.destination = geometry_msgs.msg.Point.deserialize(buffer, bufferOffset);
    // Deserialize message field [material_type]
    data.material_type = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [status]
    data.status = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [assigned_robot_id]
    data.assigned_robot_id = _deserializer.int32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.task_type);
    length += _getByteLength(object.material_type);
    length += _getByteLength(object.status);
    return length + 72;
  }

  static datatype() {
    // Returns string type for a message object
    return 'smart_factory_sim/TaskStatus';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'b60bd2ab3a7887e34ec8035f0abf6774';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    # 任务状态消息
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new TaskStatus(null);
    if (msg.task_id !== undefined) {
      resolved.task_id = msg.task_id;
    }
    else {
      resolved.task_id = 0
    }

    if (msg.task_type !== undefined) {
      resolved.task_type = msg.task_type;
    }
    else {
      resolved.task_type = ''
    }

    if (msg.priority !== undefined) {
      resolved.priority = msg.priority;
    }
    else {
      resolved.priority = 0
    }

    if (msg.source !== undefined) {
      resolved.source = geometry_msgs.msg.Point.Resolve(msg.source)
    }
    else {
      resolved.source = new geometry_msgs.msg.Point()
    }

    if (msg.destination !== undefined) {
      resolved.destination = geometry_msgs.msg.Point.Resolve(msg.destination)
    }
    else {
      resolved.destination = new geometry_msgs.msg.Point()
    }

    if (msg.material_type !== undefined) {
      resolved.material_type = msg.material_type;
    }
    else {
      resolved.material_type = ''
    }

    if (msg.status !== undefined) {
      resolved.status = msg.status;
    }
    else {
      resolved.status = ''
    }

    if (msg.assigned_robot_id !== undefined) {
      resolved.assigned_robot_id = msg.assigned_robot_id;
    }
    else {
      resolved.assigned_robot_id = 0
    }

    return resolved;
    }
};

module.exports = TaskStatus;
