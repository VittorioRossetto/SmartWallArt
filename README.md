
# Smart Wall Art Project

This project is an **interactive art installation** that combines IoT sensors, real-time data streaming, generative visualizations, and AI-driven feedback.  
Environmental parameters such as **light, temperature, humidity, and motion** are captured by an ESP32 microcontroller and transformed into both **visual art (pygame)** and **data dashboards (Grafana + InfluxDB)**.  
User feedback is collected via a Telegram bot, and an AI model learns which sensor values are most appreciated, tuning the art generation accordingly.

---


## Project Architecture

1. **ESP32 with Sensors**  
   - PIR (motion) sensor  
   - DHT11 (temperature + humidity) sensor  
   - LDR (light sensor)  
   Publishes sensor data to MQTT topics.

2. **MQTT Broker (Mosquitto)**  
   Acts as the communication backbone between ESP32, the data proxy, and the art engine.

3. **Data Proxy (Python)**  
   Subscribes to MQTT topics, unifies sensor and motion data, and pushes into InfluxDB.

4. **InfluxDB**  
   Time-series database storing all sensor values and ratings.

5. **Grafana**  
   Dashboard for real-time visualization and historical data analysis.

6. **Generative Art Engine (Python + Pygame)**  
   Subscribes to MQTT and generates evolving visual patterns in real-time, optionally tuned by AI.

7. **Telegram Bot**  
   Allows users to rate the current visual and sends ratings to the backend.

8. **Visual Rating API (Python + Flask)**  
   Provides endpoints for fetching the latest visual and storing ratings in InfluxDB.

9. **AI Model Training Workflow (Python, scikit-learn)**  
   Extracts sensor-rating pairs from InfluxDB, trains a model to predict ratings, and saves the model for use in art generation.

---


## Quickstart Guide

Follow these steps to run the entire project:

### 1. Start the MQTT Broker (Mosquitto)
```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
mosquitto -v
```

### 2. Verify MQTT Works (Optional)
Open a new terminal:
```bash
mosquitto_sub -t "smartart/sensor"
```
Publish a test message from another terminal:
```bash
mosquitto_pub -t "smartart/sensor" -m '{"light":300,"temperature":22,"humidity":50}'
```

### 3. Flash ESP32 Code
Upload the ESP32 sketch from Arduino IDE or `arduino-cli`.  
This sends sensor readings to MQTT topics:  
- `smartart/sensor`  
- `smartart/motion`  

### 4. Start InfluxDB
```bash
sudo apt install -y influxdb
influxd
```

### 5. Create Database (First Time Only)
```bash
influx
```
Inside the shell:
```sql
CREATE DATABASE smartart;
USE smartart;
```

### 6. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 7. Run the Data Proxy
```bash
python3 data_proxy/data_proxy.py
```

### 8. Run the Visual Rating API
```bash
python3 data_proxy/visual_rating_api.py
```

### 9. Run the Telegram Bot
Set your bot token and API URL:
```bash
export BOT_TOKEN=your_telegram_bot_token
export VISUAL_API_URL=http://localhost:5050
python3 telegram/tg_bot.py
```

### 10. Train the AI Model (after collecting ratings)
```bash
python3 ai_rating_model/train_rating_model.py
```

### 11. Run the Generative Art Engine
```bash
cd actuator
python3 static_art_generator.py
```

### 12. Start Grafana
```bash
sudo apt install -y grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```
Open in browser: [http://localhost:3000](http://localhost:3000)  
(default login: `admin` / `admin`)  
Configure InfluxDB as data source → `smartart` database.

---


## Component Run Order
1. **MQTT Broker** → `mosquitto -v`  
2. **ESP32** → Upload and run sketch  
3. **InfluxDB** → `influxd`  
4. **Data Proxy** → `python3 data_proxy.py`  
5. **Visual Rating API** → `python3 data_proxy/visual_rating_api.py`  
6. **Telegram Bot** → `python3 telegram/tg_bot.py`  
7. **AI Model Training** → `python3 ai_rating_model/train_rating_model.py` (after ratings are collected)  
8. **Art Engine** → `python3 actuator/static_art_generator.py`  
9. **Grafana** → `grafana-server`  

---


## About the Project
This project is a fusion of **IoT, generative art, and AI feedback**.  
While sensors measure environmental conditions in real-time, the data is both **stored for analysis** and **transformed into evolving visuals** that respond dynamically to human presence and the environment.  
User ratings are collected via Telegram, and an AI model learns which sensor values are most appreciated, tuning the art generation to maximize engagement and aesthetic value.

## AI Feedback Loop
- Ratings are linked to the sensor data that generated each visual.
- The AI model is trained to predict ratings from sensor values.
- The art engine can use the model to bias or blend sensor data toward more appreciated values, while remaining responsive to the environment.

## Project Structure
- `actuator/` — Art generation scripts (static and dynamic)
- `ai_rating_model/` — AI model training and saving
- `data_proxy/` — Data proxy, rating API
- `esp32/` — ESP32 microcontroller code
- `forecasting/` — Sensor data forecasting scripts
- `telegram/` — Telegram bot and ratings
- `requirements.txt` — Python dependencies


## Author
### Vittorio Rossetto
 - [GitHub](https://github.com/VittorioRossetto)
 - [Linkedin](https://www.linkedin.com/in/vittorio-rossetto-508086333/)