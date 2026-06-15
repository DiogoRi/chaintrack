import streamlit as st
import json
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard DePIN", page_icon="🗺️", layout="wide")

st.title("🗺️ Dashboard DePIN Urbano")
st.subheader("Ocorrências registradas")

# Lê os registros
try:
    with open("registros.json", "r") as f:
        registros = [json.loads(linha) for linha in f.readlines()]
except FileNotFoundError:
    registros = []

if registros:
    st.write(f"**{len(registros)} ocorrência(s) registrada(s)**")

    mapa = folium.Map(
        location=[registros[0]["latitude"], registros[0]["longitude"]], zoom_start=13)

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

    st_folium(mapa, width=900, height=500)

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
