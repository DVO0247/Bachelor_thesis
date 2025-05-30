#include "TCPSensorManager.h"

void serverManagementTask(void* pvParameters) {
    TCPSensorManager* manager = static_cast<TCPSensorManager*>(pvParameters);
    while (true) {
        manager->serverManage();
        vTaskDelay(1);
    }
}

void TCPSensorManager::sendInfo() {
    Serial.println("Sending info message");
    if (client.connected()) {
        // Create a temporary buffer to hold all data to send
        uint8_t dataBuffer[name.length() + 3 + sizeof(uint64_t)];
        uint16_t index = 0;

        dataBuffer[index++] = SENSOR_NODE_TYPE;

        // Copy the name into the buffer
        for (uint16_t i = 0; i < name.length(); i++) {
            dataBuffer[index++] = name[i];
        }
        dataBuffer[index++] = ASCII_ETX;
        // Add the sensor count
        dataBuffer[index++] = getSensorCount();

        memcpy(&dataBuffer[index], &unixTimeOffset, sizeof(uint64_t));
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
        uint8_t samplesPerMessage = received_bytes[i * SERVER_REQUEST_SIZE_PER_SENSOR + sizeof(uint32_t)];
        Serial.println("Set params received");
        Serial.printf("Sensor id: %d\n", i);
        Serial.printf("Sample period: %d ms\n", samplePeriodMs);
        
        if (samplesPerMessage > MAX_SAMPLES){
            Serial.printf("Max samples per message exceted! - %d > %d (received > max)\n", samplesPerMessage, MAX_SAMPLES);
            samplesPerMessage = MAX_SAMPLES;
        }
        Serial.printf("Samples per message: %d\n", samplesPerMessage);

        sensors[i]->setSamplePeriodMillis(samplePeriodMs);
        sensors[i]->setSamplesPerMessage(samplesPerMessage);
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
    while (uxQueueMessagesWaiting(preSendBufferQueue) > 0) {
        if (xQueueReceive(preSendBufferQueue, &dataToSend, portMAX_DELAY) == pdPASS) {
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
    unixTimeOffset = getUnixTimeOffset(serverIP, DEFAULT_NTP_SERVER_2, DEFAULT_NTP_SERVER_3);
    initialized_mutex = xSemaphoreCreateMutex();
    if (initialized_mutex == NULL) {
        Serial.println("Mutex creation failed for SensorManager");
    }
    set_initialized(false);
    this->preSendBufferQueue = xQueueCreate(getSensorCount() * QUEUE_SIZE_PER_SENSOR, sizeof(DataToSend));
    xTaskCreatePinnedToCore(serverManagementTask, "ServerManagement", 10000, this, 1, NULL, 1);
    // client.setNoDelay(true);
}   

void TCPSensorManager::begin(APConfig* apConfig, const char* ntpServer2, const char* ntpServer3) {
    begin(apConfig->getServerIP(), apConfig->getServerPort(), apConfig->getName(), ntpServer2, ntpServer3);
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

void TCPSensorManager::serverManage() {
    if (!client.connected()) {
            set_initialized(false);
            Serial.println("Connecting to " + String(serverIP) + ":" + String(serverPort));
            while (!client.connected()) {
                client.connect(serverIP, serverPort);
            }
            Serial.println("Connected");
            sendInfo();
            receiveParams();
        }

        sendAndClearSamples();
}