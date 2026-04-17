#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <ir_Daikin.h> // Header spesifik untuk Daikin64
#include <IRrecv.h>
#include <IRutils.h>

const char* ssid = "robotic-local"; 
const char* password = "12345678";

// --- KONFIGURASI PIN ---
const uint16_t kIrLed = 4;   // Pin IR Transmitter
const uint16_t kIrRecv = 14;  // Pin IR Receiver (DAT)
const uint16_t kCaptureBufferSize = 1024;
const uint8_t kTimeout = 50;

// --- OBJEK IR ---
IRDaikin64 ac(kIrLed);       // Class spesifik Daikin64
IRrecv irrecv(kIrRecv, kCaptureBufferSize, kTimeout, true);
decode_results results;
WebServer server(80);

// --- STATE MANAGEMENT ---
bool currentPower = false;
int currentTemp = 24;
uint8_t currentMode = kDaikin64Cool;
uint8_t currentFan = kDaikin64FanAuto;

void syncWithLibrary() {
  // Update library internal state from our global state
  ac.setTemp(currentTemp);
  ac.setMode(currentMode);
  ac.setFan(currentFan);
}

void handleStatus() {
  StaticJsonDocument<300> doc;
  doc["status"] = "online";
  doc["device"] = "Daikin64_IR_Sync";
  doc["power"] = currentPower ? "ON" : "OFF";
  doc["temp"] = currentTemp;
  doc["mode"] = currentMode;
  doc["protocol"] = "DAIKIN64";
  
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

  // 1. Update State & Power Logic
  bool targetPower = currentPower;
  if (doc.containsKey("power")) {
    String p = doc["power"];
    targetPower = (p == "ON");
  }

  if (doc.containsKey("temperature")) {
    currentTemp = doc["temperature"].as<int>();
  }

  syncWithLibrary();

  // 2. Smart Toggle Logic
  if (targetPower != currentPower) {
    Serial.println("[IR] Power State Mismatch. Sending Toggle...");
    ac.setPowerToggle(true); 
    currentPower = targetPower; 
  } else {
    ac.setPowerToggle(false);
    Serial.println("[IR] Power State Matches. Updating parameters only.");
  }

  // 3. Send IR
  Serial.printf("[IR] Sending DAIKIN64 Power:%d Temp:%d\n", currentPower, currentTemp);
  ac.send();
  
  server.send(200, "application/json", "{\"status\":\"success\",\"power\":\"" + String(currentPower ? "ON":"OFF") + "\"}");
}

void setup() {
  Serial.begin(115200);
  delay(1000); 

  Serial.println("\n[SYSTEM] ESP32 Daikin64 IR Controller + Sync Starting...");

  // Setup IR
  ac.begin();
  irrecv.enableIRIn(); 
  Serial.printf("[WIFI] IR Transmitter Pin: %d\n", kIrLed);
  Serial.printf("[WIFI] IR Receiver Pin   : %d\n", kIrRecv);

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

  // --- LOGIKA IR RECEIVER ---
  if (irrecv.decode(&results)) {
    if (results.decode_type == DAIKIN64) {
      Serial.println("[SYNC] Intercepted Daikin64 Signal!");
      ac.setRaw(results.value);
      currentTemp = ac.getTemp();
      currentPower = !currentPower; 
      Serial.printf("[SYNC] New State -> Power:%d Temp:%d\n", currentPower, currentTemp);
    }
    irrecv.resume();
  }
}