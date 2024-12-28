#include <Arduino.h>
#include <SensorData.h>

SensorData sensorData(10);
double value = PI;

void setup() {
  Serial.begin(115200);
}

void loop() {

  if (sensorData.isReadoutCountMax()) {
    Serial.println("ReadoutCountMax printing all...");
    for (int i = 0; i < sensorData.getMaxReadoutCount(); i++) {
      Readout readout = sensorData.getReadout(i);
      Serial.println(String(readout.time) + ", " + String(readout.value));
    }
    Serial.println("All data printed");
    sensorData.clear();
  }
  sensorData.append(value);
  Serial.println(String(value)+" "+String(sensorData.getReadoutCount()));
  value += PI;
  delay(1000);
}
