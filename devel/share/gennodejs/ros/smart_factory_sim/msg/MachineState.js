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

class MachineState {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.machine_id = null;
      this.machine_type = null;
      this.status = null;
      this.position = null;
      this.materials_count = null;
      this.efficiency = null;
    }
    else {
      if (initObj.hasOwnProperty('machine_id')) {
        this.machine_id = initObj.machine_id
      }
      else {
        this.machine_id = 0;
      }
      if (initObj.hasOwnProperty('machine_type')) {
        this.machine_type = initObj.machine_type
      }
      else {
        this.machine_type = '';
      }
      if (initObj.hasOwnProperty('status')) {
        this.status = initObj.status
      }
      else {
        this.status = '';
      }
      if (initObj.hasOwnProperty('position')) {
        this.position = initObj.position
      }
      else {
        this.position = new geometry_msgs.msg.Point();
      }
      if (initObj.hasOwnProperty('materials_count')) {
        this.materials_count = initObj.materials_count
      }
      else {
        this.materials_count = 0;
      }
      if (initObj.hasOwnProperty('efficiency')) {
        this.efficiency = initObj.efficiency
      }
      else {
        this.efficiency = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type MachineState
    // Serialize message field [machine_id]
    bufferOffset = _serializer.int32(obj.machine_id, buffer, bufferOffset);
    // Serialize message field [machine_type]
    bufferOffset = _serializer.string(obj.machine_type, buffer, bufferOffset);
    // Serialize message field [status]
    bufferOffset = _serializer.string(obj.status, buffer, bufferOffset);
    // Serialize message field [position]
    bufferOffset = geometry_msgs.msg.Point.serialize(obj.position, buffer, bufferOffset);
    // Serialize message field [materials_count]
    bufferOffset = _serializer.int32(obj.materials_count, buffer, bufferOffset);
    // Serialize message field [efficiency]
    bufferOffset = _serializer.float32(obj.efficiency, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type MachineState
    let len;
    let data = new MachineState(null);
    // Deserialize message field [machine_id]
    data.machine_id = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [machine_type]
    data.machine_type = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [status]
    data.status = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [position]
    data.position = geometry_msgs.msg.Point.deserialize(buffer, bufferOffset);
    // Deserialize message field [materials_count]
    data.materials_count = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [efficiency]
    data.efficiency = _deserializer.float32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.machine_type);
    length += _getByteLength(object.status);
    return length + 44;
  }

  static datatype() {
    // Returns string type for a message object
    return 'smart_factory_sim/MachineState';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '83c455b2e59b8c116d67ec85f20c9dc2';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    # 机器状态消息
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new MachineState(null);
    if (msg.machine_id !== undefined) {
      resolved.machine_id = msg.machine_id;
    }
    else {
      resolved.machine_id = 0
    }

    if (msg.machine_type !== undefined) {
      resolved.machine_type = msg.machine_type;
    }
    else {
      resolved.machine_type = ''
    }

    if (msg.status !== undefined) {
      resolved.status = msg.status;
    }
    else {
      resolved.status = ''
    }

    if (msg.position !== undefined) {
      resolved.position = geometry_msgs.msg.Point.Resolve(msg.position)
    }
    else {
      resolved.position = new geometry_msgs.msg.Point()
    }

    if (msg.materials_count !== undefined) {
      resolved.materials_count = msg.materials_count;
    }
    else {
      resolved.materials_count = 0
    }

    if (msg.efficiency !== undefined) {
      resolved.efficiency = msg.efficiency;
    }
    else {
      resolved.efficiency = 0.0
    }

    return resolved;
    }
};

module.exports = MachineState;
