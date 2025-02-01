#pragma once
#include "esp32-hal.h"
#include <Arduino.h>
#include "SensorData.h"

//#include <functional>

class Sensor {
private:
  uint32_t samplePeriodMillis;
  uint8_t samplesPerMessage; // max 89 (TCP) or 121 (UDP)
  uint32_t lastWriteMillis;
  double (*readCallback)();
  SemaphoreHandle_t parameters_mutex;
public:
  SensorData data;
  Sensor(double (*readCallback)(), uint32_t samplePeriodMillis, uint8_t samplesPerMessage);
  ~Sensor();
  byte* getBuffer(); // TODO: make this const
  uint32_t getSamplePeriodMillis();
  void setSamplePeriodMillis(uint32_t samplePeriodMillis);
  uint8_t getSamplesPerMessage();
  void setSamplesPerMessage(uint8_t samplesPerMessage);
  bool isSampleCountMax(); // TODO: rename to ...AtMax
  uint32_t getLastWriteMillis();
  void setLastWriteMillis(uint32_t writeMillis);
  bool isWriteReady(uint32_t _millis = millis());
  bool isMessageReady();
  void readAndWrite(uint32_t writeMillis = millis());
};
