import streamlit as st
import json
import os
from web3 import Web3

import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open("abi.json") as f:
    CONTRACT_ABI = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(
    CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def registrar_blockchain(cid, descricao, endereco, latitude, longitude):
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
    tx = contract.functions.registrar(
        cid, descricao, endereco,
        int(latitude * 1_000_000),
        int(longitude * 1_000_000)
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 600000,
        "gasPrice": w3.eth.gas_price,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()


PINATA_JWT = os.getenv("PINATA_JWT")


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

if st.button("Enviar ocorrência"):
    if foto and descricao and nome and rua and cidade:
        with st.spinner("Enviando para o IPFS..."):
            cid = upload_ipfs(foto)
        if cid:
            st.success(f"✅ Imagem salva no IPFS!")
            st.code(f"CID: {cid}")
            latitude, longitude = geocode_endereco(
                rua, numero, bairro, cidade, estado, cep)
            if latitude is None:
                latitude, longitude = -23.5505, -46.6333
                st.warning(
                    "Não foi possível localizar o endereço exato; usando localização padrão.")

            try:
                tx_hash = registrar_blockchain(
                    cid, descricao,
                    f"{rua}, {numero} - {bairro}, {cidade} - {estado}, {cep}",
                    latitude, longitude
                )
                st.success(f"✅ Registrado na blockchain! Tx: {tx_hash}")
            except Exception as e:
                st.warning(f"Falha ao registrar na blockchain: {e}")

            registro = {
                "nome": nome,
                "endereco": f"{rua}, {numero} - {bairro}, {cidade} - {estado}, {cep}",
                "descricao": descricao,
                "latitude": latitude,
                "longitude": longitude,
                "cid": cid,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open("registros.json", "a") as f:
                f.write(json.dumps(registro) + "\n")
            st.balloons()
        else:
            st.error("Erro ao enviar para o IPFS. Verifique a chave.")
    else:
        st.warning(
            "Por favor, preencha nome, endereço, descrição e adicione a foto.")
