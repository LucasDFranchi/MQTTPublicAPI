# 📘 JSON Schema: Application External Types

This schema defines the structure of messages used for communication between an embedded system and an application interface. It supports data reporting, command issuance, and command response for sensors.

## 🔍 Schema Overview

The schema includes definitions for:

- Sensor data reports (`device_report_st`, `sensor_report_st`)
- Commands (`command_st`)
- Command responses (`command_response_st`)
- Enums for data type, command type, and command status

---

## 💡 Use Cases

### 1. ✅ Sensor Data Report

A message sent from the device containing current sensor readings:

```json
{
  "timestamp": "2025-07-10T14:30:00",
  "sensors": [
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 23.5, "active": 1 },
    { "value": 24.1, "active": 1 },
    { "value": 00.0, "active": 0 },
    { "value": 00.0, "active": 0 }
  ],
  "num_of_channels": 24
}
```
2. ⚙️ Command to Set Calibration

Command sent to configure calibration settings on a sensor:
``` json
{
  "command_index": "CMD_SET_CALIBRATION",
  "sensor_index": 1,
  "payload": {
      "gain": 1.02,
      "offset": -0.15
  }
}
```
3. 🟢 Command Response

Response from the device after a command is processed:
``` json
{
  "command_index": "CMD_SET_CALIBRATION",
  "command_status": "COMMAND_SUCCESS",
  "sensor_index": 1
}
```

📎 Related Types and Enums

    app_data_type_et: "DATA_TYPE_REPORT", "DATA_TYPE_COMMAND", "DATA_TYPE_COMMAND_RESPONSE"

    command_index_et: "CMD_GET_TIME", "CMD_SET_CALIBRATION"

    command_status_et: "COMMAND_SUCCESS", "COMMAND_FAIL", "COMMAND_CALIBRATION_FAIL"

✅ Compliance

This schema follows JSON Schema Draft-07.

You can use tools like AJV or jsonschema in Python to validate your payloads against this schema.
📂 License

MIT