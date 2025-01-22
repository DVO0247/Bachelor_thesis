#include "freertos/projdefs.h"
#include "esp_timer.h"
#include "esp32-hal.h"
#include <iterator>
#include <stdint.h>
#include "WString.h"
#include "HardwareSerial.h"
#include <sys/types.h>
#include "UDPSensorManager.h"


void doReadAndWritesTask(void* pvParameters) {
  UDPSensorManager* manager = static_cast<UDPSensorManager*>(pvParameters);  // Přetypování parametru
  while (true) {
    manager->doReadAndWrites();
    vTaskDelay(1);  // Malá prodleva pro snížení zatížení CPU
  }
}

// Task pro správu serverových operací
void serverManagementTask(void* pvParameters) {
  UDPSensorManager* manager = static_cast<UDPSensorManager*>(pvParameters);  // Přetypování parametru
  while (true) {
    manager->serverReply();

    if (manager->isKeepAliveReady()) {
      manager->sendKeepAlive();
    }

    manager->sendAndClearSamples();
    vTaskDelay(1);  
  }
}


bool UDPSensorManager::isKeepAliveReady() {
  return keepAliveEnabled && millis() - keepAliveLastSent >= KEEP_ALIVE_PERIOD_MS;
}

void UDPSensorManager::sendKeepAlive() {
  Serial.println("Sending keep alive");
  udp.beginPacket(serverIP, serverPort);
  udp.write(MessageTypeByte::Client::KEEP_ALIVE);
  udp.endPacket();
  keepAliveLastSent = millis();
}

void UDPSensorManager::sendInfo() {
  uint8_t nameLength = name.length();
  Serial.println("Sending info");
  udp.beginPacket(serverIP, serverPort);
  udp.write(MessageTypeByte::Client::INFO);
  udp.write(nameLength);
  udp.print(name);
  udp.write(sensorCount);
  udp.write(reinterpret_cast<const uint8_t*>(&unixTimeAtZero), sizeof(uint64_t));
  udp.endPacket();
  keepAliveLastSent = millis();
}

void UDPSensorManager::sendACK(uint8_t sensorId) {
  Serial.println("Sending ACK for sensor ID: " + String(sensorId));
  udp.beginPacket(serverIP, serverPort);
  udp.write(MessageTypeByte::Client::ACK);
  udp.write(sensorId);
  udp.endPacket();
  keepAliveLastSent = millis();
}

void UDPSensorManager::serverReply() {
  int packetSize = udp.parsePacket();  // Zkontroluje, zda je k dispozici příchozí paket
  if (packetSize > 0) {
    byte received_bytes[packetSize];
    udp.read(received_bytes, packetSize);  // Přečte 5 bajtu do bufferu
    //Serial.println(String(received_bytes[0]) + String(received_bytes[0]));

    if (received_bytes[0] == MessageTypeByte::Server::REQUEST_INFO) {
      sendInfo();
    } else if (received_bytes[0] == MessageTypeByte::Server::SET_SENSOR_PARAMETERS && packetSize == SERVER_SET_SENSOR_PARAMETERS_SIZE) {
      uint8_t index = 1;
      uint8_t sensorId = received_bytes[index++];

      uint32_t samplePeriodMs;
      memcpy(&samplePeriodMs, &received_bytes[index], sizeof(uint32_t));
      index += sizeof(uint32_t);
      uint8_t samplesPerPacket = received_bytes[index];
      Serial.printf("Sensor id: %d\n", sensorId);
      Serial.printf("Sample period: %d ms\n", samplePeriodMs);
      Serial.printf("Samples per packet: %d\n", samplesPerPacket);
      if (xSemaphoreTake(sensors[sensorId]->mutex, portMAX_DELAY)) {
        sensors[sensorId]->setSamplePeriodMillis(samplePeriodMs);
        sensors[sensorId]->setSamplesPerPacket(samplesPerPacket);
        xSemaphoreGive(sensors[sensorId]->mutex);
      }

      sendACK(sensorId);
      bool _keepAliveEnabled = false;
      for (uint8_t i = 0; i < getSensorCount(); i++) {
        if (samplePeriodMs * samplesPerPacket > KEEP_ALIVE_PERIOD_MS) {
          _keepAliveEnabled = true;
          break;
        }
      }
      this->keepAliveEnabled = _keepAliveEnabled;
      keepAliveLastSent = millis();
      Serial.println("Keep Alive: " + String(keepAliveEnabled));
      resetAllSensors();
    }
  }
}

void UDPSensorManager::sendAndClearSamples() {
  BufferData data;
  while (uxQueueMessagesWaiting(bufferQueue) > 0) {
    if (xQueueReceive(bufferQueue, &data, portMAX_DELAY) == pdPASS) {
      udp.beginPacket(serverIP, serverPort);
      udp.write(MessageTypeByte::Client::SENSOR_SAMPLES);
      udp.write(data.sensorId);
      udp.write(data.sampleCount);
      udp.write(data.buffer, data.sampleCount*SAMPLE_SIZE);
      udp.endPacket();
    }
  }
}

UDPSensorManager::UDPSensorManager()
  : SensorManager(), keepAliveEnabled(true) {}

void UDPSensorManager::begin(const char* serverIP, uint16_t serverPort, String name, const char* ntpServer2, const char* ntpServer3) {
  this->serverIP = serverIP;
  this->serverPort = serverPort;
  this->name = name;
  this->unixTimeAtZero = getUnixTimeAtZero(serverIP, ntpServer2, ntpServer3);
  this->keepAliveLastSent = millis();
  sendInfo();
  //xTaskCreatePinnedToCore(doReadAndWritesTask, "DoReadAndWrites", 10000, this, 1, NULL, 0);
  bufferQueue = xQueueCreate(QUEUE_SIZE, sizeof(BufferData));
  xTaskCreatePinnedToCore(serverManagementTask, "ServerManagement", 10000, this, 1, NULL, 1);
}

void UDPSensorManager::processData() {
  doReadAndWrites();
}
