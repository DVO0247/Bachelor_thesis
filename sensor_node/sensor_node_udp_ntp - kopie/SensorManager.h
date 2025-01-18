#pragma once
#include <stdint.h>
#include "Sensor.h"

#define MAX_SENSOR_COUNT 255

class SensorManager {
protected:
  Sensor* sensors[MAX_SENSOR_COUNT];
  uint8_t sensorCount = 0;
  void doReadAndWrites();
  // TODO: make something private and protected
public:
  SensorManager();
  ~SensorManager();
  Sensor* addSensor(double (*callback)());
  Sensor* getSensor(uint8_t sensorId);
  uint8_t getSensorCount();
  bool isWriteReady(uint8_t sensorId);
  void resetAllSensors();
};
