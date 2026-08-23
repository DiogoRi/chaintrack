"""
vigia_antena.py — DePIN Urbano, Fase 3

O "vigia" da antena: fica rodando no notebook durante a apresentação,
observando a blockchain e acendendo os LEDs da antena quando algo acontece.

POR QUE ISTO EXISTE
-------------------
O app está publicado em https://chaintrack.streamlit.app, o que permite
registrar ocorrências de qualquer celular, em qualquer rede. Mas o app roda
num servidor remoto, e nenhum servidor remoto tem um cabo USB ligado à
maquete. Se a antena dependesse do app, ela nunca acenderia na demo.

A solução é inverter a direção: em vez de o app avisar a antena, a antena
observa a blockchain. Ela não sabe quem registrou nem de onde veio o
registro — apenas lê o dado público e reage.

Isso é mais fiel ao que um nó DePIN realmente faz, e é um bom argumento
para a banca: a antena é um nó independente lendo a rede, não um LED
acionado pelo mesmo programa que gerou o evento.

O QUE ELE OBSERVA
-----------------
1. `total()` no contrato de ocorrências — quando aumenta, uma ocorrência
   nova foi registrada  ->  acende o LED_REGISTRO (GPIO2)
2. `totalSupply()` no contrato do token CP — quando aumenta, uma ocorrência
   foi concluída e o token foi enviado  ->  acende o LED_CONCLUIDA (GPIO4)

O segundo é um truque simples: como o token só é criado no momento em que
uma ocorrência é concluída, o total de tokens em circulação funciona como
um contador de conclusões. Não precisa ler eventos, o que evita limitações
de alguns servidores públicos de blockchain.

COMO USAR NO DIA
----------------
1. Ligue a ESP32 no notebook pelo cabo USB.
2. Rode:  python3 vigia_antena.py
3. Deixe rodando numa janela ao lado. Ele imprime cada evento que detecta.
4. Para encerrar: Control + C.

Observação: se a ocorrência for registrada SEM carteira, nenhum token é
criado — então o LED de conclusão não acende. Na demo, sempre preencher a
carteira.
"""

import os
import sys
import json
import time
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from antena_serial import enviar_sinal  # noqa: E402

load_dotenv(BASE_DIR / ".env")

CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")

# De quantos em quantos segundos consultar a blockchain.
# 3s é um bom equilíbrio: rápido o suficiente para parecer instantâneo na
# demo, sem martelar o servidor público.
INTERVALO_SEGUNDOS = 3


# ---------------------------------------------------------------------------
# O coração do vigia, isolado para poder ser testado sem blockchain nenhuma.
# Recebe funções de leitura e de sinalização em vez de chamá-las direto.
# ---------------------------------------------------------------------------
def checar_uma_vez(estado, ler_ocorrencias, ler_tokens, sinalizar, avisar=print):
    """
    Compara os contadores atuais com os da última verificação e dispara os
    sinais correspondentes. Devolve o estado atualizado.

    `estado` é um dicionário com as chaves "ocorrencias" e "tokens".
    Se a leitura falhar (rede instável), o estado é devolvido intacto e
    nada é disparado — nunca lança exceção.
    """
    novo = dict(estado)

    try:
        total_ocorrencias = ler_ocorrencias()
    except Exception as e:
        avisar(f"   (falha ao ler ocorrências: {e})")
        total_ocorrencias = None

    try:
        total_tokens = ler_tokens()
    except Exception as e:
        avisar(f"   (falha ao ler tokens: {e})")
        total_tokens = None

    if total_ocorrencias is not None:
        if total_ocorrencias > estado["ocorrencias"]:
            quantas = total_ocorrencias - estado["ocorrencias"]
            avisar(f"📍 NOVA OCORRÊNCIA detectada na blockchain "
                   f"(total: {total_ocorrencias}). Acendendo a antena...")
            for _ in range(quantas):
                sinalizar("REGISTRO")
        novo["ocorrencias"] = total_ocorrencias

    if total_tokens is not None:
        if total_tokens > estado["tokens"]:
            avisar("✅ CONCLUSÃO detectada na blockchain — token CP enviado. "
                   "Acendendo o segundo LED...")
            sinalizar("CONCLUIDA")
        novo["tokens"] = total_tokens

    return novo


# ---------------------------------------------------------------------------
# Ligação com o mundo real
# ---------------------------------------------------------------------------
def montar_leitores():
    """Conecta na blockchain e devolve as duas funções de leitura."""
    faltando = [n for n, v in {
        "CONTRACT_ADDRESS": CONTRACT_ADDRESS,
        "TOKEN_CONTRACT_ADDRESS": TOKEN_CONTRACT_ADDRESS,
        "RPC_URL": RPC_URL,
    }.items() if not v]
    if faltando:
        raise RuntimeError(
            "Faltam variáveis no .env: " + ", ".join(faltando))

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError(
            f"Não foi possível conectar em {RPC_URL}. "
            "Confira a internet ou troque o RPC_URL no .env.")

    with open(BASE_DIR / "abi.json") as f:
        abi_ocorrencias = json.load(f)
    with open(BASE_DIR / "token_abi.json") as f:
        abi_token = json.load(f)

    contrato_ocorrencias = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi_ocorrencias)
    contrato_token = w3.eth.contract(
        address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS), abi=abi_token)

    return (
        w3,
        lambda: contrato_ocorrencias.functions.total().call(),
        lambda: contrato_token.functions.totalSupply().call(),
    )


def main():
    print("=" * 66)
    print("            VIGIA DA ANTENA — DePIN Urbano")
    print("=" * 66)
    print()
    print("Este programa observa a blockchain e acende a antena quando")
    print("uma ocorrência é registrada ou concluída — não importa de qual")
    print("celular ou rede o registro tenha vindo.")
    print()

    try:
        w3, ler_ocorrencias, ler_tokens = montar_leitores()
    except Exception as e:
        print(f"❌ {e}")
        return 1

    print(f"Conectado à rede {w3.eth.chain_id} (80002 = Polygon Amoy)")

    # Testa a antena logo de cara, para você saber ANTES da apresentação
    # se o cabo está bem conectado.
    print("\nTestando a antena...")
    if enviar_sinal("REGISTRO"):
        print("✅ Antena respondeu — o LED deve ter piscado.")
    else:
        print("⚠️  Antena não respondeu. O vigia continua funcionando e")
        print("    avisando na tela, mas nenhum LED vai acender.")
        print("    Confira o cabo USB e o SERIAL_PORT no .env.")

    # Fotografia inicial: tudo que já existe não deve disparar nada.
    estado = {"ocorrencias": 0, "tokens": 0}
    try:
        estado["ocorrencias"] = ler_ocorrencias()
        estado["tokens"] = ler_tokens()
    except Exception as e:
        print(f"❌ Falha na leitura inicial: {e}")
        return 1

    print(f"\nPonto de partida: {estado['ocorrencias']} ocorrências já "
          f"registradas, {w3.from_wei(estado['tokens'], 'ether')} CP em circulação.")
    print(f"Verificando a cada {INTERVALO_SEGUNDOS} segundos.")
    print("\n>>> Pronto. Pode registrar pelo celular. (Control+C para encerrar)")
    print("-" * 66)

    try:
        while True:
            time.sleep(INTERVALO_SEGUNDOS)
            estado = checar_uma_vez(
                estado, ler_ocorrencias, ler_tokens, enviar_sinal)
    except KeyboardInterrupt:
        print("\n\nVigia encerrado. Até a próxima!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
