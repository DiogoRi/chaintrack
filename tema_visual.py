"""
tema_visual.py — DePIN Urbano

Estilo visual compartilhado entre todas as páginas do app.

A paleta base (fundo, texto, cor de destaque) fica em `.streamlit/config.toml`,
porque só de lá o Streamlit pinta os próprios componentes internos — menus
suspensos, o seletor de arquivos, os avisos. O CSS abaixo cuida do resto:
tamanhos de título, o menu lateral, os cartões das ocorrências e espaçamentos.

TEMA (Bloco 6, 27/09): alinhado com a página da gincana do Rafa
(depinurbano.vercel.app), para o ChainTrack e o React parecerem um produto só.
Cores tiradas dos pixels de uma captura da página do Rafa (27/09):
    fundo        #FFF9EF   creme
    texto        #42302E   marrom escuro (títulos e texto)
    destaque     #E03A12   vermelho-laranja (botões) — escolhido em vez do
                           laranja do losango (#F26120) porque texto branco
                           sobre ele tem contraste 4,4:1; sobre o laranja
                           seria 3,2:1, fraco para ler no sol do evento
    detalhe      #F26120   laranja do losango (bordas em foco, realces)
    campos       #F4F0E7   fundo dos campos / #D0CBC5 borda
    apoio        #6B5652   marrom médio (legendas)
    decorativas  #2942C0 azul · #FBC467 amarelo · #F9A8A4 rosa · #6BB6A2 verde
                 — só na faixa colorida do topo, como os blocos da página do Rafa

Estilo copiado da página do Rafa: rótulos em MAIÚSCULAS com letras espaçadas,
campos e botões em formato de pílula (bem arredondados), fundo creme liso.

Fontes (Google Fonts, parecidas com as do Rafa — o nome exato das dele não foi
confirmado): DM Sans no texto e Space Mono nos rótulos. A fonte é aplicada só
a texto, título, rótulo, campo e botão — nunca com seletor genérico (*, span),
porque os ícones do Streamlit também são uma fonte e virariam texto solto
("keyboard_arrow_down") se ela fosse trocada.

Como voltar ao tema anterior (azul pastel da Fase 3): ele está no histórico
do Git, no commit anterior ao do Bloco 6 — basta restaurar este arquivo, o
`.streamlit/config.toml` e as cores do botão "Voltar" no `app.py`.

Uso:
    from tema_visual import aplicar_tema
    aplicar_tema()   # logo depois de st.set_page_config(...)
"""

import streamlit as st

_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap');

    /* ---------- Fontes ----------
       Só em elementos de texto. Ver o aviso sobre ícones no topo do arquivo. */
    .stApp, .stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp label, .stApp input, .stApp textarea, .stApp button,
    .stApp a, .stMarkdown, .titulo-dashboard, .subtitulo-dashboard,
    .titulo-sobre, .subtitulo-sobre, .frase-impacto {
        font-family: 'DM Sans', sans-serif;
    }

    /* ---------- Fundo ----------
       Creme liso, como a página do Rafa (sem degradê). */
    .stApp {
        background: #FFF9EF;
    }

    /* ---------- Faixa colorida no topo ----------
       As cores dos blocos geométricos da página do Rafa, numa faixa fina.
       É o que mais "amarra" visualmente as duas páginas, sem competir com o
       conteúdo. */
    .block-container::before {
        content: "";
        display: block;
        height: 6px;
        border-radius: 999px;
        margin-bottom: 1.4rem;
        background: linear-gradient(90deg,
            #2942C0 0 20%, #E03A12 20% 40%, #FBC467 40% 60%,
            #F9A8A4 60% 80%, #6BB6A2 80% 100%);
    }

    /* ---------- Títulos ----------
       Bem maiores que o padrão: numa apresentação projetada, o título é o
       que orienta quem assiste de longe. */
    h1 {
        color: #42302E !important;
        font-weight: 700 !important;
        font-size: 2.6rem !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem !important;
    }
    h2 {
        color: #42302E !important;
        font-weight: 700 !important;
        font-size: 1.9rem !important;
    }
    h3 {
        color: #42302E !important;
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
        color: #42302E !important;
        letter-spacing: -1px;
        margin: 0 0 0.6rem 0 !important;
        line-height: 1.1;
    }
    .subtitulo-dashboard {
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        color: #42302E !important;
        margin: 0.4rem 0 0.6rem 0 !important;
    }

    /* ---------- Títulos da página "Sobre o projeto" ----------
       Menor que o do dashboard para caber numa linha só no celular, e com
       margem positiva entre título e subtítulo (a classe da frase de
       impacto usa margem negativa, que aqui colaria os dois). */
    .titulo-sobre {
        font-size: 2.6rem !important;
        font-weight: 700 !important;
        color: #42302E !important;
        letter-spacing: -0.5px;
        line-height: 1.15;
        margin: 0 0 0.9rem 0 !important;
    }
    .subtitulo-sobre {
        font-size: 1.4rem !important;
        font-weight: 500 !important;
        color: #8A6F69 !important;
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
        color: #8A6F69 !important;
        margin: -0.4rem 0 1.4rem 0 !important;
    }

    /* ---------- Menu lateral (navegação entre as páginas) ----------
       O padrão é discreto demais para usar ao vivo diante de uma banca. */
    section[data-testid="stSidebar"] {
        background-color: #FBF1E3;
        border-right: 1px solid #EADFD2;
    }
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] a span,
    section[data-testid="stSidebar"] li a p {
        font-size: 1.12rem !important;
        font-weight: 600 !important;
        color: #42302E !important;
    }
    section[data-testid="stSidebar"] a:hover {
        background-color: #F9DCD5 !important;
        border-radius: 999px;
    }

    /* ---------- Botões ----------
       Pílula, como o botão "Entrar na caça" da página do Rafa. */
    .stButton > button {
        background: #E03A12;
        color: #FFFFFF;
        border: none;
        border-radius: 999px;
        padding: 0.9rem 2rem;
        font-weight: 700;
        font-size: 1.55rem;
        text-transform: none;
        letter-spacing: 0;
        box-shadow: 0 2px 6px rgba(66, 48, 46, 0.18);
        transition: background 0.15s ease, transform 0.15s ease;
    }
    .stButton > button:hover {
        background: #C2300E;
        color: #FFFFFF;
        transform: translateY(-1px);
    }
    .stButton > button:focus:not(:active) {
        color: #FFFFFF;
    }
    /* O Streamlit põe o texto do botão dentro de um <p> com tamanho fixo
       (14px na versão 1.64, numa <div> e num <p> por dentro), o que anulava o tamanho definido acima — por
       isso os botões grandes pensados para o evento saíam pequenos, inclusive
       no tema anterior. Aqui o texto passa a seguir o tamanho do botão. */
    .stButton > button div, .stButton > button p,
    .stDownloadButton > button div, .stDownloadButton > button p {
        font-size: inherit !important;
        font-weight: inherit !important;
    }

    /* ---------- Campos ---------- */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: #F4F0E7 !important;
        color: #42302E !important;
        border: none !important;
        border-radius: 999px !important;
    }
    .stTextArea textarea {
        border-radius: 18px !important;
    }
    /* Texto de exemplo dentro dos campos */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #857670 !important;
        font-style: italic;
    }

    /* ---------- Campos que a pessoa preenche ----------
       Listas suspensas, campo numérico e área de arquivo recebem o mesmo
       tratamento: fundo creme mais escuro, borda visível, formato de pílula
       e uma sombra interna leve (o campo parece "afundado", como o campo de
       apelido da página do Rafa). Sem contorno eles somem no fundo claro e
       a pessoa não percebe que ali tem algo para tocar.

       Os nomes usados abaixo (stSelectbox, stNumberInputContainer e
       companhia) são os que o próprio Streamlit coloca no HTML nesta
       versão. Uma tentativa anterior mirou em "data-baseweb", que a
       biblioteca usava antigamente e não usa mais — por isso o contorno
       aparecia no campo numérico e não nas listas.  */

    /* Lista suspensa: a caixa é o elemento com role="group", que envolve
       o texto e a setinha. */
    div[data-testid="stSelectbox"] div[role="group"] {
        background-color: #F4F0E7 !important;
        border: 1.5px solid #D0CBC5 !important;
        border-radius: 999px !important;
        box-shadow: inset 0 2px 4px rgba(66, 48, 46, 0.08) !important;
        min-height: 46px;
        padding-left: 0.4rem;
        cursor: pointer !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stSelectbox"] div[role="group"]:hover,
    div[data-testid="stSelectbox"] div[role="group"]:focus-within {
        border-color: #F26120 !important;
        box-shadow: 0 0 0 3px rgba(242, 97, 32, 0.15) !important;
    }
    div[data-testid="stSelectbox"] input {
        background: transparent !important;
        border: none !important;
        color: #42302E !important;
        cursor: pointer !important;
    }
    div[data-testid="stSelectbox"] button {
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
    }
    div[data-testid="stSelectbox"] svg {
        color: #E03A12 !important;
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
        background-color: #F4F0E7 !important;
        border: 1.5px solid #D0CBC5 !important;
        border-radius: 999px !important;
        box-shadow: inset 0 2px 4px rgba(66, 48, 46, 0.08) !important;
        min-height: 46px;
        cursor: pointer !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
    div[data-baseweb="select"] > div:hover {
        border-color: #F26120 !important;
        box-shadow: 0 0 0 3px rgba(242, 97, 32, 0.15) !important;
    }
    div[data-baseweb="select"] > div > div {
        border: none !important;
        background: transparent !important;
    }

    /* Campo numérico: a borda envolve o número junto com os botões de mais
       e menos. Soltos, eles não parecem ter relação com o valor ao lado. */
    div[data-testid="stNumberInputContainer"] {
        background-color: #F4F0E7 !important;
        border: 1.5px solid #D0CBC5 !important;
        border-radius: 999px !important;
        box-shadow: inset 0 2px 4px rgba(66, 48, 46, 0.08) !important;
        overflow: hidden;
        min-height: 46px;
        padding-left: 0.4rem;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stNumberInputContainer"]:hover,
    div[data-testid="stNumberInputContainer"]:focus-within {
        border-color: #F26120 !important;
        box-shadow: 0 0 0 3px rgba(242, 97, 32, 0.15) !important;
    }
    div[data-testid="stNumberInputField"] {
        background: transparent !important;
        border: none !important;
        color: #42302E !important;
    }
    div[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"] {
        background-color: #FBE3D3 !important;
        border-left: 1px solid #D0CBC5 !important;
        cursor: pointer !important;
    }
    button[data-testid="stNumberInputStepUp"]:hover,
    button[data-testid="stNumberInputStepDown"]:hover {
        background-color: #F9C9B0 !important;
    }

    /* Campos de texto: mesma borda das listas, para a coluna inteira ficar
       com um desenho só. */
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextAreaRootElement"] {
        background-color: #F4F0E7 !important;
        border: 1.5px solid #D0CBC5 !important;
        border-radius: 999px !important;
        box-shadow: inset 0 2px 4px rgba(66, 48, 46, 0.08) !important;
        padding-left: 0.4rem;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    /* Área de texto de várias linhas: pílula completa ficaria estranha num
       campo alto, então os cantos são só bem arredondados. */
    div[data-testid="stTextAreaRootElement"] {
        border-radius: 18px !important;
    }
    div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stTextAreaRootElement"]:focus-within {
        border-color: #F26120 !important;
        box-shadow: 0 0 0 3px rgba(242, 97, 32, 0.15) !important;
    }

    /* Área de envio de arquivo. */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #F4F0E7 !important;
        border: 1.5px dashed #D0CBC5 !important;
        border-radius: 18px !important;
        box-shadow: none !important;
    }
    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #F26120 !important;
    }

    /* Botão de baixar o comprovante: mesma pílula dos outros botões. */
    .stDownloadButton > button {
        background: #E03A12;
        color: #FFFFFF;
        border: none;
        border-radius: 999px;
        font-weight: 700;
        box-shadow: 0 2px 6px rgba(66, 48, 46, 0.18);
        transition: background 0.15s ease, box-shadow 0.15s ease,
                    transform 0.15s ease;
    }
    .stDownloadButton > button:hover {
        background: #C2300E;
        color: #FFFFFF;
        box-shadow: 0 3px 8px rgba(66, 48, 46, 0.24);
        transform: translateY(-1px);
    }
    .stButton > button:hover {
        box-shadow: 0 3px 8px rgba(66, 48, 46, 0.24);
    }

    /* ---------- Lista de grupos do dashboard ----------
       O seletor de grupos (Recebidas / Em andamento / Concluídas /
       Arquivadas) aparece empilhado. Aumentamos a fonte e o espaçamento
       para que cada linha seja fácil de acertar com o dedo no celular. */
    div[role="radiogroup"] label p {
        font-size: 1.12rem !important;
        font-weight: 600 !important;
        color: #42302E !important;
    }
    div[role="radiogroup"] > label {
        padding: 0.35rem 0;
    }

    /* ---------- Abas (Dashboard: Ocorrências / Status do Worker) ---------- */
    button[data-baseweb="tab"] p {
        font-weight: 700 !important;
        color: #42302E !important;
    }

    /* ---------- Cartões (expanders) ---------- */
    div[data-testid="stExpander"] {
        background-color: #FFFDF8;
        border: 1px solid #EADFD2;
        border-radius: 18px;
        margin-bottom: 0.6rem;
        box-shadow: 0 1px 3px rgba(66, 48, 46, 0.06);
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600;
        color: #42302E;
    }

    /* ---------- Avisos ---------- */
    div[data-testid="stAlert"] {
        border-radius: 16px;
        border: none;
    }

    /* ---------- Legendas ----------
       Escurecidas em relação ao padrão do Streamlit: o cinza claro fica
       quase invisível numa projeção, e essas legendas carregam informação
       que a banca precisa conseguir ler. */
    .stCaption, div[data-testid="stCaptionContainer"] p {
        color: #6B5652 !important;
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
        color: #4A4742 !important;
    }
    /* Rótulo em cima de cada campo ("Tipo de ocorrência", "Número"...):
       MAIÚSCULAS, letras espaçadas e fonte mono, como o "SEU APELIDO" da
       página do Rafa. O seletor mira só o rótulo do campo
       (stWidgetLabel), não as opções de listas e botões de rádio — essas
       continuam em texto normal, que é mais fácil de ler. Sem "div" na
       frente de propósito: na versão 1.64 do Streamlit o stWidgetLabel é o
       próprio <label>; em versões antigas era uma <div>. */
    [data-testid="stWidgetLabel"] p {
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.82rem !important;
        color: #4A4742 !important;
    }
</style>
"""


def aplicar_tema() -> None:
    """Injeta o CSS do tema. Chamar uma vez, logo após st.set_page_config(...)."""
    st.markdown(_CSS, unsafe_allow_html=True)
