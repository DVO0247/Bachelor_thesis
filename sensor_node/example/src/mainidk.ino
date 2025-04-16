#include "esp32-hal.h"
#include <Arduino.h>
#include "APConfig.h"
#include "TCPSensorManager.h"
#include "DHT.h"

#define apSSID "ESP32_CONF"
#define apPassword "Config00"
#define confResetPin 18
#define pinDHT 5

DHT dht11(pinDHT, DHT11);
APConfig apConfig;
TCPSensorManager tcpSensorManager;
// definice callback funkce pro čtení teploty
double read_temp(){
  return dht11.readTemperature(false, false);
}
// definice callback funkce pro čtení vlhkosti
double read_hum(){
  return dht11.readHumidity(false);
}

void setup() {
  Serial.begin(115200);
  apConfig.begin(apSSID, apPassword, confResetPin);
  dht11.begin();
  tcpSensorManager.addSensor(read_temp); // přidání sensoru tepla
  tcpSensorManager.addSensor(read_hum); // přidání senzoru vlhkosti
  tcpSensorManager.begin(&apConfig);
}

void loop() {
  tcpSensorManager.processData();
}
