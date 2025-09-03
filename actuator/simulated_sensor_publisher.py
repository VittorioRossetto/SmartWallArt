
# Import required libraries
import time  # For sleep/delay
import json  # For encoding data as JSON
import random  # For generating random sensor values
import paho.mqtt.client as mqtt  # For MQTT communication
import requests  # For sending HTTP requests to visual rating API


# MQTT configuration
MQTT_BROKER = "localhost"  # MQTT broker host
MQTT_TOPIC_SENSOR = "smartart/sensor"  # Topic for sensor data
MQTT_TOPIC_MOTION = "smartart/motion"  # Topic for motion data


# Create and connect MQTT client
client = mqtt.Client()
client.connect(MQTT_BROKER)
client.loop_start()  # Start MQTT loop in background


# Generate random sensor data
def generate_fake_sensor_data():
    return {
        "light": random.randint(100, 800),  # Simulate light sensor
        "temperature": random.uniform(0, 35),  # Simulate temperature sensor
        "humidity": random.uniform(30, 90)  # Simulate humidity sensor
    }


# Generate random motion data
def generate_fake_motion():
    return {
        "motion": 1  # Always motion detected (set to random.choice([0, 1]) for random)
    }


# Visual rating API configuration
VISUAL_API_URL = "http://localhost:5050/rate_visual"  # Endpoint for rating API

# Simulated user ID for ratings
SIM_USER_ID = 9999

# Main loop: publish sensor, motion, and simulated ratings
try:
    while True:
        sensor_data = generate_fake_sensor_data()  # Generate sensor values
        motion_data = generate_fake_motion()  # Generate motion value

        client.publish(MQTT_TOPIC_SENSOR, json.dumps(sensor_data))  # Publish sensor data
        client.publish(MQTT_TOPIC_MOTION, json.dumps(motion_data))  # Publish motion data

        print("Published sensor:", sensor_data)  # Log sensor data
        print("Published motion:", motion_data)  # Log motion data

        # Simulate visual rating after each motion event
        if motion_data["motion"] == 1:
            # Use current time as visual_time (ISO format)
            visual_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            rating = random.randint(0, 5)  # Random rating 0-5
            payload = {
                "user_id": SIM_USER_ID,
                "rating": rating,
                "visual_time": visual_time
            }
            try:
                resp = requests.post(VISUAL_API_URL, json=payload, timeout=2)
                if resp.status_code == 200:
                    print(f"Published simulated rating: {payload}")
                else:
                    print(f"Failed to publish rating: {resp.text}")
            except Exception as e:
                print(f"Error sending rating: {e}")

        time.sleep(5)  # Wait 5 seconds before next publish (adjust as needed)

except KeyboardInterrupt:
    print("Simulation stopped.")  # Log when simulation is stopped
    client.loop_stop()  # Stop MQTT loop
    client.disconnect()  # Disconnect MQTT client
