import pygame
import random
import math
import json
import threading
import paho.mqtt.client as mqtt
import time

# === MQTT CONFIG ===
MQTT_BROKER = "localhost" 
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "smartart/sensor"
MQTT_TOPIC_MOTION = "smartart/motion"

# === SENSOR DATA STATE ===
# Initialize with some default values
sensor_data = {
    "light": 300,
    "temperature": 22,
    "humidity": 50,
    "motion": 0
}

# === MQTT HANDLER ===
# This function will be called when a message is received on the subscribed topics
def on_message(client, userdata, msg):
    global sensor_data
    try:
        data = json.loads(msg.payload.decode()) # Decode the JSON payload
        if msg.topic == MQTT_TOPIC_SENSOR:
            sensor_data.update(data) # Update the sensor data with the new values
        elif msg.topic == MQTT_TOPIC_MOTION:
            sensor_data["motion"] = int(data["motion"]) # Update motion state
    except Exception as e: # Handle JSON decoding errors
        print("MQTT Message Error:", e) 

# === MQTT THREAD ===
def mqtt_thread():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe([(MQTT_TOPIC_SENSOR, 0), (MQTT_TOPIC_MOTION, 0)])
    client.on_message = on_message
    client.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start() # Start MQTT thread

# === PYGAME SETUP ===
pygame.init()
WIDTH, HEIGHT = 1000, 700 # Set the dimensions of the window
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Create the Pygame window
# pygame.display.set_icon(pygame.image.load("icon.png")) # Load an icon for the window
pygame.display.set_caption("Smart Wall Art: Static Abstract") # Set the window title
clock = pygame.time.Clock() # Create a clock to control the frame rate

# === UTILITY FUNCTIONS ===
# Convert temperature to a color gradient, from blue on lower to red on upper temperatures
def temp_to_color(temp):
    TEMP_MIN, TEMP_MAX = 10, 40
    t = max(0, min(1, (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)))
    r = int((1 - t) * 50 + t * 255)
    g = int((1 - t) * 150 + t * 50)
    b = int((1 - t) * 255 + t * 50)
    return (r, g, b)

# Convert light level to a grayscale background color, darker on lower light levels
def light_to_background(light):
    L_MIN, L_MAX = 0, 1000
    t = max(0, min(1, (light - L_MIN) / (L_MAX - L_MIN)))
    v = int(t * 255)
    return (v, v, v)

# Draw random shapes on the surface based on sensor data 
def draw_random_shapes(surface, base_color, count, opacity, chaos=0):
    shape_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for _ in range(count):
        shape_type = random.choice(["circle", "square", "triangle", "line"])
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(20, 60)

        # Randomly adjust the base color for each shape 
        r = max(0, min(255, base_color[0] + random.randint(-30, 30)))
        g = max(0, min(255, base_color[1] + random.randint(-30, 30)))
        b = max(0, min(255, base_color[2] + random.randint(-30, 30)))

        color = (r, g, b, opacity)

        
        if shape_type == "circle":
            pygame.draw.circle(shape_surf, color, (x, y), size)
        elif shape_type == "square":
            pygame.draw.rect(shape_surf, color, (x, y, size, size))
        elif shape_type == "triangle":
            points = [
                (x, y),
                (x + size + chaos, y + size // 2 - chaos),
                (x + size // 2, y + size + chaos)
            ]
            pygame.draw.polygon(shape_surf, color, points)
        elif shape_type == "line":
            end_x = x + size + random.randint(-chaos, chaos)
            end_y = y + size + random.randint(-chaos, chaos)
            pygame.draw.line(shape_surf, color, (x, y), (end_x, end_y), width=2)

    surface.blit(shape_surf, (0, 0)) # Draw the shapes on the surface

# === INITIAL DRAWING ===
# Draw the initial static image based on sensor data
def draw_static_image():
    screen.fill(light_to_background(sensor_data["light"]))

    base_color = temp_to_color(sensor_data["temperature"])

    count = int(30 + (sensor_data["humidity"] / 100) * 50)
    opacity = max(30, int(255 - sensor_data["humidity"] * 1.5))

    chaos = 0
    if sensor_data["motion"] == 1:
        chaos = 20
        count += 20

    draw_random_shapes(screen, base_color, count, opacity, chaos)
    pygame.display.flip()

# === MAIN LOOP ===
draw_static_image()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False # Exit the loop
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r: # Redraw the static image on 'R' key press
                draw_static_image()

    clock.tick(10) # Control the frame rate

pygame.quit()
