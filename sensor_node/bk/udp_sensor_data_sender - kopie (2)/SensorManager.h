#ifndef SENSORMANAGER_H
#define SENSORMANAGER_H

#include <stdint.h>
#include "Sensor.h"

#define MAX_SENSOR_COUNT 254
#define DEFAULT_SAMPLE_RATE 100
#define DEFAULT_SAMPLES_PER_PACKET 100

class SensorManager {
protected:
  Sensor* sensors[MAX_SENSOR_COUNT];
  uint8_t sensorCount = 0;
  // TODO: make something private and protected
public:
  SensorManager(uint8_t sensor_count = 0);
  ~SensorManager();
  Sensor* addSensor(uint16_t sampleRate = DEFAULT_SAMPLE_RATE, uint16_t samplesPerPacket = DEFAULT_SAMPLES_PER_PACKET);
  Sensor* getSensor(uint8_t sensor_id);
  bool isWriteReady(uint8_t sensor_id);
  void write(uint8_t sensor_id, double value);
};

#endif