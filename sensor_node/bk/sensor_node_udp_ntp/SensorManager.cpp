#include "esp_timer.h"
#include "esp32-hal.h"
#include <stdint.h>
#include "SensorManager.h"



void SensorManager::doReadAndWrites() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    uint32_t _millis = millis();
    if (xSemaphoreTake(sensors[i]->mutex, portMAX_DELAY)) {
      if (sensors[i]->isWriteReady(_millis)) {
        sensors[i]->readAndWrite(_millis);
        xSemaphoreGive(sensors[i]->mutex);
        if (sensors[i]->isPacketReady()) {
          BufferData bufferData;
          bufferData.sensorId = i;
          bufferData.sampleCount = sensors[i]->data.getSampleCount();
          memcpy(bufferData.buffer, sensors[i]->data.getBuffer(), sensors[i]->data.getCurrentByteSize());

          xQueueSend(bufferQueue, &bufferData, portMAX_DELAY);
          sensors[i]->data.clear();
        }
      } else {
        xSemaphoreGive(sensors[i]->mutex);
      }
    }
  }
}

SensorManager::SensorManager() {}

SensorManager::~SensorManager() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    delete sensors[i];  // Uvolnění dynamicky alokovaných objektů
  }
}

Sensor* SensorManager::getSensor(uint8_t sensorId) {
  if (sensorId < sensorCount) {
    return sensors[sensorId];
  } else {
    Serial.println("SensorManager: Sensor not found");
    return nullptr;
  }
}

uint8_t SensorManager::getSensorCount() {
  return sensorCount;
}

Sensor* SensorManager::addSensor(double (*callback)()) {
  if (sensorCount < MAX_SENSOR_COUNT) {
    sensors[sensorCount] = new Sensor(callback, UINT32_MAX, 1);
    sensorCount++;
    return sensors[sensorCount];
  } else {
    Serial.println("SensorManager: Maximum sensor count reached.");
    return nullptr;
  }
}

bool SensorManager::isWriteReady(uint8_t sensorId) {
  return sensors[sensorId]->isWriteReady();
}

void SensorManager::resetAllSensors() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    sensors[i]->data.clear();
  }
}
