#define EDA_PIN 34

void setup() {

  Serial.begin(115200);
}

void loop() {

  int edaRaw = analogRead(EDA_PIN);

  float tonic = edaRaw * 0.7;

  float phasic = edaRaw * 0.3;

  Serial.println("====== EDA ======");

  Serial.print("EDA Raw: ");
  Serial.println(edaRaw);

  Serial.print("Tonic Signal: ");
  Serial.println(tonic);

  Serial.print("Phasic Signal: ");
  Serial.println(phasic);

  delay(1000);
}