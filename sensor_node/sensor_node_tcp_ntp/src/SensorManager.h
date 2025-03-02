#pragma once
#include "esp32-hal.h"    // Includes ESP32 hardware abstraction layer for low-level hardware operations
#include <Arduino.h>       // Includes standard Arduino functions and definitions
#include "Sensor.h"        // Includes the Sensor class declaration for managing individual sensor data

#define MAX_SENSOR_COUNT 256           // Maximum number of sensors supported by SensorManager
#define QUEUE_SIZE_PER_SENSOR 10       // Maximum size of the send buffer queue for each sensor

// Struct to hold sensor data for transmission
struct DataToSend {
    uint8_t sensorId;              // Unique identifier for the sensor
    byte dataBuffer[BUFFER_SIZE];  // Buffer containing sensor data (defined in SensorData)
    uint8_t sampleCount;           // Number of samples in the data buffer
};

// SensorManager class definition
class SensorManager {
   protected:
    Sensor* sensors[MAX_SENSOR_COUNT];  // Array to hold pointers to Sensor objects
    uint8_t sensorCount = 0;             // Number of sensors currently managed by the SensorManager

    // Method to handle reading and writing of sensor data
    void doReadAndWrites(); 

    // Checks if the sensor with the given ID is ready to write data
    bool isWriteReady(uint8_t sensorId); 

    // Clears data for all sensors managed by the SensorManager
    void clearAllSensors(); 

    // Clears the transmission buffer queue
    void clearSendBufferQueue(); 

   public:
    QueueHandle_t preSendBufferQueue;    // Queue handle to store sensor data before sending

    // Constructor for SensorManager class
    SensorManager(); 

    // Destructor for SensorManager class to clean up resources
    ~SensorManager(); 

    // Adds a new sensor to the SensorManager and returns a pointer to the added sensor
    Sensor* addSensor(double (*readCallback)()); 

    // Retrieves the sensor object by its ID
    Sensor* getSensor(uint8_t sensorId); 

    // Returns the current number of sensors managed by the SensorManager
    uint8_t getSensorCount(); 
};
