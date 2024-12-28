#include <stdint.h>
#ifndef SENSORBUFFER_H
#define SENSORBUFFER_H

#include <Arduino.h>
//#include <cstdint>
#define READOUT_SIZE 12
#define BUFFER_SIZE 1464

struct Readout {
    uint32_t time;
    double value;
};

class SensorData {
private:
  byte buffer[BUFFER_SIZE];   // Buffer pro ukládání dat jako byte array
  uint16_t currentIndex = 0;  // Aktuální index pro zápis do bufferu
  uint8_t readoutCount = 0;
  uint8_t maxReadoutCount;  // 1-122
public:
  // Konstruktor
  SensorData();
  SensorData(uint8_t maxReadoutCount);

  byte* getBuffer();

  Readout getReadout(uint8_t index);
  // Metoda pro přidání dat (double) do bufferu
  void append(double value);

  // Metoda pro vymazání bufferu (resetuje index)
  void clear();

  // Metoda pro získání aktuální velikosti použitých dat v bufferu
  uint16_t getCurrentSize();

  uint8_t getReadoutCount();

  void setMaxReadoutCount(uint8_t maxReadoutCount);

  uint8_t getMaxReadoutCount();

  bool bufferIsFull();

  bool isReadoutCountMax();
};

#endif  // SENSORBUFFER_H
