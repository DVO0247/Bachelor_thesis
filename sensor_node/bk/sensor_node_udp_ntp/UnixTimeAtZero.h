#pragma once
#include <Arduino.h>
#include <stdint.h>
#include <time.h>
#include "esp32-hal.h"

uint64_t getUnixTimeAtZero(const char* ntpServer1, const char* ntpServer2, const char* ntpServer3);
