# Communication Patterns

The device communicates with the host using two messaging patterns: **Publish/Subscribe** and **Request/Response**.

## Publish/Subscribe

In the Publish/Subscribe pattern, the device periodically publishes information without requiring a request from the host.

This pattern is intended for continuously changing or asynchronous information, such as:

- Device status (heartbeat)
- Telemetry
- Events and alarms

The host subscribes to the corresponding MQTT topics and receives updates as they are published.

### Sequence

```text
Host                             Device
 |                                  |
 |-------- Subscribe -------------->|
 |                                  |
 |<------- Heartbeat ---------------|
 |<------- Telemetry ---------------|
 |<------- Heartbeat ---------------|
 |<------- Telemetry ---------------|
```

### Typical Topics

| Topic | Description |
|--------|-------------|
| `iocloud/{deviceId}/heartbeat` | Device heartbeat / liveness signal |
| `iocloud/{deviceId}/telemetry` | Periodic sensor measurements |
| `iocloud/{deviceId}/events` | Asynchronous events and alarms |

### Example Heartbeat Payload

**Topic**

```text
iocloud/A842E3422C9C/heartbeat
```

**Payload**

```json
{
    "device_id": "A842E3422C9C",
    "ip": "192.168.3.95",
    "uptime_ms": 200060
}
```

### Example Telemetry Payload

**Topic**

```text
iocloud/A842E3422C9C/telemetry
```

**Payload**

```json
{
    "device_id": "A842E3422C9C",
    "timestamp": "2026-07-16T14:32:00Z",
    "readings": [
        {
            "sensor_id": 0,
            "type": "temperature",
            "value": 23.47
        },
        {
            "sensor_id": 1,
            "type": "humidity",
            "value": 58.2
        }
    ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Device identifier, matches the `{deviceId}` in the topic |
| `timestamp` | string | Time the readings were taken, ISO 8601 (UTC) |
| `readings` | array | One entry per sensor, in the order defined by `GET_SENSORS` |
| `readings[].sensor_id` | integer | Matches the `sensor_id` from `GET_SENSORS` |
| `readings[].type` | string | Sensor type, matches `GET_SENSORS` — included for convenience so consumers don't need to cross-reference |
| `readings[].value` | number | Reading, already adjusted using the sensor's calibration `offset`/`gain` |

> Since `value` is post-calibration, consider whether you also want the **raw** reading alongside it (e.g. `raw_value`) — useful for diagnosing a bad calibration without needing to reverse the math, at the cost of a slightly larger payload.

---

## Request/Response

In the Request/Response pattern, the host sends a request to the device, which processes the request and returns a corresponding response.

This pattern is intended for on-demand operations, such as:

- Reading device capabilities
- Reading the current configuration
- Updating configuration
- Calibrating sensors
- Restarting the device — *Not Supported*
- Running diagnostics — *Not Supported*

### Sequence

```text
Host                             Device
 |                                  |
 |--------- Request --------------->|
 |                                  |
 |<-------- Response ---------------|
```

### Example Request

**Topic**

```text
iocloud/{deviceId}/commands/request
```

**Payload**

```json
{
    "id": 0,
    "cmd": 1,
    "params": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Identifier chosen by the host to correlate this request with its response |
| `cmd` | integer | Yes | Command identifier (see [Command Table](#command-table)) |
| `params` | object | No | Command-specific parameters. Omit or send `{}` if the command takes no arguments |

### Example Response

**Topic**

```text
iocloud/{deviceId}/commands/response
```

**Payload**

```json
{
    "cmd": 1,
    "id": 0,
    "data": {},
    "status": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cmd` | integer | Echoes the command identifier from the request |
| `id` | integer | Echoes the `id` from the request, used to correlate response with request |
| `data` | object | Command-specific result payload. Shape depends on `cmd` |
| `status` | string | Result of the operation (e.g. `"ok"`, `"error"`) |

### Command Table

| `cmd` | Name | Description | Request `params` | Response `data` |
|-------|------|-------------|-------------------|------------------|
| `1` | `REBOOT` | Restart the device | _(none)_ | _(none)_ |
| `2` | `SET_SENSOR_CONFIG` | Configure calibration, sampling, and enabled state for a single sensor | `{ "sensor_id": integer, "offset": number, "gain": number, "sampling_ms": integer, "enabled": boolean }` | _(none)_ |
| `3` | `GET_SENSORS` | Query the list of available sensors, their type, capabilities, and current configuration | _(none)_ | `{ "sensors": [ { "sensor_id": integer, "type": string, "capabilities": object, "config": object } ] }` |
| `4` | `SET_SENSOR_CONFIG_BULK` | Configure calibration, sampling, and enabled state for multiple sensors in one request | `{ "sensors": [ { "sensor_id": integer, "offset": number, "gain": number, "sampling_ms": integer, "enabled": boolean } ] }` | _(none)_ |
| `5` | `GET_DEVICE_INFO` | Query device identity: firmware version, hardware model, serial number | _(none)_ | `{ "model": string, "firmware": string, "serial": string }` |

*(Replace with your actual command list — this is illustrating the pattern based on the current example.)*

### Example: Configure a Sensor (`SET_SENSOR_CONFIG`)

**Request**

```json
{
    "id": 1,
    "cmd": 2,
    "params": {
        "sensor_id": 2,
        "offset": -0.35,
        "gain": 1.012,
        "sampling_ms": 5000,
        "enabled": true
    }
}
```

**Response**

```json
{
    "cmd": 2,
    "id": 1,
    "data": {},
    "status": "ok"
}
```

> **Disabled sensors**: setting `enabled: false` stops the device from sampling that sensor and it is **omitted from the `telemetry` `readings` array** — it does not appear with a null/stale value. It **still appears in `GET_SENSORS`** (with `config.enabled: false`) so the host can show it in the UI and re-enable it later. This keeps telemetry consumers simple (an entry in `readings` always means "this was read"), while the config UI can still discover and manage every sensor the device has, on or off.

### Example: Configure All Sensors (`SET_SENSOR_CONFIG_BULK`)

**Request**

```json
{
    "id": 3,
    "cmd": 4,
    "params": {
        "sensors": [
            {
                "sensor_id": 0,
                "offset": 0.12,
                "gain": 0.998,
                "sampling_ms": 10000,
                "enabled": true
            },
            {
                "sensor_id": 1,
                "offset": -0.35,
                "gain": 1.012,
                "sampling_ms": 5000,
                "enabled": false
            }
        ]
    }
}
```

**Response**

```json
{
    "cmd": 4,
    "id": 3,
    "data": {},
    "status": "ok"
}
```

> Consider defining behavior for partial failures — e.g. if `sensor_id: 5` doesn't exist but the rest are valid, does the device apply the valid ones and report a partial error, or reject the whole batch? Document this explicitly (e.g. `status: "partial"` with a `data.errors` list) so the host knows how to handle it.

### Example: Query Available Sensors (`GET_SENSORS`)

**Request**

```json
{
    "id": 2,
    "cmd": 3,
    "params": {}
}
```

**Response**

```json
{
    "cmd": 3,
    "id": 2,
    "data": {
        "sensors": [
            {
                "sensor_id": 0,
                "type": "temperature",
                "capabilities": {
                    "unit": "celsius",
                    "range_min": -40,
                    "range_max": 125,
                    "resolution": 0.01
                },
                "config": {
                    "offset": 0.12,
                    "gain": 0.998,
                    "sampling_ms": 10000,
                    "enabled": true
                }
            },
            {
                "sensor_id": 1,
                "type": "humidity",
                "capabilities": {
                    "unit": "percent",
                    "range_min": 0,
                    "range_max": 100,
                    "resolution": 0.1
                },
                "config": {
                    "offset": -0.35,
                    "gain": 1.012,
                    "sampling_ms": 5000,
                    "enabled": false
                }
            }
        ]
    },
    "status": "ok"
}
```

> `capabilities` describes what the sensor *is* (fixed, read-only) — `config` describes how it's *currently set up* (calibration, sampling, enabled state), which the host may update via `SET_SENSOR_CONFIG` / `SET_SENSOR_CONFIG_BULK`. Keeping these as separate objects avoids the frontend confusing hardware limits with user-editable settings.
>
> `capabilities` fields will vary per sensor type — document the expected keys for each `type` (e.g. `temperature`, `humidity`, `pressure`, `analog`) in a separate reference table as your sensor types stabilize.

### Example: Query Device Info (`GET_DEVICE_INFO`)

**Request**

```json
{
    "id": 4,
    "cmd": 5,
    "params": {}
}
```

**Response**

```json
{
    "cmd": 5,
    "id": 4,
    "data": {
        "model": "Dashboard ESP",
        "firmware": "1.2.0",
        "serial": "A842E3422C9C"
    },
    "status": "ok"
}
```

> Useful for fleet inventory and support — knowing the firmware version on a device tells the host which commands/fields it can expect to be supported.

---

## Choosing the Appropriate Pattern

| Pattern | Use Cases |
|----------|-----------|
| **Publish/Subscribe** | Periodic telemetry, heartbeat, status updates, events, and alarms |
| **Request/Response** | Configuration, commands, capabilities, diagnostics, and other on-demand operations |

As a general guideline:

- Use **Publish/Subscribe** for information that changes over time and should be delivered automatically.
- Use **Request/Response** for operations initiated by the host that require a specific response from the device.