"""
MQTT Communication Emulator
============================

Emulates the Host <-> Datalogger communication described in
"communication-patterns.md", entirely offline (no real MQTT broker,
no network). A tiny in-memory broker stands in for the real one so
the message flow, topics, and payloads can be inspected directly.

Run:
    python3 mqtt_emulator.py
"""

import json
import time
import fnmatch
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any


# ---------------------------------------------------------------------------
# In-memory broker (stand-in for a real MQTT broker)
# ---------------------------------------------------------------------------

class InMemoryBroker:
    """Minimal pub/sub broker supporting single-level '+' wildcards,
    just enough to emulate MQTT topic routing without a network."""

    def __init__(self):
        self._subscribers: List[tuple] = []  # (topic_pattern, callback)

    def subscribe(self, topic_pattern: str, callback: Callable[[str, dict], None]):
        # Convert MQTT-style "+" wildcard to fnmatch "*" for simple matching
        glob_pattern = topic_pattern.replace("+", "*")
        self._subscribers.append((glob_pattern, callback))

    def publish(self, topic: str, payload: dict, log: bool = True):
        if log:
            print(f"  [PUBLISH] {topic}  {json.dumps(payload)}")
        for pattern, callback in self._subscribers:
            if fnmatch.fnmatch(topic, pattern):
                callback(topic, payload)


# ---------------------------------------------------------------------------
# Device (datalogger) side
# ---------------------------------------------------------------------------

@dataclass
class Sensor:
    sensor_id: int
    type: str
    capabilities: dict
    offset: float = 0.0
    gain: float = 1.0
    sampling_ms: int = 5000
    enabled: bool = True

    def config(self) -> dict:
        return {
            "offset": self.offset,
            "gain": self.gain,
            "sampling_ms": self.sampling_ms,
            "enabled": self.enabled,
        }

    def read_raw(self) -> float:
        # Fake raw reading depending on sensor type, just for the demo
        base = {"temperature": 22.0, "humidity": 55.0}.get(self.type, 0.0)
        return base

    def read_calibrated(self) -> float:
        raw = self.read_raw()
        return round(raw * self.gain + self.offset, 2)


class Device:
    def __init__(self, broker: InMemoryBroker, device_id: str, ip: str,
                 model: str, firmware: str, sensors: List[Sensor]):
        self.broker = broker
        self.device_id = device_id
        self.ip = ip
        self.model = model
        self.firmware = firmware
        self.sensors = {s.sensor_id: s for s in sensors}
        self.uptime_ms = 0

        self.broker.subscribe(
            f"iocloud/{device_id}/commands/request", self._on_request
        )

    # -- Publish/Subscribe side -------------------------------------------

    def publish_heartbeat(self):
        self.broker.publish(f"iocloud/{self.device_id}/heartbeat", {
            "device_id": self.device_id,
            "ip": self.ip,
            "uptime_ms": self.uptime_ms,
        })

    def publish_telemetry(self):
        readings = []
        for sensor in self.sensors.values():
            if not sensor.enabled:
                continue  # disabled sensors are omitted from telemetry
            readings.append({
                "sensor_id": sensor.sensor_id,
                "type": sensor.type,
                "value": sensor.read_calibrated(),
            })

        self.broker.publish(f"iocloud/{self.device_id}/telemetry", {
            "device_id": self.device_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "readings": readings,
        })

    # -- Request/Response side ---------------------------------------------

    def _on_request(self, topic: str, payload: dict):
        req_id = payload.get("id")
        cmd = payload.get("cmd")
        params = payload.get("params", {}) or {}

        try:
            data, status = self._handle_command(cmd, params)
        except Exception as exc:
            data, status = {"error": str(exc)}, "error"

        self.broker.publish(f"iocloud/{self.device_id}/commands/response", {
            "cmd": cmd,
            "id": req_id,
            "data": data,
            "status": status,
        })

    def _handle_command(self, cmd: int, params: dict):
        if cmd == 1:  # REBOOT
            self.uptime_ms = 0
            return {}, "ok"

        elif cmd == 2:  # SET_SENSOR_CONFIG
            sensor = self.sensors[params["sensor_id"]]
            self._apply_sensor_config(sensor, params)
            return {}, "ok"

        elif cmd == 3:  # GET_SENSORS
            sensors_out = []
            for sensor in self.sensors.values():
                sensors_out.append({
                    "sensor_id": sensor.sensor_id,
                    "type": sensor.type,
                    "capabilities": sensor.capabilities,
                    "config": sensor.config(),
                })
            return {"sensors": sensors_out}, "ok"

        elif cmd == 4:  # SET_SENSOR_CONFIG_BULK
            for entry in params.get("sensors", []):
                sensor = self.sensors[entry["sensor_id"]]
                self._apply_sensor_config(sensor, entry)
            return {}, "ok"

        elif cmd == 5:  # GET_DEVICE_INFO
            return {
                "model": self.model,
                "firmware": self.firmware,
                "serial": self.device_id,
            }, "ok"

        else:
            return {"error": f"unknown cmd {cmd}"}, "error"

    @staticmethod
    def _apply_sensor_config(sensor: Sensor, params: dict):
        if "offset" in params:
            sensor.offset = params["offset"]
        if "gain" in params:
            sensor.gain = params["gain"]
        if "sampling_ms" in params:
            sensor.sampling_ms = params["sampling_ms"]
        if "enabled" in params:
            sensor.enabled = params["enabled"]


# ---------------------------------------------------------------------------
# Host side
# ---------------------------------------------------------------------------

class Host:
    def __init__(self, broker: InMemoryBroker):
        self.broker = broker
        self.known_devices = set()
        self.next_request_id = 0
        self._pending_callbacks: Dict[int, Callable[[dict], None]] = {}

        self.broker.subscribe("iocloud/+/heartbeat", self._on_heartbeat)
        self.broker.subscribe("iocloud/+/telemetry", self._on_telemetry)
        self.broker.subscribe("iocloud/+/commands/response", self._on_response)

    def _on_heartbeat(self, topic: str, payload: dict):
        device_id = payload["device_id"]
        if device_id not in self.known_devices:
            self.known_devices.add(device_id)
            print(f"[HOST] New device discovered: {device_id} ({payload['ip']})")
            self.send_command(device_id, cmd=5, params={},
                               on_response=lambda data: print(
                                   f"[HOST] Device info for {device_id}: {data}"))
            self.send_command(device_id, cmd=3, params={},
                               on_response=lambda data: print(
                                   f"[HOST] Sensors for {device_id}: "
                                   f"{json.dumps(data, indent=2)}"))

    def _on_telemetry(self, topic: str, payload: dict):
        print(f"[HOST] Telemetry from {payload['device_id']}: "
              f"{payload['readings']}")

    def _on_response(self, topic: str, payload: dict):
        req_id = payload["id"]
        callback = self._pending_callbacks.pop(req_id, None)
        if callback:
            callback(payload["data"])

    def send_command(self, device_id: str, cmd: int, params: dict,
                      on_response: Callable[[dict], None] = None):
        req_id = self.next_request_id
        self.next_request_id += 1
        if on_response:
            self._pending_callbacks[req_id] = on_response

        self.broker.publish(f"iocloud/{device_id}/commands/request", {
            "id": req_id,
            "cmd": cmd,
            "params": params,
        })


# ---------------------------------------------------------------------------
# Demo scenario
# ---------------------------------------------------------------------------

def main():
    broker = InMemoryBroker()
    host = Host(broker)

    device = Device(
        broker=broker,
        device_id="A842E3422C9C",
        ip="192.168.3.95",
        model="Dashboard ESP",
        firmware="1.2.0",
        sensors=[
            Sensor(0, "temperature", {
                "unit": "celsius", "range_min": -40, "range_max": 125,
                "resolution": 0.01,
            }),
            Sensor(1, "humidity", {
                "unit": "percent", "range_min": 0, "range_max": 100,
                "resolution": 0.1,
            }),
        ],
    )

    print("\n=== 1. Device comes online, host discovers it via heartbeat ===")
    device.publish_heartbeat()

    print("\n=== 2. Host reconfigures sensor 1 (calibration + sampling) ===")
    host.send_command(device.device_id, cmd=2, params={
        "sensor_id": 1, "offset": -0.35, "gain": 1.012, "sampling_ms": 5000,
        "enabled": True,
    })

    print("\n=== 3. Normal telemetry publish (both sensors enabled) ===")
    device.publish_telemetry()

    print("\n=== 4. Host disables sensor 0 ===")
    host.send_command(device.device_id, cmd=2, params={
        "sensor_id": 0, "enabled": False,
    })

    print("\n=== 5. Telemetry after disabling sensor 0 (it's omitted) ===")
    device.publish_telemetry()

    print("\n=== 6. Host re-checks sensor list (sensor 0 still listed, disabled) ===")
    host.send_command(device.device_id, cmd=3, params={},
                       on_response=lambda data: print(
                           f"[HOST] Sensors now: {json.dumps(data, indent=2)}"))


if __name__ == "__main__":
    main()