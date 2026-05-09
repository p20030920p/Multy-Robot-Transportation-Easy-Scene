// Auto-generated. Do not edit!

// (in-package smart_factory_sim.srv)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------


//-----------------------------------------------------------

class ProcessMaterialRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.machine_id = null;
      this.material_ids = null;
    }
    else {
      if (initObj.hasOwnProperty('machine_id')) {
        this.machine_id = initObj.machine_id
      }
      else {
        this.machine_id = 0;
      }
      if (initObj.hasOwnProperty('material_ids')) {
        this.material_ids = initObj.material_ids
      }
      else {
        this.material_ids = [];
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type ProcessMaterialRequest
    // Serialize message field [machine_id]
    bufferOffset = _serializer.int32(obj.machine_id, buffer, bufferOffset);
    // Serialize message field [material_ids]
    bufferOffset = _arraySerializer.int32(obj.material_ids, buffer, bufferOffset, null);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type ProcessMaterialRequest
    let len;
    let data = new ProcessMaterialRequest(null);
    // Deserialize message field [machine_id]
    data.machine_id = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [material_ids]
    data.material_ids = _arrayDeserializer.int32(buffer, bufferOffset, null)
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += 4 * object.material_ids.length;
    return length + 8;
  }

  static datatype() {
    // Returns string type for a service object
    return 'smart_factory_sim/ProcessMaterialRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'e881f9e53c5fd123ff75bd7f47c028ae';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    # 物料处理服务请求
    int32 machine_id
    int32[] material_ids
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new ProcessMaterialRequest(null);
    if (msg.machine_id !== undefined) {
      resolved.machine_id = msg.machine_id;
    }
    else {
      resolved.machine_id = 0
    }

    if (msg.material_ids !== undefined) {
      resolved.material_ids = msg.material_ids;
    }
    else {
      resolved.material_ids = []
    }

    return resolved;
    }
};

class ProcessMaterialResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.success = null;
      this.message = null;
      this.processed_count = null;
    }
    else {
      if (initObj.hasOwnProperty('success')) {
        this.success = initObj.success
      }
      else {
        this.success = false;
      }
      if (initObj.hasOwnProperty('message')) {
        this.message = initObj.message
      }
      else {
        this.message = '';
      }
      if (initObj.hasOwnProperty('processed_count')) {
        this.processed_count = initObj.processed_count
      }
      else {
        this.processed_count = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type ProcessMaterialResponse
    // Serialize message field [success]
    bufferOffset = _serializer.bool(obj.success, buffer, bufferOffset);
    // Serialize message field [message]
    bufferOffset = _serializer.string(obj.message, buffer, bufferOffset);
    // Serialize message field [processed_count]
    bufferOffset = _serializer.int32(obj.processed_count, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type ProcessMaterialResponse
    let len;
    let data = new ProcessMaterialResponse(null);
    // Deserialize message field [success]
    data.success = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [message]
    data.message = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [processed_count]
    data.processed_count = _deserializer.int32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.message);
    return length + 9;
  }

  static datatype() {
    // Returns string type for a service object
    return 'smart_factory_sim/ProcessMaterialResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'ccb941f6e14bbd3e1c8703c506a1fdc2';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    # 物料处理服务响应
    bool success
    string message
    int32 processed_count
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new ProcessMaterialResponse(null);
    if (msg.success !== undefined) {
      resolved.success = msg.success;
    }
    else {
      resolved.success = false
    }

    if (msg.message !== undefined) {
      resolved.message = msg.message;
    }
    else {
      resolved.message = ''
    }

    if (msg.processed_count !== undefined) {
      resolved.processed_count = msg.processed_count;
    }
    else {
      resolved.processed_count = 0
    }

    return resolved;
    }
};

module.exports = {
  Request: ProcessMaterialRequest,
  Response: ProcessMaterialResponse,
  md5sum() { return '4208032b26373306627bcd16215de808'; },
  datatype() { return 'smart_factory_sim/ProcessMaterial'; }
};
