#!/bin/bash
# ---------------------------------------------------------------
# iniciar_worker.command — DePIN Urbano, Fase 5
#
# Dê DOIS CLIQUES neste arquivo para ligar o worker da blockchain
# (worker_blockchain.py) com auto-reinício.
#
# Ideia sugerida pelo Rafa em 23/09: o reprocessamento sem duplicar
# transação já existe (o worker retoma sozinho qualquer ocorrência
# pendente ao subir de novo — ver _retomar_pendentes). O que faltava
# era detectar e reagir a uma queda do PROCESSO em si — por exceção
# não tratada, RPC da Amoy fora do ar, falta de gás ou rede do local
# oscilando. Nenhum desses é "o Mac dormiu", então o caffeinate
# sozinho não cobre.
#
# Este script resolve isso com um laço simples: se o worker cair por
# qualquer um desses motivos, ele sobe de novo sozinho em 5 segundos,
# sem precisar de ninguém notando e reabrindo o terminal na mão.
#
# NÃO substitui o caffeinate — o Mac ainda pode dormir, e aí nem este
# laço roda. Continua valendo rodar:
#   caffeinate -s ./iniciar_worker.command
# (ou ajustar as configurações de energia pra nunca dormir) no dia do
# evento, exatamente como já estava no checklist da manhã do dia 30.
#
# Para encerrar de vez: feche esta janela ou aperte Control+C duas
# vezes rápido (uma só reinicia o worker, já que o laço captura o
# encerramento do processo — Control+C duas vezes encerra o script).
# ---------------------------------------------------------------

cd "$(dirname "$0")" || exit 1

echo ""
echo "=================================================================="
echo "         DePIN URBANO — WORKER COM AUTO-REINÍCIO"
echo "=================================================================="
echo ""
echo "   Se o processo cair por qualquer motivo, ele volta sozinho"
echo "   em 5 segundos. Pra ver se está tudo certo à distância, use"
echo "   a página 'Status do Worker' em https://chaintrack.streamlit.app"
echo ""
echo "   Para encerrar de vez: Control+C (pode precisar apertar duas"
echo "   vezes, uma pra matar o worker e outra pra sair do laço)."
echo "=================================================================="
echo ""

while true; do
    python3 worker_blockchain.py
    echo ""
    echo "⚠️  Worker encerrado (código $?). Reiniciando em 5 segundos..."
    echo "    (Control+C agora encerra de vez, em vez de reiniciar.)"
    sleep 5
done
