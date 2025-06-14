# data_proxy_unified.py
import json
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

# === Configuration ===
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "smartart"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SENSOR = "smartart/sensor"
TOPIC_MOTION = "smartart/motion"

# === Initialize Clients ===
influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)
mqtt_client = mqtt.Client()

# === Unified Write Function ===
def write_to_influx(measurement, data):
    """Write any sensor data to InfluxDB under a single measurement."""
    try:
        json_body = [{
            "measurement": measurement,
            "tags": {"location": "room1"},
            "fields": {k: float(v) if isinstance(v, (int, float)) else v 
                      for k, v in data.items()}
        }]
        print(f"[InfluxDB] Writing to '{measurement}': {json_body}")
        influx_client.write_points(json_body)
    except Exception as e:
        print(f"[ERROR] Failed to write data: {e}")

# === MQTT Callbacks ===
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected (rc={rc})")
    client.subscribe([(TOPIC_SENSOR, 0), (TOPIC_MOTION, 0)])

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] Received on {msg.topic}: {payload}")
        
        # Determine measurement name from topic
        measurement = "sensor_data"  # Unified name
        write_to_influx(measurement, payload)
    except Exception as e:
        print(f"[ERROR] Message handling failed: {e}")

# === Main ===
if __name__ == "__main__":
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        influx_client.create_database(INFLUX_DB)
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        print("[System] Ready. Listening for MQTT...")
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
    finally:
        mqtt_client.disconnect()