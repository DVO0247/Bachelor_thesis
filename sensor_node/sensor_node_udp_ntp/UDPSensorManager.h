#include "Arduino.h"
#pragma once
#include <stdint.h>
#include <WiFiUdp.h>
#include "SensorManager.h"
#include "UnixTimeAtZero.h"
#include "SensorData.h"

#define SERVER_SET_SENSOR_PARAMETERS_SIZE 7
#define KEEP_ALIVE_PERIOD_MS 15000

#define DEFAULT_NTP_SERVER_2 "cz.pool.ntp.org"
#define DEFAULT_NTP_SERVER_3 "tik.cesnet.cz"

namespace MessageTypeByte {
enum Server : byte {
  REQUEST_INFO = 0X00,
  SET_SENSOR_PARAMETERS = 0X01
};
enum Client : byte {
  KEEP_ALIVE = 0x00,
  INFO = 0x01,
  SENSOR_SAMPLES = 0x02,
  ACK = 0x03
};
};

class UDPSensorManager : public SensorManager {
private:
  const char* serverIP;
  uint16_t serverPort;
  uint64_t unixTimeAtZero;
  bool keepAliveEnabled;
  uint32_t keepAliveLastSent;
  String name;
  WiFiUDP udp;
  void sendInfo();
  void sendACK(uint8_t sensorId);
  void sendAndClearSamples();
public:
  bool isKeepAliveReady();
  void sendKeepAlive();
  void serverReply();
  UDPSensorManager();
  void begin(const char* serverIP, uint16_t serverPort, String name, const char* ntpServer2 = DEFAULT_NTP_SERVER_2, const char* ntpServer3 = DEFAULT_NTP_SERVER_3);
  void processData();
};
