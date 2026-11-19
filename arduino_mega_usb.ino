// CONSERVA : Arduino Mega 2560 + DHT11 + buzzer, liaison directe USB vers l'application.
// DHT11 DATA -> broche 2 ; buzzer passif -> broche 8.
// Le port USB envoie une ligne JSON à 9600 bauds, lue par le navigateur.
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11
const int BUZZER_PIN = 8;
const float SEUIL_TEMP = 40.0;
const unsigned long PERIODE_MS = 2000;

DHT dht(DHTPIN, DHTTYPE);

void envoyerJson(Print &sortie, float temperatureC, float humidite) {
  sortie.print(F("{\"temperature\":"));
  sortie.print(temperatureC, 1);
  sortie.print(F(",\"humidite\":"));
  sortie.print(humidite, 1);
  sortie.println(F("}"));
}

void setup() {
  Serial.begin(9600);   // USB vers l'application sur le PC
  pinMode(BUZZER_PIN, OUTPUT);
  noTone(BUZZER_PIN);
  dht.begin();
}

void loop() {
  delay(PERIODE_MS);
  const float humidite = dht.readHumidity();
  const float temperatureC = dht.readTemperature();

  if (isnan(humidite) || isnan(temperatureC)) {
    noTone(BUZZER_PIN);
    return; // Ne pas envoyer de ligne invalide au navigateur.
  }

  envoyerJson(Serial, temperatureC, humidite);

  if (temperatureC > SEUIL_TEMP) {
    tone(BUZZER_PIN, 2500);
    delay(250);
    noTone(BUZZER_PIN);
    delay(250);
  } else {
    noTone(BUZZER_PIN);
  }
}
