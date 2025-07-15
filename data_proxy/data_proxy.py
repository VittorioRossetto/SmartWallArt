import json
import threading
from flask import Flask, request, jsonify
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

# === Flask app ===
app = Flask(__name__)

# === Unified Write Function ===
def write_to_influx(measurement, data):
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
        measurement = "sensor_data"  # unified measurement name
        write_to_influx(measurement, payload)
    except Exception as e:
        print(f"[ERROR] Message handling failed: {e}")

# === HTTP routes ===
@app.route('/sensor', methods=['POST'])
def sensor_data():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    try:
        mqtt_client.publish(TOPIC_SENSOR, json.dumps(data))
        print(f"[HTTP] Received sensor data: {data} -> published to MQTT")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"[ERROR] MQTT publish failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/motion', methods=['POST'])
def motion_data():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    try:
        mqtt_client.publish(TOPIC_MOTION, json.dumps(data))
        print(f"[HTTP] Received motion data: {data} -> published to MQTT")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"[ERROR] MQTT publish failed: {e}")
        return jsonify({"error": str(e)}), 500

# === Run Flask in a thread ===
def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == "__main__":
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        influx_client.create_database(INFLUX_DB)
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        print("[System] MQTT connected, starting HTTP server...")

        # Start Flask HTTP server in a thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        print("[System] Ready. Listening for HTTP POST and MQTT messages...")
        mqtt_client.loop_forever()

    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
    finally:
        mqtt_client.disconnect()
        influx_client.close()
        print("[System] Shutdown complete.")
        flask_thread.join()
        print("[System] Flask server stopped.")
        exit(0)