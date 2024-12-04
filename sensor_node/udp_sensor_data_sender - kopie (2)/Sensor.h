#ifndef SENSOR_H
#define SENSOR_H

#include <stdint.h>
#include "SensorData.h"
#include "esp32-hal.h"

class Sensor {
private:
  uint16_t sampleRate;
  uint16_t samplePeriod;
  uint16_t samplesPerPacket;
  uint32_t lastWriteMillis = millis();
  SensorData data;
public:
  Sensor(uint16_t sampleRate, uint16_t samplesPerPacket);
  void write(double value);
  void clear();
  byte* getBuffer();

  uint16_t getSampleRate();
  void setSampleRate(uint16_t sampleRate);
  uint16_t getSamplesPerPacket();
  void setSamplesPerPacket(uint16_t samplesPerPacket);
  bool isSampleCountMax();
  uint8_t getSampleCount();
  uint32_t getLastWriteMillis();
  uint32_t updateLastWriteMillis();
  bool isWriteReady();
  bool isFlushReady();
};

#endif