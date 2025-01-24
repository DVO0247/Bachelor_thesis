#include "TCPSensorManager.h"

void serverManagementTask(void* pvParameters) {
    TCPSensorManager* manager = static_cast<TCPSensorManager*>(pvParameters);  // Přetypování parametru
    while (true) {
        if (!manager->client.connected()) {
            manager->set_initialized(false);
            Serial.println("Connecting to " + String(manager->serverIP) + ":" + String(manager->serverPort));
            while (!manager->client.connected()) {
                manager->client.connect(manager->serverIP, manager->serverPort);
            }
            Serial.println("Connected");
            manager->sendInfo();
            manager->receiveParams();
        }

        manager->sendAndClearSamples();
        vTaskDelay(1);
    }
}

void TCPSensorManager::sendInfo() {
    Serial.println("Sending count and name");
    if (client.connected()) {
        // Create a temporary buffer to hold all data to send
        uint8_t dataBuffer[name.length() + 3 + sizeof(uint64_t)];  // Adjust the size as needed
        uint16_t index = 0;

        dataBuffer[index++] = STX;

        // Copy the name string length and its characters into the buffer
        for (uint16_t i = 0; i < name.length(); i++) {
            dataBuffer[index++] = name[i];
        }
        dataBuffer[index++] = ETX;
        // Add the sensor count
        dataBuffer[index++] = getSensorCount();

        memcpy(&dataBuffer[index], &unixTimeAtZero, sizeof(uint64_t));
        index += sizeof(uint64_t);
        client.write(dataBuffer, index);
    }
}

void TCPSensorManager::receiveParams() {
    byte received_bytes[getSensorCount() * SERVER_REQUEST_SIZE_PER_SENSOR];
    while (!client.available()) {
        if (!client.connected()) {
            return;
        }
    }
    client.read(received_bytes, getSensorCount() * SERVER_REQUEST_SIZE_PER_SENSOR);
    for (int i = 0; i < getSensorCount(); i++) {
        uint32_t samplePeriodMs;
        memcpy(&samplePeriodMs, &received_bytes[i * SERVER_REQUEST_SIZE_PER_SENSOR], sizeof(uint32_t));
        uint8_t samplesPerPacket = received_bytes[i * SERVER_REQUEST_SIZE_PER_SENSOR + 4];
        Serial.printf("Sensor id: %d\n", i);
        Serial.printf("Sample Period: %d ms\n", samplePeriodMs);
        Serial.printf("Samples per packet: %d\n", samplesPerPacket);

        sensors[i]->setSamplePeriodMillis(samplePeriodMs);
        sensors[i]->setSamplesPerPacket(samplesPerPacket);
    }
    set_initialized(true);
}

bool TCPSensorManager::is_initialized() {
    if (xSemaphoreTake(initialized_mutex, portMAX_DELAY)) {
        bool _initialized = this->initialized;
        xSemaphoreGive(initialized_mutex);
        return _initialized;
    } else {
        Serial.println("Error: Failed to take initialized_mutex semaphore\n");
        return false;
    }
}

void TCPSensorManager::set_initialized(bool state) {
    if (xSemaphoreTake(initialized_mutex, portMAX_DELAY)) {
        initialized = state;
        xSemaphoreGive(initialized_mutex);
    } else {
        Serial.println("Error: Failed to take initialized_mutex semaphore\n");
    }
}

void TCPSensorManager::sendAndClearSamples() {
    DataToSend dataToSend;
    while (uxQueueMessagesWaiting(sendBufferQueue) > 0) {
        if (xQueueReceive(sendBufferQueue, &dataToSend, portMAX_DELAY) == pdPASS) {
            uint16_t dataSize = dataToSend.sampleCount * SAMPLE_SIZE;
            uint8_t sendBuffer[1 + dataSize];
            // Serial.println(String(dataToSend.sensorId)+" "+ String(dataToSend.sampleCount));
            uint16_t index = 0;
            sendBuffer[index++] = dataToSend.sensorId;
            memcpy(&sendBuffer[index], dataToSend.dataBuffer, dataSize);
            index += dataSize;
            client.write(sendBuffer, index);
        }
    }
}

TCPSensorManager::TCPSensorManager()
    : SensorManager() {}

void TCPSensorManager::begin(const char* serverIP, uint16_t serverPort, String name, const char* ntpServer2, const char* ntpServer3) {
    this->serverIP = serverIP;
    this->serverPort = serverPort;
    this->name = name;
    unixTimeAtZero = getUnixTimeAtZero(serverIP, DEFAULT_NTP_SERVER_2, DEFAULT_NTP_SERVER_3);
    initialized_mutex = xSemaphoreCreateMutex();
    if (initialized_mutex == NULL) {
        Serial.println("Mutex creation failed for SensorManager");
    }
    set_initialized(false);
    this->sendBufferQueue = xQueueCreate(getSensorCount() * QUEUE_SIZE_PER_SENSOR, sizeof(DataToSend));
    xTaskCreatePinnedToCore(serverManagementTask, "ServerManagement", 10000, this, 1, NULL, 1);
    // client.setNoDelay(true);
}

void TCPSensorManager::processData() {
    if (client.connected()) {
        doReadAndWrites();
    } else {
        clearAllSensors();
        clearSendBufferQueue();
        while(!(client.connected() && is_initialized()));
    }
}
