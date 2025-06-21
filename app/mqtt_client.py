import json
import time
import random
import threading
import paho.mqtt.client as mqtt
from datetime import datetime
from app import config
from app.handlers import read, calibrate, status

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(f"{config.TOPIC_BASE}/#")


def on_message(client, userdata, msg):
    topic_parts = msg.topic.split("/")
    if len(topic_parts) < 5:
        print("Invalid topic:", msg.topic)
        return

    _, device_id, action, sensor_type, sensor_id = topic_parts
    payload = json.loads(msg.payload.decode())

    if action == "read":
        read.handle(sensor_type, sensor_id, payload)
    elif action == "calibrate":
        if topic_parts[3] == "request":
            calibrate.handle_request(sensor_type, sensor_id, payload)
        elif topic_parts[3] == "response":
            calibrate.handle_response(sensor_type, sensor_id, payload)
    elif action == "status":
        status.handle(sensor_type, sensor_id, payload)


def publish_sensor_data():
    while True:
        for sensor_type, ids in {
            "temperature": range(0, 20),
            "analog": range(20, 22),
            "voltage": [22],
            "current": [23],
        }.items():
            for sensor_id in ids:
                topic = f"{config.TOPIC_BASE}/read/{sensor_type}/{sensor_id}"
                payload = {
                    "value": round(random.uniform(20.0, 30.0), 2),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                client.publish(topic, json.dumps(payload), qos=1)
        time.sleep(60)


def start():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config.BROKER_URL, config.BROKER_PORT, 60)

    # Start publisher thread
    threading.Thread(target=publish_sensor_data, daemon=True).start()

    client.loop_forever()
