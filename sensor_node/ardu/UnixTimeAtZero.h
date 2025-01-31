#pragma once
#include "esp32-hal.h"
#include <Arduino.h>
#include <time.h>

uint64_t getUnixTimeAtZero(const char* ntpServer1, const char* ntpServer2, const char* ntpServer3);
