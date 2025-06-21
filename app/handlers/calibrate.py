def handle_request(sensor_type, sensor_id, payload):
    print(f"[CALIBRATE REQUEST] {sensor_type}[{sensor_id}]: {payload}")

def handle_response(sensor_type, sensor_id, payload):
    print(f"[CALIBRATE RESPONSE] {sensor_type}[{sensor_id}]: {payload}")
