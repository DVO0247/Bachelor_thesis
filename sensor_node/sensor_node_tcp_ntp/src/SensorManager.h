#pragma once
#include "esp32-hal.h"
#include <Arduino.h>
#include "Sensor.h"

#define MAX_SENSOR_COUNT 256
#define QUEUE_SIZE_PER_SENSOR 10

struct DataToSend {
    uint8_t sensorId;              // ID senzoru
    byte dataBuffer[BUFFER_SIZE];  // Ukazatel na buffer
    uint8_t sampleCount;           // Velikost dat v bufferu
};

class SensorManager {
   protected:
    Sensor* sensors[MAX_SENSOR_COUNT];
    uint8_t sensorCount = 0;
    void doReadAndWrites();
    // TODO: make something private and protected
   public:
    QueueHandle_t preSendBufferQueue;
    SensorManager();
    ~SensorManager();
    Sensor* addSensor(double (*callback)());
    Sensor* getSensor(uint8_t sensorId);
    uint8_t getSensorCount();
    bool isWriteReady(uint8_t sensorId);
    void clearAllSensors();
    void clearSendBufferQueue();
};
