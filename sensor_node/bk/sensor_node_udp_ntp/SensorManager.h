#pragma once
#include <stdint.h>
#include "Sensor.h"

#define MAX_SENSOR_COUNT 256

struct BufferData {
  uint8_t sensorId;   // ID senzoru
  byte buffer[BUFFER_SIZE];       // Ukazatel na buffer
  uint8_t sampleCount;  // Velikost dat v bufferu
};

class SensorManager {
protected:
  Sensor* sensors[MAX_SENSOR_COUNT];
  uint8_t sensorCount = 0;

  // TODO: make something private and protected
public:
  QueueHandle_t bufferQueue;
  SensorManager();
  ~SensorManager();
  void doReadAndWrites();
  Sensor* addSensor(double (*callback)());
  Sensor* getSensor(uint8_t sensorId);
  uint8_t getSensorCount();
  bool isWriteReady(uint8_t sensorId);
  void resetAllSensors();
};
