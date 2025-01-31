#pragma once
#include "esp32-hal.h"
#include <Arduino.h>
#include "WiFiClient.h"

#include "SensorData.h"
#include "SensorManager.h"
#include "UnixTimeOffset.h"

#define STX 0x02
#define ETX 0x03
#define SERVER_REQUEST_SIZE_PER_SENSOR 5

#define DEFAULT_NTP_SERVER_2 "cz.pool.ntp.org"
#define DEFAULT_NTP_SERVER_3 "tik.cesnet.cz"

class TCPSensorManager : public SensorManager {
  private:
bool initialized;
   public:
    const char* serverIP;
    uint16_t serverPort;
    String name;
    WiFiClient client;
    uint64_t unixTimeOffset;
    void sendInfo();
    void receiveParams();
    void sendAndClearSamples();
    
    bool is_initialized();
    void set_initialized(bool state);
    SemaphoreHandle_t initialized_mutex;

    TCPSensorManager();
    void begin(
      const char* serverIP,
      uint16_t serverPort,
      String name,
      const char* ntpServer2 = DEFAULT_NTP_SERVER_2,
      const char* ntpServer3 = DEFAULT_NTP_SERVER_3
      );
    void processData();
};
