#pragma once
#include "esp32-hal.h"
#include <Arduino.h>
#include <time.h>

// Calculates the offset between NTP-synced time and system uptime (millis)
uint64_t getUnixTimeOffset(const char* ntpServer1, const char* ntpServer2, const char* ntpServer3);
