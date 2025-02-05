#pragma once
#include <DNSServer.h>
#include <EEPROM.h>
#include <WebServer.h>
#include <WiFi.h>
#include "esp32-hal.h"

#define DNS_PORT 53

// EEPROM START ADDRESSES
#define SSID_ADDR 0
#define PASS_ADDR 32
#define SERVER_IP_ADDR 64
#define PORT_ADDR 79
#define NAME_ADDR 81

#define SSID_SIZE 32
#define PASS_SIZE 32
#define SERVER_IP_SIZE 15
#define PORT_SIZE 2
#define NAME_SIZE 40

constexpr uint8_t EEPROM_SIZE = SSID_SIZE + PASS_SIZE + SERVER_IP_SIZE + PORT_SIZE + NAME_SIZE;  // Total used size

class APConfig {
   public:
    void begin(const char* apSSID, const char* apPassword, int confResetPin, int statusLED = BUILTIN_LED);

    const char* getServerIP();
    uint16_t getServerPort();
    String getName();
    bool isInAPMode();
   private:
    void apLoop();
    void checkReset();
    const char* apSSID;
    const char* apPassword;
    int confResetPin;
    int statusLED;
    DNSServer dnsServer;
    WebServer server;

    char serverIP[16];
    int serverPort;
    String name;
    bool apMode;

    void startAccessPoint();
    void handleRoot();
    void handleSave();
    bool connectToSavedWiFi();
    void clearEEPROM();
};
