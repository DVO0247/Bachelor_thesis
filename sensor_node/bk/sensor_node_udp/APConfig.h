#ifndef APCONFIG_H
#define APCONFIG_H

#include <WiFi.h>
#include <WebServer.h>
#include <EEPROM.h>
#include <DNSServer.h>

#define EEPROM_SIZE 121  // 32 pro SSID, 32 pro heslo, 15 pro IP, 2 pro port, 40 pro name/hostname
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
  APConfig(const char* apSSID, const char* apPassword, int resetPin, int statusLED = 2);
  void begin();   // Spuštění konfigurace WiFi a serveru
  void apLoop();  // Hlavní smyčka pro obsluhu AP
  void checkReset();
  const char* getServerIP();  // Získání IP adresy serveru
  uint16_t getServerPort();   // Získání portu serveru
  String getName();
  bool isInAPMode();

private:
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


#endif
