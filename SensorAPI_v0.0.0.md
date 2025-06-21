
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

| Action     | Topic Example                                     | Description                            |
|:----------:|:-------------------------------------------------:|:--------------------------------------:|
| Read       | `iocloud/device123/read/temperature/0`            | Auto-published temperature temperature |
| Calibrate  | `iocloud/device123/calibrate/request/analog/0`    | Send calibration message               |
| Calibrate  | `iocloud/device123/calibrate/response/analog/0`   | Send or receive calibration message    |
| Status     | `iocloud/device123/status/temperature/0`          | Sensor status report                   |

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
  "gain": 12.0,
  "offset": 12.0,
}
```

### 🔁 Calibration Response Success

```json
{
  "status": 0,
}
```

### 🔁 Calibration Response Error

```json
{
  "status": 201,
}
```

### ℹ️ Status Message

```json
{
  "uptime": 86400,
  "error_code": 0,
  "timestamp": "2025-06-01T14:00:00Z"
}
```

### ❌ Error Report in Status Message

```json
{
  "uptime": 86400,
  "error_code": 102,
  "timestamp": "2025-06-01T14:00:00Z"
}
```

---

## 📋 Sensor Reference Table

| Sensor Type   | Sensor ID Range  | Description             |
|:-------------:|:----------------:|:-----------------------:|
| `temperature` | `0`–`19`         | Temperature Sensors     |
| `analog`      | `20`–`21`        | 4–20 mA Analog Sensors  |
| `voltage`     | `22`             | Voltage Sensor (0–10 V) |
| `current`     | `23`             | Current Sensor (0–10 A) |

---

## ✅ Best Practices

- Subscribe to `iocloud/<device_id>/read/+/#` to receive all sensor data from a device.
- Use retained messages for status and error updates.
- Validate calibration responses before applying corrections.
- Use QoS 1 or higher for data reliability.
- All timestamps should be in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`).

---

## 🚀 Example Usage

### Subscribe to all temperature readings from device123:
```bash
mosquitto_sub -h mqtt.example.com -t "iocloud/device123/read/temperature/+" -v
```

### Send calibration for analog sensor 0 on device123:
```bash
mosquitto_pub -h mqtt.example.com -t "iocloud/device123/calibrate/request/analog/0" -m '{
  "gain": 12.0,
  "offset": 12.0,
}'
```

---
