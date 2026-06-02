#define PPG_PIN 32

void setup() {
  Serial.begin(115200);
}

void loop() {

  int ppgRaw = analogRead(PPG_PIN);

  int heartRate = map(ppgRaw, 0, 4095, 60, 120);

  int spo2 = map(ppgRaw, 0, 4095, 90, 100);

  Serial.println("====== PPG / SpO2 ======");

  Serial.print("PPG Raw: ");
  Serial.println(ppgRaw);

  Serial.print("Heart Rate: ");
  Serial.print(heartRate);
  Serial.println(" BPM");

  Serial.print("SpO2: ");
  Serial.print(spo2);
  Serial.println(" %");

  delay(1000);
}