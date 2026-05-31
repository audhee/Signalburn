#define ECG_PIN 35

void setup() {

  Serial.begin(115200);
}

void loop() {

  int ecgRaw = analogRead(ECG_PIN);

  Serial.println("====== ECG ======");

  Serial.print("ECG Raw Signal: ");

  Serial.println(ecgRaw);

  delay(500);
}