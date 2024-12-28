#include <Arduino.h>
#include "APConfig.h"
#include "UDPSensorManager.h"

const char* apSSID = "ESP32_CONF";
const char* apPassword = "Config00";
const int resetPin = 4;
const char* host;
uint16_t port;
String name;

APConfig apConfig(apSSID, apPassword, resetPin);
UDPSensorManager sensorManager;

double value = PI;

double writePI() {
  double _value = value;
  value += 1.0;
  return _value;
}

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

  sensorManager.addSensor(writePI, 0., 121);
  sensorManager.begin(host, port, name);
}

void loop() {
  sensorManager.processData();
}
