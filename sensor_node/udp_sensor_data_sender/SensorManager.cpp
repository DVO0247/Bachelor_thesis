#include "SensorManager.h"

void SensorManager::doReadAndWrites() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    if (sensors[i]->isWriteReady()) {
      sensors[i]->readAndWrite();
    }
  }
}

SensorManager::SensorManager() {}

SensorManager::~SensorManager() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    delete sensors[i];  // Uvolnění dynamicky alokovaných objektů
  }
}

Sensor* SensorManager::getSensor(uint8_t sensor_id) {
  if (sensor_id < sensorCount) {
    return sensors[sensor_id];
  } else {
    Serial.println("SensorManager: Sensor not found");
    return nullptr;
  }
}

uint8_t SensorManager::getSensorCount() {
  return sensorCount;
}

Sensor* SensorManager::addSensor(double (*callback)(), uint16_t sampleRate, uint8_t samplesPerPacket) {
  if (sensorCount < MAX_SENSOR_COUNT) {
    sensors[sensorCount] = new Sensor(callback, sampleRate, samplesPerPacket);
    sensorCount++;
    return sensors[sensorCount];
  } else {
    Serial.println("SensorManager: Maximum sensor count reached.");
    return nullptr;
  }
}

bool SensorManager::isWriteReady(uint8_t sensor_id) {
  return sensors[sensor_id]->isWriteReady();
}

// Write a value to the specified sensor
void SensorManager::write(uint8_t sensor_id, double value) {
  sensors[sensor_id]->data.write(value);
}
