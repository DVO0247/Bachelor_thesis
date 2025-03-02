#pragma once
#include "esp32-hal.h"    // ESP32 hardware abstraction layer
#include <Arduino.h>       // Standard Arduino functions

#include "APConfig.h"      // Configuration for Access Point mode
#include "SensorData.h"    // Handles sensor data storage
#include "SensorManager.h" // Base class for managing sensors
#include "UnixTimeOffset.h"// Handles Unix time synchronization
#include "WiFiClient.h"    // WiFi client for TCP communication
#include <WiFi.h>          // ESP32 WiFi functionality

// Sensor node type identifier
#define SENSOR_NODE_TYPE 0x00

// Null character used in ASCII encoding
#define ASCII_NULL 0x00

// Number of bytes required per sensor request from the server
#define SERVER_REQUEST_SIZE_PER_SENSOR 5

// Default NTP server addresses for time synchronization
#define DEFAULT_NTP_SERVER_2 "cz.pool.ntp.org"
#define DEFAULT_NTP_SERVER_3 "tik.cesnet.cz"

// TCPSensorManager class handles TCP communication with a server for sensor data transmission
class TCPSensorManager : public SensorManager {
   private:
    bool initialized;    // Tracks if the sensor manager is initialized

    void sendInfo();          // Sends device information to the server
    void receiveParams();     // Receives configuration parameters from the server
    void sendAndClearSamples(); // Sends collected sensor data and clears the buffer
    bool is_initialized();    // Checks if the manager is initialized
    void set_initialized(bool state); // Sets initialization state

    SemaphoreHandle_t initialized_mutex; // Mutex for thread-safe access to initialization flag
    uint64_t unixTimeOffset; // Offset for Unix time synchronization
    WiFiClient client;       // TCP client for server communication
    const char* serverIP;    // Server IP address
    uint16_t serverPort;     // Server port
    String name;             // Device name

   public:
    // Constructor
    TCPSensorManager();

    // Initializes the sensor manager with a server IP, port, and device name
    void begin(
        const char* serverIP,
        uint16_t serverPort,
        String name,
        const char* ntpServer2 = DEFAULT_NTP_SERVER_2,
        const char* ntpServer3 = DEFAULT_NTP_SERVER_3
        );

    // Overloaded begin method using APConfig for initialization
    void begin(
        APConfig* apConfig,
        const char* ntpServer2 = DEFAULT_NTP_SERVER_2,
        const char* ntpServer3 = DEFAULT_NTP_SERVER_3
        );

    // Handles reading and processing of sensor data
    void processData();

    // Manages connection and data exchange with the server
    void serverManage();
};
