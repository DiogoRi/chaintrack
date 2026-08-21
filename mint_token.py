"""
mint_token.py — DePIN Urbano, Fase 3

Envia o token de recompensa (DEPIN) automaticamente para a carteira do
cidadão quando uma ocorrência é marcada como "concluída" no dashboard.

Pré-requisito: o contrato DePinToken.sol já deployado na Polygon Amoy via
Remix (mesmo fluxo do contrato de registro da Fase 2), com o endereço
salvo em TOKEN_CONTRACT_ADDRESS no .env.

A wallet que assina a transação de mint é a mesma WALLET_ADDRESS/PRIVATE_KEY
já usada para registrar ocorrências — ela precisa ser a "owner" do contrato
do token (ou seja, a mesma conta que fez o deploy no Remix).
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")
TOKEN_REWARD_AMOUNT = float(os.getenv("TOKEN_REWARD_AMOUNT", "10"))
TOKEN_DECIMALS = 18

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open("token_abi.json") as f:
    TOKEN_ABI = json.load(f)

_token_contract = None


def _get_contract():
    global _token_contract
    if _token_contract is None:
        if not TOKEN_CONTRACT_ADDRESS:
            raise RuntimeError(
                "TOKEN_CONTRACT_ADDRESS não configurado no .env. "
                "Faça o deploy do DePinToken.sol no Remix primeiro."
            )
        _token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS),
            abi=TOKEN_ABI,
        )
    return _token_contract


def mint_para(wallet_destino: str, quantidade_tokens: float = None) -> str:
    """
    Faz o mint de `quantidade_tokens` DEPIN para `wallet_destino`.
    Retorna o hash da transação (string). Lança exceção se der errado
    (o dashboard.py deve capturar e mostrar o erro sem travar a tela).
    """
    if quantidade_tokens is None:
        quantidade_tokens = TOKEN_REWARD_AMOUNT

    contract = _get_contract()
    quantidade_wei = int(quantidade_tokens * (10 ** TOKEN_DECIMALS))

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
    tx = contract.functions.mint(
        Web3.to_checksum_address(wallet_destino),
        quantidade_wei,
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 200000,
        "gasPrice": w3.eth.gas_price,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()


if __name__ == "__main__":
    # Teste manual rápido:
    #   python mint_token.py 0xSEU_ENDERECO_DE_TESTE
    import sys
    if len(sys.argv) < 2:
        print("Uso: python mint_token.py <endereco_wallet_destino>")
    else:
        destino = sys.argv[1]
        print(f"Mintando {TOKEN_REWARD_AMOUNT} DEPIN para {destino}...")
        tx = mint_para(destino)
        print(f"OK! Tx hash: {tx}")
        print(f"Veja em: https://amoy.polygonscan.com/tx/{tx}")
