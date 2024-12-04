#ifndef UDPSENSORMANAGER_H
#define UDPSENSORMANAGER_H

#include <WiFiUdp.h>
#include "SensorManager.h"

class UDPSensorManager : public SensorManager {
private:
  const char* serverIP;
  uint16_t serverPort;
  String name;
public:
  UDPSensorManager();
  void init(const char* serverIP, uint16_t serverPort, String name);
  void checkAndSend();
};

#endif