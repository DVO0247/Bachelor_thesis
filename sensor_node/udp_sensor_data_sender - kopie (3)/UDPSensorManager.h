#ifndef UDPSENSORMANAGER_H
#define UDPSENSORMANAGER_H

#include <WiFiUdp.h>
#include "SensorManager.h"

#define REPLY_START_BYTE 0xFF
#define START_OF_TEXT_BYTE 0x02
#define END_OF_TEXT_BYTE 0x03
#define ACK_BYTE 0x06
#define SERVER_REQUEST_SIZE 7

class UDPSensorManager : public SensorManager {
private:
  const char* serverIP;
  uint16_t serverPort;
  String name;
  WiFiUDP udp;
  void serverReply();
  void sendAndClear();
public:
  UDPSensorManager();
  void begin(const char* serverIP, uint16_t serverPort, String name);
  void processData();
};

#endif