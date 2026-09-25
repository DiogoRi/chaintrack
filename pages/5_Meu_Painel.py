"""
Meu Painel — DePIN Urbano, Bloco 9 (vitrine)

Área pessoal do cidadão do fluxo normal (fora da gincana) — decidida em
10/09, com o mecanismo de identidade fechado em 23/09. Mostra as ocorrências
que a pessoa registrou, quanto CP (Cidadão Participativo) ela já acumulou, e
o que dá pra fazer com esse CP: trocar por diária de Zona Azul, abater no
IPTU, ou sacar via Pix.

Nenhum desses três resgates acontece de verdade, e não tem como acontecer
até o Talent Summit: Zona Azul e IPTU dependem de a prefeitura existir do
outro lado, e Pix é dinheiro real — sair de protótipo pra isso entra em
regulação de meio de pagamento (ver "Custódia do token CP", 05/09). Por
isso esta tela é uma VITRINE: mostra as opções, marcadas como simulação,
pra quem passar no estande entender por que o token existe. Sem isso, CP é
só um número; com isso, vira moeda de participação cívica.

Identidade: reaproveita exatamente o mesmo mecanismo de três camadas já
usado no app.py (sessão → localStorage → código de recuperação manual) —
mesma chave de localStorage, para que quem já registrou uma ocorrência no
app principal seja reconhecido aqui automaticamente, sem fazer nada.

Dados: reaproveita a função `painel(p_id)` que já existe no Supabase desde
18/09 e que o React do Rafa já usa e já testou — não criamos nenhuma função
nova no banco, então isso não muda nada do que o Rafa consome.
"""

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ocorrencias import (                              # noqa: E402
    STATUS_LABELS,
    obter_painel_cidadao,
    recuperar_participante_por_codigo,
)
from tema_visual import aplicar_tema                   # noqa: E402
from streamlit_js_eval import streamlit_js_eval        # noqa: E402

st.set_page_config(
    page_title="Meu Painel — DePIN Urbano",
    page_icon="🎁",
    initial_sidebar_state="expanded",
)
aplicar_tema()

st.markdown("<p class='titulo-sobre'>🎁 Meu Painel</p>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitulo-sobre'>Suas ocorrências e os CP que você já "
    "acumulou</p>",
    unsafe_allow_html=True,
)

# ===========================================================================
# Identidade — MESMO mecanismo de três camadas do app.py (Bloco 9).
# As duas constantes abaixo precisam ser exatamente iguais às de app.py:
# são a chave e o valor-sentinela do localStorage do MESMO navegador, e só
# funcionam se as duas páginas concordarem sobre eles.
CHAVE_LOCALSTORAGE_PARTICIPANTE = "depin_participante_id"
_SEM_ID_SALVO = "__sem_id__"

participante_id = st.query_params.get("p")

if not participante_id and "participante_id_ativo" in st.session_state:
    participante_id = st.session_state["participante_id_ativo"]

if not participante_id:
    if "id_local_verificado" not in st.session_state:
        st.session_state["id_local_verificado"] = False

    if not st.session_state["id_local_verificado"]:
        resultado_local = streamlit_js_eval(
            js_expressions=(
                f"localStorage.getItem('{CHAVE_LOCALSTORAGE_PARTICIPANTE}') "
                f"|| '{_SEM_ID_SALVO}'"
            ),
            key="ler_participante_id_local",
        )
        if resultado_local is not None:
            st.session_state["id_local_verificado"] = True
            if resultado_local != _SEM_ID_SALVO:
                participante_id = resultado_local
                st.session_state["participante_id_ativo"] = participante_id

if not participante_id:
    # Ajuste pedido pelo Diogo (25/09): esta recuperação morava também no
    # app.py, escondida num expander bem em cima do formulário de registro —
    # ficava com cara de "opção do registro", quando na verdade é sobre outra
    # coisa (entrar numa conta já existente). Agora mora só aqui, com uma
    # pergunta direta em vez de um texto genérico escondido.
    st.markdown("### Você já tem uma conta no DePIN Urbano?")
    st.markdown(
        "Se você já registrou uma ocorrência antes — neste ou em outro "
        "aparelho — digite o código de recuperação que você recebeu no "
        "comprovante, na hora do registro, para acessar seu painel de novo."
    )
    codigo_digitado = st.text_input(
        "Código de recuperação",
        placeholder="Ex.: RDRMH65X",
        key="codigo_recuperacao_input_painel",
    )
    if st.button("Acessar meu painel", key="botao_recuperar_participante_painel"):
        participante_recuperado = recuperar_participante_por_codigo(
            codigo_digitado)
        if participante_recuperado:
            participante_id = participante_recuperado["id"]
            st.session_state["participante_id_ativo"] = participante_id
            streamlit_js_eval(
                js_expressions=(
                    f"localStorage.setItem("
                    f"'{CHAVE_LOCALSTORAGE_PARTICIPANTE}', "
                    f"'{participante_id}')"
                ),
                key="salvar_participante_id_recuperado_painel",
            )
            st.success("Painel recuperado!")
            st.rerun()
        else:
            st.error("Código não encontrado. Confira e tente de novo.")

    st.markdown("---")
    st.markdown("**Ainda não registrou nenhuma ocorrência?**")
    st.page_link("app.py", label="📝 Registrar uma ocorrência", icon="📝")
    st.stop()

# ===========================================================================
# Dados do painel
painel = obter_painel_cidadao(participante_id)

if not painel["ok"]:
    st.error(f"⚠️ Não foi possível carregar seu painel agora: {painel['erro']}")
    st.caption("Tente atualizar a página em alguns instantes.")
    st.stop()

ocorrencias = painel["ocorrencias"]
cp_real = painel["cp"]

st.markdown("---")

colunas = st.columns(3) if painel["pontos_gincana"] else st.columns(2)
colunas[0].metric("💎 CP acumulado", cp_real)
colunas[1].metric("📋 Ocorrências registradas", len(ocorrencias))
if painel["pontos_gincana"]:
    colunas[2].metric("🏆 Pontos de gincana", painel["pontos_gincana"])

with st.expander("🔑 Meu código de recuperação"):
    st.markdown(f"`{painel['codigo_recup']}`")
    st.caption(
        "Guarde-o. É com ele que você recupera este painel caso troque de "
        "celular ou computador, ou limpe os dados do navegador."
    )

# ===========================================================================
# Minhas ocorrências
st.markdown("### Minhas ocorrências")

if not ocorrencias:
    st.info(
        "Você ainda não tem ocorrências registradas. Assim que registrar a "
        "primeira, ela aparece aqui."
    )
else:
    for o in ocorrencias:
        rotulo_status = STATUS_LABELS.get(o["status"], o["status"])
        with st.expander(f"{rotulo_status} — {o['tipo']} · {o['criado_em']}"):
            st.markdown(f"**Situação:** {rotulo_status}")
            st.markdown(f"**Tipo:** {o['tipo']}")
            st.markdown(f"**Registrada em:** {o['criado_em']}")
            if o["cp_ganho"]:
                st.markdown(f"**CP creditado:** {o['cp_ganho']}")
            if o["tx_hash"]:
                st.markdown(
                    f"[Ver a prova pública na blockchain]"
                    f"(https://amoy.polygonscan.com/tx/{o['tx_hash']})"
                )
            else:
                st.caption(
                    "Ainda sem transação confirmada na blockchain — isso "
                    "acontece pouco depois do registro, automaticamente."
                )

st.markdown("---")

# ===========================================================================
# Vitrine de resgate — SIMULAÇÃO, nada aqui debita nada de verdade.
#
# Valores abaixo são ilustrativos (não fechados com a prefeitura nem com
# nenhum parceiro de pagamento) — servem só para o estande mostrar "para
# que serve o CP". Fáceis de ajustar depois, é só mudar os números aqui.
st.markdown("### O que dá pra fazer com o CP")
st.caption(
    "🎭 **Simulação** — nada abaixo é uma transação real. Zona Azul e IPTU "
    "dependem de integração com a prefeitura; Pix é dinheiro de verdade e "
    "sair de protótipo para isso entra em regulação de meio de pagamento. "
    "Esta vitrine existe para mostrar o que o CP pode virar quando o "
    "projeto crescer."
)

RESGATES = [
    {"chave": "zona_azul", "emoji": "🅿️", "nome": "1 diária de Zona Azul",
     "custo": 5},
    {"chave": "iptu", "emoji": "🏠", "nome": "R$ 5 de abatimento no IPTU",
     "custo": 10},
    {"chave": "pix", "emoji": "💸", "nome": "R$ 5 via Pix",
     "custo": 5},
]

# Saldo simulado: começa igual ao CP real e só existe durante esta visita
# (não grava nada no banco). Assim dá pra "testar" o resgate no estande sem
# afetar o saldo de verdade de ninguém, e sem precisar desenhar uma tabela
# nova só para isso.
chave_saldo_sim = f"cp_simulado_{participante_id}"
if chave_saldo_sim not in st.session_state:
    st.session_state[chave_saldo_sim] = cp_real
saldo_sim = st.session_state[chave_saldo_sim]

if saldo_sim != cp_real:
    st.caption(
        f"Saldo simulado nesta visita: **{saldo_sim} CP** "
        f"(o saldo real continua {cp_real} CP — nada foi debitado de "
        "verdade)."
    )

colunas_resgate = st.columns(len(RESGATES))
for coluna, resgate in zip(colunas_resgate, RESGATES):
    with coluna:
        st.markdown(f"#### {resgate['emoji']} {resgate['nome']}")
        st.caption(f"Custo: {resgate['custo']} CP")
        clicado = st.button(
            "Resgatar (simulação)",
            key=f"resgatar_{resgate['chave']}",
            disabled=saldo_sim < resgate["custo"],
        )
        if clicado:
            st.session_state[chave_saldo_sim] = saldo_sim - resgate["custo"]
            st.success(
                f"🎭 Simulação: {resgate['nome']} resgatado! Em um produto "
                "real, isso creditaria o benefício na sua conta. Aqui, é só "
                "para mostrar como funcionaria."
            )
            st.rerun()
        if saldo_sim < resgate["custo"]:
            st.caption("CP insuficiente para este resgate ainda.")

st.markdown("---")
st.caption(
    "O CP é creditado automaticamente quando uma ocorrência sua é concluída "
    "e a transação correspondente é confirmada na blockchain — sem precisar "
    "de carteira nem cadastro. Cada transação é pública e permanente: "
    "ninguém, nem a prefeitura, nem quem desenvolveu o sistema, pode apagá-la."
)
