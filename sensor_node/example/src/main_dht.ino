#include "esp32-hal.h"
#include <Arduino.h>
#include "APConfig.h"
#include "TCPSensorManager.h"
#include <Adafruit_Sensor.h>
#include "DHT.h"

#define apSSID "ESP32_CONF"
#define apPassword "Config00"
#define resetPin 18

#define pinDHT 5
DHT dht11(pinDHT, DHT11);

APConfig apConfig;
TCPSensorManager sensorManager;

double read_temp(){
  return dht11.readTemperature();
}

double read_hum(){
  return dht11.readHumidity();
}

void setup() {
  Serial.begin(115200);
  apConfig.begin(apSSID, apPassword, resetPin);
  sensorManager.addSensor(read_temp);
  sensorManager.addSensor(read_hum);
  sensorManager.begin(apConfig.getServerIP(), apConfig.getServerPort(), apConfig.getName());
}

void loop() {
  sensorManager.processData();
}