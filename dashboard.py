import streamlit as st
import json
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

from antena_serial import enviar_sinal
from mint_token import concluir_ocorrencia
from tema_visual import aplicar_tema

st.set_page_config(page_title="Dashboard DePIN", page_icon="🗺️", layout="wide")
aplicar_tema()

# ===== Auto-refresh =====
# Intervalo em milissegundos. 2000 = 2 segundos.
# Aumente para 5000 se quiser um refresh mais suave durante a gravação.
INTERVALO_MS = 2000
st_autorefresh(interval=INTERVALO_MS, key="auto_refresh_dashboard")

st.title("🗺️ Dashboard DePIN Urbano")
st.subheader("Ocorrências registradas")

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

REGISTROS_PATH = "registros.json"


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

if registros:
    st.write(f"**{len(registros)} ocorrência(s) registrada(s)**")

    # Centraliza o mapa automaticamente na média das coordenadas
    lats = [r["latitude"] for r in registros]
    lons = [r["longitude"] for r in registros]
    centro = [sum(lats) / len(lats), sum(lons) / len(lons)]

    mapa = folium.Map(location=centro, zoom_start=12)

    # Ajusta o zoom para enquadrar todos os pontos
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
                # Se já está "concluída" mas a transação on-chain falhou antes
                # (token_tx ainda vazio), o botão tenta de novo mesmo sem
                # mudar o status — é o "tentar de novo" prometido no erro.
                precisa_tentar_onchain = (
                    novo_status == "concluida" and not r.get("token_tx")
                )

                if not mudou_status and not precisa_tentar_onchain:
                    st.info("Esse já é o status atual.")
                else:
                    r["status"] = novo_status

                    if precisa_tentar_onchain:
                        if r.get("wallet"):
                            try:
                                tx = concluir_ocorrencia(r["cid"], r["wallet"])
                                r["token_tx"] = tx
                                st.success(
                                    f"✅ Conclusão registrada na blockchain e token CP enviado! "
                                    f"Tx: {tx}"
                                )
                            except Exception as e:
                                st.error(
                                    f"⚠️ Falha ao registrar a conclusão on-chain: {e}. "
                                    f"Status salvo como concluída mesmo assim; "
                                    f"clique em Atualizar de novo (com Concluída "
                                    f"selecionada) para tentar mais uma vez."
                                )
                        else:
                            st.warning(
                                "Ocorrência concluída, mas sem carteira informada — "
                                "nenhuma transação de conclusão foi enviada."
                            )
                        # Sinaliza a antena (não trava se ela não estiver conectada)
                        enviar_sinal("CONCLUIDA")

                    salvar_registros(registros)
                    st.rerun()
else:
    st.warning(
        "Nenhuma ocorrência registrada ainda. Envie pelo formulário primeiro!")
