#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <IRac.h> 

const char* ssid = "robotic-local"; 
const char* password = "12345678";

const uint16_t kIrLed = 4; // Pin IR
IRac ac(kIrLed);
WebServer server(80);

void handleStatus() {
  server.send(200, "application/json", "{\"status\":\"online\",\"device\":\"Daikin128_IR\"}");
}

void handleControl() {
  if (server.hasArg("plain") == false) {
    server.send(400, "application/json", "{\"error\":\"Body empty\"}");
    return;
  }

  StaticJsonDocument<500> doc;
  DeserializationError error = deserializeJson(doc, server.arg("plain"));

  if (error) {
    server.send(400, "application/json", "{\"error\":\"JSON parse error\"}");
    return;
  }

  // Set the Daikin128 Protocol
  ac.next.protocol = decode_type_t::DAIKIN128; // Protocol 68

  // Mapping Values
  if (doc.containsKey("power")) {
    String power = doc["power"];
    ac.next.power = (power == "ON");
  } else {
    ac.next.power = true; // default
  }

  // Set Default Celsius
  ac.next.celsius = true;
  if (doc.containsKey("temperature")) {
    ac.next.degrees = doc["temperature"].as<int>();
  } else {
    ac.next.degrees = 24; // Default if omitted
  }
  
  ac.next.mode = stdAc::opmode_t::kCool;
  ac.next.fanspeed = stdAc::fanspeed_t::kAuto;

  // Tembak burst
  Serial.println("------------------------------------");
  Serial.printf("[API] Power: %s\n", ac.next.power ? "ON" : "OFF");
  Serial.printf("[API] Temp : %d Celsius\n", ac.next.degrees);
  Serial.printf("[API] Mode : %d\n", ac.next.mode);
  Serial.printf("[API] Fan  : %d\n", ac.next.fanspeed);
  Serial.println("[API] Menembakkan IR Burst...");
  for(int i = 0; i < 3; i++) {
    ac.sendAc(); 
    delay(150);
  }

  server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"IR Sent\"}");
}

void setup() {
  Serial.begin(115200);
  delay(1000); 

  Serial.println("\n[SYSTEM] ESP32 AC IR Server Starting...");

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  server.on("/status", HTTP_GET, handleStatus);
  server.on("/control", HTTP_POST, handleControl);

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}