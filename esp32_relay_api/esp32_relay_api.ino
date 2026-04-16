#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// --- KONFIGURASI WIFI (Silakan isi kembali) ---
const char* ssid = "robotic-local"; 
const char* password = "12345678";

// Pin Relay (ESP32-S3)
//const int relayPins[] = {4, 5, 6, 10, 11, 12, 13, };
const int relayPins[] = {10, 11, 12, 13};
const int numRelays = 4;

// Konfigurasi Active High
#define RELAY_ON HIGH
#define RELAY_OFF LOW

WebServer server(80);

void handleStatus() {
  StaticJsonDocument<500> doc;
  JsonArray relays = doc.createNestedArray("relays");
  
  for (int i = 0; i < numRelays; i++) {
    JsonObject relay = relays.createNestedObject();
    relay["channel"] = i + 1;
    relay["state"] = (digitalRead(relayPins[i]) == RELAY_ON) ? "ON" : "OFF";
  }
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
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

  if (doc.containsKey("channel") && doc.containsKey("state")) {
    int channel = doc["channel"]; 
    String state = doc["state"];  

    if (channel < 1 || channel > numRelays) {
      server.send(400, "application/json", "{\"error\":\"Invalid channel\"}");
      return;
    }

    if (state == "ON") {
      digitalWrite(relayPins[channel - 1], RELAY_ON);
      Serial.printf("[API] Channel %d set to ON\n", channel);
    } else if (state == "OFF") {
      digitalWrite(relayPins[channel - 1], RELAY_OFF);
      Serial.printf("[API] Channel %d set to OFF\n", channel);
    } else {
      server.send(400, "application/json", "{\"error\":\"Invalid state\"}");
      return;
    }

    server.send(200, "application/json", "{\"status\":\"success\"}");
  } else {
    server.send(400, "application/json", "{\"error\":\"Missing parameters\"}");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000); 
  Serial.println("\n[SYSTEM] ESP32-S3 Starting...");
  Serial.println("[SYSTEM] Initializing Relay Pins...");

  for (int i = 0; i < numRelays; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], RELAY_OFF); 
  }

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
