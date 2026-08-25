"""
Acompanhar ocorrência — DePIN Urbano, Fase 3

A tela do cidadão depois que ele registrou. Ele digita o número de protocolo
que recebeu no comprovante e vê em que pé está o atendimento.

Por que isso importa no projeto: sem esta página, a promessa de transparência
fica só na blockchain, que é um lugar que o cidadão comum não sabe consultar.
Aqui ele vê o mesmo dado, em português, com o link da prova pública ao lado
para quem quiser conferir na fonte.

O acesso é só pelo protocolo, sem login, seguindo o modelo do SP156 para
solicitações não identificadas. Nenhum dado pessoal é exigido para consultar.
"""

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ocorrencias import (                     # noqa: E402
    STATUS_LABELS,
    adicionar_mensagem,
    buscar_por_protocolo,
    carregar_registros,
    data_curta,
    formatar_data,
    info_prazo,
    protocolo_de,
    salvar_registros,
    texto_prazo,
)
from tema_visual import aplicar_tema          # noqa: E402

st.set_page_config(
    page_title="Acompanhar ocorrência — DePIN Urbano",
    page_icon="🔎",
    initial_sidebar_state="expanded",
)
aplicar_tema()

st.markdown("<p class='titulo-sobre'>🔎 Acompanhar ocorrência</p>",
            unsafe_allow_html=True)
st.markdown("<p class='subtitulo-sobre'>Consulte pelo número de protocolo</p>",
            unsafe_allow_html=True)

st.markdown(
    "Digite abaixo o número de protocolo que aparece no comprovante que você "
    "recebeu ao registrar. Não é preciso fazer login nem informar seus dados."
)

protocolo_digitado = st.text_input(
    "Número de protocolo",
    placeholder="Exemplo: A1B2C3D4",
    key="consulta_protocolo",
)

registros = carregar_registros()
encontrada = buscar_por_protocolo(registros, protocolo_digitado)

if protocolo_digitado and not encontrada:
    st.error("Não encontramos nenhuma ocorrência com esse protocolo.")
    st.caption(
        "Confira se digitou exatamente como está no comprovante. Se você "
        "registrou há poucos segundos, aguarde um instante e consulte de novo."
    )

if not protocolo_digitado:
    st.info(
        "O número de protocolo fica no alto do comprovante, logo depois de "
        "**Protocolo:**. Ele também aparece na tela de confirmação, assim que "
        "o registro é enviado."
    )

if encontrada:
    r = encontrada
    status = r.get("status", "recebida")
    dados_prazo = info_prazo(r)

    st.markdown("---")

    # ---- Faixa de status ----
    # A informação que a pessoa veio buscar aparece primeiro e sozinha, sem
    # competir com o resto. Só depois vêm os detalhes do registro.
    st.markdown(f"### {STATUS_LABELS.get(status, status)}")

    frase = texto_prazo(r)
    if status == "concluida":
        st.success(frase)
    elif dados_prazo["atrasada"]:
        st.error(frase)
    elif status == "em_andamento":
        st.info(frase)
    else:
        st.info(frase)

    if status == "em_andamento" and r.get("setor") and r["setor"] != "Não atribuído":
        st.markdown(f"**Equipe responsável:** {r['setor']}")

    # ---- Linha do tempo ----
    st.markdown("### Andamento")

    etapas = [
        ("Ocorrência registrada", data_curta(r), True),
        ("Encaminhada à equipe responsável",
         data_curta({"data": r.get("data_andamento")})
         if r.get("data_andamento") else "aguardando",
         bool(r.get("data_andamento"))),
        ("Atendimento concluído",
         data_curta({"data": r.get("data_conclusao")})
         if r.get("data_conclusao") else "aguardando",
         bool(r.get("data_conclusao"))),
    ]

    for titulo, quando, cumprida in etapas:
        marca = "✅" if cumprida else "⬜"
        if cumprida:
            st.markdown(f"{marca} **{titulo}** — {quando}")
        else:
            st.markdown(f"{marca} {titulo} — _{quando}_")

    if status == "em_andamento" and dados_prazo["tem_prazo"]:
        st.caption(
            f"Previsão de conclusão: **{formatar_data(dados_prazo['previsao'])}**. "
            "O prazo é contado em dias úteis a partir do encaminhamento à equipe."
        )

    # ---- Dados do registro ----
    st.markdown("### Dados da ocorrência")

    st.markdown(f"**Protocolo:** `{protocolo_de(r)}`")
    st.markdown(f"**Registrada em:** {data_curta(r)}")
    st.markdown(f"**Endereço:** {r.get('endereco', 'Não informado')}")
    st.markdown(f"**Descrição:** {r.get('descricao', 'Não informada')}")

    if r.get("cid"):
        link_foto = f"https://gateway.pinata.cloud/ipfs/{r['cid']}"
        st.image(link_foto, width=320)
        st.caption(f"[Abrir a foto em tamanho original]({link_foto})")

    # ---- Prova pública ----
    if r.get("tx_registro"):
        st.markdown("### Prova pública")
        st.markdown(
            f"[Ver este registro na blockchain]"
            f"(https://amoy.polygonscan.com/tx/{r['tx_registro']})"
        )
        st.caption(
            "Este registro está gravado numa blockchain pública. Ninguém pode "
            "apagá-lo ou alterar a data em que ele foi feito, nem a prefeitura, "
            "nem quem desenvolveu o sistema."
        )

    if r.get("token_tx"):
        st.markdown(
            f"[Ver a conclusão e o envio do token]"
            f"(https://amoy.polygonscan.com/tx/{r['token_tx']})"
        )
        st.caption(
            "A conclusão do atendimento e o envio do token CP saíram na mesma "
            "operação: uma não existe sem a outra."
        )

    # ---- Recompensa ----
    if status == "concluida" and r.get("wallet"):
        st.success(
            "🎉 Você recebeu **1 CP (Cidadão Participativo)** por esta "
            "contribuição. O token foi enviado para a carteira informada no "
            "registro."
        )
    elif status == "concluida" and not r.get("wallet"):
        st.info(
            "Esta ocorrência foi registrada sem carteira, então não houve "
            "envio de token. Nos próximos registros, informe uma carteira "
            "para receber o CP quando o problema for resolvido."
        )

    # ---- Mensagens ----
    st.markdown("### Mensagens")

    mensagens = r.get("mensagens", [])
    if mensagens:
        for m in mensagens:
            quem = ("Você" if m.get("autor") == "cidadao"
                    else "Equipe do município")
            quando = data_curta({"data": m.get("data", "")})
            st.markdown(f"**{quem}** · {quando}")
            st.markdown(f"> {m.get('texto', '')}")
            st.markdown("")
    else:
        st.caption("Nenhuma mensagem nesta ocorrência ainda.")

    with st.form("nova_mensagem", clear_on_submit=True):
        texto = st.text_area(
            "Quer acrescentar alguma informação?",
            placeholder="Exemplo: o buraco aumentou desde que registrei, "
                        "e agora ocupa metade da pista.",
            height=110,
        )
        enviada = st.form_submit_button("Enviar mensagem")

    if enviada:
        if texto.strip():
            adicionar_mensagem(r, texto, autor="cidadao")
            salvar_registros(registros)
            st.success(
                "Mensagem enviada. Ela aparece para a equipe responsável junto "
                "com a sua ocorrência."
            )
            st.rerun()
        else:
            st.warning("Escreva a mensagem antes de enviar.")

st.markdown("---")
st.caption(
    "Esta consulta mostra o andamento informado pelo município. O registro "
    "original, com data e hora, está gravado numa blockchain pública e pode "
    "ser conferido por qualquer pessoa, a qualquer momento."
)
