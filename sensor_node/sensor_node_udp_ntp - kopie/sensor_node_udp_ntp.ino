#include <Arduino.h>
#include "APConfig.h"
#include "UDPSensorManager.h"
//#include "DHT.h"

#define apSSID "ESP32_CONF"
#define apPassword "Config00"
#define resetPin 18


#define DHT_PIN 4
#define DHTTYPE DHT11

APConfig apConfig;
UDPSensorManager sensorManager;
/*
DHT dht(DHT_PIN, DHTTYPE);

double readTemp(){
  return dht.readTemperature();
}

double readHum(){
  return dht.readHumidity();
}
*/
bool state = true;
double readPi() {
  if (state) {
    state = !state;
    return 3.14159265358979311599796346854;
  } else {
    state = !state;
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