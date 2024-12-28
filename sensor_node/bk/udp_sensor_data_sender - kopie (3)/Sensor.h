#ifndef SENSOR_H
#define SENSOR_H

#include <stdint.h>
#include "SensorData.h"
#include "esp32-hal.h"

class Sensor {
private:
  float samplePeriodMs;
  uint16_t samplesPerPacket; // max 121 TODO: uint8_t 
  uint32_t lastWriteMillis;
  double (*readCallback)();
public:
  SensorData data;
  Sensor(double (*readCallback)(), float samplePeriodMs, uint16_t samplesPerPacket);
  byte* getBuffer();
  float getSamplePeriodMs();
  void setSamplePeriodMs(float samplePeriodMs);
  float getSampleRate();
  uint16_t getSamplesPerPacket();
  void setSamplesPerPacket(uint16_t samplesPerPacket);
  bool isSampleCountMax();
  uint32_t getLastWriteMillis();
  void setLastWriteMillis(uint32_t write_time_millis);
  bool isWriteReady();
  bool isPacketReady();
  void readAndWrite();
};

#endif