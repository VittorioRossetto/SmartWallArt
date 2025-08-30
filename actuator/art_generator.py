import pygame
import random
import math
import json
import threading
import paho.mqtt.client as mqtt
import time

"""
ALTERNATIVE SCRIPT FOR ANIMATED PARTICLE ART: DEPRECATED
"""


# === MQTT CONFIG ===
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "smartart/sensor"
MQTT_TOPIC_MOTION = "smartart/motion"

# === SENSOR DATA STATE ===
sensor_data = {
    "light": 300,
    "temperature": 22,
    "humidity": 50,
    "motion": 0
}

def on_message(client, userdata, msg):
    global sensor_data
    try:
        data = json.loads(msg.payload.decode())
        if msg.topic == MQTT_TOPIC_SENSOR:
            sensor_data.update(data)
        elif msg.topic == MQTT_TOPIC_MOTION:
            sensor_data["motion"] = int(data["motion"])
    except Exception as e:
        print("MQTT Message Error:", e)

def mqtt_thread():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe([(MQTT_TOPIC_SENSOR, 0), (MQTT_TOPIC_MOTION, 0)])
    client.on_message = on_message
    client.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start()

# === PYGAME SETUP ===
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smart Wall Art: Fluid Motion")
clock = pygame.time.Clock()

# === PARTICLES ===
class Particle:
    def __init__(self, x, y, dx, dy, color, size):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.size *= 0.98

    def draw(self, surface):
        if self.size > 1:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

# === UTILITY FUNCTIONS ===
def temp_to_color(temp):
    TEMP_MIN, TEMP_MAX = 10, 40
    t = max(0, min(1, (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)))
    r = int((1 - t) * 0 + t * 255)
    g = int((1 - t) * 100 + t * 80)
    b = int((1 - t) * 255 + t * 0)
    return (r, g, b)

def light_to_background(light):
    L_MIN, L_MAX = 0, 1000
    t = max(0, min(1, (light - L_MIN) / (L_MAX - L_MIN)))
    v = int(t * 255)
    return (v, v, v)

def varied_color(base_color, variation=30):
    return tuple(
        max(0, min(255, base + random.randint(-variation, variation)))
        for base in base_color
    )

def draw_evolving_waves(surface, time_elapsed, wave_color):
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    for y in range(0, HEIGHT, 10):
        for x in range(0, WIDTH, 10):
            dx = x - center_x
            dy = y - center_y
            dist = math.sqrt(dx * dx + dy * dy)
            wave = math.sin(dist / 40.0 - time_elapsed * 0.5)
            brightness = (wave + 1) / 2  # Normalize 0–1
            r = int(wave_color[0] * brightness)
            g = int(wave_color[1] * brightness)
            b = int(wave_color[2] * brightness)
            pygame.draw.rect(surface, (r, g, b), (x, y, 10, 10))

# === MAIN LOOP ===
particles = []
angle = 0
running = True
start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    time_elapsed = time.time() - start_time

    # === BACKGROUND COLOR ===
    bg_color = light_to_background(sensor_data["light"])
    screen.fill(bg_color)

    # === RADIANT WAVES COLOR BASED ON TEMP ===
    wave_color = temp_to_color(sensor_data["temperature"])
    draw_evolving_waves(screen, time_elapsed, wave_color)

    # === FADE TRAILS ===
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(int(100 - sensor_data["humidity"]))
    fade.fill((0, 0, 0))
    screen.blit(fade, (0, 0))

    # === PARTICLE GENERATION BASED ON MOTION ===
    if sensor_data["motion"] == 1:
        angle += 0.05
        base_x = WIDTH // 2 + math.sin(angle) * 150
        base_y = HEIGHT // 2 + math.cos(angle * 1.3) * 100

        light_clamped = max(0, min(sensor_data["light"], 1000))
        num_particles = int(light_clamped / 20)

        base_color = temp_to_color(sensor_data["temperature"])

        for _ in range(num_particles):
            dx = random.uniform(-1.5, 1.5)
            dy = random.uniform(-1.5, 1.5)
            size = random.uniform(4, 10)
            color = varied_color(base_color)
            particles.append(Particle(base_x, base_y, dx, dy, color, size))

    for p in particles[:]:
        p.update()
        p.draw(screen)
        if p.size < 1:
            particles.remove(p)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
