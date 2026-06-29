import streamlit as st
import json
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Dashboard DePIN", page_icon="🗺️", layout="wide")

# ===== Auto-refresh =====
# Intervalo em milissegundos. 2000 = 2 segundos.
# Aumente para 5000 se quiser um refresh mais suave durante a gravação.
INTERVALO_MS = 2000
st_autorefresh(interval=INTERVALO_MS, key="auto_refresh_dashboard")

st.title("🗺️ Dashboard DePIN Urbano")
st.subheader("Ocorrências registradas")

# Lê os registros
try:
    with open("registros.json", "r", encoding="utf-8") as f:
        registros = [json.loads(linha) for linha in f.readlines() if linha.strip()]
except FileNotFoundError:
    registros = []

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
        popup_html = f"""
        <b>{r.get('descricao', 'Sem descrição')}</b><br>
        Endereço: {r.get('endereco', 'N/A')}<br>
        Nome: {r.get('nome', 'N/A')}<br>
        Data: {r.get('data', 'N/A')}<br>
        CID: <a href='https://gateway.pinata.cloud/ipfs/{r.get("cid", "")}' target='_blank'>{r.get('cid', 'N/A')[:20]}...</a>
        """
        folium.Marker(
            location=[r["latitude"], r["longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="red", icon="exclamation-sign")
        ).add_to(mapa)

    st_folium(mapa, width=900, height=500, key="mapa_depin")

    st.markdown("### Detalhes das ocorrências")
    for i, r in enumerate(registros):
        with st.expander(f"Ocorrência {i+1} - {r.get('descricao', 'Sem descrição')[:80]}"):
            st.write(f"**Nome:** {r.get('nome', 'N/A')}")
            st.write(f"**Endereço:** {r.get('endereco', 'N/A')}")
            st.write(f"**Descrição:** {r.get('descricao', 'N/A')}")
            st.write(f"**Data:** {r.get('data', 'N/A')}")
            if r.get("cid"):
                st.write(f"**CID:** {r['cid']}")
                st.image(
                    f"https://gateway.pinata.cloud/ipfs/{r['cid']}", width=300)
else:
    st.warning(
        "Nenhuma ocorrência registrada ainda. Envie pelo formulário primeiro!")
