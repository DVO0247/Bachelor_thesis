#include "UnixTimeOffset.h"

uint64_t getUnixTimeOffset(const char* ntpServer1, const char* ntpServer2, const char* ntpServer3) {
  configTime(0, 3600, ntpServer1, ntpServer2, ntpServer3);

  // Wait till time is synced
  Serial.print("Syncing time");
  int i = 0;
  while (time(nullptr) < 1000000000l && i < 40) {
    Serial.print(".");
    delay(500);
    i++;
  }
  Serial.println();

  // Show time
  time_t tnow = time(nullptr);
  Serial.print("Synchronized time: ");
  Serial.println(ctime(&tnow));
  
  struct timeval tv;
  gettimeofday(&tv, NULL);
  uint32_t _millis = millis();
  return (tv.tv_sec * (uint64_t)1000) + (tv.tv_usec / 1000) - _millis;
}
