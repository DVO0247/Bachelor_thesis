#include <Arduino.h>

#include "APConfig.h"
#include "MPU9250.h"
#include "TCPSensorManager.h"
#include "esp32-hal.h"

#define apSSID "ESP32_CONF"
#define apPassword "Config00"

#define confResetPin 18

APConfig apConfig;
TCPSensorManager tcpSensorManager;

MPU9250 IMU(Wire, 0x68);

void mpu_setup() {
    while (!Serial) {}
    int status = IMU.begin();
    if (status < 0) {
        while (1) {}
    }
}

double ax() {
    return IMU.getAccelX_mss();
}

double ay() {
    return IMU.getAccelY_mss();
}

double az() {
    return IMU.getAccelZ_mss();
}

double gx() {
    return IMU.getGyroX_rads();
}

double gy() {
    return IMU.getGyroY_rads();
}

double gz() {
    return IMU.getGyroZ_rads();
}

void setup() {
    Serial.begin(115200);
    mpu_setup();
    apConfig.begin(apSSID, apPassword, confResetPin);
    tcpSensorManager.addSensor(ax);
    tcpSensorManager.addSensor(ay);
    tcpSensorManager.addSensor(az);
    tcpSensorManager.addSensor(gx);
    tcpSensorManager.addSensor(gy);
    tcpSensorManager.addSensor(gz);
    tcpSensorManager.begin(&apConfig);
}

void loop() {
    IMU.readSensor();
    tcpSensorManager.processData();
}
