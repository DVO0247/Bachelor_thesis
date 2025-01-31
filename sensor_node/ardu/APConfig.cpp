#include "APConfig.h"

void APConfig::begin(const char* apSSID, const char* apPassword, int resetPin, int statusLED) {
  this->apSSID = apSSID;
  this->apPassword = apPassword;
  this->resetPin = resetPin;
  this->statusLED = statusLED;

  pinMode(resetPin, INPUT_PULLUP);
  if (statusLED >= 0) {
    pinMode(statusLED, OUTPUT);
  }

  EEPROM.begin(EEPROM_SIZE);
  checkReset();

  // Načtení IP adresy z EEPROM a výpis pro kontrolu
  //serverIP = readStringFromEEPROM(64, 15);
  EEPROM.readString(SERVER_IP_ADDR).toCharArray(serverIP, sizeof(serverIP));

  serverPort = EEPROM.readUShort(PORT_ADDR);

  name = EEPROM.readString(NAME_ADDR);

  // Attempt to connect to saved WiFi, if that fails, hotspot will start.
  if (!connectToSavedWiFi()) {
    Serial.println("Connection failed, starting hotspot.");
    WiFi.mode(WIFI_OFF);
    startAccessPoint();

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
    Serial.println("Web server started");
    apMode = true;
    apLoop();
  } else {
    Serial.println("Connected to wifi");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  }
}

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
      Serial.print("Reset pin was grounded. ");
      clearEEPROM();
      delay(1000);
      digitalWrite(statusLED, HIGH);
      Serial.println("EEPROM erased, waiting for reset pin to be released.");
      while (digitalRead(resetPin) == LOW) {
        delay(10);
      }
      digitalWrite(statusLED, LOW);
      ESP.restart();
    }
  }
}

bool APConfig::isInAPMode() {
  return apMode;
}

void APConfig::startAccessPoint() {
  WiFi.softAP(apSSID, apPassword);
  Serial.println("Access Point spuštěn");
  Serial.println(WiFi.softAPIP());
  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());
  dnsServer.setTTL(0);
}

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
  html += "Name: <input type='text' name='name' maxlength='36'><br>";
  html += "<input type='submit' value='Save'>";
  html += "</form></body></html>";
  server.send(200, "text/html", html);
}

void APConfig::handleSave() {
  String inputSSID = server.arg("ssid");
  String inputPassword = server.arg("password");
  String inputServerIP = server.arg("serverip");
  int inputServerPort = server.arg("port").toInt();
  String inputname = server.arg("name");

  EEPROM.writeString(SSID_ADDR, inputSSID);         
  EEPROM.writeString(PASS_ADDR, inputPassword);     
  EEPROM.writeString(SERVER_IP_ADDR, inputServerIP);
  EEPROM.writeUShort(PORT_ADDR, inputServerPort);   
  EEPROM.writeString(NAME_ADDR, inputname);

  EEPROM.commit();
  server.send(200, "text/html", "<html><body><h2>Settings saved. Restarting ESP32.</h2></body></html>");

  delay(1000);
  ESP.restart();
}

bool APConfig::connectToSavedWiFi() {
  String savedSSID = EEPROM.readString(SSID_ADDR);
  String savedPassword = EEPROM.readString(PASS_ADDR);

  if (savedSSID.length() > 0) {
    Serial.println("Připojování k uložené WiFi...");
    WiFi.setHostname(getName().c_str());
    WiFi.begin(savedSSID.c_str(), savedPassword.c_str());

    unsigned long startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 60000) {
      digitalWrite(statusLED, LOW);
      delay(300);
      digitalWrite(statusLED, HIGH);
      delay(100);
    }
    digitalWrite(statusLED, LOW);
    return WiFi.status() == WL_CONNECTED;
  }
  return false;
}

void APConfig::clearEEPROM() {
  for (int i = 0; i < EEPROM_SIZE; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
}

const char* APConfig::getServerIP() {
  return serverIP;
}


uint16_t APConfig::getServerPort() {
  return serverPort;
}

String APConfig::getName() {
  return name;
}