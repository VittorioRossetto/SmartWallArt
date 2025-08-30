
# Import required libraries
import time  # For sleep/delay
import json  # For encoding data as JSON
import random  # For generating random sensor values
import paho.mqtt.client as mqtt  # For MQTT communication


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


# Main loop: publish sensor and motion data at intervals
try:
    while True:
        sensor_data = generate_fake_sensor_data()  # Generate sensor values
        motion_data = generate_fake_motion()  # Generate motion value

        client.publish(MQTT_TOPIC_SENSOR, json.dumps(sensor_data))  # Publish sensor data
        client.publish(MQTT_TOPIC_MOTION, json.dumps(motion_data))  # Publish motion data

        print("Published sensor:", sensor_data)  # Log sensor data
        print("Published motion:", motion_data)  # Log motion data

        time.sleep(5)  # Wait 5 seconds before next publish (adjust as needed)

except KeyboardInterrupt:
    print("Simulation stopped.")  # Log when simulation is stopped
    client.loop_stop()  # Stop MQTT loop
    client.disconnect()  # Disconnect MQTT client
