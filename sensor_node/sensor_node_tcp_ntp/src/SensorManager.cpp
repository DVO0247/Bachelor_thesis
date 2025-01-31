#include "SensorManager.h"

void SensorManager::doReadAndWrites() {
    for (uint8_t i = 0; i < sensorCount; i++) {
        int64_t _millis = millis();
        if (sensors[i]->isWriteReady(_millis)) {
            sensors[i]->readAndWrite(_millis);
            if (sensors[i]->isPacketReady()) {
                DataToSend dataToSend;
                dataToSend.sensorId = i;
                dataToSend.sampleCount = sensors[i]->data.getSampleCount();
                memcpy(dataToSend.dataBuffer, sensors[i]->data.getBuffer(), sensors[i]->data.getCurrentByteSize());

                xQueueSend(sendBufferQueue, &dataToSend, portMAX_DELAY);
                sensors[i]->data.clear();
            }
        }
    }
}

SensorManager::SensorManager() {}

SensorManager::~SensorManager() {
    for (uint8_t i = 0; i < sensorCount; i++) {
        delete sensors[i];  // Uvolnění dynamicky alokovaných objektů
    }
}

Sensor* SensorManager::getSensor(uint8_t sensorId) {
    if (sensorId < sensorCount) {
        return sensors[sensorId];
    } else {
        Serial.println("SensorManager: Sensor not found");
        return nullptr;
    }
}

uint8_t SensorManager::getSensorCount() {
    return sensorCount;
}

Sensor* SensorManager::addSensor(double (*callback)()) {
    if (sensorCount < MAX_SENSOR_COUNT) {
        sensors[sensorCount] = new Sensor(callback, UINT32_MAX, 1);
        sensorCount++;
        return sensors[sensorCount - 1];
    } else {
        Serial.println("SensorManager: Maximum sensor count reached.");
        return nullptr;
    }
}

bool SensorManager::isWriteReady(uint8_t sensorId) {
    return sensors[sensorId]->isWriteReady();
}

void SensorManager::clearAllSensors() {
    for (uint8_t i = 0; i < sensorCount; i++) {
        sensors[i]->data.clear();
    }
}

void SensorManager::clearSendBufferQueue() {
    void* dummy;
    while (xQueueReceive(sendBufferQueue, &dummy, 0) == pdTRUE);
}
