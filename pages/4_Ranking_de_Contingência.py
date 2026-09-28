"""
Ranking de Contingência — DePIN Urbano, Bloco 7 (28/09)

"Seguro-incêndio" do telão: se o React do Rafa cair no dia do evento, esta
página do Streamlit mostra o mesmo ranking, de forma mínima e propositalmente
feia (~30 min de trabalho — ver "Ordem do dia" no Plano de execução). Não é
para ser bonita; é para sempre existir.

Lê exatamente a mesma função `telao()` que o React já usa e já testou desde
18/09 — nenhuma função nova no banco, `telao()` continua intocada, e o que o
Rafa consome dela não muda em nada (REGRA QUE NÃO SE QUEBRA). Por isso não há
senha aqui: é o mesmo dado público que já aparece no telão para qualquer
pessoa no evento.
"""

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ocorrencias import obter_ranking_contingencia   # noqa: E402
from tema_visual import aplicar_tema                 # noqa: E402

st.set_page_config(
    page_title="Ranking (contingência) — DePIN Urbano",
    page_icon="🏆",
    initial_sidebar_state="collapsed",
)
aplicar_tema()

st.markdown("<p class='titulo-sobre'>🏆 Ranking da Gincana</p>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitulo-sobre'>Modo de contingência — use só se o telão "
    "principal não estiver funcionando</p>",
    unsafe_allow_html=True,
)
st.caption(
    "Página simples, de propósito: existe só para nunca deixar o evento sem "
    "ranking. O telão de verdade é o do Rafa."
)

if st.button("🔄 Atualizar"):
    st.rerun()

st.markdown("---")

dados = obter_ranking_contingencia()

if not dados["ok"]:
    st.error(f"⚠️ Não foi possível carregar o ranking agora: {dados['erro']}")
    st.caption("Tente atualizar em alguns instantes.")
    st.stop()

evento = dados["evento"]
ranking = dados["ranking"]

col1, col2, col3 = st.columns(3)
col1.metric("📋 Ocorrências da gincana", evento.get("total_ocorrencias", "—"))
col2.metric("👥 Participantes", evento.get("participantes", "—"))
col3.metric("📡 Antenas ativas", evento.get("antenas_ativas", "—"))

meta = evento.get("meta")
total = evento.get("total_ocorrencias")
if meta:
    st.progress(min(1.0, (total or 0) / meta), text=f"{total or 0} de {meta} ocorrências")

st.markdown("---")
st.markdown("### Classificação")

if not ranking:
    st.info("Ainda não há ninguém no ranking.")
else:
    for linha in ranking:
        posicao = linha.get("posicao", "—")
        apelido = linha.get("apelido", "—")
        pontos = linha.get("pontos", 0)
        cp = linha.get("cp", 0)
        st.markdown(
            f"**{posicao}º** — {apelido} · {pontos} pontos · {cp} CP"
        )

st.markdown("---")
st.caption(
    "Dado ao vivo, direto do mesmo banco que o telão principal usa. Recarregue "
    "a página ou aperte \"Atualizar\" para ver o placar mais recente."
)
