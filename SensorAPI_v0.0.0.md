
# Embedded Sensor Device – MQTT Interface Documentation

The IoCloud Datalogger monitors a collection of temperature, analog, and voltage/current sensors. It uses **MQTT** for data communication and publishes sensor data, calibration requests/responses, and system status/error messages in **JSON** format.

---

## 📡 MQTT Topic Structure

### 🔹 General Topic Format

```
<device_id>/<action>/<sensor_type>/<sensor_id>
```

- `device_id`: Unique device identifier (e.g., `device123`)
- `action`: One of `read`, `calibrate`, `status`
- `sensor_type`: One of `temperature`, `analog`, `voltage`, `current`
- `sensor_id`: Sensor identifier (e.g., `0`, `1`, ..., `19`)

### 🔹 Topic Examples

| Action     | Topic Example                             | Description                            |
|:----------:|:-----------------------------------------:|:--------------------------------------:|
| Read       | `device123/read/temperature/0`            | Auto-published temperature temperature |
| Calibrate  | `device123/calibrate/request/analog/0`    | Send calibration message               |
| Calibrate  | `device123/calibrate/response/analog/0`   | Send or receive calibration message    |
| Status     | `device123/status/temperature/0`          | Sensor status report                   |

---

## 📦 JSON Payload Examples

### ✅ Sensor Data Payload

```json
{
  "value": 25.63,
  "timestamp": "2025-06-01T14:03:25Z"
}
```

### 🛠️ Calibration Request

```json
{
  "action": "start",
  "reference_value": 12.0
}
```

### 🔁 Calibration Response

```json
{
  "sensor_id": "0",
  "status": "success",
  "adjusted_offset": -0.03,
  "adjusted_gain": 1.52
}
```

### ℹ️ Status Message

```json
{
  "device_id": "device123",
  "uptime": 86400,
  "error_code": 0,
  "message": "",
  "timestamp": "2025-06-01T14:00:00Z"
}
```

### ❌ Error Report in Status Message

```json
{
  "device_id": "device123",
  "uptime": 86400,
  "error_code": 102,
  "message": "Sensor temperature_07 timeout",
  "timestamp": "2025-06-01T14:00:00Z"
}
```

---

## 📋 Sensor Reference Table

| Sensor Type   | Sensor ID Range  | Description             |
|:-------------:|:----------------:|:-----------------------:|
| `temperature` | `0`–`19`         | Temperature Sensors     |
| `analog`      | `0`–`1`          | 4–20 mA Analog Sensors  |
| `voltage`     | `0`              | Voltage Sensor (0–10 V) |
| `current`     | `0`              | Current Sensor (0–10 A) |

---

## ✅ Best Practices

- Subscribe to `<device_id>/read/+/#` to receive all sensor data from a device.
- Use retained messages for status and error updates.
- Validate calibration responses before applying corrections.
- Use QoS 1 or higher for data reliability.
- All timestamps should be in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`).

---

## 🚀 Example Usage

### Subscribe to all temperature readings from device123:
```bash
mosquitto_sub -h mqtt.example.com -t "device123/read/temperature/+" -v
```

### Send calibration for analog sensor 0 on device123:
```bash
mosquitto_pub -h mqtt.example.com -t "device123/calibrate/request/analog/0" -m '{
  "sensor_id": "0",
  "sensor_type": "analog",
  "action": "start",
  "reference_value": 12.0
}'
```

---
