#include <stdint.h>
#include "SensorData.h"

// Konstruktor
SensorData::SensorData(){
  this->maxReadoutCount = 122;
}
SensorData::SensorData(uint8_t maxReadoutCount){
  this->maxReadoutCount = maxReadoutCount;
}

byte* SensorData::getBuffer(){
  return buffer;
}

Readout SensorData::getReadout(uint8_t index){
    index *= READOUT_SIZE;
    Readout readout;
    
    // Přečteme 4 bajty do uint32_t
    memcpy(&readout.time, &buffer[index], sizeof(uint32_t));

    // Přečteme 8 bajtů do double
    memcpy(&readout.value, &buffer[index+sizeof(uint32_t)], sizeof(double));

    return readout;  // Vrátí strukturu se dvěma hodnotami
}

// Metoda pro přidání dat (double) do bufferu
void SensorData::append(double value) {
    if (currentIndex + sizeof(uint32_t) + sizeof(double) <= BUFFER_SIZE) {
        // Přidání časového razítka (millis()) - uložené jako 4 bajty (uint32_t)
        uint32_t timeStamp = millis();  // Získání aktuálního času v ms
        memcpy(&buffer[currentIndex], &timeStamp, sizeof(uint32_t));
        currentIndex += sizeof(uint32_t);

        // Přidání dat (double) - uložené jako 8 bajtů
        memcpy(&buffer[currentIndex], &value, sizeof(double));
        currentIndex += sizeof(double);
        readoutCount++;
    } else {
        Serial.println("Buffer is full, cannot add more data");
    }
}

// Metoda pro vymazání bufferu (resetuje index)
void SensorData::clear() {
    currentIndex = 0;
    memset(buffer, 0, BUFFER_SIZE);
    readoutCount = 0;
}

// Metoda pro získání aktuální velikosti použitých dat v bufferu
uint16_t SensorData::getCurrentSize() {
    return currentIndex;
}

uint8_t SensorData::getReadoutCount() {
    return readoutCount;
}

void SensorData::setMaxReadoutCount(uint8_t maxReadoutCount) {
  this->maxReadoutCount = maxReadoutCount;
}

uint8_t SensorData::getMaxReadoutCount(){
  return maxReadoutCount;
}

bool SensorData::bufferIsFull(){
  return currentIndex >= BUFFER_SIZE;
}

bool SensorData::isReadoutCountMax(){
  return readoutCount >= maxReadoutCount;
}
