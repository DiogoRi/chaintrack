"""
Status do Worker — DePIN Urbano, Fase 5

Pedido do Rafa em 23/09, depois de a gente conversar sobre o risco de o
worker cair durante o evento sem ninguém perceber: uma tela simples,
aberta de qualquer navegador (inclusive do celular, sem precisar estar na
mesma rede do notebook), que responde "o worker está de pé, e há quanto
tempo foi a última volta dele?".

Não substitui o `iniciar_worker.command` (que reinicia o processo sozinho
se ele cair por exceção/RPC fora do ar/rede) nem o `caffeinate` (que evita
o Mac dormir) — os três trabalham juntos: um evita a queda, o outro
recupera dela, e esta tela é só o "olho" pra alguém saber se precisa agir.

Não expõe nenhum dado sensível: só o horário da última volta do worker,
lido da tabela worker_lease pela mesma chave secreta que o resto do app já
usa (nada de nova função pública no Supabase, nada que o Rafa consome).
"""

import sys
from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ocorrencias import obter_status_worker    # noqa: E402
from tema_visual import aplicar_tema           # noqa: E402

st.set_page_config(
    page_title="Status do Worker — DePIN Urbano",
    page_icon="💓",
    initial_sidebar_state="expanded",
)
aplicar_tema()

st.markdown("<p class='titulo-sobre'>💓 Status do Worker</p>",
            unsafe_allow_html=True)
st.markdown(
    "<p class='subtitulo-sobre'>Sinal de vida do processo que grava as "
    "ocorrências na blockchain</p>",
    unsafe_allow_html=True,
)

# Atualiza sozinha a cada 10s — pra quem deixar essa aba aberta no celular
# durante o evento não precisar ficar puxando pra atualizar na mão.
st_autorefresh(interval=10_000, key="auto_refresh_status_worker")

status = obter_status_worker()

if not status["ok"]:
    st.error(f"⚠️ Não foi possível checar o worker: {status['erro']}")
    st.caption(
        "Isso pode ser o Supabase fora do ar (o que também afetaria o "
        "resto do app), não necessariamente o worker parado."
    )
else:
    segundos = status["segundos_desde_ultima_volta"]

    # As faixas abaixo espelham as constantes reais do worker_blockchain.py:
    # INTERVALO_LOOP_SEG = 5 (a cada quantos segundos ele tenta de novo, em
    # operação normal) e DURACAO_LEASE_SEG = 180 (a janela de concessão do
    # lease — escolhida de propósito bem acima do timeout de confirmação de
    # uma transação, 120s, pra uma espera real não parecer uma queda).
    if segundos <= 30:
        st.success(f"🟢 **Worker ativo.** Última volta há {segundos:.0f} segundos.")
    elif segundos <= 180:
        st.warning(
            f"🟡 **Sem novidade há {segundos / 60:.1f} minutos.** Ainda dentro do "
            "esperado — pode ser só uma transação demorando a confirmar na Amoy."
        )
    else:
        st.error(
            f"🔴 **Parado há {segundos / 60:.1f} minutos.** Isso já passa da "
            "janela normal — vale checar o terminal do worker."
        )

    st.caption(f"Dono do lease: `{status['owner']}`")
    st.caption(
        f"Última volta (horário do banco): "
        f"{status['visto_em'].strftime('%d/%m/%Y às %H:%M:%S')}"
    )

st.markdown("---")
st.caption(
    "Esta página só lê um horário — não mostra nem altera nenhuma "
    "ocorrência. Pra agir sobre uma queda, é preciso estar no notebook "
    "onde o worker roda."
)
