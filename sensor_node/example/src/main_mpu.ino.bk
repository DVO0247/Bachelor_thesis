#include <Arduino.h>

#include "APConfig.h"
#include "MPU9250.h"
#include "TCPSensorManager.h"
#include "esp32-hal.h"

#define apSSID "ESP32_CONF"
#define apPassword "Config00"

#define confResetPin 18

MPU9250 IMU(Wire, 0x68);
int status;

APConfig apConfig;
TCPSensorManager tcpSensorManager;

void mpu_setup() {
    while (!Serial) {
    }
    status = IMU.begin();
    if (status < 0) {
        Serial.println("IMU initialization unsuccessful");
        Serial.println("Check IMU wiring or try cycling power");
        Serial.print("Status: ");
        Serial.println(status);
        while (1) {
        }
    }
}
/*
void nevim() {
    IMU.readSensor();
    // display the data
    Serial.print("(");
    Serial.print(IMU.getAccelX_mss(), 6);
    Serial.print(" ");
    Serial.print(IMU.getAccelY_mss(), 6);
    Serial.print(" ");
    Serial.print(IMU.getAccelZ_mss(), 6);
    Serial.print(") (");
    Serial.print(IMU.getGyroX_rads(), 6);
    Serial.print(" ");
    Serial.print(IMU.getGyroY_rads(), 6);
    Serial.print(" ");
    Serial.print(IMU.getGyroZ_rads(), 6);
    Serial.print(") (");
    Serial.print(IMU.getMagX_uT(), 6);
    Serial.print(" ");
    Serial.print(IMU.getMagY_uT(), 6);
    Serial.print(" ");
    Serial.print(IMU.getMagZ_uT(), 6);
    Serial.print(") ");
    Serial.print(IMU.getTemperature_C(), 6);
    Serial.print("°C\r");
}
*/

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
