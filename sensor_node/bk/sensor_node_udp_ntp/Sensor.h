#pragma once
#include <stdint.h>
#include "SensorData.h"
#include "esp32-hal.h"

class Sensor {
private:
  uint32_t samplePeriodMillis;
  uint8_t samplesPerPacket; // max 89 (TCP) or 121 (UDP)
  uint32_t lastWriteMillis;
  double (*readCallback)();
public:
  SemaphoreHandle_t mutex;
  SensorData data;
  Sensor(double (*readCallback)(), uint32_t samplePeriodMillis, uint8_t samplesPerPacket);
  ~Sensor();
  byte* getBuffer();
  uint32_t getSamplePeriodMillis();
  void setSamplePeriodMillis(uint32_t samplePeriodMillis);
  uint8_t getSamplesPerPacket();
  void setSamplesPerPacket(uint8_t samplesPerPacket);
  bool isSampleCountMax(); // TODO: rename to ...AtMax
  uint32_t getLastWriteMillis();
  void setLastWriteMillis(uint32_t writeMillis);
  bool isWriteReady(uint32_t _millis = millis());
  bool isPacketReady();
  void readAndWrite(uint32_t writeMillis = millis());
};
