#include <functional>
#include "esp32-hal.h"
#include "Sensor.h"

// Constructor
Sensor::Sensor(double (*readCallback)(), float samplePeriodMs, uint16_t samplesPerPacket)
  : readCallback(readCallback),
    samplePeriodMs(samplePeriodMs),
    samplesPerPacket(samplesPerPacket),
    lastWriteMillis(0.) {}

byte* Sensor::getBuffer() {
  return data.getBuffer();
}

float Sensor::getSamplePeriodMs() {
  return samplePeriodMs;
}
void Sensor::setSamplePeriodMs(float samplePeriodMs) {
  this->samplePeriodMs = samplePeriodMs;
}


float Sensor::getSampleRate() {
  return 1000. / samplePeriodMs;
}


// Getter for samples per packet
uint16_t Sensor::getSamplesPerPacket() {
  return samplesPerPacket;
}

// Setter for samples per packet
void Sensor::setSamplesPerPacket(uint16_t samplesPerPacket) {
  this->samplesPerPacket = samplesPerPacket;
}

// Check if the sample count in the SensorData is at its maximum
bool Sensor::isSampleCountMax() {
  return data.getSampleCount() >= samplesPerPacket;
}

uint32_t Sensor::getLastWriteMillis() {
  return lastWriteMillis;
}

void Sensor::setLastWriteMillis(uint32_t write_time_millis) {
  this->lastWriteMillis = write_time_millis;
}

bool Sensor::isWriteReady() {
  return (millis() - lastWriteMillis) >= samplePeriodMs;
}

bool Sensor::isPacketReady() {
  return data.getSampleCount() >= samplesPerPacket;
}

void Sensor::readAndWrite() {
  uint32_t write_time = data.write(readCallback());
  setLastWriteMillis(write_time);
}
