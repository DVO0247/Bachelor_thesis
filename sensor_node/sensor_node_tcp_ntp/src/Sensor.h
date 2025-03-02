#pragma once
#include "esp32-hal.h"     // Includes hardware-specific definitions for ESP32
#include <Arduino.h>        // Includes standard Arduino functions and definitions
#include "SensorData.h"      // Includes the custom SensorData class for storing sensor data

// Sensor class handles sensor data reading, storing, and transmission.
class Sensor {
private:
  uint32_t samplePeriodMillis;   // Time between each sensor reading in milliseconds
  uint8_t samplesPerMessage;     // Maximum number of samples to be included in a single message
  uint32_t lastWriteMillis;      // Timestamp for the last time data was written
  double (*readCallback)();      // Pointer to the callback function for reading sensor data
  SemaphoreHandle_t parameters_mutex;  // Mutex for synchronizing access to shared parameters
  
public:
  SensorData data;               // Object to store the sensor data

  // Constructor to initialize the sensor object
  // readCallback: function pointer to read data from the sensor
  // samplePeriodMillis: time period in ms between sensor samples
  // samplesPerMessage: maximum samples to be included per message
  Sensor(double (*readCallback)(), uint32_t samplePeriodMillis, uint8_t samplesPerMessage);

  // Destructor to clean up the sensor object
  ~Sensor();

  // Returns the pointer to the buffer for the sensor data
  byte* getBuffer();

  // Gets the sample period in milliseconds
  uint32_t getSamplePeriodMillis();

  // Sets the sample period in milliseconds
  void setSamplePeriodMillis(uint32_t samplePeriodMillis);

  // Returns the number of samples per message
  uint8_t getSamplesPerMessage();

  // Sets the maximum number of samples per message
  void setSamplesPerMessage(uint8_t samplesPerMessage);

  // Checks if the sample count has reached its maximum limit
  bool isSampleCountAtMax();

  // Gets the timestamp of the last write operation
  uint32_t getLastWriteMillis();

  // Sets the timestamp of the last write operation
  void setLastWriteMillis(uint32_t writeMillis);

  // Checks if the sensor is ready to write based on the current time
  // Default is current time using millis()
  bool isWriteReady(uint32_t _millis = millis());

  // Checks if the message with sensor data is ready to be sent
  bool isMessageReady();

  // Reads data from the sensor and writes it if ready, based on the provided timestamp
  void readAndWrite(uint32_t writeMillis = millis());
};
