#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <LittleFS.h>

struct Asset {
  const char *path;
  const char *mime;
  size_t length;
};
#include "assets.generated.h"

static WebServer *server = nullptr;
static DNSServer *dns = nullptr;
static const IPAddress address(192, 168, 1, 1);
static const char *landing = "/1302-1352/index.html";

static void redirectToHost() {
  server->sendHeader("Location", String("http://192.168.1.1") + landing, true);
  server->sendHeader("Cache-Control", "no-store");
  server->send(302, "text/plain", "Open the local PS4 host.");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.printf("Starting ESP32 host: CPU=%u MHz, heap=%u\n",
                ESP.getCpuFreqMHz(), ESP.getFreeHeap());
  Serial.println("Initializing Wi-Fi AP...");
  for (uintptr_t p = 0x40080540; p < 0x40080570; p += 4) {
    Serial.printf("IRAM %08x = %08x\n", unsigned(p),
                  unsigned(*reinterpret_cast<volatile uint32_t *>(p)));
  }
  if (!WiFi.softAP("ESP32_Xploithost", "password") ||
      !WiFi.softAPConfig(address, address, IPAddress(255, 255, 255, 0))) {
    Serial.println("ERROR: Wi-Fi AP setup failed");
    return;
  }
  WiFi.setSleep(false);
  server = new WebServer(80);
  dns = new DNSServer();
  if (!LittleFS.begin(false)) {
    Serial.println("ERROR: LittleFS mount failed; flash the filesystem image");
    return;
  }
  for (const auto &asset : assets) {
    File file = LittleFS.open(String(asset.path) + ".gz", "r");
    if (!file || file.size() != asset.length) {
      Serial.printf("ERROR: missing or truncated asset %s\n", asset.path);
      return;
    }
  }
  Serial.printf("Assets ready: %u files, LittleFS %u/%u bytes\n",
                unsigned(sizeof(assets) / sizeof(assets[0])),
                unsigned(LittleFS.usedBytes()), unsigned(LittleFS.totalBytes()));
  dns->setErrorReplyCode(DNSReplyCode::NoError);
  if (!dns->start(53, "*", address)) {
    Serial.println("ERROR: DNS startup failed");
    return;
  }
  server->on("/", HTTP_GET, redirectToHost);
  server->on("/index.html", HTTP_GET, redirectToHost);
  server->on("/main.html", HTTP_GET, redirectToHost);
  server->on("/1302-1352/", HTTP_GET, redirectToHost);
  for (const auto &asset : assets) {
    const Asset *item = &asset;
    server->on(item->path, HTTP_GET, [item]() {
      File file = LittleFS.open(String(item->path) + ".gz", "r");
      if (!file || file.size() != item->length) {
        server->send(500, "text/plain", "Asset unavailable");
        return;
      }
      // streamFile adds gzip for .gz files except application/octet-stream.
      if (strcmp(item->mime, "application/octet-stream") == 0) {
        server->sendHeader("Content-Encoding", "gzip");
      }
      server->sendHeader("Cache-Control", "no-cache");
      server->streamFile(file, item->mime);
    });
  }
  server->onNotFound([]() {
    // Captive portal/User's Guide probes go to our canonical local origin.
    // Missing assets must stay errors, otherwise appcache could cache HTML
    // as a script, patch or payload.
    if (server->uri().startsWith("/1302-1352/")) {
      server->send(404, "text/plain", "Asset not found");
    } else {
      redirectToHost();
    }
  });
  server->begin();
  Serial.println("ESP32 13.52 host ready: ESP32_Xploithost / http://192.168.1.1");
  Serial.printf("Free heap: %u bytes\n", ESP.getFreeHeap());
}

void loop() {
  if (dns) dns->processNextRequest();
  if (server) server->handleClient();
  delay(2);
}
