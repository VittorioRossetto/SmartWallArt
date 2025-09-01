import pygame  # Library for graphics and game development
import random  # For random number generation
import math    # For mathematical functions
import json    # For parsing JSON data
import threading  # For running MQTT client in a separate thread
import paho.mqtt.client as mqtt  # MQTT client for sensor data
import time    # For time tracking

"""
ALTERNATIVE SCRIPT FOR ANIMATED PARTICLE ART: DEPRECATED
"""


## === MQTT CONFIGURATION ===
MQTT_BROKER = "localhost"  # Address of the MQTT broker
MQTT_PORT = 1883           # Default MQTT port
MQTT_TOPIC_SENSOR = "smartart/sensor"  # Topic for sensor data
MQTT_TOPIC_MOTION = "smartart/motion"  # Topic for motion data

## === SENSOR DATA STATE ===
sensor_data = {
    "light": 300,        # Initial light value
    "temperature": 22,   # Initial temperature value
    "humidity": 50,      # Initial humidity value
    "motion": 0          # Initial motion state
}

def on_message(client, userdata, msg):
    """
    Callback for MQTT messages. Updates sensor_data dict based on topic.
    """
    global sensor_data
    try:
        data = json.loads(msg.payload.decode())  # Parse JSON payload
        if msg.topic == MQTT_TOPIC_SENSOR:
            sensor_data.update(data)  # Update sensor values
        elif msg.topic == MQTT_TOPIC_MOTION:
            sensor_data["motion"] = int(data["motion"])  # Update motion state
    except Exception as e:
        print("MQTT Message Error:", e)  # Print error if message can't be parsed


def mqtt_thread():
    """
    Runs the MQTT client in a separate thread to receive sensor and motion data.
    """
    client = mqtt.Client()  # Create MQTT client
    client.connect(MQTT_BROKER, MQTT_PORT)  # Connect to broker
    client.subscribe([(MQTT_TOPIC_SENSOR, 0), (MQTT_TOPIC_MOTION, 0)])  # Subscribe to topics
    client.on_message = on_message  # Set message callback
    client.loop_forever()  # Start listening loop

threading.Thread(target=mqtt_thread, daemon=True).start()  # Start MQTT thread as daemon

## === PYGAME SETUP ===
pygame.init()  # Initialize Pygame
WIDTH, HEIGHT = 1000, 700  # Window size
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Create window
pygame.display.set_caption("Smart Wall Art: Fluid Motion")  # Set window title
clock = pygame.time.Clock()  # Create clock for framerate control

## === PARTICLE CLASS ===
class Particle:
    def __init__(self, x, y, dx, dy, color, size):
        self.x = x          # X position
        self.y = y          # Y position
        self.dx = dx        # X velocity
        self.dy = dy        # Y velocity
        self.color = color  # Particle color
        self.size = size    # Particle size

    def update(self):
        self.x += self.dx   # Move particle
        self.y += self.dy
        self.size *= 0.98   # Gradually shrink particle

    def draw(self, surface):
        if self.size > 1:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))  # Draw particle

## === UTILITY FUNCTIONS ===
def temp_to_color(temp):
    """
    Maps temperature value to an RGB color.
    """
    TEMP_MIN, TEMP_MAX = 10, 40
    t = max(0, min(1, (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)))  # Normalize temp
    r = int((1 - t) * 0 + t * 255)     # Red increases with temp
    g = int((1 - t) * 100 + t * 80)    # Green transitions
    b = int((1 - t) * 255 + t * 0)     # Blue decreases with temp
    return (r, g, b)

def light_to_background(light):
    """
    Maps light value to grayscale background color.
    """
    L_MIN, L_MAX = 0, 1000
    t = max(0, min(1, (light - L_MIN) / (L_MAX - L_MIN)))  # Normalize light
    v = int(t * 255)
    return (v, v, v)

def varied_color(base_color, variation=30):
    """
    Returns a color with random variation from a base color.
    """
    return tuple(
        max(0, min(255, base + random.randint(-variation, variation)))
        for base in base_color
    )

def draw_evolving_waves(surface, time_elapsed, wave_color):
    """
    Draws animated wave patterns based on time and color.
    """
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    for y in range(0, HEIGHT, 10):
        for x in range(0, WIDTH, 10):
            dx = x - center_x
            dy = y - center_y
            dist = math.sqrt(dx * dx + dy * dy)
            wave = math.sin(dist / 40.0 - time_elapsed * 0.5)  # Wave function
            brightness = (wave + 1) / 2  # Normalize to 0–1
            r = int(wave_color[0] * brightness)
            g = int(wave_color[1] * brightness)
            b = int(wave_color[2] * brightness)
            pygame.draw.rect(surface, (r, g, b), (x, y, 10, 10))  # Draw colored block

## === MAIN LOOP ===
particles = []  # List to hold all particles
angle = 0       # Angle for particle emission
running = True  # Main loop flag
start_time = time.time()  # Track start time

while running:
    # Handle window events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False  # Exit loop if window closed

    time_elapsed = time.time() - start_time  # Time since start

    # === BACKGROUND COLOR ===
    bg_color = light_to_background(sensor_data["light"])  # Set background based on light
    screen.fill(bg_color)

    # === RADIANT WAVES COLOR BASED ON TEMP ===
    wave_color = temp_to_color(sensor_data["temperature"])  # Color based on temperature
    draw_evolving_waves(screen, time_elapsed, wave_color)   # Draw animated waves

    # === FADE TRAILS ===
    fade = pygame.Surface((WIDTH, HEIGHT))  # Create fade overlay
    fade.set_alpha(int(100 - sensor_data["humidity"]))     # Fade strength based on humidity
    fade.fill((0, 0, 0))
    screen.blit(fade, (0, 0))  # Apply fade to screen

    # === PARTICLE GENERATION BASED ON MOTION ===
    if sensor_data["motion"] == 1:
        angle += 0.05  # Animate emission angle
        base_x = WIDTH // 2 + math.sin(angle) * 150  # Particle emission X
        base_y = HEIGHT // 2 + math.cos(angle * 1.3) * 100  # Particle emission Y

        light_clamped = max(0, min(sensor_data["light"], 1000))  # Clamp light value
        num_particles = int(light_clamped / 20)  # Number of particles based on light

        base_color = temp_to_color(sensor_data["temperature"])  # Particle color base

        for _ in range(num_particles):
            dx = random.uniform(-1.5, 1.5)  # Random X velocity
            dy = random.uniform(-1.5, 1.5)  # Random Y velocity
            size = random.uniform(4, 10)    # Random size
            color = varied_color(base_color)  # Slightly varied color
            particles.append(Particle(base_x, base_y, dx, dy, color, size))  # Add particle

    # Update and draw all particles
    for p in particles[:]:
        p.update()      # Move and shrink particle
        p.draw(screen)  # Draw particle
        if p.size < 1:
            particles.remove(p)  # Remove if too small

    pygame.display.flip()  # Update display
    clock.tick(60)         # Limit to 60 FPS

pygame.quit()  # Clean up and close window
