"""
Script de DIAGNÓSTICO, temporário — não faz parte do app.

Faz exatamente a mesma chamada que criar_participante_automatico() faz
dentro do app, mas mostrando o erro de verdade em vez de escondê-lo, para
descobrimos por que a criação automática do participante não está
funcionando.

Rodar com: python3 diagnostico_participante.py
Pode apagar este arquivo depois de usar.
"""

import os
import uuid

import requests
from dotenv import load_dotenv

load_dotenv(".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

print("SUPABASE_URL carregado:", SUPABASE_URL)
print("SUPABASE_SECRET_KEY carregado:", "sim, tem valor" if SUPABASE_SECRET_KEY else "NÃO — está vazio!")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    print("\nParou aqui: falta SUPABASE_URL ou SUPABASE_SECRET_KEY no .env.")
    raise SystemExit(1)

url = f"{SUPABASE_URL}/rest/v1/rpc/criar_participante"
headers = {
    "apikey": SUPABASE_SECRET_KEY,
    "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
    "Content-Type": "application/json",
}
apelido_teste = "cidadao_diagnostico_" + uuid.uuid4().hex[:6]

print("\nChamando:", url)
print("Corpo enviado:", {"p_apelido": apelido_teste})

try:
    resp = requests.post(
        url,
        headers=headers,
        json={"p_apelido": apelido_teste},
        timeout=15,
    )
    print("\nStatus HTTP:", resp.status_code)
    print("Resposta (texto puro):")
    print(resp.text)
except Exception as e:
    print("\nDeu uma exceção de verdade ao tentar chamar:")
    print(type(e).__name__, "-", e)
