#define PPG_PIN 32

void setup() {

  Serial.begin(115200);
}

void loop() {

  int ppgRaw = analogRead(PPG_PIN);

  int respirationRate = map(ppgRaw, 0, 4095, 10, 24);

  Serial.println("====== RESPIRATION ======");

  Serial.print("Respiration Rate: ");

  Serial.print(respirationRate);

  Serial.println(" BPM");

  delay(1000);
}