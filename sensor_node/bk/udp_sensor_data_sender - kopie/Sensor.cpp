#include "esp32-hal.h"
#include "Sensor.h"

// Constructor
Sensor::Sensor(uint16_t sampleRate, uint16_t samplesPerPacket)
    : sampleRate(sampleRate), samplesPerPacket(samplesPerPacket), lastSent(millis()), data() {}

// Getter for sample rate
uint16_t Sensor::getSampleRate() {
    return sampleRate;
}

// Setter for sample rate
void Sensor::setSampleRate(uint16_t sampleRate) {
    this->sampleRate = sampleRate;
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

// Write a new value to the SensorData buffer
void Sensor::write(double value) {
    data.write(value);
}

uint32_t Sensor::getLastWriteMillis(){
  return lastWriteMillis;
}
uint32_t Sensor::updateLastWriteMillis(){
  this->lastWriteMillis = millis();
  return this->lastWriteMillis;
}
