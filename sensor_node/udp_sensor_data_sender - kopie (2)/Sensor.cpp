#include "esp32-hal.h"
#include "Sensor.h"

// Constructor
Sensor::Sensor(uint16_t sampleRate, uint16_t samplesPerPacket) {
  this->sampleRate = sampleRate;
  this->samplePeriod = 1000 / sampleRate;
  this->samplesPerPacket = samplesPerPacket;
}

void Sensor::clear(){
  data.clear();
}

byte* Sensor::getBuffer(){
  return data.getBuffer();
}

// Getter for sample rate
uint16_t Sensor::getSampleRate() {
  return sampleRate;
}

// Setter for sample rate
void Sensor::setSampleRate(uint16_t sampleRate) {
  this->sampleRate = sampleRate;
  this->samplePeriod = 1000 / sampleRate;
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

uint8_t Sensor::getSampleCount() {
  return data.getSampleCount();
}

// Write a new value to the SensorData buffer
void Sensor::write(double value) {
  updateLastWriteMillis();
  data.write(value);
}

uint32_t Sensor::getLastWriteMillis() {
  return lastWriteMillis;
}

uint32_t Sensor::updateLastWriteMillis() {
  this->lastWriteMillis = millis();
  return this->lastWriteMillis;
}

bool Sensor::isWriteReady() {
  return (millis() - lastWriteMillis) >= samplePeriod;
}

bool Sensor::isFlushReady(){
  return data.getSampleCount() >= samplesPerPacket;
}
