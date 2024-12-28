#include "HardwareSerial.h"
#include <sys/types.h>
#include "UDPSensorManager.h"

UDPSensorManager::UDPSensorManager()
  : SensorManager() {}

void UDPSensorManager::init(const char* serverIP, uint16_t serverPort, String name) {
  this->serverIP = serverIP;
  this->serverPort = serverPort;
  this->name = name;
}

void UDPSensorManager::checkAndSend() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    if (sensors[i]->isFlushReady()) {
      Serial.println(sensors[i]->getSampleCount());
      sensors[i]->clear();
      Serial.println(sensors[i]->getSampleCount());
    }
  }
}