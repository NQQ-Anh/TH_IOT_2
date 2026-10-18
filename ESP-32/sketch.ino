#include <WiFi.h>
#include <PubSubClient.h> 
#include <DHTesp.h> 

// 1. Sửa lỗi cú pháp khai báo chuỗi
const char* WIFI_SSID = "Wokwi-GUEST"; 
const char* WIFI_PASSWORD = ""; 
const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
const char* mqtt_topic = "telemetry/esp32/sensors";

const int DHT_PIN = 15; 
const int TRIG_PIN = 5; 
const int ECHO_PIN = 18; 
const int LED_PIN = 2; 
const unsigned long SEND_INTERVAL_MS = 5000; 

WiFiClient wifiClient; 
PubSubClient mqttClient(wifiClient); 
DHTesp dht; 
unsigned long lastSend = 0; 
unsigned long sequenceNo = 0; 

void connectWiFi() { 
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6); 
  Serial.print("Connecting WiFi"); 
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  } 
  Serial.println(" connected"); 
} 

void connectMQTT() { 
  while (!mqttClient.connected()) { 
    String clientId = "ESP32-Bai2-" + String((uint32_t)ESP.getEfuseMac(), HEX); 
    Serial.print("Connecting MQTT..."); 
    
    // 2. Bỏ biến TOKEN vì HiveMQ không cần mật khẩu xác thực
    if (mqttClient.connect(clientId.c_str())) { 
      Serial.println(" connected"); 
    } else { 
      Serial.printf(" failed, rc=%d. Retry in 2 s\n", mqttClient.state()); 
      delay(2000);
    }
  } 
} 

float readDistanceCm() { 
  digitalWrite(TRIG_PIN, LOW); 
  delayMicroseconds(2); 
  digitalWrite(TRIG_PIN, HIGH); 
  delayMicroseconds(10); 
  digitalWrite(TRIG_PIN, LOW); 
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000); 
  if (duration == 0) return NAN; 
  return duration * 0.0343f / 2.0f; 
} 

void setup() { 
  Serial.begin(115200); 
  pinMode(TRIG_PIN, OUTPUT); 
  pinMode(ECHO_PIN, INPUT); 
  pinMode(LED_PIN, OUTPUT); 
  dht.setup(DHT_PIN, DHTesp::DHT22); 
  connectWiFi(); 
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT); 
  mqttClient.setBufferSize(256); 
} 

void loop() { 
  if (WiFi.status() != WL_CONNECTED) connectWiFi(); 
  if (!mqttClient.connected()) connectMQTT(); 
  mqttClient.loop(); 
  
  unsigned long now = millis(); 
  if (now - lastSend < SEND_INTERVAL_MS) return; 
  lastSend = now; 
  
  TempAndHumidity data = dht.getTempAndHumidity(); 
  float distance = readDistanceCm(); 
  
  float temp = isfinite(data.temperature) ? data.temperature : -999.0f;
  float hum = isfinite(data.humidity) ? data.humidity : -999.0f;
  float dist = isfinite(distance) ? distance : -999.0f;
  
  sequenceNo++; 
  char payload[256]; 
  
  // 3. Truyền các biến temp, hum, dist vào chuỗi thay vì data gốc
  // Bổ sung thêm "device_id":"esp32_01" để code Python đọc Database không bị lỗi
  snprintf(payload, sizeof(payload), 
    "{\"device_id\":\"esp32_01\",\"temperature\":%.2f,\"humidity\":%.2f,\"distance_cm\":%.2f," 
    "\"rssi\":%d,\"sequence\":%lu,\"uptime_s\":%lu}", 
    temp, hum, dist, WiFi.RSSI(), sequenceNo, millis() / 1000); 
  
  // 4. Publish vào mqtt_topic thay vì "v1/devices/me/telemetry"
  bool ok = mqttClient.publish(mqtt_topic, payload); 
  
  Serial.printf("%s | publish=%s\n", payload, ok ? "OK" : "FAILED"); 
  digitalWrite(LED_PIN, HIGH); 
  delay(80); 
  digitalWrite(LED_PIN, LOW); 
}