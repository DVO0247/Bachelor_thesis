#pragma once
#include <DNSServer.h>
#include <EEPROM.h>
#include <WebServer.h>
#include <WiFi.h>

#include "esp32-hal.h"

// Port for DNS server
#define DNS_PORT 53

// Sizes of the settings data
constexpr uint8_t SSID_SIZE = 32;
constexpr uint8_t PASS_SIZE = 32;
constexpr uint8_t SERVER_IP_SIZE = 15;
constexpr uint8_t PORT_SIZE = 2;
constexpr uint8_t NAME_SIZE = 40;

// EEPROM START ADDRESSES for different settings
constexpr uint16_t SSID_ADDR = 0;
constexpr uint16_t PASS_ADDR = SSID_ADDR + SSID_SIZE;
constexpr uint16_t SERVER_IP_ADDR = PASS_ADDR + PASS_SIZE;
constexpr uint16_t PORT_ADDR = SERVER_IP_ADDR + SERVER_IP_SIZE;
constexpr uint16_t NAME_ADDR = PORT_ADDR + PORT_SIZE;


// Total EEPROM size used for storing settings
constexpr uint16_t EEPROM_SIZE = SSID_SIZE + PASS_SIZE + SERVER_IP_SIZE + PORT_SIZE + NAME_SIZE;

class APConfig {
   private:
    // Main loop that handles DNS requests (for captive web portal) and client requests when in AP mode
    void apLoop();

    // Checks if reset pin is pressed for resetting configuration
    void checkReset();

    // AP credentials and other configuration variables
    const char* apSSID;      // Stores the SSID of the AP
    const char* apPassword;  // Stores the password for AP
    int confResetPin;        // Pin for triggering a configuration reset
    int statusLED;           // LED pin to show status

    // Objects for handling DNS and Web Server functionality
    DNSServer dnsServer;  // DNS server for AP mode
    WebServer server;     // Web server for handling client requests

    // Server configuration details
    char serverIP[16];  // Stores the server's IP address
    int serverPort;     // Stores the server's port number
    String name;        // Stores the configured name of the device
    bool apMode;        // Flag to track if the device is in AP mode

    // Starts the access point (AP) mode
    void startAccessPoint();

    // Handles the root page for the web server (configuration page)
    void handleRoot();

    // Saves the configuration data sent from the client (web form)
    void handleSave();

    // Connects to a previously saved WiFi network
    bool connectToSavedWiFi();

    // Clears the EEPROM settings
    void clearEEPROM();

   public:
    // Initializes the AP configuration with SSID, password, etc.
    void begin(const char* apSSID, const char* apPassword, int confResetPin, int statusLED = BUILTIN_LED);

    // Retrieves the server's IP address
    const char* getServerIP();

    // Retrieves the server's port number
    uint16_t getServerPort();

    // Retrieves the configured name
    String getName();

    // Checks if the device is in AP mode
    bool isInAPMode();
};
