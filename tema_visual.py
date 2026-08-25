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

    /* ---------- Campos que a pessoa preenche ----------
       Listas suspensas, campo numérico e área de arquivo recebem o mesmo
       tratamento: caixa branca, borda visível, cantos arredondados e uma
       sombra leve. Sem isso eles somem no fundo claro e a pessoa não
       percebe que ali tem algo para tocar.

       Os nomes usados abaixo (stSelectbox, stNumberInputContainer e
       companhia) são os que o próprio Streamlit coloca no HTML nesta
       versão. Uma tentativa anterior mirou em "data-baseweb", que a
       biblioteca usava antigamente e não usa mais — por isso o contorno
       aparecia no campo numérico e não nas listas.  */

    /* Lista suspensa: a caixa é o elemento com role="group", que envolve
       o texto e a setinha. */
    div[data-testid="stSelectbox"] div[role="group"] {
        background-color: #FFFFFF !important;
        border: 1px solid #C3D0E0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(59, 89, 116, 0.10) !important;
        min-height: 46px;
        cursor: pointer !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stSelectbox"] div[role="group"]:hover,
    div[data-testid="stSelectbox"] div[role="group"]:focus-within {
        border-color: #5B8FB9 !important;
        box-shadow: 0 2px 6px rgba(59, 89, 116, 0.18) !important;
    }
    div[data-testid="stSelectbox"] input {
        background: transparent !important;
        border: none !important;
        color: #33404D !important;
        cursor: pointer !important;
    }
    div[data-testid="stSelectbox"] button {
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
    }
    div[data-testid="stSelectbox"] svg {
        color: #5B8FB9 !important;
    }

    /* A MESMA caixa, para a estrutura antiga do componente.
       O Streamlit trocou a biblioteca das listas suspensas: nas versões
       novas a caixa é o elemento com role="group" (regra acima), nas
       antigas era um div marcado com data-baseweb. Como a máquina que
       publica o app pode estar numa versão diferente da que usamos para
       desenvolver, as duas formas ficam descritas. Elas nunca coexistem
       no mesmo HTML, então não há risco de desenhar caixa dentro de
       caixa: a que não existir simplesmente não encontra nada. */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #C3D0E0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(59, 89, 116, 0.10) !important;
        min-height: 46px;
        cursor: pointer !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
    div[data-baseweb="select"] > div:hover {
        border-color: #5B8FB9 !important;
        box-shadow: 0 2px 6px rgba(59, 89, 116, 0.18) !important;
    }
    div[data-baseweb="select"] > div > div {
        border: none !important;
        background: transparent !important;
    }

    /* Campo numérico: a borda envolve o número junto com os botões de mais
       e menos. Soltos, eles não parecem ter relação com o valor ao lado. */
    div[data-testid="stNumberInputContainer"] {
        background-color: #FFFFFF !important;
        border: 1px solid #C3D0E0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(59, 89, 116, 0.10) !important;
        overflow: hidden;
        min-height: 46px;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stNumberInputContainer"]:hover,
    div[data-testid="stNumberInputContainer"]:focus-within {
        border-color: #5B8FB9 !important;
        box-shadow: 0 2px 6px rgba(59, 89, 116, 0.18) !important;
    }
    div[data-testid="stNumberInputField"] {
        background: transparent !important;
        border: none !important;
        color: #33404D !important;
    }
    div[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"] {
        background-color: #EEF4FA !important;
        border-left: 1px solid #C3D0E0 !important;
        cursor: pointer !important;
    }
    button[data-testid="stNumberInputStepUp"]:hover,
    button[data-testid="stNumberInputStepDown"]:hover {
        background-color: #DCE8F4 !important;
    }

    /* Campos de texto: mesma borda das listas, para a coluna inteira ficar
       com um desenho só. */
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextAreaRootElement"] {
        background-color: #FFFFFF !important;
        border: 1px solid #C3D0E0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(59, 89, 116, 0.08) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stTextAreaRootElement"]:focus-within {
        border-color: #5B8FB9 !important;
        box-shadow: 0 0 0 2px rgba(91, 143, 185, 0.15) !important;
    }

    /* Área de envio de arquivo. */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #C3D0E0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(59, 89, 116, 0.08) !important;
    }
    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #5B8FB9 !important;
    }

    /* Sombra leve em todo botão, inclusive o de baixar o comprovante. */
    .stDownloadButton > button {
        background: #5B8FB9;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        font-weight: 650;
        box-shadow: 0 1px 3px rgba(59, 89, 116, 0.18);
        transition: background 0.15s ease, box-shadow 0.15s ease,
                    transform 0.15s ease;
    }
    .stDownloadButton > button:hover {
        background: #4A7FA5;
        box-shadow: 0 3px 8px rgba(59, 89, 116, 0.24);
        transform: translateY(-1px);
    }
    .stButton > button:hover {
        box-shadow: 0 3px 8px rgba(59, 89, 116, 0.24);
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

    /* ---------- Celular ----------
       Duas correções que só aparecem em telas estreitas:

       1. Os títulos grandes, pensados para projeção, não cabem numa linha
          e quebram em lugares esquisitos. O clamp() faz o tamanho
          acompanhar a largura da tela, entre um minimo e o valor cheio.
       2. O conteúdo encosta na borda esquerda, o que dá a impressão de
          texto desalinhado. Uma margem igual dos dois lados resolve. */
    @media (max-width: 640px) {
        .block-container {
            padding-left: 1.1rem !important;
            padding-right: 1.1rem !important;
            padding-top: 2.6rem !important;
        }
        h1 { font-size: clamp(1.5rem, 7vw, 2.6rem) !important; }
        h2 { font-size: clamp(1.25rem, 5.4vw, 1.9rem) !important; }
        h3 { font-size: clamp(1.05rem, 4.8vw, 1.35rem) !important; }

        /* Os títulos longos das páginas ("Dashboard do Município",
           "Acompanhar ocorrência") quebravam em duas linhas, e a segunda
           linha sozinha à esquerda dava a impressão de desalinho. Numa
           tela estreita eles encolhem o suficiente para caber numa linha
           só, que é como um título deve se comportar. */
        .titulo-dashboard { font-size: clamp(1.2rem, 6.2vw, 3.2rem) !important; }
        .subtitulo-dashboard { font-size: clamp(1.15rem, 5vw, 2.2rem) !important; }
        .titulo-sobre { font-size: clamp(1.2rem, 6.4vw, 2.6rem) !important; }
        .subtitulo-sobre { font-size: clamp(1rem, 4.2vw, 1.4rem) !important; }
        .frase-impacto { font-size: clamp(1rem, 4.4vw, 1.45rem) !important; }
        .stButton > button { font-size: 1.2rem; padding: 0.8rem 1.2rem; }
    }

    /* Títulos das páginas: mesma margem esquerda do texto que vem depois.
       Sem isto, um título dentro de <p> e um título em <h1> começam em
       pontos ligeiramente diferentes, e a coluna parece torta. */
    .titulo-sobre, .subtitulo-sobre, .titulo-dashboard,
    .subtitulo-dashboard, .frase-impacto {
        padding-left: 0 !important;
        margin-left: 0 !important;
        max-width: 100%;
        overflow-wrap: break-word;
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
