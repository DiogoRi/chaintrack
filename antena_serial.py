"""
antena_serial.py — DePIN Urbano, Fase 3

Camada de comunicação com a antena física (Arduino) via USB serial.

Design importante: NUNCA deixa uma falha na antena travar o app principal.
Se o Arduino não estiver plugado, com a porta errada, ou desconectar no meio
da apresentação, o app continua funcionando normalmente (só não acende a luz).
Isso segue o mesmo princípio de resiliência dos "ajustes de risco" da Fase 2.

Uso:
    from antena_serial import enviar_sinal
    enviar_sinal("REGISTRO")    # ocorrência recebida
    enviar_sinal("CONCLUIDA")   # ocorrência concluída / token enviado
"""

import os
import time
import serial  # pyserial

# Configuração via .env (veja .env.example)
#   Windows costuma ser algo como "COM3", "COM4"...
#   Mac costuma ser algo como "/dev/cu.usbmodemXXXX" ou "/dev/cu.usbserial-XXXX"
#   Linux costuma ser "/dev/ttyUSB0" ou "/dev/ttyACM0"
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = int(os.getenv("BAUD_RATE", "9600"))

# Tempo que o Arduino leva pra reiniciar quando a porta serial é aberta
# (comportamento normal de placas Uno/Nano ao conectar por USB).
TEMPO_BOOT_ARDUINO = 2.0


def enviar_sinal(comando: str, timeout: float = 3.0) -> bool:
    """
    Abre a porta serial, envia o comando (ex: "REGISTRO" ou "CONCLUIDA")
    e fecha a conexão em seguida.

    Retorna True se o comando foi enviado, False se a antena não está
    acessível (não plugada, porta errada, etc). Nunca lança exceção.
    """
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=timeout) as ser:
            time.sleep(TEMPO_BOOT_ARDUINO)
            ser.write(f"{comando}\n".encode("utf-8"))
        return True
    except Exception as e:
        print(f"[antena] Não foi possível enviar sinal '{comando}' para a antena: {e}")
        return False


def testar_conexao() -> bool:
    """
    Testa rapidamente se a antena responde "ANTENA_PRONTA" ao conectar.
    Útil para rodar antes da apresentação e confirmar que está tudo certo.
    Rode: python antena_serial.py
    """
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=3.0) as ser:
            time.sleep(TEMPO_BOOT_ARDUINO)
            linha = ser.readline().decode("utf-8", errors="ignore").strip()
            if linha:
                print(f"[antena] Antena respondeu: '{linha}'")
                return True
            print("[antena] Antena conectou, mas não respondeu nada. Confira o sketch.")
            return False
    except Exception as e:
        print(f"[antena] Falha ao conectar na porta {SERIAL_PORT}: {e}")
        return False


if __name__ == "__main__":
    print(f"Testando conexão com a antena em {SERIAL_PORT} @ {BAUD_RATE} baud...")
    ok = testar_conexao()
    if ok:
        print("Enviando sinal de teste REGISTRO...")
        enviar_sinal("REGISTRO")
    else:
        print("Ajuste SERIAL_PORT no .env e tente novamente.")
