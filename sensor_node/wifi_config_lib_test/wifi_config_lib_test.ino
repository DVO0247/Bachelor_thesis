#include "APConfig.h"
#include <WiFiUdp.h>
#include <Arduino.h>

#define END_CHAR '|'
#define RECEIVED_SIZE 5

// Konfigurace AP
const char* apSSID = "ESP32_CONF";
const char* apPassword = "Kolokolo";
const int resetPin = 4;
const char* host;
uint16_t port;
String name;

APConfig apConfig(apSSID, apPassword, resetPin);

WiFiUDP udp;                 // UDP objekt pro komunikaci
unsigned long last_udp;      //millis
unsigned long last_measure;  //millis
String dataBuffer = "";

void setup() {
  Serial.begin(115200);
  apConfig.begin();
  apConfig.checkReset();
  /*
  Serial.println(apConfig.getServerIP());
  Serial.println(String(apConfig.getServerPort()));
  Serial.println(apConfig.getName());
  */
  host = apConfig.getServerIP();
  port = apConfig.getServerPort();
  name = apConfig.getName();
}

void loop() {
  if (apConfig.isInAPMode()) {
    apConfig.apLoop();
  } else {
    if (millis() - last_measure >= 1) {
      last_measure = millis();
      dataBuffer += "0," + String(millis()) + "," + String(dataBuffer.length()) + END_CHAR;
      //dataBuffer += "0," + String(millis()) + "," + String(random(100, 999)) + END_CHAR;
    }

    // Odeslání, když buffer dosáhne určité velikosti
    if (dataBuffer.length() >= 1430) {
      udp.beginPacket(host, port);  // Zahájení nového UDP paketu
      udp.print(dataBuffer);        // Odeslání dat z bufferu
      udp.endPacket();              // Konec UDP paketu - data se odesílají
      dataBuffer = "";              // Vymazání bufferu po odeslání

      int packetSize = udp.parsePacket();  // Zkontrolujte, zda je k dispozici příchozí paket
      if (packetSize >= RECEIVED_SIZE) {
        byte received_bytes[RECEIVED_SIZE];
        udp.read(received_bytes, RECEIVED_SIZE);  // Přečtěte 5 bajtu do bufferu

        bool allZero = true;
        for (int i = 0; i < RECEIVED_SIZE; i++) {
          if (received_bytes[i] != 0) {
            allZero = false;
            break;
          }
        }

        if (allZero) {
          Serial.println("Sending name");
          udp.beginPacket(host, port);
          udp.write(0xFF);
          udp.print(name);
          udp.write(END_CHAR);
          udp.endPacket();
        } else {
          uint8_t firstByte = received_bytes[0];
          uint16_t secondValue = received_bytes[1] | (received_bytes[2] << 8);  // Sloučí 2 bajty na uint16_t
          uint16_t thirdValue = received_bytes[3] | (received_bytes[4] << 8);   // Sloučí další 2 bajty na uint16_t

          Serial.printf("First Byte: %d\n", firstByte);
          Serial.printf("Second Value: %d\n", secondValue);
          Serial.printf("Third Value: %d\n", thirdValue);

          // Odešlete zprávu s jedním bajtem hodnoty 1
          udp.beginPacket(host, port);
          udp.write(1);  // Odešlete jeden bajt s hodnotou 1
          udp.endPacket();
        }

        //Serial.printf("Received byte: %d\n", incomingByte);
      }
    }
  }
}
