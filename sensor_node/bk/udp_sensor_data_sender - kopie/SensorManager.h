#ifndef SENSORMANAGER_H
#define SENSORMANAGER_H

#include <stdint.h>
#include "Sensor.h"

#define MAX_SENSOR_COUNT 254

class SensorManager {
public:
  Sensor* sensors[MAX_SENSOR_COUNT];
  uint8_t sensorCount = 0;
  Sensor* getSensor(uint8_t sensor_id);
  // TODO: make something private and protected
  SensorManager();
  ~SensorManager();
  void addSensor(uint16_t sampleRate, uint16_t samplesPerPacket);
  uint16_t getSampleRate(uint8_t sensor_id);
  void setSampleRate(uint8_t sensor_id,uint16_t sampleRate);
  uint16_t getSamplesPerPacket(uint8_t sensor_id);
  void setSamplesPerPacket(uint8_t sensor_id, uint16_t samplesPerPacket);
  void write(uint8_t sensor_id, double value);
  uint32_t getLastWriteMillis(uint8_t sensor_id);
  uint32_t updateLastWriteMillis(uint8_t sensor_id);
};

#endif