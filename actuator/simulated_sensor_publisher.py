import time
import json
import random
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_TOPIC_SENSOR = "smartart/sensor"
MQTT_TOPIC_MOTION = "smartart/motion"

client = mqtt.Client()
client.connect(MQTT_BROKER)
client.loop_start()

def generate_fake_sensor_data():
    return {
        "light": random.randint(100, 800),
        "temperature": random.uniform(0, 35),
        "humidity": random.uniform(30, 90)
    }

def generate_fake_motion():
    return {
        "motion": 1 #random.choice([0, 1])
    }

try:
    while True:
        sensor_data = generate_fake_sensor_data()
        motion_data = generate_fake_motion()

        client.publish(MQTT_TOPIC_SENSOR, json.dumps(sensor_data))
        client.publish(MQTT_TOPIC_MOTION, json.dumps(motion_data))

        print("Published sensor:", sensor_data)
        print("Published motion:", motion_data)

        time.sleep(5)  # adjust simulation rate here

except KeyboardInterrupt:
    print("Simulation stopped.")
    client.loop_stop()
    client.disconnect()
