#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 4

OneWire oneWire(ONE_WIRE_BUS);

DallasTemperature sensors(&oneWire);

void setup() {

  Serial.begin(115200);

  sensors.begin();
}

void loop() {

  sensors.requestTemperatures();

  float temp = sensors.getTempCByIndex(0);

  Serial.println("====== TEMPERATURE ======");

  Serial.print("Skin Temperature: ");
  Serial.print(temp);
  Serial.println(" C");

  delay(1000);
}