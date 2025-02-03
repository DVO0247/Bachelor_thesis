#include <functional>
#include "esp32-hal.h"
#include "Sensor.h"

// Constructor
Sensor::Sensor(double (*readCallback)(), uint32_t samplePeriodMillis, uint8_t samplesPerPacket)
  : readCallback(readCallback),
    samplePeriodMillis(samplePeriodMillis),
    samplesPerPacket(samplesPerPacket),
    lastWriteMillis(0) {
  mutex = xSemaphoreCreateMutex();
  if (mutex == NULL) {
    Serial.println("Mutex creation failed for Sensor");
  }
}

Sensor::~Sensor() {
  if (mutex != NULL) {
    vSemaphoreDelete(mutex);
  }
}

byte* Sensor::getBuffer() {
  return data.getBuffer();
}

uint32_t Sensor::getSamplePeriodMillis() {
  return samplePeriodMillis;
}
void Sensor::setSamplePeriodMillis(uint32_t samplePeriodMillis) {
  this->samplePeriodMillis = samplePeriodMillis;
}

// Getter for samples per packet
uint8_t Sensor::getSamplesPerPacket() {
  return samplesPerPacket;
}

// Setter for samples per packet
void Sensor::setSamplesPerPacket(uint8_t samplesPerPacket) {
  this->samplesPerPacket = samplesPerPacket;
}

// Check if the sample count in the SensorData is at its maximum
bool Sensor::isSampleCountMax() {
  return data.getSampleCount() >= samplesPerPacket;
}

uint32_t Sensor::getLastWriteMillis() {
  return lastWriteMillis;
}

void Sensor::setLastWriteMillis(uint32_t writeMillis) {
  this->lastWriteMillis = writeMillis;
}

bool Sensor::isWriteReady(uint32_t _millis) {
  return _millis - lastWriteMillis >= samplePeriodMillis;
}

bool Sensor::isPacketReady() {
  return data.getSampleCount() >= samplesPerPacket;
}

void Sensor::readAndWrite(uint32_t writeMillis) {
  data.write(writeMillis, readCallback());
  setLastWriteMillis(writeMillis);
}
