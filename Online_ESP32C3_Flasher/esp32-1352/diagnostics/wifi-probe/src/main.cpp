#include <Arduino.h>
#include <WiFi.h>

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.printf("Wi-Fi-only probe: cpu=%u heap=%u\n", ESP.getCpuFreqMHz(), ESP.getFreeHeap());
  const bool ok = WiFi.softAP("ESP32_WiFi_Probe", "password");
  Serial.printf("Wi-Fi-only probe AP result: %s IP=%s\n", ok ? "PASS" : "FAIL",
                WiFi.softAPIP().toString().c_str());
}

void loop() {
  Serial.printf("Probe alive: uptime=%lu ms, stations=%u\n", millis(), WiFi.softAPgetStationNum());
  delay(5000);
}
