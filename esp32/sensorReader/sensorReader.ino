#include <WiFiManager.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <DHT.h>

// === Pins ===
#define DHTPIN  32          // GPIO where DHT11 is connected
#define DHTTYPE DHT11      // DHT 11
#define PIRPIN  14         // GPIO for PIR motion sensor
#define LIGHT_PIN 34      // GPIO (ADC1) for LDR light sensor

// === Server Configuration ===
const char* http_server = "http://192.168.1.10:5000";  // replace with your PC IP address
const char* mqtt_broker = "192.168.1.10";              // replace with your MQTT broker IP
const int mqtt_port = 1883;
const char* config_topic = "smartart/config";

// === MQTT Setup ===
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// === DHT Setup ===
DHT dht(DHTPIN, DHTTYPE);

// === Configurable Parameters ===
int samplingRate = 2;      // seconds
int motionThreshold = 1;    // dummy motion alert

// === Sensor values ===
float temperature = 22.5;
float humidity = 50.0;
float light = 300.0;
bool motion = false;

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.print("[MQTT] Config received: ");
  Serial.println(msg);

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

  String json = "{\"temperature\":" + String(temperature, 1) +
                ",\"humidity\":" + String(humidity, 1) +
                ",\"light\":" + String(light, 1) + "}";

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
  String json = "{\"motion\":" + String(motion ? 1 : 0) + "}";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int code = http.POST(json);
  Serial.print("[HTTP] Motion POST -> Code: ");
  Serial.println(code);
  http.end();
}

unsigned long lastSend = 0;

void setup() {
  Serial.begin(115200);

  // PIR motion sensor pin as input
  pinMode(PIRPIN, INPUT);

  // Light sensor pin input (analog)
  pinMode(LIGHT_PIN, INPUT);

  dht.begin();

  // WiFiManager
  WiFiManager wm;
  bool res = wm.autoConnect("SmartWallArt_Config");
  if (!res) {
    Serial.println("Failed to connect to WiFi, rebooting...");
    ESP.restart();
  }
  Serial.println("Connected to WiFi: " + WiFi.SSID());

  // MQTT Setup
  mqttClient.setServer(mqtt_broker, mqtt_port);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (!mqttClient.connected()) connectToMQTT();
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastSend > samplingRate * 1000) {
    lastSend = now;

    // Read sensors
    float newHum = dht.readHumidity();
    float newTemp = dht.readTemperature();

    if (!isnan(newHum)) humidity = newHum;
    else Serial.println("Failed to read humidity");

    if (!isnan(newTemp)) temperature = newTemp;
    else Serial.println("Failed to read temperature");

    motion = digitalRead(PIRPIN) == HIGH;

    int rawLight = analogRead(LIGHT_PIN);
    light = (float)rawLight;

    Serial.printf("Temperature: %.1f °C, Humidity: %.1f %%, Motion: %d, Light raw ADC: %d\n",
                  temperature, humidity, motion ? 1 : 0, rawLight);

    sendSensorData();
    sendMotionData();
  }
}
