import streamlit as st
import json
import os
import re
import uuid
from web3 import Web3

import requests
from datetime import datetime
from dotenv import load_dotenv

from antena_serial import enviar_sinal

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")
PINATA_JWT = os.getenv("PINATA_JWT")

required_env_vars = {
    "PRIVATE_KEY": PRIVATE_KEY,
    "WALLET_ADDRESS": WALLET_ADDRESS,
    "CONTRACT_ADDRESS": CONTRACT_ADDRESS,
    "RPC_URL": RPC_URL,
    "PINATA_JWT": PINATA_JWT,
}

missing_env_vars = [name for name, value in required_env_vars.items() if not value]

if missing_env_vars:
    st.set_page_config(page_title="DePIN Urbano", page_icon="📡")
    st.title("📡 DePIN Urbano")
    st.error(
        "Faltam variaveis de ambiente no arquivo .env: " + ", ".join(missing_env_vars)
    )
    st.info("Crie um .env na raiz do projeto com base em .env.example e preencha os valores.")
    st.stop()

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open("abi.json") as f:
    CONTRACT_ABI = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(
    CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def registrar_blockchain(cid, descricao, latitude, longitude):
    """
    Chama registrarOcorrencia(string _cid, string _descricao, string _lat, string _lng)
    O contrato Ocorrencia.sol guarda lat/lng como STRING, entao convertemos com str().
    Retorna o hash da transacao (sem o prefixo 0x; ele e adicionado na hora de montar o link).
    """
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
    tx = contract.functions.registrarOcorrencia(
        cid,
        descricao,
        str(latitude),
        str(longitude)
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 600000,
        "gasPrice": w3.eth.gas_price,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()


def upload_ipfs(arquivo):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {PINATA_JWT}"}
    files = {"file": arquivo}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()["IpfsHash"]
    return None


def geocode_endereco(rua, numero, bairro, cidade, estado, cep):
    endereco_completo = f"{rua}, {numero}, {bairro}, {cidade}, {estado}, {cep}, Brasil"
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": endereco_completo, "format": "json", "limit": 1}
    headers = {"User-Agent": "DePINUrbano/1.0"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200 and response.json():
        resultado = response.json()[0]
        return float(resultado["lat"]), float(resultado["lon"])
    return None, None


WALLET_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


def wallet_valida(endereco: str) -> bool:
    return bool(WALLET_REGEX.match(endereco.strip()))


st.set_page_config(page_title="DePIN Urbano", page_icon="📡")
st.title("📡 DePIN Urbano")
st.subheader("Registre um problema na sua cidade")

foto = st.camera_input("Tire uma foto do problema") or st.file_uploader(
    "Ou envie uma foto", type=["jpg", "jpeg", "png"])

st.markdown("### Seus dados")
nome = st.text_input("Nome completo")

st.markdown("### Endereço do problema")
rua = st.text_input("Rua")
numero = st.text_input("Número")
bairro = st.text_input("Bairro")
cidade = st.text_input("Cidade")
estado = st.text_input("Estado")
cep = st.text_input("CEP")

st.markdown("### O que está acontecendo?")
descricao = st.text_area("Descreva o problema")

st.markdown("### Recompensa (opcional)")
wallet = st.text_input(
    "Carteira Web3 (endereço, ex: 0xabc123...) — receba um token quando o "
    "problema for resolvido",
    help="Campo opcional. Se você não tiver ou não quiser informar, pode deixar em branco.",
)

if st.button("Enviar ocorrência"):
    wallet_limpa = wallet.strip()
    wallet_ok = True
    if wallet_limpa and not wallet_valida(wallet_limpa):
        wallet_ok = False
        st.error(
            "O endereço de carteira informado não parece válido "
            "(precisa começar com '0x' e ter 42 caracteres). "
            "Corrija ou deixe o campo em branco."
        )

    if foto and descricao and nome and rua and cidade and wallet_ok:
        with st.spinner("Enviando para o IPFS..."):
            cid = upload_ipfs(foto)
        if cid:
            st.success("✅ Imagem salva no IPFS!")
            st.code(f"CID: {cid}")
            latitude, longitude = geocode_endereco(
                rua, numero, bairro, cidade, estado, cep)
            if latitude is None:
                latitude, longitude = -23.5505, -46.6333
                st.warning(
                    "Não foi possível localizar o endereço exato; usando localização padrão.")
            else:
                st.success("📍 Endereço localizado com precisão.")

            try:
                with st.spinner("Registrando na blockchain..."):
                    tx_hash = registrar_blockchain(
                        cid, descricao, latitude, longitude)
                    recibo = w3.eth.wait_for_transaction_receipt(
                        tx_hash, timeout=120)

                if recibo.status == 1:
                    st.success("✅ Registrado na blockchain!")
                    st.markdown(
                        f"🔗 [Ver no PolygonScan](https://amoy.polygonscan.com/tx/0x{tx_hash})")
                else:
                    st.error(
                        "❌ A transação foi minerada mas reverteu (status 0). "
                        "O dado NÃO foi gravado on-chain. Confira o ABI e os tipos dos parâmetros.")
            except Exception as e:
                st.warning(f"Falha ao registrar na blockchain: {e}")

            # Sinaliza a antena física (nunca trava o app se ela não responder)
            antena_ok = enviar_sinal("REGISTRO")
            if antena_ok:
                st.info("📡 Antena acionada — nó da rede recebeu o sinal.")
            else:
                st.info(
                    "📡 Antena não respondeu (ok para testar sem hardware conectado).")

            registro = {
                "id": uuid.uuid4().hex[:8],
                "nome": nome,
                "endereco": f"{rua}, {numero} - {bairro}, {cidade} - {estado}, {cep}",
                "descricao": descricao,
                "latitude": latitude,
                "longitude": longitude,
                "cid": cid,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "recebida",
                "wallet": wallet_limpa,
                "token_tx": "",
            }
            with open("registros.json", "a") as f:
                f.write(json.dumps(registro) + "\n")
            st.balloons()
        else:
            st.error("Erro ao enviar para o IPFS. Verifique a chave.")
    elif wallet_ok:
        st.warning(
            "Por favor, preencha nome, endereço, descrição e adicione a foto.")
