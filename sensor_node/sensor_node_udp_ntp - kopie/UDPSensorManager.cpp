#include "esp_timer.h"
#include "esp32-hal.h"
#include <iterator>
#include <stdint.h>
#include "WString.h"
#include "HardwareSerial.h"
#include <sys/types.h>
#include "UDPSensorManager.h"

TaskHandle_t serverReplyTaskHandle = NULL;

void serverReplyTask(void* parameter) {
  UDPSensorManager* udpManager = static_cast<UDPSensorManager*>(parameter);

  while (true) {
    udpManager->serverReply();
    if (udpManager->isKeepAliveReady()) {
      udpManager->sendKeepAlive();
    }
    vTaskDelay(pdMS_TO_TICKS(500));  // 500 ms delay
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
      sensors[sensorId]->setSamplePeriodMillis(samplePeriodMs);
      sensors[sensorId]->setSamplesPerPacket(samplesPerPacket);

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
  int64_t end;
  int64_t start;
  start = esp_timer_get_time();
  for (uint8_t i = 0; i < sensorCount; i++) {
    if (sensors[i]->isPacketReady()) {
      udp.beginPacket(serverIP, serverPort);
      udp.write(MessageTypeByte::Client::SENSOR_SAMPLES);
      udp.write(i);  // sensor ID
      udp.write(sensors[i]->data.getSampleCount());
      udp.write(sensors[i]->data.getBuffer(), sensors[i]->data.getCurrentByteSize());
      udp.endPacket();
      sensors[i]->data.clear();
    }
  }
  end = esp_timer_get_time();
  int64_t elapsed = end - start;
  if (elapsed > 800) {
    Serial.println("et: " + String(elapsed));
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
  sendInfo(); /*
  xTaskCreatePinnedToCore(
    serverReplyTask,         // Task function
    "ServerReplyTask",       // Task name
    4096,                    // Stack size in bytes
    this,                    // Parameter passed to task
    1,                       // Priority (1 is low priority)
    &serverReplyTaskHandle,  // Task handle
    1                        // Core 1 (second core)
  );
  */
}

void UDPSensorManager::processData() {
  serverReply();
  if (isKeepAliveReady()) {
    sendKeepAlive();
  }
  doReadAndWrites();
  //serverReply();
  sendAndClearSamples();
}
