#!/bin/bash
# ---------------------------------------------------------------
# iniciar_demo.command — DePIN Urbano, Fase 3
#
# Dê DOIS CLIQUES neste arquivo (no Finder) para subir o formulário
# e o dashboard de uma vez, sem precisar digitar nada no terminal.
#
# Ele descobre sozinho o endereço da rede em que o notebook está
# (Wi-Fi de casa, da FIAP ou hotspot do iPhone) e mostra na tela o
# link que deve ser aberto no celular.
#
# Para encerrar: feche esta janela ou aperte Control+C.
# ---------------------------------------------------------------

cd "$(dirname "$0")" || exit 1

# Descobre o IP local, testando as interfaces de rede mais comuns do Mac.
IP=""
for iface in en0 en1 en2 en3; do
    CANDIDATO=$(ipconfig getifaddr "$iface" 2>/dev/null)
    if [ -n "$CANDIDATO" ]; then
        IP="$CANDIDATO"
        break
    fi
done

echo ""
echo "=================================================================="
echo "                    DePIN URBANO  -  DEMO"
echo "=================================================================="
echo ""
if [ -n "$IP" ]; then
    echo "   >>> NO CELULAR, ABRA ESTE ENDERECO:"
    echo ""
    echo "          http://$IP:8501"
    echo ""
else
    echo "   !!! Nao foi possivel descobrir o IP da rede."
    echo "       Conecte o notebook ao Wi-Fi (ou ao hotspot do iPhone)"
    echo "       e rode este arquivo de novo."
    echo ""
fi
echo "   Neste notebook:  http://localhost:8501"
echo ""
echo "   O app tem DUAS PAGINAS. Use o menu na lateral esquerda para"
echo "   alternar entre o formulario do cidadao e o Dashboard da Prefeitura."
echo ""
echo "   Lembretes da demo:"
echo "       - O celular precisa estar na MESMA rede do notebook."
echo "       - Carteira do cidadao (colar no formulario):"
echo "         0xF208C8d2a3c6375257B5cC7A719d89E6E7aeB7d4"
echo ""
echo "   Para encerrar tudo: feche esta janela ou Control+C"
echo "=================================================================="
echo ""

# Um comando só: o Streamlit descobre sozinho a segunda página em pages/.
streamlit run app.py --server.port 8501
