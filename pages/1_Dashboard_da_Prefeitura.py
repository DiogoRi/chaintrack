"""
Dashboard da Prefeitura — DePIN Urbano, Fase 3

Esta é a SEGUNDA PÁGINA do app. O Streamlit descobre sozinho tudo que está
dentro da pasta "pages/" e monta o menu lateral automaticamente.

Por que as duas telas precisam viver no MESMO app: elas se comunicam pelo
arquivo registros.json. Se o formulário estivesse na nuvem e o dashboard no
notebook, cada um teria o seu próprio arquivo e um não veria o que o outro
gravou. Estando no mesmo app, dividem o mesmo espaço em disco.
"""

import sys
import json
from pathlib import Path

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# A pasta raiz do projeto é a "avó" deste arquivo (pages/ -> raiz).
# Isso garante que os arquivos sejam encontrados independentemente de onde
# o Streamlit for iniciado, tanto no notebook quanto na nuvem.
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mint_token import concluir_ocorrencia      # noqa: E402
from tema_visual import aplicar_tema            # noqa: E402

st.set_page_config(
    page_title="Dashboard DePIN",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_tema()


# ---------------------------------------------------------------------------
# Acesso ao painel
# ---------------------------------------------------------------------------
# Este painel é a visão de quem atende as ocorrências: muda status, conclui e
# dispara o envio de tokens. Publicado na internet, ficaria aberto a qualquer
# um. A proteção é opcional de propósito: se a senha não estiver configurada,
# o painel abre normalmente (útil na demonstração e no notebook). Basta criar
# SENHA_DASHBOARD nos Secrets do Streamlit para que ela passe a ser exigida.
def _senha_configurada():
    try:
        return str(st.secrets.get("SENHA_DASHBOARD", "")).strip()
    except Exception:
        return ""


def exigir_acesso():
    senha = _senha_configurada()
    if not senha:
        return
    if st.session_state.get("dashboard_liberado"):
        return

    st.markdown("<p class='titulo-dashboard'>Painel da Prefeitura</p>",
                unsafe_allow_html=True)
    st.info("Esta área é restrita à equipe que atende as ocorrências.")
    digitada = st.text_input("Senha de acesso", type="password")
    if digitada:
        if digitada == senha:
            st.session_state["dashboard_liberado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()


exigir_acesso()

INTERVALO_MS = 2000

STATUS_LABELS = {
    "recebida": "🔴 Recebida",
    "em_andamento": "🟠 Em andamento",
    "concluida": "🟢 Concluída",
}
STATUS_CORES_MAPA = {
    "recebida": "red",
    "em_andamento": "orange",
    "concluida": "green",
}
LABEL_PARA_STATUS = {v: k for k, v in STATUS_LABELS.items()}

REGISTROS_PATH = BASE_DIR / "registros.json"


def carregar_registros():
    """Lê registros.json e garante que todo registro tenha id/status/wallet/token_tx
    (registros antigos, salvos antes desses campos existirem, ganham valores padrão)."""
    try:
        with open(REGISTROS_PATH, "r", encoding="utf-8") as f:
            linhas = [json.loads(linha) for linha in f.readlines() if linha.strip()]
    except FileNotFoundError:
        linhas = []

    for i, r in enumerate(linhas):
        r.setdefault("id", f"legacy-{i}")
        r.setdefault("status", "recebida")
        r.setdefault("wallet", "")
        r.setdefault("token_tx", "")
        # "arquivada" é independente do status: uma ocorrência arquivada
        # continua sendo concluída (ou recebida). Arquivar só a tira da
        # vista do dia a dia, sem apagar nada.
        r.setdefault("arquivada", False)
        # Registros da Fase 2 não guardavam o hash da transação de registro.
        # Nesses casos "onchain" fica indefinido: não dá para afirmar nem
        # negar que existe prova pública, então o dashboard não inventa uma.
        r.setdefault("tx_registro", "")
        if "onchain" not in r:
            r["onchain"] = bool(r.get("tx_registro"))
    return linhas


def ordenar_por_data(lista):
    """Mais recentes primeiro. A data é gravada como 'AAAA-MM-DD HH:MM:SS',
    formato em que a ordem alfabética coincide com a cronológica."""
    return sorted(lista, key=lambda r: str(r.get("data", "")), reverse=True)


def data_curta(r):
    """Converte '2026-08-22 21:25:12' em '22/08/2026 21:25'."""
    bruta = str(r.get("data", ""))
    try:
        d, h = bruta.split(" ")
        ano, mes, dia = d.split("-")
        return f"{dia}/{mes}/{ano} {h[:5]}"
    except Exception:
        return bruta or "sem data"


def salvar_registros(registros):
    with open(REGISTROS_PATH, "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r) + "\n")


registros = carregar_registros()

# ===========================================================================
# Conclusão on-chain: por que existe esta etapa separada
#
# A transação de conclusão leva de 5 a 30 segundos. O auto-refresh de 2s
# reiniciaria o script no meio do envio e o resultado nunca apareceria na
# tela. Por isso o fluxo é dividido em dois momentos:
#
#   1. O botão "Atualizar" apenas ANOTA que aquela ocorrência precisa ser
#      concluída on-chain (em st.session_state) e recarrega a página.
#   2. Nesse novo carregamento, o auto-refresh NÃO é montado, então nada
#      interrompe a transação. Ela roda com calma e o resultado é guardado
#      para ser exibido no carregamento seguinte.
# ===========================================================================
pendente = st.session_state.get("conclusao_pendente")

if not pendente:
    st_autorefresh(interval=INTERVALO_MS, key="auto_refresh_dashboard")

st.markdown(
    "<p class='titulo-dashboard'>🗺️ Dashboard</p>", unsafe_allow_html=True)

if pendente:
    alvo = next((r for r in registros if r.get("id") == pendente), None)

    if alvo is None:
        st.session_state.pop("conclusao_pendente", None)
        st.rerun()

    st.info(
        "⏳ Registrando a conclusão na blockchain e enviando o token CP. "
        "Isso leva de 5 a 30 segundos — **não feche nem atualize a página.**"
    )
    with st.spinner("Enviando transação para a Polygon Amoy..."):
        try:
            tx = concluir_ocorrencia(alvo["cid"], alvo["wallet"])
            alvo["token_tx"] = tx
            salvar_registros(registros)
            st.session_state["conclusao_resultado"] = ("ok", tx)
        except Exception as e:
            st.session_state["conclusao_resultado"] = ("erro", str(e))

    # A antena NÃO é acionada daqui. Quem a aciona é o vigia_antena.py, que
    # observa os contratos na blockchain de forma independente. Se o dashboard
    # também sinalizasse, o LED piscaria duas vezes e, pior, a antena passaria
    # a confiar no aplicativo em vez de confiar no registro público, que é
    # exatamente o contrário da tese do projeto.

    st.session_state.pop("conclusao_pendente", None)
    st.rerun()

resultado = st.session_state.pop("conclusao_resultado", None)
if resultado:
    tipo, valor = resultado
    if tipo == "ok":
        st.success("✅ Conclusão registrada na blockchain e token CP enviado!")
        st.markdown(
            f"🔗 [Ver a transação no Polygonscan](https://amoy.polygonscan.com/tx/{valor})"
        )
    elif tipo == "sem_carteira":
        st.warning(
            "Ocorrência marcada como concluída, mas sem carteira informada — "
            "nenhuma transação de conclusão foi enviada."
        )
    else:
        st.error(
            f"⚠️ Falha ao registrar a conclusão on-chain: {valor}\n\n"
            "O status foi salvo como concluída mesmo assim. Selecione "
            "**Concluída** e clique em **Atualizar** de novo para tentar outra vez."
        )

st.markdown(
    "<p class='subtitulo-dashboard'>Ocorrências registradas</p>",
    unsafe_allow_html=True)

if registros:
    st.write(f"**{len(registros)} ocorrência(s) registrada(s)**")

    lats = [r["latitude"] for r in registros]
    lons = [r["longitude"] for r in registros]
    centro = [sum(lats) / len(lats), sum(lons) / len(lons)]

    mapa = folium.Map(location=centro, zoom_start=12)

    if len(registros) > 1:
        mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    for r in registros:
        status = r.get("status", "recebida")
        popup_html = f"""
        <b>{r.get('descricao', 'Sem descrição')}</b><br>
        Status: {STATUS_LABELS.get(status, status)}<br>
        Endereço: {r.get('endereco', 'N/A')}<br>
        Nome: {r.get('nome', 'N/A')}<br>
        Data: {r.get('data', 'N/A')}<br>
        CID: <a href='https://gateway.pinata.cloud/ipfs/{r.get("cid", "")}' target='_blank'>{r.get('cid', 'N/A')[:20]}...</a>
        """
        folium.Marker(
            location=[r["latitude"], r["longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(
                color=STATUS_CORES_MAPA.get(status, "gray"),
                icon="exclamation-sign"
            )
        ).add_to(mapa)

    st_folium(mapa, width=900, height=500, key="mapa_depin")

    st.markdown("### Ocorrências e status")
    # Texto normal em vez de legenda: esta instrução é operacional (explica o
    # que acontece ao concluir) e precisa ser lida sem esforço na projeção.
    st.markdown(
        "Atualize o status manualmente conforme o andamento. Ao marcar como "
        "**Concluída**, se a ocorrência tiver uma carteira informada, sai uma "
        "transação na blockchain que registra a conclusão e envia o token "
        "CP (Cidadão Participativo), tudo de uma vez, além de acionar o sinal "
        "da antena."
    )

    def protocolo_de(r):
        """Número de protocolo exibido na lista.

        Os registros feitos a partir de agora já nascem com um id curto que
        serve de protocolo. Os herdados da Fase 2 não tinham isso, e recebem
        um rótulo próprio para não aparecerem como 'LEGACY-3' na tela.
        """
        ident = str(r.get("id", ""))
        if ident.startswith("legacy-"):
            return f"FASE2-{ident.split('-')[-1].zfill(2)}"
        return ident.upper()

    def mostrar_ocorrencia(r):
        """Desenha o cartão de uma ocorrência, com os detalhes e os controles
        de status e exclusão. Usado pelas três abas."""
        status_atual = r.get("status", "recebida")
        # Protocolo e data vêm primeiro: identificam a ocorrência sem
        # ambiguidade. A descrição entra encurtada, só como pista — assim
        # todas as linhas ficam com a mesma altura, em vez de umas com uma
        # linha e outras com quatro.
        desc = r.get("descricao", "Sem descrição")
        if len(desc) > 40:
            desc = desc[:40].rstrip() + "…"
        titulo = (f"{STATUS_LABELS.get(status_atual, status_atual)}  "
                  f"{protocolo_de(r)}  ·  {data_curta(r)}  ·  {desc}")
        with st.expander(titulo):
            st.write(f"**Protocolo:** `{protocolo_de(r)}`")
            st.write(f"**Nome:** {r.get('nome', 'N/A')}")
            if r.get("email"):
                st.write(f"**E-mail:** {r['email']}")
            st.write(f"**Endereço:** {r.get('endereco', 'N/A')}")
            st.write(f"**Descrição:** {r.get('descricao', 'N/A')}")
            st.write(f"**Data:** {r.get('data', 'N/A')}")
            st.write(f"**Carteira:** {r.get('wallet') or '_não informada_'}")

            if r.get("cid"):
                link_foto = f"https://gateway.pinata.cloud/ipfs/{r['cid']}"
                st.image(link_foto, width=300)
                # O link fica sempre disponível: o gateway do IPFS às vezes
                # demora ou não responde, e nesse caso a imagem acima não
                # carrega. Com o link, a foto continua acessível.
                st.caption(
                    f"🔐 Impressão digital da foto: `{r['cid']}` — "
                    f"[abrir a imagem]({link_foto})")

            # Prova pública do registro. Se ela não existe, o dashboard diz
            # isso com todas as letras: uma ocorrência que ficou só no arquivo
            # local não tem o valor central que o projeto promete.
            if r.get("tx_registro"):
                st.markdown(
                    f"**Comprovante do registro:** "
                    f"[abrir no Polygonscan]"
                    f"(https://amoy.polygonscan.com/tx/{r['tx_registro']})"
                )
            elif not str(r.get("id", "")).startswith("legacy-"):
                st.warning(
                    "Esta ocorrência não tem prova on-chain: a gravação na "
                    "blockchain falhou no momento do envio. O registro existe "
                    "aqui, mas não é auditável publicamente."
                )

            if r.get("token_tx"):
                st.markdown(
                    f"**Comprovante de conclusão e recompensa:** "
                    f"[abrir no Polygonscan](https://amoy.polygonscan.com/tx/{r['token_tx']})"
                )
                st.caption(
                    "⛓️ A conclusão e o envio do token saíram na mesma operação — "
                    "uma não existe sem a outra."
                )

            col1, col2 = st.columns([3, 1])
            with col1:
                label_escolhido = st.selectbox(
                    "Status",
                    options=list(STATUS_LABELS.values()),
                    index=list(STATUS_LABELS.keys()).index(status_atual),
                    key=f"status_{r['id']}",
                )
            with col2:
                atualizar = st.button("Atualizar", key=f"upd_{r['id']}")

            if atualizar:
                novo_status = LABEL_PARA_STATUS[label_escolhido]
                mudou_status = novo_status != status_atual
                precisa_tentar_onchain = (
                    novo_status == "concluida" and not r.get("token_tx")
                )

                if not mudou_status and not precisa_tentar_onchain:
                    st.info("Esse já é o status atual.")
                else:
                    r["status"] = novo_status
                    salvar_registros(registros)

                    if precisa_tentar_onchain:
                        if r.get("wallet"):
                            st.session_state["conclusao_pendente"] = r["id"]
                        else:
                            st.session_state["conclusao_resultado"] = (
                                "sem_carteira", "")

                    st.rerun()

            # ---- Arquivar / restaurar ----
            # Arquivar em vez de excluir: nada é apagado, a ocorrência apenas
            # sai da vista do dia a dia. Isso é coerente com o próprio projeto,
            # em que o registro na blockchain é permanente por definição.
            st.markdown("")
            if r.get("arquivada"):
                if st.button("↩️ Restaurar", key=f"rest_{r['id']}"):
                    r["arquivada"] = False
                    salvar_registros(registros)
                    st.rerun()
            else:
                if st.button("🗂️ Arquivar", key=f"arq_{r['id']}"):
                    r["arquivada"] = True
                    salvar_registros(registros)
                    st.rerun()

    # Uma aba para cada status, nas mesmas cores dos pinos do mapa.
    # Usamos abas em vez de expansores porque o Streamlit não permite um
    # expansor dentro de outro, e cada ocorrência já é um expansor.
    ativas = [r for r in registros if not r.get("arquivada")]

    recebidas = ordenar_por_data(
        [r for r in ativas if r.get("status", "recebida") == "recebida"])
    em_andamento = ordenar_por_data(
        [r for r in ativas if r.get("status") == "em_andamento"])
    concluidas = ordenar_por_data(
        [r for r in ativas if r.get("status") == "concluida"])
    arquivadas = ordenar_por_data(
        [r for r in registros if r.get("arquivada")])

    # Lista vertical em vez de abas lado a lado: no celular, quatro abas
    # horizontais ficam apertadas e a contagem some. Empilhadas, cada grupo
    # ocupa uma linha inteira e o número fica sempre visível.
    GRUPOS = [
        (f"🔴 Recebidas ({len(recebidas)})", recebidas,
         "Nenhuma ocorrência aguardando atendimento.", "sucesso"),
        (f"🟠 Em andamento ({len(em_andamento)})", em_andamento,
         "Nenhuma ocorrência em andamento no momento.", "info"),
        (f"🟢 Concluídas ({len(concluidas)})", concluidas,
         "Nenhuma ocorrência concluída ainda.", "info"),
        (f"🗂️ Arquivadas ({len(arquivadas)})", arquivadas,
         "Nenhuma ocorrência arquivada ainda.", "info"),
    ]

    rotulos = [g[0] for g in GRUPOS]
    escolhido = st.radio("Ver:", rotulos, key="filtro_grupo",
                         label_visibility="collapsed")

    st.markdown("---")

    _, lista, vazio, tipo_vazio = next(g for g in GRUPOS if g[0] == escolhido)

    if escolhido.startswith("🗂️"):
        st.markdown(
            "Ocorrências já atendidas saem das listas do dia a dia e ficam "
            "guardadas aqui, mantendo o histórico do que a cidade resolveu. "
            "**Nada é apagado:** o registro de cada uma continua público e "
            "permanente na blockchain, e qualquer ocorrência pode ser "
            "restaurada a qualquer momento."
        )
        st.markdown("")

    if lista:
        for r in lista:
            mostrar_ocorrencia(r)
    elif tipo_vazio == "sucesso":
        st.success(vazio)
    else:
        st.info(vazio)
else:
    st.warning(
        "Nenhuma ocorrência registrada ainda. Envie pelo formulário primeiro!")
