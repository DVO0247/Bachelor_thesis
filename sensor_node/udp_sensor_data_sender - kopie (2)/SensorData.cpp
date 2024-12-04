#include "SensorData.h"

// Konstruktor
SensorData::SensorData() {}

byte* SensorData::getBuffer() {
  return buffer;
}

uint16_t SensorData::getCurrentByteSize() {
  return currentIndex;
}

bool SensorData::bufferIsFull() {
  return currentIndex >= BUFFER_SIZE;
}

Sample SensorData::getSample(uint8_t index) {
  index *= SAMPLE_SIZE;
  Sample sample;

  // Přečteme 4 bajty do uint32_t
  memcpy(&sample.time, &buffer[index], sizeof(uint32_t));

  // Přečteme 8 bajtů do double
  memcpy(&sample.value, &buffer[index + sizeof(uint32_t)], sizeof(double));

  return sample;  // Vrátí strukturu se dvěma hodnotami
}

uint8_t SensorData::getSampleCount() {
  return sampleCount;
}

void SensorData::write(double value) {
  if (currentIndex + sizeof(uint32_t) + sizeof(double) <= BUFFER_SIZE) {
    // Přidání časového razítka (millis()) - uložené jako 4 bajty (uint32_t)
    uint32_t timeStamp = millis();  // Získání aktuálního času v ms
    memcpy(&buffer[currentIndex], &timeStamp, sizeof(uint32_t));
    currentIndex += sizeof(uint32_t);

    // Přidání dat (double) - uložené jako 8 bajtů
    memcpy(&buffer[currentIndex], &value, sizeof(double));
    currentIndex += sizeof(double);
    sampleCount++;
  } else {
    Serial.println("Buffer is full, cannot add more data");
  }
}

// Metoda pro vymazání bufferu (resetuje index)
void SensorData::clear() {
  currentIndex = 0;
  memset(buffer, 0, BUFFER_SIZE);
  sampleCount = 0;
}

