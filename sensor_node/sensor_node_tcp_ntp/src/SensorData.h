#pragma once
#include "esp32-hal.h"    // Includes hardware-specific definitions for ESP32
#include <Arduino.h>       // Includes standard Arduino functions and definitions

// Define maximum number of samples and sample size in bytes
#define MAX_SAMPLES 89
#define SAMPLE_SIZE 12     // Each sample takes 12 bytes (time + value)
constexpr uint16_t BUFFER_SIZE = MAX_SAMPLES * SAMPLE_SIZE;  // Total buffer size in bytes for all samples

// Sample structure to store each sample's time and value
struct Sample {
  uint32_t time;    // Timestamp of when the sample was taken (milliseconds)
  double value;     // The actual sensor reading value
};

// SensorData class to handle the storage and management of sensor samples
class SensorData {
private:
  byte buffer[BUFFER_SIZE];   // Buffer array to store sensor data as bytes (to save memory)
  uint16_t currentIndex = 0;  // Keeps track of the next position to write in the buffer
  uint8_t sampleCount = 0;    // Keeps track of how many samples have been written
public:
  // Returns a pointer to the data buffer
  byte* getBuffer();

  // Returns the current size of the buffer in bytes (based on the number of samples)
  uint16_t getCurrentByteSize();

  // Checks if the buffer is full (i.e., no space left to store more samples)
  bool bufferIsFull();

  // Retrieves a specific sample from the buffer by index
  Sample getSample(uint8_t index);

  // Returns the current count of samples in the buffer
  uint8_t getSampleCount();

  // Writes a new sample (with time and value) to the buffer
  void write(uint32_t _millis, double value);

  // Clears the buffer and resets the sample count and current index
  void clear();
};
