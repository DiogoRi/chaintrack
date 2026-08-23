"""
diagnostico_registro.py — DePIN Urbano, Fase 3 (versão 2)

Script temporário de diagnóstico. Não faz parte do sistema.

Descobriu-se que o abi.json mudou durante o projeto:
  - versão ORIGINAL:  registrar(string,string,string,int256,int256) / total()
  - versão ATUAL:     registrarOcorrencia(string,string,string,string) / totalRegistros()

Este script testa AS DUAS contra o contrato realmente publicado no endereço
do .env, e diz qual delas corresponde. Só faz leitura: NÃO envia transação
e NÃO gasta gas.

Rode:
    python3 diagnostico_registro.py
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")

print("=" * 64)
print("DIAGNÓSTICO — qual ABI corresponde ao contrato publicado?")
print("=" * 64)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
print(f"\nRPC: {RPC_URL}")
print(f"Conectado: {w3.is_connected()}  |  Chain ID: {w3.eth.chain_id}")
print(f"Contrato analisado: {CONTRACT_ADDRESS}")

endereco = Web3.to_checksum_address(CONTRACT_ADDRESS)
codigo = w3.eth.get_code(endereco)
print(f"Bytes de código no endereço: {len(codigo)}")
if len(codigo) == 0:
    print("\n>>> Não existe contrato nesse endereço. Pare aqui.")
    raise SystemExit(1)

remetente = Web3.to_checksum_address(WALLET_ADDRESS)


def testar(nome_abi, caminho_abi, nome_funcao_leitura):
    """Carrega um ABI e tenta chamar a função de leitura de contagem."""
    print(f"\n--- Testando ABI {nome_abi} ({caminho_abi}) ---")
    try:
        with open(caminho_abi) as f:
            abi = json.load(f)
    except FileNotFoundError:
        print(f"    Arquivo {caminho_abi} não encontrado — pulando.")
        return False

    contrato = w3.eth.contract(address=endereco, abi=abi)
    try:
        valor = getattr(contrato.functions, nome_funcao_leitura)().call()
        print(f"    ✅ {nome_funcao_leitura}() respondeu: {valor}")
        print(f"    >>> ESTE ABI CORRESPONDE AO CONTRATO PUBLICADO.")
        return True
    except Exception as e:
        print(f"    ❌ {nome_funcao_leitura}() falhou: {type(e).__name__}")
        return False


ok_atual = testar("ATUAL", "abi.json", "totalRegistros")
ok_original = testar("ORIGINAL (Fase 2)", "abi_original_fase2.json", "total")

print("\n" + "=" * 64)
print("CONCLUSÃO")
print("=" * 64)

if ok_original and not ok_atual:
    print("O contrato publicado é o ORIGINAL da Fase 2.")
    print("A função correta é: registrar(cid, descricao, endereco, lat, lng)")
    print("com latitude/longitude como NÚMEROS INTEIROS (int256).")
    print("=> Precisamos ajustar o app.py para chamar essa função.")
elif ok_atual and not ok_original:
    print("O contrato publicado corresponde ao abi.json ATUAL.")
    print("=> O problema é outro. Mande esta saída para o Claude.")
elif ok_atual and ok_original:
    print("Os dois responderam (situação inesperada).")
    print("=> Mande esta saída para o Claude.")
else:
    print("NENHUM dos dois ABIs corresponde ao contrato desse endereço.")
    print("=> O CONTRACT_ADDRESS do .env aponta para outro contrato.")
    print("=> Solução mais rápida: republicar o contrato de ocorrências")
    print("   no Remix (como fizemos com o token) e usar o novo endereço.")

print("\nCopie tudo acima e mande para o Claude.")
print("=" * 64)
