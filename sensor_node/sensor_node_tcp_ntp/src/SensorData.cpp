#include "SensorData.h"

byte* SensorData::getBuffer() {
  return buffer;
}

uint16_t SensorData::getCurrentByteSize() {
  return currentIndex;
}

bool SensorData::bufferIsFull() {
  return currentIndex >= BUFFER_SIZE;
}

Sample SensorData::getSample(uint8_t index) {
  index *= SAMPLE_SIZE;
  Sample sample;

  memcpy(&sample.time, &buffer[index], sizeof(uint32_t));

  memcpy(&sample.value, &buffer[index + sizeof(uint32_t)], sizeof(double));

  return sample;
}

uint8_t SensorData::getSampleCount() {
  return sampleCount;
}

void SensorData::write(uint32_t _millis, double value) {
  if (currentIndex + sizeof(uint32_t) + sizeof(double) <= BUFFER_SIZE) {
    uint64_t timestamp = _millis;

    // Copy timestamp to buffer
    memcpy(&buffer[currentIndex], &timestamp, sizeof(uint32_t));
    currentIndex += sizeof(uint32_t);

    // Copy value to buffer
    memcpy(&buffer[currentIndex], &value, sizeof(double));
    currentIndex += sizeof(double);
    sampleCount++;
  } else {
    Serial.println("Buffer is full, cannot add more data");
  }
}

void SensorData::clear() {
  currentIndex = 0;
  sampleCount = 0;
}
