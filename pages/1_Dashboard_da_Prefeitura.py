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

from antena_serial import enviar_sinal          # noqa: E402
from mint_token import concluir_ocorrencia      # noqa: E402
from tema_visual import aplicar_tema            # noqa: E402

st.set_page_config(page_title="Dashboard DePIN", page_icon="🗺️", layout="wide")
aplicar_tema()

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
    return linhas


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

st.title("🗺️ Dashboard DePIN Urbano")

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

    # Sinaliza a antena (nunca trava se ela não estiver conectada).
    # Na nuvem a antena nunca responde, e isso é esperado: o LED só funciona
    # quando o app roda no notebook ligado por USB à ESP32.
    enviar_sinal("CONCLUIDA")

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

st.subheader("Ocorrências registradas")

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
    st.caption(
        "Atualize o status manualmente conforme o andamento. Ao marcar como "
        "**Concluída**, se a ocorrência tiver uma carteira informada, sai uma "
        "transação na blockchain que registra a conclusão E envia o token "
        "CP (Cidadão Participativo), tudo de uma vez — além de acionar o sinal da antena."
    )

    for i, r in enumerate(registros):
        status_atual = r.get("status", "recebida")
        titulo = f"{STATUS_LABELS.get(status_atual, status_atual)} — {r.get('descricao', 'Sem descrição')[:70]}"
        with st.expander(titulo):
            st.write(f"**Nome:** {r.get('nome', 'N/A')}")
            st.write(f"**Endereço:** {r.get('endereco', 'N/A')}")
            st.write(f"**Descrição:** {r.get('descricao', 'N/A')}")
            st.write(f"**Data:** {r.get('data', 'N/A')}")
            st.write(f"**Carteira:** {r.get('wallet') or '_não informada_'}")
            if r.get("cid"):
                st.write(f"**CID:** {r['cid']}")
                st.image(
                    f"https://gateway.pinata.cloud/ipfs/{r['cid']}", width=300)
            if r.get("token_tx"):
                st.write(
                    f"**Conclusão + token on-chain:** "
                    f"[ver transação](https://amoy.polygonscan.com/tx/{r['token_tx']})"
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
                            enviar_sinal("CONCLUIDA")

                    st.rerun()
else:
    st.warning(
        "Nenhuma ocorrência registrada ainda. Envie pelo formulário primeiro!")
