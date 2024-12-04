#ifndef SENSOR_H
#define SENSOR_H

#include <stdint.h>
#include "SensorData.h"
#include "esp32-hal.h"

class Sensor {
private:
  uint16_t sampleRate;
  uint16_t samplesPerPacket;
  uint32_t lastWriteMillis = millis();
  SensorData data;

public:
  Sensor(uint16_t sampleRate, uint16_t samplesPerPacket);
  uint16_t getSampleRate();
  void setSampleRate(uint16_t sampleRate);
  uint16_t getSamplesPerPacket();
  void setSamplesPerPacket(uint16_t samplesPerPacket);
  bool isSampleCountMax();
  void write(double value);
  uint32_t getLastWriteMillis();
  uint32_t updateLastWriteMillis();
};

#endif