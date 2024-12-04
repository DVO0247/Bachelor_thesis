#include <Arduino.h>
#include "APConfig.h"
#include "UDPSensorManager.h"

#define TEPLOTA 0
#define TLAK 1

const char* apSSID = "ESP32_CONF";
const char* apPassword = "Config00";
const int resetPin = 4;
const char* host;
uint16_t port;
String name;

APConfig apConfig(apSSID, apPassword, resetPin);
UDPSensorManager sensorManager;

double value = PI;

void setup() {
  Serial.begin(115200);
  apConfig.begin();
  apConfig.checkReset();
  if (apConfig.isInAPMode()) {
    apConfig.apLoop();
  }

  host = apConfig.getServerIP();
  port = apConfig.getServerPort();
  name = apConfig.getName();
  sensorManager.init(host, port, name);
  sensorManager.addSensor(1, 10);
}

void loop() {
  if (sensorManager.isWriteReady(TEPLOTA)) {
    sensorManager.write(TEPLOTA, value);
    Serial.println(String(value));
    value += 1.;
  }
  sensorManager.checkAndSend();
}
