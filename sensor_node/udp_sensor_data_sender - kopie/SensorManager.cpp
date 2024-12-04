#include "SensorManager.h"

Sensor* SensorManager::getSensor(uint8_t sensor_id) {
  if (sensor_id < sensorCount) {
    return sensors[sensor_id]
  } else {
    Serial.println("SensorManager: Sensor not found");
    return nullptr;
  }

  // Constructor
  SensorManager::SensorManager() {}

  // Destructor
  SensorManager::~SensorManager() {
    for (uint8_t i = 0; i < sensorCount; i++) {
      delete sensors[i];  // Uvolnění dynamicky alokovaných objektů
    }
  }

  void SensorManager::addSensor(uint16_t sampleRate, uint16_t samplesPerPacket) {
    if (sensorCount < MAX_SENSOR_COUNT) {
      sensors[sensorCount] = new Sensor(sampleRate, samplesPerPacket);
      sensorCount++;
    } else {
      Serial.println("SensorManager: Maximum sensor count reached.");
    }
  }

  uint16_t SensorManager::getSampleRate(uint8_t sensor_id) {
    return getSensor(sensor_id)->getSampleRate();
  }
  void SensorManager::setSampleRate(uint8_t sensor_id, uint16_t sampleRate) {
    getSensor(sensor_id)->setSampleRate(sampleRate);
  }
  uint16_t SensorManager::getSamplesPerPacket(uint8_t sensor_id) {
    return getSensor(sensor_id)->getSamplesPerPacket();
  }
  void SensorManager::setSamplesPerPacket(uint8_t sensor_id, uint16_t samplesPerPacket) {
    getSensor(sensor_id)->setSamplesPerPacket(samplesPerPacket);
  }

  // Write a value to the specified sensor
  void SensorManager::write(uint8_t sensor_id, double value) {
    getSensor(sensor_id)->write(value);
  }

  uint32_t SensorManager::getLastWriteMillis(uint8_t sensor_id) {
    return getSensor(sensor_id)->getLastWriteMillis();
  }
  uint32_t SensorManager::updateLastWriteMillis(uint8_t sensor_id) {
    return getSensor(sensor_id)->updateLastWriteMillis();
  }
