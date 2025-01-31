#pragma once
#include "esp32-hal.h"
#include <Arduino.h>

#define MAX_SAMPLES 89

#define SAMPLE_SIZE 12 // bytes
constexpr uint16_t BUFFER_SIZE = MAX_SAMPLES*SAMPLE_SIZE; // bytes

struct Sample {
  uint32_t time;
  double value;
};

class SensorData {
private:
  byte buffer[BUFFER_SIZE];   // Buffer for storing data as a byte array
  uint16_t currentIndex = 0;  // Current index for writing to the buffer
  uint8_t sampleCount = 0;
public:
  byte* getBuffer();
  uint16_t getCurrentByteSize();
  bool bufferIsFull();

  Sample getSample(uint8_t index);
  uint8_t getSampleCount();
  void write(uint32_t _millis, double value);

  void clear();
};
