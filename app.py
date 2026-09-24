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
from ocorrencias import (
    criar_registro,
    buscar_antena_por_slug,
    buscar_endereco_por_coordenada,
    criar_participante_automatico,
    recuperar_participante_por_codigo,
)
from streamlit_js_eval import get_geolocation, streamlit_js_eval

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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

required_env_vars = {
    "PRIVATE_KEY": PRIVATE_KEY,
    "WALLET_ADDRESS": WALLET_ADDRESS,
    "CONTRACT_ADDRESS": CONTRACT_ADDRESS,
    "RPC_URL": RPC_URL,
    "PINATA_JWT": PINATA_JWT,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SECRET_KEY": SUPABASE_SECRET_KEY,
}

missing_env_vars = [name for name,
                    value in required_env_vars.items() if not value]

if missing_env_vars:
    st.set_page_config(
        page_title="DePIN Urbano",
        page_icon="📡",
        initial_sidebar_state="expanded",
    )
    aplicar_tema()
    st.title("📡 DePIN Urbano")
    st.error(
        "Faltam variaveis de ambiente no arquivo .env: " +
        ", ".join(missing_env_vars)
    )
    st.info(
        "Crie um .env na raiz do projeto com base em .env.example e preencha os valores.")
    st.stop()

# BLOCO 3: leitura da URL da gincana. Se a pessoa chegou aqui a partir do
# QR Code de uma antena (via o site do Rafa), a URL traz "a" (o slug da
# antena) e "p" (o id do participante). Conferimos a antena ANTES de
# desenhar qualquer parte do formulário — se ela não bater com uma antena
# ativa no banco, a pessoa nunca chega a ver o formulário, evitando
# ocorrências "meio registradas" sem pontos definidos.
slug_antena = st.query_params.get("a")
participante_id = st.query_params.get("p")
antena_numero = None

if slug_antena:
    antena_numero = buscar_antena_por_slug(slug_antena)
    if antena_numero is None:
        st.set_page_config(
            page_title="DePIN Urbano",
            page_icon="📡",
            initial_sidebar_state="expanded",
        )
        aplicar_tema()
        st.title("📡 DePIN Urbano")
        st.error("Não conseguimos confirmar esta antena da gincana agora.")
        st.info("Procure a equipe de apoio no estande — ela resolve isso rapidinho.")
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
    params = {"q": consulta, "format": "json",
              "limit": 1, "countrycodes": "br"}
    headers = {"User-Agent": "DePINUrbano/1.0"}
    try:
        resposta = requests.get(
            url, params=params, headers=headers, timeout=10)
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


UF_POR_ESTADO = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF",
    "Espírito Santo": "ES", "Goiás": "GO", "Maranhão": "MA",
    "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG",
    "Pará": "PA", "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE",
    "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE",
    "Tocantins": "TO",
}


def separar_tipo_logradouro(via_completa):
    """Tenta separar o tipo (Rua, Avenida, ...) do resto do nome da via,
    a partir do texto que o Nominatim devolveu (ex: "Avenida Paulista").
    Se nao reconhecer nenhum tipo conhecido no comeco do texto, devolve
    "Rua" como padrao e o texto inteiro no lugar do nome, para a pessoa
    ajustar se precisar.
    """
    if not via_completa:
        return "Rua", ""
    for tipo in TIPOS_LOGRADOURO:
        prefixo = tipo + " "
        if via_completa.lower().startswith(prefixo.lower()):
            return tipo, via_completa[len(prefixo):].strip()
    return "Rua", via_completa


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

# ===========================================================================
# BLOCO 9: identidade do cidadão no fluxo normal (fora da gincana)
#
# No fluxo da gincana, o participante_id já chega pronto na URL (?p=...),
# criado pelo site em React antes de mandar a pessoa pra cá — por isso este
# bloco inteiro fica de fora quando `antena_numero is not None`.
#
# No fluxo normal, o cidadão comum também passa a ganhar um participante_id
# persistente, pra poder ver o painel dele em depinurbano.vercel.app/eu mais
# tarde. Resolvido em camadas:
#   1) dentro da mesma sessão do navegador (mesma aba aberta), guardado em
#      st.session_state — não precisa resolver de novo a cada rodada;
#   2) entre sessões, no mesmo aparelho — o navegador guarda o id no
#      localStorage (streamlit_js_eval, a mesma biblioteca já usada desde o
#      Bloco 3-B pra geolocalização), lido sozinho, uma vez, quando a pessoa
#      chega numa aba nova;
#   3) manual, escondida num expander — um código de recuperação, pra quem
#      troca de aparelho e perdeu o localStorage.
# Se nenhuma das três achar nada, um participante novo só é criado na hora
# de enviar a ocorrência (lá embaixo, dentro do "if enviar:") — de propósito
# na primeira ocorrência, não já na visita, pra não sobrar participante
# "fantasma" de quem só passou pra olhar o formulário.
#
# Precisa vir DEPOIS do st.set_page_config() logo acima: streamlit_js_eval é
# um componente de verdade (não um widget nativo do Streamlit), e chamá-lo
# antes do set_page_config quebra a página inteira.
CHAVE_LOCALSTORAGE_PARTICIPANTE = "depin_participante_id"
_SEM_ID_SALVO = "__sem_id__"
codigo_recuperacao_novo = None

if antena_numero is None:
    if "participante_id_ativo" in st.session_state:
        participante_id = st.session_state["participante_id_ativo"]

    if not participante_id:
        if "id_local_verificado" not in st.session_state:
            st.session_state["id_local_verificado"] = False

        if not st.session_state["id_local_verificado"]:
            # O "|| '...'" do lado do JavaScript existe só pra diferenciar
            # duas situações que a biblioteca devolveria como o mesmo None:
            # "o navegador ainda não respondeu" e "respondeu, e o valor
            # realmente está vazio". Sem isso nunca saberíamos quando parar
            # de esperar.
            resultado_local = streamlit_js_eval(
                js_expressions=(
                    f"localStorage.getItem('{CHAVE_LOCALSTORAGE_PARTICIPANTE}') "
                    f"|| '{_SEM_ID_SALVO}'"
                ),
                key="ler_participante_id_local",
            )
            if resultado_local is not None:
                st.session_state["id_local_verificado"] = True
                if resultado_local != _SEM_ID_SALVO:
                    participante_id = resultado_local
                    st.session_state["participante_id_ativo"] = participante_id

    if not participante_id:
        with st.expander("Já registrou antes? Recupere o seu painel"):
            codigo_digitado = st.text_input(
                "Código de recuperação",
                placeholder="Ex.: RDRMH65X",
                key="codigo_recuperacao_input",
            )
            if st.button("Recuperar", key="botao_recuperar_participante"):
                participante_recuperado = recuperar_participante_por_codigo(
                    codigo_digitado)
                if participante_recuperado:
                    participante_id = participante_recuperado["id"]
                    st.session_state["participante_id_ativo"] = participante_id
                    streamlit_js_eval(
                        js_expressions=(
                            f"localStorage.setItem("
                            f"'{CHAVE_LOCALSTORAGE_PARTICIPANTE}', "
                            f"'{participante_id}')"
                        ),
                        key="salvar_participante_id_recuperado",
                    )
                    st.success(
                        "Painel recuperado! Pode continuar e registrar sua "
                        "ocorrência.")
                else:
                    st.error(
                        "Código não encontrado. Confira e tente de novo.")

TIPOS_LOGRADOURO = [
    "Rua", "Avenida", "Alameda", "Travessa", "Praça",
    "Estrada", "Rodovia", "Largo", "Viela", "Via",
]

ESTADOS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

st.markdown("### Foto da ocorrência")

# A câmera só liga quando a pessoa pede. Antes, o app abria já com a câmera
# em funcionamento e a imagem de quem estava na frente do celular na tela, o
# que é invasivo e assusta quem só queria olhar o formulário.
#
# A ordem dos dois caminhos também importa: fotografar na hora é o que a
# maioria vai fazer, então esse botão vem primeiro, logo abaixo do título.
# Escolher um arquivo é a alternativa, e por isso vem depois.
if "camera_ligada" not in st.session_state:
    st.session_state["camera_ligada"] = False

foto = None

if st.session_state["camera_ligada"]:
    foto = st.camera_input("Enquadre a ocorrência e toque em Take Photo")
    if st.button("✖️ Desligar a câmera"):
        st.session_state["camera_ligada"] = False
        st.rerun()
else:
    if st.button("📷 Tirar uma foto agora"):
        st.session_state["camera_ligada"] = True
        st.rerun()

    st.markdown("")
    foto = st.file_uploader(
        "Ou escolha uma foto da galeria do seu celular ou computador",
        type=["jpg", "jpeg", "png"])

st.caption("A foto é o que comprova a ocorrência. Ela vai para o IPFS e ganha "
           "um código próprio, calculado a partir da própria imagem.")

st.markdown("### O que está acontecendo?")
descricao = st.text_area(
    "Descreva a ocorrência",
    placeholder="Ex.: Buraco na calçada em frente ao número 120, "
                "com risco de queda para pedestres.")

st.markdown("### Onde fica a ocorrência?")

# BLOCO 3-B: geolocalizacao automatica. A pessoa aperta o botao, o navegador
# pede permissao e devolve a coordenada (lat/lon) dela. Traduzimos essa
# coordenada em endereco (rua, bairro, cidade, estado, CEP) e usamos como
# valor inicial dos campos abaixo — que continuam editaveis, exatamente
# como se a pessoa tivesse digitado. Numero e complemento nunca sao
# preenchidos sozinhos: o GPS nao sabe o numero da casa, entao esses campos
# ficam sempre esperando a pessoa completar.
if "aguardando_localizacao" not in st.session_state:
    st.session_state["aguardando_localizacao"] = False
if "endereco_preenchido_auto" not in st.session_state:
    st.session_state["endereco_preenchido_auto"] = False

if st.button("📍 Usar minha localização"):
    st.session_state["aguardando_localizacao"] = True
    st.rerun()

if st.session_state["aguardando_localizacao"]:
    localizacao = get_geolocation()
    if localizacao and localizacao.get("coords"):
        st.session_state["aguardando_localizacao"] = False
        lat = localizacao["coords"]["latitude"]
        lon = localizacao["coords"]["longitude"]
        resultado = buscar_endereco_por_coordenada(lat, lon)
        if resultado:
            tipo_detectado, via_detectada = separar_tipo_logradouro(
                resultado["via"])
            if via_detectada:
                st.session_state["tipo_logradouro_input"] = tipo_detectado
                st.session_state["via_input"] = via_detectada
            if resultado["bairro"]:
                st.session_state["bairro_input"] = resultado["bairro"]
            if resultado["cidade"]:
                st.session_state["cidade_input"] = resultado["cidade"]
            if resultado["estado"] in UF_POR_ESTADO:
                st.session_state["estado_input"] = UF_POR_ESTADO[resultado["estado"]]
            if resultado["cep"]:
                st.session_state["cep_input"] = formatar_cep(resultado["cep"])
            if resultado["numero"]:
                st.session_state["numero_input"] = resultado["numero"]
            st.session_state["endereco_preenchido_auto"] = True
        else:
            st.warning(
                "Não conseguimos identificar um endereço a partir da sua "
                "localização. Preencha os campos abaixo manualmente.")
        st.rerun()
    else:
        st.caption("📍 Aguardando permissão de localização do navegador...")

if st.session_state["endereco_preenchido_auto"]:
    st.caption(
        "📍 Endereço preenchido automaticamente. Confira se está certo e "
        "complete o número e o complemento.")

# Tipo e nome do logradouro lado a lado: além de encurtar a página no celular,
# informar "Avenida" ou "Rua" melhora muito o acerto da busca de coordenadas —
# o OpenStreetMap encontra "Avenida Maestro Cardim", mas tropeça em
# "Maestro Cardim" sozinho.
col_tipo, col_via = st.columns([1, 2])
with col_tipo:
    tipo_logradouro = st.selectbox(
        "Tipo", TIPOS_LOGRADOURO, key="tipo_logradouro_input")
with col_via:
    via = st.text_input(
        "Logradouro", placeholder="Maestro Cardim", key="via_input")

col_num, col_compl = st.columns(2)
with col_num:
    numero = st.text_input("Número", placeholder="963", key="numero_input")
with col_compl:
    complemento = st.text_input(
        "Complemento (opcional)", placeholder="apto 52, bloco B, casa 2")

bairro = st.text_input(
    "Bairro", placeholder="Bela Vista", key="bairro_input")

col_cidade, col_estado = st.columns([3, 1])
with col_cidade:
    cidade = st.text_input(
        "Cidade", placeholder="São Paulo", key="cidade_input")
with col_estado:
    estado = st.selectbox(
        "Estado", ESTADOS, index=ESTADOS.index("SP"), key="estado_input")

cep = st.text_input("CEP (pode digitar com ou sem o hífen)",
                    placeholder="01323-001", key="cep_input")
st.markdown("### Seus dados")
nome = st.text_input("Nome completo", placeholder="Maria da Silva Santos")
email = st.text_input(
    "E-mail (opcional)", placeholder="maria@email.com")
st.caption(
    "Futuramente, será usado para avisar você quando a ocorrência for atendida "
    "e para entrarmos em contato, caso precisemos de mais detalhes sobre a "
    "ocorrência."
)

st.markdown("### Recompensa")
st.markdown(
    "Ao ter sua ocorrência atendida, você ganha pontos **CP (Cidadão "
    "Participativo)**. Eles ficam guardados automaticamente no seu painel, "
    "junto com o histórico das suas ocorrências — sem precisar de carteira "
    "digital nem de nenhum cadastro extra. Os pontos poderão ser usados em "
    "serviços e benefícios municipais."
)

st.markdown("")  # respiro antes do botão

# Botão centralizado e largo: no celular fica confortável de acertar com o
# dedo, e na projeção deixa claro qual é a ação principal da tela.
_, col_botao, _ = st.columns([1, 2, 1])
with col_botao:
    enviar = st.button("Enviar ocorrência", use_container_width=True)

if enviar:
    if foto and descricao and nome and via and cidade:
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

            partes_endereco = [
                f"{logradouro}, {numero}" if numero else logradouro]
            if complemento.strip():
                partes_endereco.append(complemento.strip())
            partes_endereco.append(f"{bairro} - {cidade}/{estado}")
            if cep_formatado:
                partes_endereco.append(f"CEP {cep_formatado}")
            endereco_completo = " - ".join(partes_endereco)

            # BLOCO 9: se chegou até aqui sem participante_id (fluxo normal,
            # sem localStorage nem código de recuperação), cria um agora —
            # de propósito só neste momento, na primeira ocorrência de
            # verdade, e não já ao abrir a página.
            if antena_numero is None and not participante_id:
                novo_participante = criar_participante_automatico()
                if novo_participante:
                    participante_id = novo_participante["id"]
                    codigo_recuperacao_novo = novo_participante.get(
                        "codigo_recup")
                    st.session_state["participante_id_ativo"] = participante_id
                    streamlit_js_eval(
                        js_expressions=(
                            f"localStorage.setItem("
                            f"'{CHAVE_LOCALSTORAGE_PARTICIPANTE}', "
                            f"'{participante_id}')"
                        ),
                        key="salvar_participante_id_novo",
                    )

            dados = {
                "nome": nome,
                "email": email.strip(),
                "endereco": endereco_completo,
                "descricao": descricao,
                "latitude": latitude,
                "longitude": longitude,
                "cid": cid,
            }
            if antena_numero is not None:
                dados["origem"] = "evento"
                dados["antena_numero"] = antena_numero
            if participante_id:
                dados["participante_id"] = participante_id

            try:
                registro_criado = criar_registro(dados)
            except Exception as e:
                st.error(
                    f"❌ Não foi possível salvar sua ocorrência agora: {e}. "
                    "Tente novamente em instantes.")
                st.stop()

            # O app NÃO registra na blockchain nem aciona a antena diretamente.
            # Isso agora é trabalho de um processo separado (o "worker"), que
            # roda de forma independente e depois preenche o hash da
            # transação nesta ocorrência. Assim, se a blockchain estiver
            # lenta ou fora do ar, o cidadão não fica esperando: a
            # ocorrência já está salva e o comprovante já existe.
            st.info(
                "📡 O registro na blockchain e a detecção pela antena da "
                "rede acontecem de forma independente deste aplicativo, "
                "logo em seguida.")

            protocolo = registro_criado["id"].upper()
            momento = datetime.now().strftime("%d/%m/%Y às %H:%M")
            tx_hash = ""

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
                # BLOCO 9: só vem preenchido quando um participante foi
                # criado AGORA (primeira ocorrência do fluxo normal nesse
                # dispositivo). Em recargas seguintes o comprovante antigo
                # continua na sessão sem esse campo — por isso o `.get(...)`
                # ao exibir, mais abaixo.
                "codigo_recuperacao": codigo_recuperacao_novo,
            }
            st.balloons()
            # A pessoa acabou de enviar e a tela dela está no meio do
            # formulário. Sem este aviso ela não descobre que o comprovante
            # foi gerado mais abaixo, e sai da página sem baixá-lo.
            st.success(
                "✅ **Pronto! Sua ocorrência foi registrada.**\n\n"
                "⬇️ **Role a tela para baixo** para ver o seu comprovante e "
                "baixar o arquivo. Guarde o número de protocolo: é com ele "
                "que você acompanha o atendimento."
            )
        else:
            st.error("Erro ao enviar para o IPFS. Verifique a chave.")
    else:
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
            faltando.append("a descrição da ocorrência")
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

    # BLOCO 9: se este comprovante acabou de criar um participante novo
    # (fluxo normal, primeiro registro neste navegador), mostra o código de
    # recuperação. É a única vez que ele aparece — depois disso o app conta
    # com o localStorage deste mesmo navegador/dispositivo, e o código só
    # volta a ser necessário se a pessoa trocar de aparelho ou limpar os
    # dados do site.
    codigo_recuperacao_exibir = comprovante.get("codigo_recuperacao")
    if codigo_recuperacao_exibir:
        st.info(
            f"🔑 **Seu código de recuperação: `{codigo_recuperacao_exibir}`**\n\n"
            "Guarde-o. É com ele que você recupera seu cadastro caso "
            "troque de celular ou computador."
        )

    if participante_id and antena_numero is not None:
        # st.link_button sempre abre em nova aba (limitação do próprio
        # Streamlit, sem parâmetro pra mudar isso — pedido do Rafa em 19/09).
        # Trocado por um link HTML puro com target="_self", que abre na
        # mesma aba, estilizado igual aos outros botões do app (mesmas cores
        # e medidas de .stButton > button em tema_visual.py).
        st.markdown(
            f'<a href="https://depinurbano.vercel.app/eu?p={participante_id}" '
            'target="_self" style="display:inline-block;background:#5B8FB9;'
            'color:#FFFFFF;border:none;border-radius:10px;padding:0.9rem 2rem;'
            'font-weight:650;font-size:1.55rem;text-decoration:none;'
            'box-shadow:0 1px 3px rgba(59,89,116,0.18);">'
            'Voltar para o meu painel da gincana</a>',
            unsafe_allow_html=True,
        )

    link_foto = f"https://gateway.pinata.cloud/ipfs/{comprovante['cid']}"
    link_tx = (f"https://amoy.polygonscan.com/tx/{comprovante['tx_hash']}"
               if comprovante["tx_hash"] else "")

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

    linhas_texto += [
        "COMPROVAÇÕES PERMANENTES",
        "-" * 46,
        f"Registro na blockchain: {link_tx or 'não concluído'}",
        f"Foto no IPFS:           {link_foto}",
        f"Impressão digital:      {comprovante['cid']}",
        "",
    ]

    # BLOCO 9: só entra no texto quando um participante foi criado agora
    # (primeira ocorrência do fluxo normal neste dispositivo) — mesma
    # condição do aviso mostrado na tela, para o arquivo baixado carregar
    # a mesma informação de quem só olhou a tela e não baixou nada.
    if codigo_recuperacao_exibir:
        linhas_texto += [
            "SEU CÓDIGO DE RECUPERAÇÃO",
            "-" * 46,
            f"{codigo_recuperacao_exibir}",
            "Guarde-o: é com ele que você recupera seu cadastro caso",
            "troque de celular ou computador.",
            "",
        ]

    linhas_texto += [
        "COMO ACOMPANHAR",
        "-" * 46,
        "Acesse https://chaintrack.streamlit.app, vá em",
        "'Acompanhar ocorrência' e informe o número de protocolo",
        "no alto deste comprovante. Não é preciso fazer login.",
        "",
        "Obrigado por ser um cidadão participativo e contribuir",
        "para uma cidade melhor.",
    ]

    # O botão de baixar aparece duas vezes de propósito: aqui em cima, onde a
    # pessoa chega, e de novo no fim do comprovante. Antes ele existia só no
    # rodapé, e quem não rolava a tela inteira ia embora sem o arquivo.
    st.download_button(
        "⬇️  Baixar o meu comprovante",
        data="\n".join(linhas_texto).encode("utf-8"),
        file_name=f"comprovante_{comprovante['protocolo']}.txt",
        mime="text/plain",
        use_container_width=True,
        key="baixar_topo",
    )
    st.caption("O arquivo é um texto simples, que abre em qualquer celular ou "
               "computador e pode ser guardado ou encaminhado.")

    st.markdown("")

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

    col_baixar, col_novo = st.columns(2)
    with col_baixar:
        st.download_button(
            "⬇️ Baixar comprovante",
            data="\n".join(linhas_texto).encode("utf-8"),
            file_name=f"comprovante_{comprovante['protocolo']}.txt",
            mime="text/plain",
            use_container_width=True,
            key="baixar_rodape",
        )
    with col_novo:
        if st.button("Registrar outra ocorrência", use_container_width=True):
            st.session_state.pop("comprovante", None)
            st.rerun()
