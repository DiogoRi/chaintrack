"""
mint_token.py — DePIN Urbano, Fase 3

Quando uma ocorrência é marcada como "concluída" no dashboard, este módulo
dispara UMA transação na blockchain que faz duas coisas ao mesmo tempo:
  1. Registra permanentemente que a ocorrência (identificada pelo CID da
     foto, o mesmo CID já usado no registro original) foi concluída.
  2. Envia o token de recompensa CP (Cidadão Participativo) para a
     carteira do cidadão.

Sendo uma transação só (função concluirOcorrencia no contrato), as duas
coisas ficam atomicamente ligadas — não tem como o token ser enviado sem
a prova de conclusão ficar registrada, nem o contrário.

Pré-requisito: o contrato CidadaoParticipativoToken.sol já deployado na Polygon Amoy via
Remix (mesmo fluxo do contrato de registro da Fase 2), com o endereço
salvo em TOKEN_CONTRACT_ADDRESS no .env.

A wallet que assina a transação é a mesma WALLET_ADDRESS/PRIVATE_KEY já
usada para registrar ocorrências — ela precisa ser a "owner" do contrato
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
                "Faça o deploy do CidadaoParticipativoToken.sol no Remix primeiro."
            )
        _token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS),
            abi=TOKEN_ABI,
        )
    return _token_contract


def concluir_ocorrencia(cid: str, wallet_destino: str, quantidade_tokens: float = None) -> str:
    """
    Chama concluirOcorrencia(cid, destinatario, quantidade) no contrato:
    registra on-chain que a ocorrência de CID `cid` foi concluída E manda
    o token pra `wallet_destino`, na mesma transação.

    Espera a transação ser minerada e confere se ela não reverteu antes
    de devolver o hash. Lança exceção se der errado — o dashboard.py
    captura e mostra o erro sem travar a tela.
    """
    if quantidade_tokens is None:
        quantidade_tokens = TOKEN_REWARD_AMOUNT

    contract = _get_contract()
    quantidade_wei = int(quantidade_tokens * (10 ** TOKEN_DECIMALS))

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
    tx = contract.functions.concluirOcorrencia(
        cid,
        Web3.to_checksum_address(wallet_destino),
        quantidade_wei,
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 250000,
        "gasPrice": w3.eth.gas_price,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    recibo = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if recibo.status != 1:
        raise RuntimeError(
            "A transação foi minerada mas reverteu (status 0). "
            "Confira se a wallet configurada é a dona (owner) do contrato do token."
        )

    return tx_hash.hex()


if __name__ == "__main__":
    # Teste manual rápido:
    #   python mint_token.py <cid_de_teste> <endereco_wallet_destino>
    import sys
    if len(sys.argv) < 3:
        print("Uso: python mint_token.py <cid_de_teste> <endereco_wallet_destino>")
    else:
        cid_teste, destino = sys.argv[1], sys.argv[2]
        print(f"Concluindo ocorrência '{cid_teste}' e mintando {TOKEN_REWARD_AMOUNT} CP para {destino}...")
        tx = concluir_ocorrencia(cid_teste, destino)
        print(f"OK! Tx hash: {tx}")
        print(f"Veja em: https://amoy.polygonscan.com/tx/{tx}")
