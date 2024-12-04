#include "HardwareSerial.h"
#include <sys/types.h>
#include "UDPSensorManager.h"

void UDPSensorManager::serverReply() {
  int packetSize = udp.parsePacket();  // Zkontroluje, zda je k dispozici příchozí paket
  if (packetSize >= SERVER_REQUEST_SIZE) {
    byte received_bytes[SERVER_REQUEST_SIZE];
    udp.read(received_bytes, SERVER_REQUEST_SIZE);  // Přečte 5 bajtu do bufferu

    bool isAllZero = true;
    for (int i = 0; i < SERVER_REQUEST_SIZE; i++) {
      if (received_bytes[i] != 0) {
        isAllZero = false;
        break;
      }
    }

    udp.beginPacket(serverIP, serverPort);
    udp.write(REPLY_START_BYTE);
    if (isAllZero) {
      Serial.println("Sending count and name");
      udp.write(sensorCount);
      udp.print(name);
    } else {
      uint8_t firstByte = received_bytes[0];
      float secondValue;
      memcpy(&secondValue, &received_bytes[1], sizeof(float));
      uint16_t thirdValue = received_bytes[5] | (received_bytes[6] << 8);  // Sloučí další 2 bajty na uint16_t

      Serial.printf("First Byte: %d\n", firstByte);
      Serial.printf("Second Value: %f\n", secondValue);
      Serial.printf("Third Value: %d\n", thirdValue);
      Serial.println("Sending ACK");
      udp.write(ACK_BYTE);
    }
    udp.endPacket();
  }
}

void UDPSensorManager::sendAndClear() {
  for (uint8_t i = 0; i < sensorCount; i++) {
    if (sensors[i]->isPacketReady()) {
      udp.beginPacket(serverIP, serverPort);
      udp.write(i);
      udp.write(sensors[i]->data.getBuffer(), sensors[i]->data.getCurrentByteSize());
      udp.endPacket();
      sensors[i]->data.clear();
    }
  }
}

UDPSensorManager::UDPSensorManager()
  : SensorManager() {}

void UDPSensorManager::begin(const char* serverIP, uint16_t serverPort, String name) {
  this->serverIP = serverIP;
  this->serverPort = serverPort;
  this->name = name;

  Serial.println("Sending count and name");
  udp.beginPacket(serverIP, serverPort);
  udp.write(REPLY_START_BYTE);
  udp.write(sensorCount);
  udp.print(name);
  udp.endPacket();
}

void UDPSensorManager::processData() {
  doReadAndWrites();
  serverReply();
  sendAndClear();
}