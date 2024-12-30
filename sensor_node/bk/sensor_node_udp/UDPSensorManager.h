#ifndef UDPSENSORMANAGER_H
#define UDPSENSORMANAGER_H

#include <WiFiUdp.h>
#include "SensorManager.h"

#define START_OF_SAMPLES_BYTE 0x02
#define END_OF_SAMPLES_BYTE 0x03
#define SPECIAL_IDENTIFIER_BYTE 0xFF
#define ACK_BYTE 0x06
#define SERVER_REQUEST_SIZE 6

class UDPSensorManager : public SensorManager {
private:
  const char* serverIP;
  uint16_t serverPort;
  String name;
  WiFiUDP udp;
  void sendInfo();
  void sendACK();
  void serverReply();
  void sendAndClearSamples();
public:
  UDPSensorManager();
  void begin(const char* serverIP, uint16_t serverPort, String name);
  void processData();
};

#endif