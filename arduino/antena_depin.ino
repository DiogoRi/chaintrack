/*
  antena_depin.ino
  DePIN Urbano — Future Makers FIAP — Fase 3

  Roda no Arduino (Uno/Nano/compatível) e recebe comandos via USB serial
  vindos do notebook (enviados por antena_serial.py). Acende/pisca LEDs
  que representam a antena/nó da rede reagindo em tempo real.

  Comandos aceitos (uma linha terminada em \n):
    REGISTRO   -> pisca o LED_REGISTRO 3x e deixa aceso (ocorrência recebida)
    CONCLUIDA  -> acende o LED_CONCLUIDA (ocorrência concluída + token enviado)
    RESET      -> apaga os dois LEDs (usar entre uma demo e outra)

  Ligação (se só tiver 1 LED disponível, ligue só o LED_REGISTRO e ignore
  o comando CONCLUIDA — ele simplesmente não vai fazer nada, sem causar erro):
    Pino 8  -> resistor 220-330 ohm -> perna longa (anodo) do LED -> perna
               curta (catodo) no GND         [LED_REGISTRO]
    Pino 9  -> resistor 220-330 ohm -> perna longa (anodo) do LED -> perna
               curta (catodo) no GND         [LED_CONCLUIDA]
*/

const int LED_REGISTRO = 8;
const int LED_CONCLUIDA = 9;

void piscar(int pino, int vezes, int duracaoMs) {
  for (int i = 0; i < vezes; i++) {
    digitalWrite(pino, HIGH);
    delay(duracaoMs);
    digitalWrite(pino, LOW);
    delay(duracaoMs);
  }
}

void setup() {
  pinMode(LED_REGISTRO, OUTPUT);
  pinMode(LED_CONCLUIDA, OUTPUT);
  digitalWrite(LED_REGISTRO, LOW);
  digitalWrite(LED_CONCLUIDA, LOW);

  Serial.begin(9600);
  delay(500);
  Serial.println("ANTENA_PRONTA");
}

void loop() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "REGISTRO") {
      piscar(LED_REGISTRO, 3, 200);
      digitalWrite(LED_REGISTRO, HIGH);
      Serial.println("OK_REGISTRO");
    } else if (comando == "CONCLUIDA") {
      digitalWrite(LED_CONCLUIDA, HIGH);
      Serial.println("OK_CONCLUIDA");
    } else if (comando == "RESET") {
      digitalWrite(LED_REGISTRO, LOW);
      digitalWrite(LED_CONCLUIDA, LOW);
      Serial.println("OK_RESET");
    }
  }
}
