"""
tema_visual.py — DePIN Urbano

Estilo visual compartilhado entre app.py e dashboard.py: tema escuro com
azul de destaque, no mesmo clima do vídeo pitch da Fase 2 (visual
"painel tech / blockchain"). Só CSS por cima do Streamlit — nenhuma
lógica de negócio muda, nenhuma dependência nova.

Uso:
    from tema_visual import aplicar_tema
    aplicar_tema()   # chamar logo depois de st.set_page_config(...)
"""

import streamlit as st

_CSS = """
<style>
    /* Fundo geral em degradê escuro */
    .stApp {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        color: #e6edf3;
    }

    /* Títulos com o azul de destaque */
    h1, h2, h3 {
        color: #58a6ff !important;
        font-weight: 700;
    }

    /* Botões com gradiente azul */
    .stButton > button {
        background: linear-gradient(90deg, #1f6feb, #58a6ff);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 0 14px rgba(88, 166, 255, 0.55);
        transform: translateY(-1px);
    }

    /* Campos de texto e área de texto */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
    }

    /* Cartões (expanders) com borda sutil, tipo "card" */
    div[data-testid="stExpander"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }

    /* Mensagens de sucesso/aviso/erro com cantos arredondados */
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }

    /* Métricas e legendas */
    .stCaption, .stMarkdown p {
        color: #c9d1d9;
    }
</style>
"""


def aplicar_tema() -> None:
    """Injeta o CSS do tema escuro/azul. Chamar uma vez, logo após
    st.set_page_config(...)."""
    st.markdown(_CSS, unsafe_allow_html=True)
