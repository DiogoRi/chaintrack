"""
tema_visual.py — DePIN Urbano

Estilo visual compartilhado entre as duas páginas do app.

A paleta base (fundo, texto, cor de destaque) fica em `.streamlit/config.toml`,
porque só de lá o Streamlit pinta os próprios componentes internos — menus
suspensos, o seletor de arquivos, os avisos. O CSS abaixo cuida do resto:
tamanhos de título, o menu lateral, os cartões das ocorrências e espaçamentos.

Paleta em tons pastéis:
    fundo      #F5F7FA   cinza-azulado bem claro
    cartões    #FFFFFF   branco
    destaque   #5B8FB9   azul suave
    texto      #33404D   cinza-azulado escuro
    apoio      #7A8794   cinza médio (legendas)

Uso:
    from tema_visual import aplicar_tema
    aplicar_tema()   # logo depois de st.set_page_config(...)
"""

import streamlit as st

_CSS = """
<style>
    /* ---------- Fundo ---------- */
    .stApp {
        background: linear-gradient(180deg, #F7F9FC 0%, #EEF2F7 100%);
    }

    /* ---------- Títulos ----------
       Bem maiores que o padrão: numa apresentação projetada, o título é o
       que orienta quem assiste de longe. */
    h1 {
        color: #3D6E94 !important;
        font-weight: 700 !important;
        font-size: 2.6rem !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem !important;
    }
    h2 {
        color: #3D6E94 !important;
        font-weight: 650 !important;
        font-size: 1.9rem !important;
    }
    h3 {
        color: #4A7FA5 !important;
        font-weight: 600 !important;
        font-size: 1.35rem !important;
        margin-top: 1.6rem !important;
    }

    /* ---------- Títulos do dashboard ----------
       Têm tamanho próprio, maior que o do formulário: o dashboard é a tela
       projetada para a plateia, enquanto o formulário é lido de perto, na
       mão de quem registra. */
    .titulo-dashboard {
        font-size: 3.2rem !important;
        font-weight: 700 !important;
        color: #3D6E94 !important;
        letter-spacing: -1px;
        margin: 0 0 0.6rem 0 !important;
        line-height: 1.1;
    }
    .subtitulo-dashboard {
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        color: #3D6E94 !important;
        margin: 0.4rem 0 0.6rem 0 !important;
    }

    /* ---------- Títulos da página "Sobre o projeto" ----------
       Menor que o do dashboard para caber numa linha só no celular, e com
       margem positiva entre título e subtítulo (a classe da frase de
       impacto usa margem negativa, que aqui colaria os dois). */
    .titulo-sobre {
        font-size: 2.6rem !important;
        font-weight: 700 !important;
        color: #3D6E94 !important;
        letter-spacing: -0.5px;
        line-height: 1.15;
        margin: 0 0 0.9rem 0 !important;
    }
    .subtitulo-sobre {
        font-size: 1.4rem !important;
        font-weight: 500 !important;
        color: #6B8FA8 !important;
        margin: 0 0 1.6rem 0 !important;
    }

    /* ---------- Frase de impacto ----------
       Fica entre o título e o subtítulo. Tamanho intermediário de propósito:
       maior que o texto comum, para ser lida de longe numa projeção, mas
       menor que o título, para não competir com ele. */
    .frase-impacto {
        font-size: 1.45rem !important;
        line-height: 1.35;
        font-weight: 500;
        color: #6B8FA8 !important;
        margin: -0.4rem 0 1.4rem 0 !important;
    }

    /* ---------- Menu lateral (navegação entre as páginas) ----------
       O padrão é discreto demais para usar ao vivo diante de uma banca. */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E1E8F0;
    }
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] a span,
    section[data-testid="stSidebar"] li a p {
        font-size: 1.12rem !important;
        font-weight: 600 !important;
        color: #3D6E94 !important;
    }
    section[data-testid="stSidebar"] a:hover {
        background-color: #EEF4FA !important;
        border-radius: 8px;
    }

    /* ---------- Botões ---------- */
    .stButton > button {
        background: #5B8FB9;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.9rem 2rem;
        font-weight: 650;
        font-size: 1.55rem;
        text-transform: none;
        letter-spacing: 0;
        box-shadow: 0 1px 3px rgba(59, 89, 116, 0.18);
        transition: background 0.15s ease, transform 0.15s ease;
    }
    .stButton > button:hover {
        background: #4A7FA5;
        transform: translateY(-1px);
    }

    /* ---------- Campos ---------- */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #33404D !important;
        border: 1px solid #D6DFEA !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: #5B8FB9 !important;
        box-shadow: 0 0 0 2px rgba(91, 143, 185, 0.15) !important;
    }
    /* Texto de exemplo dentro dos campos */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #A9B4C0 !important;
        font-style: italic;
    }

    /* ---------- Lista de grupos do dashboard ----------
       O seletor de grupos (Recebidas / Em andamento / Concluídas /
       Arquivadas) aparece empilhado. Aumentamos a fonte e o espaçamento
       para que cada linha seja fácil de acertar com o dedo no celular. */
    div[role="radiogroup"] label p {
        font-size: 1.12rem !important;
        font-weight: 600 !important;
        color: #33404D !important;
    }
    div[role="radiogroup"] > label {
        padding: 0.35rem 0;
    }

    /* ---------- Cartões (expanders) ---------- */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E1E8F0;
        border-radius: 12px;
        margin-bottom: 0.6rem;
        box-shadow: 0 1px 3px rgba(59, 89, 116, 0.06);
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600;
        color: #33404D;
    }

    /* ---------- Avisos ---------- */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: none;
    }

    /* ---------- Legendas ----------
       Escurecidas em relação ao padrão do Streamlit: o cinza claro fica
       quase invisível numa projeção, e essas legendas carregam informação
       que a banca precisa conseguir ler. */
    .stCaption, div[data-testid="stCaptionContainer"] p {
        color: #46525F !important;
        font-size: 0.96rem !important;
    }

    /* ---------- Rótulos dos campos ---------- */
    label p {
        font-weight: 600 !important;
        color: #4A5765 !important;
    }
</style>
"""


def aplicar_tema() -> None:
    """Injeta o CSS do tema. Chamar uma vez, logo após st.set_page_config(...)."""
    st.markdown(_CSS, unsafe_allow_html=True)
