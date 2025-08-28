# Smart Wall Art Project

This project is an **interactive art installation** that combines IoT sensors, real-time data streaming, and generative visualizations.  
Environmental parameters such as **light, temperature, humidity, and motion** are captured by an ESP32 microcontroller and transformed into both **visual art (pygame)** and **data dashboards (Grafana + InfluxDB)**.  

The system allows for both **scientific monitoring** and **artistic exploration**, bridging the gap between sensor networks and aesthetics.

---

## 📡 Project Architecture

1. **ESP32 with Sensors**  
   - PIR (motion) sensor  
   - DHT11 (temperature + humidity) sensor  
   - LDR (light sensor)  
   Publishes sensor data to MQTT topics.

2. **MQTT Broker (Mosquitto)**  
   Acts as the communication backbone between ESP32, the data proxy, and the art engine.

3. **Data Proxy (Python)**  
   Subscribes to MQTT topics, unifies data, and pushes into InfluxDB.

4. **InfluxDB**  
   Time-series database storing all sensor values.

5. **Grafana**  
   Dashboard for real-time visualization and historical data analysis.

6. **Generative Art Engine (Python + Pygame)**  
   Subscribes to MQTT and generates evolving visual patterns in real-time.

---

## 🚀 Quickstart Guide

Follow these steps in order to run the entire project.

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

### 6. Run the Data Proxy
Install Python dependencies:
```bash
pip install paho-mqtt influxdb
```
Run the script:
```bash
python3 data_proxy_unified.py
```

### 7. Start Grafana
```bash
sudo apt install -y grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```
Open in browser: [http://localhost:3000](http://localhost:3000)  
(default login: `admin` / `admin`)  
Configure InfluxDB as data source → `smartart` database.

### 8. Run the Generative Art Engine
Install dependencies:
```bash
pip install pygame paho-mqtt
```
Run:
```bash
python3 static_art_generator.py
```

---

## ✅ Component Run Order
1. **MQTT Broker** → `mosquitto -v`  
2. **ESP32** → Upload and run sketch  
3. **InfluxDB** → `influxd`  
4. **Data Proxy** → `python3 data_proxy_unified.py`  
5. **Grafana** → `grafana-server`  
6. **Art Engine** → `python3 static_art_generator.py`  

---

## 🎨 About the Project
This project is a fusion of **IoT and generative art**.  
While sensors measure environmental conditions in real-time, the data is both **stored for analysis** and **transformed into evolving visuals** that respond dynamically to human presence and the environment.

## Author
### Vittorio Rossetto