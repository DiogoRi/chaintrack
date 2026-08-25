import streamlit as st
import json
import os
import re
import uuid
from pathlib import Path
from web3 import Web3

import requests
from datetime import datetime
from dotenv import load_dotenv

from tema_visual import aplicar_tema

# Caminhos absolutos a partir da pasta deste arquivo. Isso é necessário
# porque o app agora tem duas páginas (a segunda vive em pages/), e caminhos
# relativos deixariam de apontar para o lugar certo dependendo de qual página
# estivesse sendo executada.
BASE_DIR = Path(__file__).resolve().parent
ABI_PATH = BASE_DIR / "abi.json"
REGISTROS_PATH = BASE_DIR / "registros.json"

load_dotenv(BASE_DIR / ".env")

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
    st.set_page_config(
        page_title="DePIN Urbano",
        page_icon="📡",
        initial_sidebar_state="expanded",
    )
    aplicar_tema()
    st.title("📡 DePIN Urbano")
    st.error(
        "Faltam variaveis de ambiente no arquivo .env: " + ", ".join(missing_env_vars)
    )
    st.info("Crie um .env na raiz do projeto com base em .env.example e preencha os valores.")
    st.stop()

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open(ABI_PATH) as f:
    CONTRACT_ABI = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(
    CONTRACT_ADDRESS), abi=CONTRACT_ABI)


# O contrato publicado na Amoy (o mesmo desde a Fase 2, com 13 registros)
# guarda latitude e longitude como INTEIROS, multiplicados por 1.000.000.
# Ex: -23.5505 vira -23550500. É assim que os 13 registros existentes estão
# gravados, então mantemos a mesma convenção.
COORD_ESCALA = 1_000_000


def registrar_blockchain(cid, descricao, endereco, latitude, longitude):
    """
    Chama registrar(string _cid, string _descricao, string _endereco,
                    int256 _latitude, int256 _longitude) no contrato da Fase 2.

    O gas não é mais fixo: perguntamos à blockchain quanto a chamada vai
    custar e adicionamos 30% de folga. Além de evitar falta de gas, o
    estimate_gas revela ANTES de enviar se a chamada iria reverter — assim
    não se paga por uma transação que falharia.

    Retorna o hash da transação já com o prefixo "0x".
    """
    conta = Web3.to_checksum_address(WALLET_ADDRESS)
    fn = contract.functions.registrar(
        cid,
        descricao,
        endereco,
        int(latitude * COORD_ESCALA),
        int(longitude * COORD_ESCALA),
    )

    try:
        gas = int(fn.estimate_gas({"from": conta}) * 1.3)
    except Exception:
        # Se a estimativa falhar (RPC instável, por exemplo), usa um teto
        # generoso. Lembrando: gas é limite, não cobrança — o que sobra volta.
        gas = 900_000

    nonce = w3.eth.get_transaction_count(conta)
    tx = fn.build_transaction({
        "from": conta,
        "nonce": nonce,
        "gas": gas,
        "gasPrice": w3.eth.gas_price,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    tx_hex = tx_hash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex
    return tx_hex


def upload_ipfs(arquivo):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {PINATA_JWT}"}
    files = {"file": arquivo}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()["IpfsHash"]
    return None


def _consultar_nominatim(consulta):
    """Uma tentativa de busca no OpenStreetMap. Devolve (lat, lon) ou (None, None)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": consulta, "format": "json", "limit": 1, "countrycodes": "br"}
    headers = {"User-Agent": "DePINUrbano/1.0"}
    try:
        resposta = requests.get(url, params=params, headers=headers, timeout=10)
        if resposta.status_code == 200 and resposta.json():
            r = resposta.json()[0]
            return float(r["lat"]), float(r["lon"])
    except Exception:
        pass
    return None, None


def geocode_endereco(logradouro, numero, bairro, cidade, estado, cep):
    """
    Descobre as coordenadas do endereço, tentando em cascata — do mais
    específico ao mais genérico.

    Por que em cascata: o Nominatim (a busca do OpenStreetMap) é exigente.
    Ele frequentemente não tem o número exato de um imóvel, e nesse caso
    devolve vazio — o que antes fazia o app cair no centro de São Paulo e
    colocar o pino no lugar errado. Tentando também sem o número, e depois
    só bairro/cidade, o ponto cai no lugar certo (ou pelo menos no bairro
    certo) em vez de a quilômetros de distância.

    Devolve (lat, lon, precisao), onde precisao é:
        "exata"   — achou com número
        "rua"     — achou a via, sem o número
        "bairro"  — achou o bairro
        "cidade"  — achou só a cidade
        None      — não achou nada
    """
    cep_limpo = (cep or "").strip()
    partes_cidade = f"{cidade}, {estado}, Brasil"

    tentativas = [
        (f"{logradouro}, {numero}, {bairro}, {partes_cidade}", "exata"),
        (f"{logradouro}, {numero}, {partes_cidade}", "exata"),
        (f"{logradouro}, {bairro}, {partes_cidade}", "rua"),
        (f"{logradouro}, {partes_cidade}", "rua"),
        (f"{cep_limpo}, Brasil", "rua") if cep_limpo else None,
        (f"{bairro}, {partes_cidade}", "bairro") if bairro else None,
        (partes_cidade, "cidade"),
    ]

    for tentativa in tentativas:
        if tentativa is None:
            continue
        consulta, precisao = tentativa
        lat, lon = _consultar_nominatim(consulta)
        if lat is not None:
            return lat, lon, precisao

    return None, None, None


WALLET_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


def wallet_valida(endereco: str) -> bool:
    return bool(WALLET_REGEX.match(endereco.strip()))


def formatar_cep(cep_bruto: str) -> str:
    """
    Devolve o CEP no formato 00000-000, aceitando que a pessoa digite com
    hífen, sem hífen, com pontos ou com espaços. Se não tiver 8 dígitos,
    devolve o que foi digitado, sem inventar nada.
    """
    digitos = re.sub(r"\D", "", cep_bruto or "")
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return (cep_bruto or "").strip()


st.set_page_config(
    page_title="DePIN Urbano",
    page_icon="📡",
    # Mantém o menu de páginas sempre visível na lateral. Sem isso o
    # Streamlit às vezes começa com a barra recolhida, e o botão de abrir
    # é discreto demais para se procurar no meio de uma apresentação.
    initial_sidebar_state="expanded",
)
aplicar_tema()
st.title("📡 DePIN Urbano")
st.markdown(
    "<p class='frase-impacto'>Seja um cidadão participativo e ajude a "
    "construir uma cidade melhor</p>",
    unsafe_allow_html=True,
)
st.subheader("Registre uma ocorrência")

TIPOS_LOGRADOURO = [
    "Rua", "Avenida", "Alameda", "Travessa", "Praça",
    "Estrada", "Rodovia", "Largo", "Viela", "Via",
]

ESTADOS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

# A câmera nativa funciona no celular porque o app é servido por https.
# O campo de envio abaixo continua existindo para quem já tem a foto salva
# na galeria, ou para quem preferir escolher um arquivo.
foto = st.camera_input(
    "📷 Tire uma foto que identifique o problema") or st.file_uploader(
    "📁 Ou escolha uma foto do seu celular",
    type=["jpg", "jpeg", "png"])

st.markdown("### O que está acontecendo?")
descricao = st.text_area(
    "Descreva o problema",
    placeholder="Ex.: Buraco na calçada em frente ao número 120, "
                "com risco de queda para pedestres.")

st.markdown("### Onde está o problema?")

# Tipo e nome do logradouro lado a lado: além de encurtar a página no celular,
# informar "Avenida" ou "Rua" melhora muito o acerto da busca de coordenadas —
# o OpenStreetMap encontra "Avenida Maestro Cardim", mas tropeça em
# "Maestro Cardim" sozinho.
col_tipo, col_via = st.columns([1, 2])
with col_tipo:
    tipo_logradouro = st.selectbox("Tipo", TIPOS_LOGRADOURO)
with col_via:
    via = st.text_input("Logradouro", placeholder="Maestro Cardim")

col_num, col_compl = st.columns(2)
with col_num:
    numero = st.text_input("Número", placeholder="963")
with col_compl:
    complemento = st.text_input(
        "Complemento (opcional)", placeholder="apto 52, bloco B, casa 2")

bairro = st.text_input("Bairro", placeholder="Bela Vista")

col_cidade, col_estado = st.columns([3, 1])
with col_cidade:
    cidade = st.text_input("Cidade", placeholder="São Paulo")
with col_estado:
    estado = st.selectbox("Estado", ESTADOS, index=ESTADOS.index("SP"))

cep = st.text_input("CEP (pode digitar com ou sem o hífen)",
                    placeholder="01323-001")

st.markdown("### Seus dados")
nome = st.text_input("Nome completo", placeholder="Maria da Silva Santos")
email = st.text_input(
    "E-mail (opcional)", placeholder="maria@email.com")
st.caption(
    "Futuramente, será usado para avisar você quando o problema for resolvido "
    "e para entrarmos em contato, caso precisemos de mais detalhes sobre a "
    "ocorrência."
)

st.markdown("### Recompensa (opcional)")
st.markdown(
    "Copie o endereço da sua carteira digital e cole abaixo. "
    "Quando o problema for resolvido e atualizado no sistema, você receberá "
    "tokens **CP (Cidadão Participativo)**, que poderão ser usados em "
    "serviços e benefícios municipais."
)
wallet = st.text_input(
    "Endereço da carteira",
    placeholder="0x0000000000000000000000000000000000000000",
)
st.caption(
    "Não tem carteira ou prefere não informar? Deixe em branco. "
    "A ocorrência é registrada do mesmo jeito."
)

st.markdown("")  # respiro antes do botão

# Botão centralizado e largo: no celular fica confortável de acertar com o
# dedo, e na projeção deixa claro qual é a ação principal da tela.
_, col_botao, _ = st.columns([1, 2, 1])
with col_botao:
    enviar = st.button("Enviar ocorrência", use_container_width=True)

if enviar:
    wallet_limpa = wallet.strip()
    wallet_ok = True
    if wallet_limpa and not wallet_valida(wallet_limpa):
        wallet_ok = False
        st.error(
            "O endereço de carteira informado não parece válido "
            "(precisa começar com '0x' e ter 42 caracteres). "
            "Corrija ou deixe o campo em branco."
        )

    if foto and descricao and nome and via and cidade and wallet_ok:
        with st.spinner("Enviando para o IPFS..."):
            cid = upload_ipfs(foto)
        if cid:
            st.success("✅ Imagem salva no IPFS!")
            st.code(f"CID: {cid}")
            st.caption(
                "🔐 **É a impressão digital da sua foto.** "
                "Se alguém trocar a imagem, este código muda e a troca aparece."
            )

            logradouro = f"{tipo_logradouro} {via}".strip()
            cep_formatado = formatar_cep(cep)

            with st.spinner("Localizando o endereço no mapa..."):
                latitude, longitude, precisao = geocode_endereco(
                    logradouro, numero, bairro, cidade, estado, cep_formatado)

            if precisao == "exata":
                st.success("📍 Endereço localizado com precisão.")
            elif precisao == "rua":
                st.info(
                    "📍 Localizamos a via, mas não o número exato. "
                    "O ponto no mapa fica na rua indicada.")
            elif precisao == "bairro":
                st.warning(
                    "📍 Não encontramos a via; o ponto foi marcado no bairro informado.")
            elif precisao == "cidade":
                st.warning(
                    "📍 Não encontramos o endereço; o ponto foi marcado no centro da cidade. "
                    "Confira se o logradouro está escrito corretamente.")
            else:
                latitude, longitude = -23.5505, -46.6333
                st.warning(
                    "📍 Não foi possível localizar o endereço. "
                    "Usando uma localização padrão — confira os campos e, "
                    "se possível, registre de novo.")

            partes_endereco = [f"{logradouro}, {numero}" if numero else logradouro]
            if complemento.strip():
                partes_endereco.append(complemento.strip())
            partes_endereco.append(f"{bairro} - {cidade}/{estado}")
            if cep_formatado:
                partes_endereco.append(f"CEP {cep_formatado}")
            endereco_completo = " - ".join(partes_endereco)

            tx_hash = ""
            onchain_ok = False
            try:
                with st.spinner("Registrando na blockchain..."):
                    tx_hash = registrar_blockchain(
                        cid, descricao, endereco_completo, latitude, longitude)
                    recibo = w3.eth.wait_for_transaction_receipt(
                        tx_hash, timeout=120)

                if recibo.status == 1:
                    onchain_ok = True
                    st.success("✅ Registrado na blockchain!")
                    st.markdown(
                        f"🔗 [Ver o registro no PolygonScan](https://amoy.polygonscan.com/tx/{tx_hash})")
                    st.caption(
                        "⛓️ **Ninguém pode apagar ou alterar esta ocorrência.** "
                        "O link é a sua prova, com data e hora."
                    )
                else:
                    st.error(
                        "❌ A transação foi minerada mas reverteu (status 0). "
                        "O dado NÃO foi gravado on-chain. Confira o ABI e os tipos dos parâmetros.")
            except Exception as e:
                st.warning(f"Falha ao registrar na blockchain: {e}")

            # O app NÃO aciona a antena. Quem faz isso é o vigia_antena.py,
            # observando a blockchain de forma independente. Manter as duas
            # coisas geraria acionamento duplicado e, pior, enfraqueceria a
            # tese do projeto: a antena não deve confiar no aplicativo, e sim
            # no registro público.
            st.info(
                "📡 A antena da rede detecta este registro diretamente na "
                "blockchain, sem depender deste aplicativo.")

            protocolo = uuid.uuid4().hex[:8].upper()
            momento = datetime.now().strftime("%d/%m/%Y às %H:%M")

            registro = {
                "id": protocolo.lower(),
                "nome": nome,
                "email": email.strip(),
                "endereco": endereco_completo,
                "descricao": descricao,
                "latitude": latitude,
                "longitude": longitude,
                "cid": cid,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "recebida",
                "wallet": wallet_limpa,
                "token_tx": "",
                # Hash da transação de registro. Guardar isso permite que o
                # dashboard mostre a prova on-chain de cada ocorrência e,
                # principalmente, distinga as que ficaram só no arquivo local
                # porque a blockchain falhou naquele momento.
                "tx_registro": tx_hash if onchain_ok else "",
                "onchain": onchain_ok,
                # Campos da etapa de atendimento. Nascem vazios: quem os
                # preenche é o painel do município, conforme a ocorrência
                # avança. O prazo só começa a correr quando ela é encaminhada
                # a uma equipe, então aqui ainda não há data nenhuma.
                "setor": "Não atribuído",
                "prazo_dias": 10,
                "data_andamento": "",
                "data_conclusao": "",
                "mensagens": [],
            }
            with open(REGISTROS_PATH, "a") as f:
                f.write(json.dumps(registro) + "\n")

            # Guarda o comprovante na memória da sessão em vez de desenhá-lo
            # aqui dentro. Motivo: o botão de download recarrega a página, e
            # tudo o que estivesse dentro deste bloco desapareceria justamente
            # quando a pessoa tentasse baixar o comprovante.
            st.session_state["comprovante"] = {
                "protocolo": protocolo,
                "momento": momento,
                "nome": nome,
                "email": email.strip(),
                "endereco": endereco_completo,
                "descricao": descricao,
                "cid": cid,
                "tx_hash": tx_hash,
                "wallet": wallet_limpa,
            }
            st.balloons()
        else:
            st.error("Erro ao enviar para o IPFS. Verifique a chave.")
    elif wallet_ok:
        faltando = []
        if not foto:
            faltando.append("a foto")
        if not nome:
            faltando.append("o nome")
        if not via:
            faltando.append("o logradouro")
        if not cidade:
            faltando.append("a cidade")
        if not descricao:
            faltando.append("a descrição do problema")
        st.warning("Falta preencher: " + ", ".join(faltando) + ".")


# ===========================================================================
# COMPROVANTE
#
# Fica FORA do bloco do botão de propósito. O botão de download recarrega a
# página; se o comprovante fosse desenhado dentro do "if enviar", ele sumiria
# no exato momento em que a pessoa tentasse baixá-lo. Guardado em
# st.session_state, ele sobrevive a essas recargas.
# ===========================================================================
comprovante = st.session_state.get("comprovante")

if comprovante:
    st.markdown("---")
    st.markdown("## ✅ Comprovante da sua ocorrência")
    st.markdown(
        "**Obrigado por ser um cidadão participativo e contribuir para uma "
        "cidade melhor.** Guarde este comprovante: ele reúne os links que "
        "comprovam o seu registro."
    )
    st.info(
        "🔎 **Guarde o número de protocolo.** Com ele você acompanha o "
        "andamento na página **Acompanhar ocorrência**, no menu ao lado, sem "
        "precisar de login."
    )

    link_foto = f"https://gateway.pinata.cloud/ipfs/{comprovante['cid']}"
    link_tx = (f"https://amoy.polygonscan.com/tx/{comprovante['tx_hash']}"
               if comprovante["tx_hash"] else "")

    with st.container(border=True):
        col_dados, col_foto = st.columns([2, 1])

        with col_dados:
            st.markdown(f"**Protocolo:** `{comprovante['protocolo']}`")
            st.markdown(f"**Registrado em:** {comprovante['momento']}")
            st.markdown(f"**Nome:** {comprovante['nome']}")
            if comprovante["email"]:
                st.markdown(f"**E-mail:** {comprovante['email']}")
            st.markdown(f"**Endereço:** {comprovante['endereco']}")
            st.markdown(f"**Ocorrência:** {comprovante['descricao']}")
            if comprovante["wallet"]:
                st.markdown(
                    f"**Carteira para a recompensa:** `{comprovante['wallet']}`")

        with col_foto:
            st.image(link_foto, width=220)
            st.markdown(f"[📷 Abrir ou salvar a foto]({link_foto})")

        st.markdown("**Comprovações permanentes:**")
        if link_tx:
            st.markdown(f"⛓️ [Registro na blockchain]({link_tx})")
        else:
            st.markdown(
                "⛓️ _O registro na blockchain não foi concluído nesta tentativa._")
        st.markdown(f"🔐 [Foto no IPFS]({link_foto})")

    # Versão em texto, para a pessoa levar consigo.
    linhas_texto = [
        "COMPROVANTE DE OCORRÊNCIA — DePIN URBANO",
        "=" * 46,
        "",
        f"Protocolo:     {comprovante['protocolo']}",
        f"Registrado em: {comprovante['momento']}",
        "",
        f"Nome:          {comprovante['nome']}",
    ]
    if comprovante["email"]:
        linhas_texto.append(f"E-mail:        {comprovante['email']}")
    linhas_texto += [
        f"Endereço:      {comprovante['endereco']}",
        "",
        "Ocorrência:",
        f"  {comprovante['descricao']}",
        "",
    ]
    if comprovante["wallet"]:
        linhas_texto += [
            f"Carteira para a recompensa: {comprovante['wallet']}", ""]
    linhas_texto += [
        "COMPROVAÇÕES PERMANENTES",
        "-" * 46,
        f"Registro na blockchain: {link_tx or 'não concluído'}",
        f"Foto no IPFS:           {link_foto}",
        f"Impressão digital:      {comprovante['cid']}",
        "",
        "COMO ACOMPANHAR",
        "-" * 46,
        "Acesse https://chaintrack.streamlit.app, vá em",
        "'Acompanhar ocorrência' e informe o número de protocolo",
        "no alto deste comprovante. Não é preciso fazer login.",
        "",
        "Obrigado por ser um cidadão participativo e contribuir",
        "para uma cidade melhor.",
    ]

    col_baixar, col_novo = st.columns(2)
    with col_baixar:
        st.download_button(
            "⬇️ Baixar comprovante",
            data="\n".join(linhas_texto).encode("utf-8"),
            file_name=f"comprovante_{comprovante['protocolo']}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_novo:
        if st.button("Registrar outra ocorrência", use_container_width=True):
            st.session_state.pop("comprovante", None)
            st.rerun()
