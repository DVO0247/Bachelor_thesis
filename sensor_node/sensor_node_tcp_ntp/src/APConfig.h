#pragma once
#include "esp32-hal.h"
#include <EEPROM.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>

#define EEPROM_SIZE 121  // 32 for SSID, 32 for password, 15 pro IP, 2 for port, 40 for name/hostname
#define DNS_PORT 53      // Port DNS

// EEPROM START ADDRESSES
#define SSID_ADDR 0
#define PASS_ADDR 32
#define SERVER_IP_ADDR 64
#define PORT_ADDR 79
#define NAME_ADDR 81

#define SSID_SIZE 32
#define PASS_SIZE 32
#define SERVER_IP_SIZE 15
#define PORT_SIZE 79
#define NAME_SIZE 40

class APConfig {
public:
  void begin(const char* apSSID, const char* apPassword, int resetPin, int statusLED = 2);  // Spuštění konfigurace WiFi a serveru
  void apLoop();                                                                            // Hlavní smyčka pro obsluhu AP

  const char* getServerIP();  // Získání IP adresy serveru
  uint16_t getServerPort();   // Získání portu serveru
  String getName();
  bool isInAPMode();

private:
  void checkReset();
  const char* apSSID;
  const char* apPassword;
  int resetPin;
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
  String readStringFromEEPROM(int start, int length);
  void writeStringToEEPROM(int start, const String& value);
  void writeUint16ToEEPROM(int address, uint16_t value);
  uint16_t readUint16FromEEPROM(int address);
  void clearEEPROM();
};
