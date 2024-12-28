#include <Arduino.h>
#include "APConfig.h"

const char* apSSID = "ESP32_CONF";
const char* apPassword = "Config00";
const int resetPin = 4;
const char* host;
uint16_t port;
String name;

APConfig apConfig(apSSID, apPassword, resetPin);

void setup() {
  Serial.begin(115200);
  apConfig.begin();
  apConfig.checkReset();

  host = apConfig.getServerIP();
  port = apConfig.getServerPort();
  name = apConfig.getName();
}

void loop() {
  if (apConfig.isInAPMode()) {
    apConfig.apLoop();
  } else {
    Serial.println(host);
    Serial.println(String(port));
    Serial.println(name);
    Serial.println("");
    delay(1000);
  }
}
