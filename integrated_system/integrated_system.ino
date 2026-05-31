#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ============================
// MPU6050
// ============================

Adafruit_MPU6050 mpu;

// ============================
// DS18B20
// ============================

#define ONE_WIRE_BUS 4

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

// ============================
// Analog Sensor Pins
// ============================

#define EDA_PIN 34
#define ECG_PIN 35
#define PPG_PIN 32

void setup() {

  Serial.begin(115200);

  // ============================
  // I2C START
  // ============================

  Wire.begin(21, 22);

  // ============================
  // MPU6050 INIT
  // ============================

  if (!mpu.begin()) {
    Serial.println("MPU6050 NOT FOUND");
    while (1);
  }

  // ============================
  // TEMP SENSOR INIT
  // ============================

  tempSensor.begin();

  Serial.println("=================================");
  Serial.println("HEALTHCARE MONITORING SYSTEM");
  Serial.println("ALL SENSORS INITIALIZED");
  Serial.println("=================================");
}

void loop() {

  // =========================================
  // TIMESTAMP
  // =========================================

  unsigned long timestamp = millis();

  // =========================================
  // TEMPERATURE
  // =========================================

  tempSensor.requestTemperatures();
  float skinTemp = tempSensor.getTempCByIndex(0);

  // =========================================
  // MPU6050 DATA
  // =========================================

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // =========================================
  // EDA
  // =========================================

  int edaRaw = analogRead(EDA_PIN);

  float tonic = edaRaw * 0.7;
  float phasic = edaRaw * 0.3;

  // =========================================
  // ECG
  // =========================================

  int ecgRaw = analogRead(ECG_PIN);

  // =========================================
  // PPG / SPO2
  // =========================================

  int ppgRaw = analogRead(PPG_PIN);

  int heartRate = map(ppgRaw, 0, 4095, 60, 120);

  int spo2 = map(ppgRaw, 0, 4095, 90, 100);

  // =========================================
  // RESPIRATION RATE
  // =========================================

  int respirationRate = map(ppgRaw, 0, 4095, 10, 24);

  // =========================================
  // BLOOD PRESSURE ESTIMATION
  // =========================================

  float systolic = 100 + (heartRate * 0.5);

  float diastolic = 65 + (heartRate * 0.2);

  // =========================================
  // SERIAL MONITOR OUTPUT
  // =========================================

  Serial.println("\n=================================");

  Serial.print("Timestamp: ");
  Serial.println(timestamp);

  // =====================
  // PPG / SPO2
  // =====================

  Serial.print("PPG Raw: ");
  Serial.println(ppgRaw);

  Serial.print("Heart Rate: ");
  Serial.print(heartRate);
  Serial.println(" BPM");

  Serial.print("SpO2: ");
  Serial.print(spo2);
  Serial.println(" %");

  // =====================
  // TEMPERATURE
  // =====================

  Serial.print("Skin Temperature: ");
  Serial.print(skinTemp);
  Serial.println(" C");

  // =====================
  // IMU
  // =====================

  Serial.println("Accelerometer:");

  Serial.print("X: ");
  Serial.print(a.acceleration.x);

  Serial.print("  Y: ");
  Serial.print(a.acceleration.y);

  Serial.print("  Z: ");
  Serial.println(a.acceleration.z);

  Serial.println("Gyroscope:");

  Serial.print("X: ");
  Serial.print(g.gyro.x);

  Serial.print("  Y: ");
  Serial.print(g.gyro.y);

  Serial.print("  Z: ");
  Serial.println(g.gyro.z);

  // =====================
  // EDA
  // =====================

  Serial.print("EDA Raw: ");
  Serial.println(edaRaw);

  Serial.print("Tonic Signal: ");
  Serial.println(tonic);

  Serial.print("Phasic Signal: ");
  Serial.println(phasic);

  // =====================
  // ECG
  // =====================

  Serial.print("ECG Raw: ");
  Serial.println(ecgRaw);

  // =====================
  // RESPIRATION
  // =====================

  Serial.print("Respiration Rate: ");
  Serial.print(respirationRate);
  Serial.println(" BPM");

  // =====================
  // BLOOD PRESSURE
  // =====================

  Serial.print("Blood Pressure: ");

  Serial.print((int)systolic);

  Serial.print("/");

  Serial.println((int)diastolic);

  delay(1000);
}