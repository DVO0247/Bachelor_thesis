#include <Arduino.h>
#include "APConfig.h"
#include "UDPSensorManager.h"

const char* apSSID = "ESP32_CONF";
const char* apPassword = "Config00";
const int resetPin = 4;

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

  const char* host = apConfig.getServerIP();
  uint16_t port = apConfig.getServerPort();
  String name = apConfig.getName();

  sensorManager.addSensor(writePI, 1., 121);
  sensorManager.begin(host, port, name);
}

void loop() {
  sensorManager.processData();
}
