#!/bin/bash
# ---------------------------------------------------------------
# iniciar_antena.command — DePIN Urbano, Fase 3
#
# Dê DOIS CLIQUES neste arquivo para ligar o "vigia da antena".
#
# Ele fica observando a blockchain e acende os LEDs da maquete
# quando uma ocorrência é registrada ou concluída — não importa de
# qual celular ou de qual rede o registro tenha vindo.
#
# Use junto com o app publicado: https://chaintrack.streamlit.app
#
# Antes de rodar: plugue a ESP32 no notebook pelo cabo USB.
# Para encerrar: feche esta janela ou aperte Control+C.
# ---------------------------------------------------------------

cd "$(dirname "$0")" || exit 1

python3 vigia_antena.py

# Mantém a janela aberta se algo der errado, para dar tempo de ler o erro.
echo ""
echo "(Pressione Enter para fechar esta janela)"
read -r
