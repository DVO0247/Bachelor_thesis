#ifndef UDPSENSORMANAGER_H
#define UDPSENSORMANAGER_H

#include <WiFiUdp.h>
#include "SensorManager.h"

class UDPSensorManager : public SensorManager {
private:
  const char* host;
  uint16_t port;
  String name;
public:
  UDPSensorManager();
  void checkAndSend();
};

#endif