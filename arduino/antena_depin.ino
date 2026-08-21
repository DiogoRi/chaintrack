/*
  antena_depin.ino
  DePIN Urbano — Future Makers FIAP — Fase 3

  Roda na placa ESP32 e recebe comandos via USB serial vindos do notebook
  (enviados por antena_serial.py, em Python). Acende/pisca LEDs que
  representam a antena/nó da rede reagindo em tempo real.

  IMPORTANTE (placa é ESP32, não Arduino Uno): usamos os pinos GPIO2 e
  GPIO4, que são seguros de usar como saída na maioria das placas ESP32
  Dev Module. Evite usar os pinos GPIO6 a GPIO11 — no ESP32 eles costumam
  estar ligados internamente à memória flash e não devem ser usados como
  E/S. O GPIO2, inclusive, já é o LED azul embutido em muitas placas ESP32
  — então mesmo sem LED externo ligado, dá pra ver o "REGISTRO" piscando
  nesse LED da própria placa.

  No Arduino IDE, configure a placa como "ESP32 Dev Module" (Boards
  Manager → procure "esp32" → instalar o pacote da Espressif; se ainda
  não tiver o link, adicione em File > Preferences > Additional Board
  Manager URLs:
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json)

  Comandos aceitos (uma linha terminada em \n):
    REGISTRO   -> pisca o LED_REGISTRO 3x e deixa aceso (ocorrência recebida)
    CONCLUIDA  -> acende o LED_CONCLUIDA (ocorrência concluída + token enviado)
    RESET      -> apaga os dois LEDs (usar entre uma demo e outra)

  Ligação (se só tiver 1 LED externo disponível, ligue só o LED_REGISTRO
  e ignore o comando CONCLUIDA — ele simplesmente não vai fazer nada, sem
  causar erro; o GPIO2 já pisca sozinho no LED embutido da placa mesmo
  sem nada ligado):
    GPIO2 -> resistor 220-330 ohm -> perna longa (anodo) do LED -> perna
             curta (catodo) no GND         [LED_REGISTRO]
    GPIO4 -> resistor 220-330 ohm -> perna longa (anodo) do LED -> perna
             curta (catodo) no GND         [LED_CONCLUIDA]
*/

const int LED_REGISTRO = 2;
const int LED_CONCLUIDA = 4;

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
