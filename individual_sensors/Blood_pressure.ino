#define PPG_PIN 32

void setup() {

  Serial.begin(115200);
}

void loop() {

  int ppgRaw = analogRead(PPG_PIN);

  int heartRate = map(ppgRaw, 0, 4095, 60, 120);

  float systolic = 100 + (heartRate * 0.5);

  float diastolic = 65 + (heartRate * 0.2);

  Serial.println("====== BLOOD PRESSURE ======");

  Serial.print("Heart Rate: ");
  Serial.println(heartRate);

  Serial.print("Blood Pressure: ");

  Serial.print((int)systolic);

  Serial.print("/");

  Serial.println((int)diastolic);

  delay(1000);
}