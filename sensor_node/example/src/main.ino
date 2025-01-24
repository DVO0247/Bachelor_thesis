#include "esp32-hal.h"
#include <Arduino.h>
#include "APConfig.h"
#include "TCPSensorManager.h"

#define apSSID "ESP32_CONF"
#define apPassword "Config00"
#define resetPin 18

APConfig apConfig;
TCPSensorManager sensorManager;

bool state = false;
double readPi() {
  state = !state;
  if (state) {
    return PI;
  } else {
    return 0.0;
  }
}

void setup() {
  Serial.begin(115200);
  apConfig.begin(apSSID, apPassword, resetPin);
  sensorManager.addSensor(readPi);
  sensorManager.begin(apConfig.getServerIP(), apConfig.getServerPort(), apConfig.getName());
}

void loop() {
  sensorManager.processData();
}