"""
worker_blockchain.py — Bloco 5 (DePIN Urbano / ChainTrack)

Duas responsabilidades independentes, chamadas em sequência a cada volta do
laço principal. Elas não compartilham estado nem se chamam uma à outra —
só rodam uma depois da outra no mesmo processo por simplicidade (ver
conversa sobre "duas linhas de execução"; migrar cada uma pra sua própria
thread no futuro é só embrulhar a chamada abaixo num `while True` separado).

1. avancar_status_automatico()
   Só ocorrências da gincana (origem='evento'). Empurra sozinho o status
   por TEMPO, sem depender de a blockchain já ter confirmado nada:

       registrado --seg_para_andamento--> em_andamento
       em_andamento --seg_para_conclusao--> concluido

   Os segundos são lidos ao vivo de `evento_config` a cada volta (hoje 15
   e 15), então dá pra ajustar no banco sem reiniciar o worker.

2. processar_fila_blockchain()
   TODAS as ocorrências (normais ou de evento). Cuida da máquina de estados
   técnica (`etapa`: criada/foto_ok -> registrada -> concluida):
     - manda a transação de REGISTRO assim que a ocorrência existir (ela já
       nasce com a foto no Pinata, então na prática já está pronta assim
       que aparece no banco);
     - manda a transação de CONCLUSÃO (mint do CP) assim que o status virar
       'concluido' (pelo ciclo automático acima OU pelo botão do dashboard
       da prefeitura) **e** o registro já estiver confirmado on-chain.
   O CP mintado vai sempre para a carteira de custódia do próprio projeto
   (WALLET_ADDRESS) — nunca para uma carteira de cidadão, porque esse campo
   foi removido do formulário (decisão de 16/09).

Regras de segurança contra transação duplicada e nonce colidindo, tiradas
direto do documento de esquema do Supabase (06/09):
  - o hash é gravado no banco NO INSTANTE DO ENVIO, antes de esperar a
    confirmação. Se o processo cair ou a confirmação demorar demais, o
    hash já vai estar lá — o worker NUNCA reenvia uma ocorrência que já
    tem hash, só confere se já minerou (`_retomar_pendentes`).
  - no máximo UMA transação de blockchain é enviada por volta do laço —
    mantém tudo em fila, sem risco de duas transações pegarem o mesmo
    nonce.
  - depois de 3 tentativas sem sucesso, o worker desiste daquela ocorrência
    e grava o erro em `erro` — ela aparece na futura lista de "ocorrências
    travadas" do dashboard, mas não trava o worker nem as outras.

Uso:
    python worker_blockchain.py
Roda para sempre até Ctrl+C. Precisa do mesmo `.env` que o `app.py` e o
`mint_token.py` já usam (SUPABASE_URL, SUPABASE_SECRET_KEY, PRIVATE_KEY,
WALLET_ADDRESS, CONTRACT_ADDRESS, TOKEN_CONTRACT_ADDRESS, RPC_URL,
TOKEN_REWARD_AMOUNT) e dos mesmos `abi.json` / `token_abi.json` na mesma
pasta.
"""

import os
import time
import json
import socket
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv
from web3 import Web3

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")
TOKEN_REWARD_AMOUNT = float(os.getenv("TOKEN_REWARD_AMOUNT", "10"))
TOKEN_DECIMALS = 18
COORD_ESCALA = 1_000_000

_HEADERS = {
    "apikey": SUPABASE_SECRET_KEY,
    "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
    "Content-Type": "application/json",
}
_TIMEOUT = 15  # segundos, pra cada chamada REST individual

_REST_OCORRENCIAS = f"{SUPABASE_URL}/rest/v1/ocorrencias"
_REST_EVENTO_CONFIG = f"{SUPABASE_URL}/rest/v1/evento_config"
_REST_WORKER_LEASE = f"{SUPABASE_URL}/rest/v1/worker_lease"

NOME_WORKER = "worker_blockchain"
DONO_LEASE = f"{socket.gethostname()}-{os.getpid()}"

# A confirmação de uma transação pode levar até 120s (ver wait_for_transaction_receipt
# abaixo). O lease PRECISA durar mais que isso, senão um segundo worker acha que o
# primeiro morreu (porque ele fica bloqueado esperando, sem renovar) e assume no meio
# de um envio real — é exatamente a colisão de nonce que a fila de 1-por-vez existe
# pra evitar. Por isso 180s aqui, bem acima do timeout de confirmação (120s) e do
# timeout de rede de cada chamada (15s).
DURACAO_LEASE_SEG = 180
INTERVALO_LOOP_SEG = 5

RETRIES_MAX = 3                 # regra do documento de esquema (06/09)
SEG_ESPERA_RETOMADA = 60        # não reprocessa uma tentativa mais nova que isso

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open(BASE_DIR / "abi.json") as f:
    CONTRACT_ABI = json.load(f)
with open(BASE_DIR / "token_abi.json") as f:
    TOKEN_ABI = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)
token_contract = w3.eth.contract(
    address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS), abi=TOKEN_ABI
)


def _log(msg):
    agora = datetime.now().strftime("%H:%M:%S")
    print(f"[{agora}] {msg}", flush=True)


def _agora_iso():
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(valor):
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Acesso ao Supabase — REST puro com a chave de serviço, igual ao resto do
# projeto (ocorrencias.py já faz assim pro Pinata e pro Nominatim).
# ---------------------------------------------------------------------------

def _patch_ocorrencia(id_, campos):
    resp = requests.patch(
        _REST_OCORRENCIAS, headers=_HEADERS,
        params={"id": f"eq.{id_}"}, json=campos, timeout=_TIMEOUT,
    )
    resp.raise_for_status()


def buscar_evento_config():
    """evento_config tem as colunas (chave, valor) — ver esquema de 06/09."""
    resp = requests.get(_REST_EVENTO_CONFIG, headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    return {linha["chave"]: linha["valor"] for linha in resp.json()}


# ---------------------------------------------------------------------------
# Lease — garante um único worker "ativo" por vez (tabela worker_lease, já
# existente no banco: nome, owner, lease_ate, visto_em, fila, ultimo_erro).
# ---------------------------------------------------------------------------

def obter_lease():
    """
    True se este processo pode trabalhar nesta volta (e já renovou a
    concessão); False se outro worker é dono e a concessão dele não venceu.
    """
    resp = requests.get(
        _REST_WORKER_LEASE, headers=_HEADERS,
        params={"nome": f"eq.{NOME_WORKER}", "select": "*"}, timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    linhas = resp.json()
    agora = datetime.now(timezone.utc)

    if not linhas:
        requests.post(
            _REST_WORKER_LEASE, headers=_HEADERS,
            json={
                "nome": NOME_WORKER, "owner": DONO_LEASE,
                "lease_ate": (agora + timedelta(seconds=DURACAO_LEASE_SEG)).isoformat(),
                "visto_em": _agora_iso(), "fila": 0,
            }, timeout=_TIMEOUT,
        )
        return True

    linha = linhas[0]
    lease_ate = linha.get("lease_ate")
    dono_atual = linha.get("owner")

    livre = (
        not lease_ate
        or not dono_atual
        or dono_atual == DONO_LEASE
        or _parse_iso(lease_ate) < agora
    )
    if not livre:
        return False

    _patch_worker_lease({
        "owner": DONO_LEASE,
        "lease_ate": (agora + timedelta(seconds=DURACAO_LEASE_SEG)).isoformat(),
        "visto_em": _agora_iso(),
    })
    return True


def _patch_worker_lease(campos):
    resp = requests.patch(
        _REST_WORKER_LEASE, headers=_HEADERS,
        params={"nome": f"eq.{NOME_WORKER}"}, json=campos, timeout=_TIMEOUT,
    )
    resp.raise_for_status()


def registrar_erro_lease(mensagem):
    try:
        _patch_worker_lease({"ultimo_erro": str(mensagem)[:500], "visto_em": _agora_iso()})
    except Exception:
        pass  # heartbeat/diagnóstico não pode derrubar o worker


def _atualizar_fila_visivel():
    """
    DESLIGADA por enquanto (19/09) — o Diogo pediu pra confirmar primeiro
    pra que a coluna `fila` realmente serve antes de escrever nela, já que
    não tinha documentação nenhuma. Ver "Fase 5 - Plano de execucao.md"
    pra checar se já foi confirmado; enquanto não for, esta função não é
    chamada em lugar nenhum (ver rodar_uma_volta abaixo).
    """
    try:
        resp = requests.get(
            _REST_OCORRENCIAS,
            headers={**_HEADERS, "Prefer": "count=exact"},
            params={"etapa": "neq.concluida", "select": "id", "limit": "1"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Range", "0/0").split("/")[-1])
        _patch_worker_lease({"fila": total})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1) Ciclo automático do evento — só por tempo, só origem='evento'
# ---------------------------------------------------------------------------

def avancar_status_automatico():
    config = buscar_evento_config()
    seg_andamento = int(config.get("seg_para_andamento", 15))
    seg_conclusao = int(config.get("seg_para_conclusao", 15))
    agora = datetime.now(timezone.utc)

    resp = requests.get(
        _REST_OCORRENCIAS, headers=_HEADERS,
        params={"origem": "eq.evento", "status": "eq.registrado", "select": "id,criado_em"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    for linha in resp.json():
        if (agora - _parse_iso(linha["criado_em"])).total_seconds() >= seg_andamento:
            _patch_ocorrencia(linha["id"], {"status": "em_andamento", "em_andamento_em": _agora_iso()})
            _log(f"ocorrência {linha['id']}: registrado -> em_andamento (automático)")

    resp = requests.get(
        _REST_OCORRENCIAS, headers=_HEADERS,
        params={"origem": "eq.evento", "status": "eq.em_andamento", "select": "id,em_andamento_em"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    for linha in resp.json():
        if not linha.get("em_andamento_em"):
            continue
        if (agora - _parse_iso(linha["em_andamento_em"])).total_seconds() >= seg_conclusao:
            _patch_ocorrencia(linha["id"], {"status": "concluido", "concluido_em": _agora_iso()})
            _log(f"ocorrência {linha['id']}: em_andamento -> concluido (automático)")


# ---------------------------------------------------------------------------
# 2) Fila de blockchain — registro + conclusão (mint), qualquer origem
# ---------------------------------------------------------------------------

def processar_fila_blockchain():
    # Primeiro confere transações já enviadas que ainda não confirmaram
    # (nunca reenvia — só olha se já minerou).
    _retomar_pendentes()

    if _enviar_um_registro_pendente():
        return  # uma ação de blockchain por volta

    _enviar_uma_conclusao_pendente()


def _candidatas(params):
    resp = requests.get(_REST_OCORRENCIAS, headers=_HEADERS, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    limite = time.time() - SEG_ESPERA_RETOMADA
    return [
        o for o in resp.json()
        if not o.get("ultima_tentativa") or _parse_iso(o["ultima_tentativa"]).timestamp() < limite
    ]


def _enviar_um_registro_pendente():
    candidatas = _candidatas({
        "etapa": "in.(criada,foto_ok)",
        "foto_cid": "not.is.null",
        "foto_falhou": "eq.false",
        "tx_hash_registro": "is.null",
        "tentativas": f"lt.{RETRIES_MAX}",
        "select": "id,foto_cid,descricao,endereco,lat,lng,tentativas",
        "order": "criado_em.asc",
        "limit": "5",
    })
    if not candidatas:
        return False
    try:
        _enviar_registro(candidatas[0])
    except Exception as e:
        _tratar_falha_antes_do_envio(candidatas[0], e)
    return True


def _enviar_uma_conclusao_pendente():
    candidatas = _candidatas({
        "etapa": "eq.registrada",
        "status": "eq.concluido",
        "tx_hash_conclusao": "is.null",
        "tentativas": f"lt.{RETRIES_MAX}",
        "select": "id,foto_cid,tentativas",
        "order": "concluido_em.asc",
        "limit": "5",
    })
    if not candidatas:
        return False
    try:
        _enviar_conclusao(candidatas[0])
    except Exception as e:
        _tratar_falha_antes_do_envio(candidatas[0], e)
    return True


def _tratar_falha_antes_do_envio(ocorrencia, excecao):
    """
    Só é chamada quando a transação NEM CHEGOU A SER MANDADA (erro de rede,
    de gas, etc.) — se o envio deu certo e só a confirmação demorou, isso é
    tratado dentro de _enviar_registro/_enviar_conclusao, sem contar aqui
    de novo (senão a tentativa seria contada duas vezes).
    """
    id_ = ocorrencia["id"]
    tentativas = ocorrencia.get("tentativas", 0) + 1
    mensagem = f"{type(excecao).__name__}: {excecao}"
    _log(f"ocorrência {id_}: falha antes de enviar ({mensagem}) — tentativa {tentativas}/{RETRIES_MAX}")
    try:
        _patch_ocorrencia(id_, {
            "tentativas": tentativas, "ultima_tentativa": _agora_iso(), "erro": mensagem[:500],
        })
    except Exception:
        pass
    registrar_erro_lease(f"ocorrência {id_}: {mensagem}")


def _enviar_registro(ocorrencia):
    """
    Adaptado de `registrar_blockchain()`, que hoje está órfão dentro do
    app.py (não é mais chamado de lá desde que a blockchain saiu do
    formulário no Bloco 2) — mesma assinatura de contrato, mesma escala de
    coordenadas.
    """
    id_ = ocorrencia["id"]
    conta = Web3.to_checksum_address(WALLET_ADDRESS)
    fn = contract.functions.registrar(
        ocorrencia["foto_cid"],
        ocorrencia.get("descricao") or "",
        ocorrencia.get("endereco") or "",
        int((ocorrencia.get("lat") or 0) * COORD_ESCALA),
        int((ocorrencia.get("lng") or 0) * COORD_ESCALA),
    )
    try:
        gas = int(fn.estimate_gas({"from": conta}) * 1.3)
    except Exception:
        gas = 900_000
    nonce = w3.eth.get_transaction_count(conta)
    tx = fn.build_transaction({"from": conta, "nonce": nonce, "gas": gas, "gasPrice": w3.eth.gas_price})
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hex = tx_hash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex

    _log(f"ocorrência {id_}: transação de REGISTRO enviada ({tx_hex})")
    # Ponto de não-retorno: a partir daqui o hash já está gravado, então
    # esta ocorrência nunca mais será re-enviada, só re-conferida.
    _patch_ocorrencia(id_, {
        "tx_hash_registro": tx_hex, "nonce_registro": nonce,
        "ultima_tentativa": _agora_iso(), "tentativas": ocorrencia.get("tentativas", 0) + 1,
    })

    try:
        recibo = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    except Exception as e:
        _log(f"ocorrência {id_}: enviada mas a confirmação não chegou a tempo ({e}); "
             f"confiro de novo na próxima volta")
        return

    if recibo.status != 1:
        _patch_ocorrencia(id_, {"erro": "transação de registro revertida on-chain"})
        _log(f"ocorrência {id_}: registro revertido (status 0)")
        return

    _patch_ocorrencia(id_, {"etapa": "registrada", "erro": None})
    _log(f"ocorrência {id_}: registro confirmado ({tx_hex})")


def _enviar_conclusao(ocorrencia):
    """
    Adaptado de `mint_token.concluir_ocorrencia()` — mesma chamada de
    contrato, só que `wallet_destino` é SEMPRE a carteira de custódia do
    próprio projeto (WALLET_ADDRESS), nunca a de um cidadão (esse campo foi
    removido do formulário em 16/09).
    """
    id_ = ocorrencia["id"]
    conta = Web3.to_checksum_address(WALLET_ADDRESS)
    quantidade_wei = int(TOKEN_REWARD_AMOUNT * (10 ** TOKEN_DECIMALS))
    nonce = w3.eth.get_transaction_count(conta)
    tx = token_contract.functions.concluirOcorrencia(
        ocorrencia["foto_cid"], conta, quantidade_wei,
    ).build_transaction({"from": conta, "nonce": nonce, "gas": 250000, "gasPrice": w3.eth.gas_price})
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hex = tx_hash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex

    _log(f"ocorrência {id_}: transação de CONCLUSÃO (mint do CP) enviada ({tx_hex})")
    _patch_ocorrencia(id_, {
        "tx_hash_conclusao": tx_hex, "nonce_conclusao": nonce,
        "ultima_tentativa": _agora_iso(), "tentativas": ocorrencia.get("tentativas", 0) + 1,
    })

    try:
        recibo = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    except Exception as e:
        _log(f"ocorrência {id_}: enviada mas a confirmação não chegou a tempo ({e}); "
             f"confiro de novo na próxima volta")
        return

    if recibo.status != 1:
        _patch_ocorrencia(id_, {"erro": "transação de conclusão revertida on-chain"})
        _log(f"ocorrência {id_}: conclusão revertida (status 0)")
        return

    _patch_ocorrencia(id_, {"etapa": "concluida", "cp_ganho": int(TOKEN_REWARD_AMOUNT), "erro": None})
    _log(f"ocorrência {id_}: conclusão confirmada ({tx_hex}) — {int(TOKEN_REWARD_AMOUNT)} CP creditado")


def _retomar_pendentes():
    """Transações já enviadas (hash gravado) mas cuja etapa não avançou ainda."""
    resp = requests.get(
        _REST_OCORRENCIAS, headers=_HEADERS,
        params={
            "tx_hash_registro": "not.is.null", "etapa": "in.(criada,foto_ok)",
            "select": "id,tx_hash_registro", "limit": "5",
        }, timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    for o in resp.json():
        _conferir_registro_pendente(o)

    resp = requests.get(
        _REST_OCORRENCIAS, headers=_HEADERS,
        params={
            "tx_hash_conclusao": "not.is.null", "etapa": "eq.registrada",
            "select": "id,tx_hash_conclusao", "limit": "5",
        }, timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    for o in resp.json():
        _conferir_conclusao_pendente(o)


def _conferir_registro_pendente(o):
    id_ = o["id"]
    try:
        recibo = w3.eth.get_transaction_receipt(o["tx_hash_registro"])
    except Exception:
        return  # ainda não minerou — confere de novo na próxima volta
    if recibo.status == 1:
        _patch_ocorrencia(id_, {"etapa": "registrada", "erro": None})
        _log(f"ocorrência {id_}: registro confirmado ao retomar ({o['tx_hash_registro']})")
    else:
        _patch_ocorrencia(id_, {"erro": "transação de registro revertida on-chain"})
        _log(f"ocorrência {id_}: registro revertido, achado ao retomar")


def _conferir_conclusao_pendente(o):
    id_ = o["id"]
    try:
        recibo = w3.eth.get_transaction_receipt(o["tx_hash_conclusao"])
    except Exception:
        return
    if recibo.status == 1:
        _patch_ocorrencia(id_, {"etapa": "concluida", "cp_ganho": int(TOKEN_REWARD_AMOUNT), "erro": None})
        _log(f"ocorrência {id_}: conclusão confirmada ao retomar ({o['tx_hash_conclusao']})")
    else:
        _patch_ocorrencia(id_, {"erro": "transação de conclusão revertida on-chain"})
        _log(f"ocorrência {id_}: conclusão revertida, achada ao retomar")


# ---------------------------------------------------------------------------
# Laço principal
# ---------------------------------------------------------------------------

def rodar_uma_volta():
    if not obter_lease():
        _log("lease ocupado por outro worker — aguardando")
        return

    try:
        avancar_status_automatico()
    except Exception as e:
        _log(f"erro em avancar_status_automatico: {e}")
        registrar_erro_lease(f"avancar_status_automatico: {e}")

    try:
        processar_fila_blockchain()
    except Exception as e:
        _log(f"erro em processar_fila_blockchain: {e}")
        registrar_erro_lease(f"processar_fila_blockchain: {e}")

    # _atualizar_fila_visivel() — desligada até confirmar pra que a coluna
    # `fila` serve de verdade (ver comentário na função acima).


def main():
    _log(f"worker_blockchain iniciado (dono do lease: {DONO_LEASE})")
    while True:
        try:
            rodar_uma_volta()
        except Exception:
            _log("erro inesperado no laço principal:")
            traceback.print_exc()
        time.sleep(INTERVALO_LOOP_SEG)


if __name__ == "__main__":
    main()
