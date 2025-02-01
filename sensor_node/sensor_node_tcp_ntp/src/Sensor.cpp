#include "Sensor.h"

Sensor::Sensor(double (*readCallback)(), uint32_t samplePeriodMillis, uint8_t samplesPerMessage)
    : readCallback(readCallback),
      samplePeriodMillis(samplePeriodMillis),
      samplesPerMessage(samplesPerMessage),
      lastWriteMillis(0) {
    parameters_mutex = xSemaphoreCreateMutex();
    if (parameters_mutex == NULL) {
        Serial.println("Mutex creation failed for Sensor");
    }
}

Sensor::~Sensor() {
    if (parameters_mutex != NULL) {
        vSemaphoreDelete(parameters_mutex);
    }
}

byte* Sensor::getBuffer() {
    return data.getBuffer();
}

uint32_t Sensor::getSamplePeriodMillis() {
    if (xSemaphoreTake(parameters_mutex, portMAX_DELAY)) {
        uint32_t _samplePeriodMillis = this->samplePeriodMillis;
        xSemaphoreGive(parameters_mutex);
        return _samplePeriodMillis;
    } else {
        Serial.println("Error: Failed to take parameters_mutex semaphore\n");
        return 0;
    }
}
void Sensor::setSamplePeriodMillis(uint32_t samplePeriodMillis) {
    if (xSemaphoreTake(parameters_mutex, portMAX_DELAY)) {
        this->samplePeriodMillis = samplePeriodMillis;
        xSemaphoreGive(parameters_mutex);
    }
    else {
        Serial.println("Error: Failed to take parameters_mutex semaphore\n");
    }
}

// Getter for samples per message
uint8_t Sensor::getSamplesPerMessage() {
    if (xSemaphoreTake(parameters_mutex, portMAX_DELAY)) {
        uint8_t _samplesPerMessage = this->samplesPerMessage;
        xSemaphoreGive(parameters_mutex);
        return _samplesPerMessage;
    } else {
        Serial.println("Error: Failed to take parameters_mutex semaphore\n");
        return 0;
    }
}

// Setter for samples per message
void Sensor::setSamplesPerMessage(uint8_t samplesPerMessage) {
    if (xSemaphoreTake(parameters_mutex, portMAX_DELAY)) {
        this->samplesPerMessage = samplesPerMessage;
        xSemaphoreGive(parameters_mutex);
    }else {
        Serial.println("Error: Failed to take parameters_mutex semaphore\n");
    }
}

// Check if the sample count in the SensorData is at its maximum
bool Sensor::isSampleCountMax() {
    return data.getSampleCount() >= getSamplesPerMessage();
}

uint32_t Sensor::getLastWriteMillis() {
    return lastWriteMillis;
}

void Sensor::setLastWriteMillis(uint32_t writeMillis) {
    if (xSemaphoreTake(parameters_mutex, portMAX_DELAY)) {
        this->lastWriteMillis = writeMillis;
        xSemaphoreGive(parameters_mutex);
    }else {
        Serial.println("Error: Failed to take parameters_mutex semaphore\n");
    }
}

bool Sensor::isWriteReady(uint32_t _millis) {
    return _millis - getLastWriteMillis() >= getSamplePeriodMillis();
}

bool Sensor::isMessageReady() {
    return data.getSampleCount() >= getSamplesPerMessage();
}

void Sensor::readAndWrite(uint32_t writeMillis) {
    data.write(writeMillis, readCallback());
    setLastWriteMillis(writeMillis);
}
