#include <WiFiManager.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <PubSubClient.h>

// === Server Configuration ===
const char* http_server = "http://192.168.1.10:5000";  // PC's IP
const char* mqtt_broker = "192.168.1.10";              
const int mqtt_port = 1883;
const char* config_topic = "smartart/config";

// === MQTT Setup ===
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// === Configurable Parameters ===
int samplingRate = 10;      // seconds
int motionThreshold = 1;    // dummy motion alert

// === Simulated Sensor Values ===
float fakeTemp = 22.5;
float fakeHum = 50.0;
float fakeLight = 300.0;
bool fakeMotion = false;

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.print("[MQTT] Config received: ");
  Serial.println(msg);

  // Example JSON: {"sampling_rate":15,"motion_alert":2}
  if (msg.indexOf("sampling_rate") > 0) {
    int newRate = msg.substring(msg.indexOf(":") + 1, msg.indexOf(",")).toInt();
    if (newRate > 0) samplingRate = newRate;
  }

  if (msg.indexOf("motion_alert") > 0) {
    int mt = msg.substring(msg.lastIndexOf(":") + 1).toInt();
    motionThreshold = mt;
  }
}

void connectToMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqttClient.connect("ESP32Client")) {
      Serial.println(" connected.");
      mqttClient.subscribe(config_topic);
    } else {
      Serial.print(" failed, rc=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

void sendSensorData() {
  HTTPClient http;
  String url = String(http_server) + "/sensor";

  String json = "{\"temperature\":" + String(fakeTemp, 1) +
                ",\"humidity\":" + String(fakeHum, 1) +
                ",\"light\":" + String(fakeLight, 1) + "}";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(json);
  Serial.print("[HTTP] Sensor POST -> Code: ");
  Serial.println(httpResponseCode);
  http.end();
}

void sendMotionData() {
  HTTPClient http;
  String url = String(http_server) + "/motion";
  String json = "{\"motion\":" + String(fakeMotion ? 1 : 0) + "}";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int code = http.POST(json);
  Serial.print("[HTTP] Motion POST -> Code: ");
  Serial.println(code);
  http.end();
}

void setup() {
  Serial.begin(115200);

  // === Start WiFi Manager (no credentials needed in code!) ===
  WiFiManager wm;
  bool res = wm.autoConnect("SmartWallArt_Config");
  if (!res) {
    Serial.println("Failed to connect to WiFi, rebooting...");
    ESP.restart();
  }
  Serial.println("Connected to WiFi: " + WiFi.SSID());

  // === MQTT Setup ===
  mqttClient.setServer(mqtt_broker, mqtt_port);
  mqttClient.setCallback(mqttCallback);
}

unsigned long lastSend = 0;

void loop() {
  if (!mqttClient.connected()) connectToMQTT();
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastSend > samplingRate * 1000) {
    lastSend = now;

    // Simulate drift in readings
    fakeTemp += random(-5, 5) * 0.1;
    fakeHum += random(-10, 10) * 0.1;
    fakeLight += random(-30, 30);
    fakeMotion = 1;

    sendSensorData();
    sendMotionData();
  }
}
