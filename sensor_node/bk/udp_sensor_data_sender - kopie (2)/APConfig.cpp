#include "APConfig.h"

APConfig::APConfig(const char* apSSID, const char* apPassword, int resetPin)
  : apSSID(apSSID), apPassword(apPassword), resetPin(resetPin), server(80) {
}

// Metoda pro spuštění konfigurace
void APConfig::begin() {
  pinMode(resetPin, INPUT_PULLUP);

  EEPROM.begin(EEPROM_SIZE);

  // Načtení IP adresy z EEPROM a výpis pro kontrolu
  //serverIP = readStringFromEEPROM(64, 15);
  readStringFromEEPROM(SERVER_IP_ADDR, SERVER_IP_SIZE).toCharArray(serverIP, sizeof(serverIP));

  // Načtení portu z EEPROM a výpis pro kontrolu
  serverPort = readUint16FromEEPROM(PORT_ADDR);

  name = readStringFromEEPROM(NAME_ADDR, NAME_SIZE);

  // Pokus o připojení k uložené WiFi
  if (!connectToSavedWiFi()) {
    // Pokud se připojení nezdaří, vytvoří se hotspot a spustí se server
    Serial.println("Připojení selhalo, spouští se hotspot.");
    WiFi.mode(WIFI_OFF);
    startAccessPoint();

    // Spustíme server pro konfiguraci pouze v režimu hotspotu
    server.on("/", [this]() {
      handleRoot();
    });
    server.on("/save", HTTP_POST, [this]() {
      handleSave();
    });

    server.onNotFound([this]() {
      server.sendHeader("Location", String("http://") + WiFi.softAPIP().toString(), true);
      server.send(302, "text/plain", "");
    });

    server.begin();
    Serial.println("Web server spuštěn");
  } else {
    Serial.println("Připojeno k WiFi!");
    Serial.print("IP Adresa: ");
    Serial.println(WiFi.localIP());
  }

  if (WiFi.getMode() == WIFI_AP) {
    apMode = true;
  }
}

// Hlavní smyčka pro obsluhu serveru
void APConfig::apLoop() {
  while (true) {
    dnsServer.processNextRequest();
    server.handleClient();
  }
}

void APConfig::checkReset() {
  if (digitalRead(resetPin) == LOW) {
    delay(1000);
    if (digitalRead(resetPin) == LOW) {
      Serial.println("Resetovací tlačítko stisknuto. Vymazání EEPROM a restart.");
      clearEEPROM();
      delay(1000);
      ESP.restart();
    }
  }
}

bool APConfig::isInAPMode() {
  return apMode;
}

// Metoda pro inicializaci hotspotu
void APConfig::startAccessPoint() {
  WiFi.softAP(apSSID, apPassword);
  Serial.println("Access Point spuštěn");
  Serial.println(WiFi.softAPIP());
  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());
  dnsServer.setTTL(0);
}

// Metoda pro obsluhu hlavní stránky konfigurace
void APConfig::handleRoot() {
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Pragma", "no-cache");
  server.sendHeader("Expires", "-1");
  String html = "<html><body><h2>WiFi Configuration</h2>";
  html += "<form action='/save' method='POST'>";
  html += "SSID: <input type='text' name='ssid'><br>";
  html += "Password: <input type='password' name='password'><br>";
  html += "Server IP: <input type='text' name='serverip'><br>";
  html += "Port: <input type='number' name='port'><br>";
  html += "Name: <input type='text' name='name'><br>";
  html += "<input type='submit' value='Save'>";
  html += "</form></body></html>";
  server.send(200, "text/html", html);
}

// Metoda pro uložení konfigurace z formuláře do EEPROM
void APConfig::handleSave() {
  String inputSSID = server.arg("ssid");
  String inputPassword = server.arg("password");
  String inputServerIP = server.arg("serverip");
  int inputServerPort = server.arg("port").toInt();
  String inputname = server.arg("name");

  writeStringToEEPROM(SSID_ADDR, inputSSID);           // SSID na pozici 0
  writeStringToEEPROM(PASS_ADDR, inputPassword);       // Heslo na pozici 32
  writeStringToEEPROM(SERVER_IP_ADDR, inputServerIP);  // IP na pozici 64
  writeUint16ToEEPROM(PORT_ADDR, inputServerPort);     // Port na pozici 79
  writeStringToEEPROM(NAME_ADDR, inputname);

  EEPROM.commit();
  server.send(200, "text/html", "<html><body><h2>Settings saved. Restarting ESP32.</h2></body></html>");

  delay(1000);
  ESP.restart();
}

// Metoda pro připojení k uložené WiFi
bool APConfig::connectToSavedWiFi() {
  String savedSSID = readStringFromEEPROM(SSID_ADDR, SSID_SIZE);
  String savedPassword = readStringFromEEPROM(PASS_ADDR, PASS_SIZE);

  if (savedSSID.length() > 0) {
    Serial.println("Připojování k uložené WiFi...");
    //WiFi.setHostname(...);
    WiFi.begin(savedSSID.c_str(), savedPassword.c_str());

    unsigned long startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
      delay(100);
    }
    return WiFi.status() == WL_CONNECTED;
  }
  return false;
}

// Metoda pro čtení řetězce z EEPROM
String APConfig::readStringFromEEPROM(int start, int length) {
  String value = "";
  for (int i = 0; i < length; i++) {
    char c = EEPROM.read(start + i);
    if (c != 0) value += c;
  }
  return value;
}

// Metoda pro zápis řetězce do EEPROM
void APConfig::writeStringToEEPROM(int start, const String& value) {
  for (int i = 0; i < value.length(); i++) {
    EEPROM.write(start + i, value[i]);
  }
  EEPROM.write(start + value.length(), 0);  // Null terminátor
}

uint16_t APConfig::readUint16FromEEPROM(int address) {
  uint16_t value = EEPROM.read(address) | (EEPROM.read(address + 1) << 8);
  return value;
}

// Metoda pro zápis 16bitového čísla do EEPROM (pro port)
void APConfig::writeUint16ToEEPROM(int address, uint16_t value) {
  EEPROM.write(address, value & 0xFF);
  EEPROM.write(address + 1, (value >> 8) & 0xFF);
}

// Metoda pro vymazání EEPROM
void APConfig::clearEEPROM() {
  for (int i = 0; i < EEPROM_SIZE; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
}

// Metoda pro vrácení IP serveru
const char* APConfig::getServerIP() {
  return serverIP;
}


// Metoda pro vrácení portu serveru
uint16_t APConfig::getServerPort() {
  return serverPort;
}

String APConfig::getName() {
  return name;
}