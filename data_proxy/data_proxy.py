
# Import required libraries
import json  # For JSON handling
import threading  # For running Flask in a separate thread
from flask import Flask, request, jsonify  # For API endpoints
import paho.mqtt.client as mqtt  # For MQTT communication
from influxdb import InfluxDBClient  # For connecting to InfluxDB


# === Configuration ===
INFLUX_HOST = "localhost"  # InfluxDB host
INFLUX_PORT = 8086         # InfluxDB port
INFLUX_DB = "smartart"    # InfluxDB database name

MQTT_BROKER = "localhost"  # MQTT broker host
MQTT_PORT = 1883            # MQTT broker port
TOPIC_SENSOR = "smartart/sensor"  # MQTT topic for sensor data
TOPIC_MOTION = "smartart/motion"  # MQTT topic for motion data


# === Initialize Clients ===
influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)  # Connect to InfluxDB
mqtt_client = mqtt.Client()  # Create MQTT client


# === Flask app ===
app = Flask(__name__)  # Create Flask app


# === Unified Write Function ===
def write_to_influx(measurement, data):
    # Write a data point to InfluxDB
    try:
        json_body = [{
            "measurement": measurement,  # Measurement name
            "tags": {"location": "room1"},  # Example tag
            "fields": {k: float(v) if isinstance(v, (int, float)) else v
                       for k, v in data.items()}  # Store fields
        }]
        print(f"[InfluxDB] Writing to '{measurement}': {json_body}")  # Log write
        influx_client.write_points(json_body)  # Write to DB
    except Exception as e:
        print(f"[ERROR] Failed to write data: {e}")  # Log error


# === MQTT Callbacks ===
latest_sensor_data = {}  # Buffer for latest sensor data

def on_connect(client, userdata, flags, rc):
    # Callback when MQTT connects
    print(f"[MQTT] Connected (rc={rc})")
    client.subscribe([(TOPIC_SENSOR, 0), (TOPIC_MOTION, 0)])  # Subscribe to topics

def on_message(client, userdata, msg):
    # Callback for incoming MQTT messages
    global latest_sensor_data
    try:
        payload = json.loads(msg.payload.decode())  # Decode JSON payload
        print(f"[MQTT] Received on {msg.topic}: {payload}")  # Log received message
        if msg.topic == TOPIC_SENSOR:
            # Buffer the latest sensor data
            latest_sensor_data = payload

            # Write every sensor reading to 'all_sensor_data' for full-data forecasting
            write_to_influx("all_sensor_data", payload)
            
        elif msg.topic == TOPIC_MOTION:
            # Only write a unified entry when motion is detected
            if 'motion' in payload and int(payload['motion']) == 1:
                unified_data = latest_sensor_data.copy() if latest_sensor_data else {}
                unified_data['motion'] = 1  # Set motion to 1
                write_to_influx("sensor_data", unified_data)  # Write unified entry
    except Exception as e:
        print(f"[ERROR] Message handling failed: {e}")  # Log error


# === HTTP routes ===
@app.route('/sensor', methods=['POST'])
def sensor_data():
    # HTTP endpoint to receive sensor data
    data = request.json  # Get JSON body
    if not data:
        return jsonify({"error": "No JSON body"}), 400  # Error if missing
    try:
        mqtt_client.publish(TOPIC_SENSOR, json.dumps(data))  # Publish to MQTT
        print(f"[HTTP] Received sensor data: {data} -> published to MQTT")  # Log
        return jsonify({"status": "success"}), 200  # Success response
    except Exception as e:
        print(f"[ERROR] MQTT publish failed: {e}")  # Log error
        return jsonify({"error": str(e)}), 500  # Error response

@app.route('/motion', methods=['POST'])
def motion_data():
    # HTTP endpoint to receive motion data
    data = request.json  # Get JSON body
    if not data:
        return jsonify({"error": "No JSON body"}), 400  # Error if missing
    try:
        mqtt_client.publish(TOPIC_MOTION, json.dumps(data))  # Publish to MQTT
        print(f"[HTTP] Received motion data: {data} -> published to MQTT")  # Log
        return jsonify({"status": "success"}), 200  # Success response
    except Exception as e:
        print(f"[ERROR] MQTT publish failed: {e}")  # Log error
        return jsonify({"error": str(e)}), 500  # Error response


# === Run Flask in a thread ===
def run_flask():
    # Run Flask app in a separate thread
    app.run(host='0.0.0.0', port=5000, threaded=True)


# === Main Entrypoint ===
if __name__ == "__main__":
    mqtt_client.on_connect = on_connect  # Set MQTT connect callback
    mqtt_client.on_message = on_message  # Set MQTT message callback

    try:
        influx_client.create_database(INFLUX_DB)  # Create DB if not exists
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)  # Connect to MQTT broker
        print("[System] MQTT connected, starting HTTP server...")

        # Start Flask HTTP server in a thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True  # Daemon thread
        flask_thread.start()

        print("[System] Ready. Listening for HTTP POST and MQTT messages...")
        mqtt_client.loop_forever()  # Start MQTT loop

    except KeyboardInterrupt:
        print("\n[System] Shutting down...")  # Handle Ctrl+C
    finally:
        mqtt_client.disconnect()  # Disconnect MQTT
        influx_client.close()     # Close InfluxDB
        print("[System] Shutdown complete.")
        flask_thread.join()      # Wait for Flask thread
        print("[System] Flask server stopped.")
        exit(0)