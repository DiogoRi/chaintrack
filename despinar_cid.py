"""
Script pra despinar (unpin) um CID específico do Pinata — a pedido do Rafa,
depois do teste dele com foto e endereço reais indo pro IPFS.

Importante: isso NÃO garante que o arquivo suma da rede IPFS por completo
(qualquer outro nó que já tenha baixado uma cópia pode continuar servindo o
conteúdo), mas remove do nosso próprio Pinata — reduz a exposição, não é
apagamento garantido. Isso também não afeta o que já foi gravado on-chain
(a transação de registro na Amoy é permanente e não tem como ser desfeita).

Rodar com: python3 despinar_cid.py <CID>
Exemplo:   python3 despinar_cid.py QmXdwxxFvhPgv345JFRgJE3CMkqqZRGwn8r2RB8B....

Pode apagar este arquivo depois de usar.
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(".env")

PINATA_JWT = os.getenv("PINATA_JWT")

print("PINATA_JWT carregado:", "sim, tem valor" if PINATA_JWT else "NÃO — está vazio!")

if not PINATA_JWT:
    print("\nParou aqui: falta PINATA_JWT no .env.")
    raise SystemExit(1)

if len(sys.argv) < 2:
    print("\nUso: python3 despinar_cid.py <CID>")
    raise SystemExit(1)

cid = sys.argv[1].strip()
url = f"https://api.pinata.cloud/pinning/unpin/{cid}"
headers = {"Authorization": f"Bearer {PINATA_JWT}"}

print("\nDespinando:", cid)

try:
    resp = requests.delete(url, headers=headers, timeout=15)
    print("\nStatus HTTP:", resp.status_code)
    print("Resposta:")
    print(resp.text)
    if resp.status_code == 200:
        print("\nOK — despinado do nosso Pinata.")
except Exception as e:
    print("\nDeu uma exceção de verdade ao tentar despinar:")
    print(type(e).__name__, "-", e)
