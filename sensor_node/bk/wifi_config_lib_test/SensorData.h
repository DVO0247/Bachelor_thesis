#ifndef SENSORBUFFER_H
#define SENSORBUFFER_H

#include <Arduino.h>
#include <cstdint>
#define BUFFER_SIZE 1464

class SensorData {
  private:
    byte buffer[BUFFER_SIZE];     // Buffer pro ukládání dat jako byte array
    uint16_t currentIndex = 0; // Aktuální index pro zápis do bufferu

  public:
    // Konstruktor
    SensorData();

    // Metoda pro přidání dat (double) do bufferu
    void addData(double sensorData);

    // Metoda pro vymazání bufferu (resetuje index)
    void clearBuffer();

    // Metoda pro flush (odeslání dat nebo vyprázdnění bufferu)
    void flush();

    // Metoda pro získání aktuální velikosti použitých dat v bufferu
    uint16_t getCurrentSize();

    bool bufferIsFull();
};

#endif // SENSORBUFFER_H
