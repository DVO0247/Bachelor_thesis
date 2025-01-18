#pragma once
#include <Arduino.h>
#include <stdint.h>

#define SAMPLE_SIZE 12    //bytes
#define BUFFER_SIZE 1452  // safe UDP payload size

struct Sample {
  uint32_t time;
  double value;
};

class SensorData {
private:
  byte buffer[BUFFER_SIZE];   // Buffer pro ukládání dat jako byte array
  uint16_t currentIndex = 0;  // Aktuální index pro zápis do bufferu
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
