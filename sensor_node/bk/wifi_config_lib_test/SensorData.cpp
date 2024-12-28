#include "SensorData.h"

// Konstruktor
SensorData::SensorData(){}

// Metoda pro přidání dat (double) do bufferu
void SensorData::addData(double value) {
    if (currentIndex + sizeof(uint32_t) + sizeof(double) <= BUFFER_SIZE) {
        // Přidání časového razítka (millis()) - uložené jako 4 bajty (uint32_t)
        uint32_t timeStamp = millis();  // Získání aktuálního času v ms
        memcpy(&buffer[currentIndex], &timeStamp, sizeof(uint32_t));
        currentIndex += sizeof(uint32_t);

        // Přidání dat (double) - uložené jako 8 bajtů
        memcpy(&buffer[currentIndex], &value, sizeof(double));
        currentIndex += sizeof(double);
    } else {
        Serial.println("Buffer is full, cannot add more data");
    }
}

// Metoda pro vymazání bufferu (resetuje index)
void SensorData::clearBuffer() {
    currentIndex = 0;
    memset(buffer, 0, BUFFER_SIZE);
}

// Metoda pro získání aktuální velikosti použitých dat v bufferu
uint16_t SensorData::getCurrentSize() {
    return currentIndex;
}

bool SensorData::bufferIsFull(){
  return currentIndex >= BUFFER_SIZE;
}
