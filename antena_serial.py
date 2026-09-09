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
from pathlib import Path

from dotenv import load_dotenv

# Carrega o .env aqui dentro, e não só no app que importa este arquivo.
# Motivo: este módulo também é usado sozinho (python3 antena_serial.py) e
# pelo vigia. Se depender de quem importa ter carregado o .env antes, a
# porta serial vem errada e a antena simplesmente não responde, sem erro
# aparente. Foi exatamente o que aconteceu no primeiro teste no Mac.
load_dotenv(Path(__file__).resolve().parent / ".env")

# O pyserial é importado de forma tolerante: se a biblioteca não estiver
# instalada na máquina (por exemplo, num notebook que só vai rodar o
# dashboard, sem antena), o app PRECISA continuar funcionando. Sem essa
# proteção, um "import serial" no topo derrubaria o app inteiro só porque
# a antena não está em uso.
try:
    import serial  # pyserial
    SERIAL_DISPONIVEL = True
except ImportError:
    serial = None
    SERIAL_DISPONIVEL = False
    print(
        "[antena] Biblioteca 'pyserial' não instalada — a antena fica "
        "desativada, mas o resto do sistema funciona normalmente. "
        "Para habilitar: pip3 install pyserial"
    )

# Configuração via .env (veja .env.example)
#   Windows costuma ser algo como "COM3", "COM4"...
#   Mac costuma ser algo como "/dev/cu.usbmodemXXXX" ou "/dev/cu.usbserial-XXXX"
#   Linux costuma ser "/dev/ttyUSB0" ou "/dev/ttyACM0"
# Lidas por função, e não uma única vez ao importar. Assim, mesmo que o
# .env seja carregado depois deste modulo, o valor certo é usado.
def porta_serial() -> str:
    return os.getenv("SERIAL_PORT", "/dev/ttyUSB0")


def baud_rate() -> int:
    try:
        return int(os.getenv("BAUD_RATE", "9600"))
    except ValueError:
        return 9600

# Tempo que o Arduino leva pra reiniciar quando a porta serial é aberta
# (comportamento normal de placas Uno/Nano ao conectar por USB).
TEMPO_BOOT_ARDUINO = 2.0


def enviar_sinal(comando: str, timeout: float = 3.0) -> bool:
    """
    Abre a porta serial, envia o comando (ex: "REGISTRO" ou "CONCLUIDA")
    e fecha a conexão em seguida.

    Retorna True se o comando foi enviado, False se a antena não está
    acessível (não plugada, porta errada, pyserial ausente, etc).
    Nunca lança exceção.
    """
    if not SERIAL_DISPONIVEL:
        print(f"[antena] Sinal '{comando}' ignorado: pyserial não instalado.")
        return False
    try:
        with serial.Serial(porta_serial(), baud_rate(), timeout=timeout) as ser:
            # Abrir a porta reinicia a placa. Esperamos ela terminar de subir
            # antes de falar, senão o comando se perde no meio do arranque.
            time.sleep(TEMPO_BOOT_ARDUINO)
            ser.reset_input_buffer()
            ser.write(f"{comando}\n".encode("utf-8"))
            ser.flush()
            # Um respiro antes de fechar: fechar imediatamente após escrever
            # pode cortar a transmissão no meio.
            time.sleep(0.3)
        return True
    except Exception as e:
        print(f"[antena] Não foi possível enviar sinal '{comando}' para a antena: {e}")
        return False


def testar_conexao() -> bool:
    """
    Testa rapidamente se a antena responde "ANTENA_PRONTA" ao conectar.
    Útil para rodar antes da apresentação e confirmar que está tudo certo.
    Rode: python3 antena_serial.py
    """
    if not SERIAL_DISPONIVEL:
        print("[antena] pyserial não instalado. Rode: pip3 install pyserial")
        return False
    try:
        with serial.Serial(porta_serial(), baud_rate(), timeout=1.0) as ser:
            # Ao abrir a porta, a ESP32 reinicia e imprime as mensagens do
            # próprio carregador dela, numa velocidade diferente da nossa.
            # Lido a 9600, isso vira lixo. Por isso esperamos a placa subir e
            # jogamos fora tudo que chegou antes de começar a conversa.
            time.sleep(TEMPO_BOOT_ARDUINO)
            ser.reset_input_buffer()

            # Em vez de só escutar, mandamos um comando. Assim o teste também
            # acende o LED, e dá para confirmar com os olhos, não só pela tela.
            ser.write(b"REGISTRO\n")
            ser.flush()

            esperadas = ("ANTENA_PRONTA", "OK_REGISTRO", "OK_")
            limite = time.time() + 6.0
            recebidas = []

            while time.time() < limite:
                bruta = ser.readline()
                if not bruta:
                    continue
                linha = bruta.decode("utf-8", errors="ignore").strip()
                if not linha:
                    continue
                recebidas.append(linha)
                if any(linha.startswith(e) for e in esperadas):
                    print(f"[antena] Antena respondeu: '{linha}'")
                    print("[antena] O LED deve ter piscado 3 vezes.")
                    return True

            if recebidas:
                print("[antena] A placa respondeu, mas nada reconhecível:")
                for linha in recebidas[-5:]:
                    print(f"         {linha!r}")
                print("[antena] Confira se o sketch gravado é o antena_depin.ino")
                print("         e se a velocidade no .env é 9600.")
            else:
                print("[antena] A porta abriu, mas a placa não respondeu nada.")
                print("         Possíveis causas, nesta ordem:")
                print("         1. O cabo é só de carga, sem fios de dados")
                print("         2. O Serial Monitor do Arduino IDE está aberto")
                print("         3. O sketch não está gravado na placa")
            return False
    except Exception as e:
        print(f"[antena] Falha ao conectar na porta {porta_serial()}: {e}")
        return False


if __name__ == "__main__":
    print(f"Testando conexão com a antena em {porta_serial()} @ {baud_rate()} baud...")
    if testar_conexao():
        print("\nTudo certo. A antena está pronta para a demonstração.")
    else:
        print("\nConfira o SERIAL_PORT no .env e as causas acima.")
