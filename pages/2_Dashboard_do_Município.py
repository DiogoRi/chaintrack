"""
Dashboard do Município — DePIN Urbano, Fase 3

A tela de quem atende as ocorrências. Mostra o mapa, a lista por situação, e
os controles de status, prazo, equipe responsável e mensagens.

Por que esta tela e a do cidadão vivem no mesmo app: elas compartilham o
arquivo registros.json e o módulo ocorrencias.py. Se estivessem separadas,
cada uma teria a sua própria cópia dos dados e o cidadão poderia ver um
andamento diferente do que o município registrou.
"""

import sys
from pathlib import Path

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# A pasta raiz do projeto é a "avó" deste arquivo (pages/ -> raiz).
# Isso garante que os arquivos sejam encontrados independentemente de onde
# o Streamlit for iniciado, tanto no notebook quanto na nuvem.
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mint_token import concluir_ocorrencia    # noqa: E402
from ocorrencias import (                      # noqa: E402
    LABEL_PARA_STATUS,
    PRAZO_PADRAO_DIAS,
    SETORES,
    STATUS_CORES_MAPA,
    STATUS_LABELS,
    adicionar_mensagem,
    aplicar_status,
    carregar_registros,
    data_curta,
    formatar_data,
    info_prazo,
    ordenar_por_data,
    protocolo_de,
    salvar_registros,
    texto_prazo,
)
from tema_visual import aplicar_tema           # noqa: E402

st.set_page_config(
    page_title="Dashboard do Município — DePIN Urbano",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_tema()


# ---------------------------------------------------------------------------
# Acesso ao painel
# ---------------------------------------------------------------------------
# Este painel é a visão de quem atende as ocorrências: muda status, conclui e
# dispara o envio de tokens. Publicado na internet, ficaria aberto a qualquer
# um. A proteção é opcional de propósito: se a senha não estiver configurada,
# o painel abre normalmente (útil na demonstração e no notebook). Basta criar
# SENHA_DASHBOARD nos Secrets do Streamlit para que ela passe a ser exigida.
def _senha_configurada():
    try:
        return str(st.secrets.get("SENHA_DASHBOARD", "")).strip()
    except Exception:
        return ""


def exigir_acesso():
    senha = _senha_configurada()
    if not senha:
        return
    if st.session_state.get("dashboard_liberado"):
        return

    st.markdown("<p class='titulo-dashboard'>Dashboard do Município</p>",
                unsafe_allow_html=True)
    st.info("Esta área é restrita à equipe que atende as ocorrências.")
    digitada = st.text_input("Senha de acesso", type="password")
    if digitada:
        if digitada == senha:
            st.session_state["dashboard_liberado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()


exigir_acesso()

INTERVALO_MS = 2000

registros = carregar_registros()

# ===========================================================================
# Conclusão on-chain: por que existe esta etapa separada
#
# A transação de conclusão leva de 5 a 30 segundos. O auto-refresh de 2s
# reiniciaria o script no meio do envio e o resultado nunca apareceria na
# tela. Por isso o fluxo é dividido em dois momentos:
#
#   1. O botão "Atualizar" apenas ANOTA que aquela ocorrência precisa ser
#      concluída on-chain (em st.session_state) e recarrega a página.
#   2. Nesse novo carregamento, o auto-refresh NÃO é montado, então nada
#      interrompe a transação. Ela roda com calma e o resultado é guardado
#      para ser exibido no carregamento seguinte.
# ===========================================================================
pendente = st.session_state.get("conclusao_pendente")

if not pendente:
    st_autorefresh(interval=INTERVALO_MS, key="auto_refresh_dashboard")

st.markdown(
    "<p class='titulo-dashboard'>🗺️ Dashboard do Município</p>",
    unsafe_allow_html=True)

if pendente:
    alvo = next((r for r in registros if r.get("id") == pendente), None)

    if alvo is None:
        st.session_state.pop("conclusao_pendente", None)
        st.rerun()

    st.info(
        "⏳ Registrando a conclusão na blockchain e enviando o token CP. "
        "Isso leva de 5 a 30 segundos — **não feche nem atualize a página.**"
    )
    with st.spinner("Enviando transação para a Polygon Amoy..."):
        try:
            tx = concluir_ocorrencia(alvo["cid"], alvo["wallet"])
            alvo["token_tx"] = tx
            salvar_registros(registros)
            st.session_state["conclusao_resultado"] = ("ok", tx)
        except Exception as e:
            st.session_state["conclusao_resultado"] = ("erro", str(e))

    # A antena NÃO é acionada daqui. Quem a aciona é o vigia_antena.py, que
    # observa os contratos na blockchain de forma independente. Se o dashboard
    # também sinalizasse, o LED piscaria duas vezes e, pior, a antena passaria
    # a confiar no aplicativo em vez de confiar no registro público, que é
    # exatamente o contrário da tese do projeto.

    st.session_state.pop("conclusao_pendente", None)
    st.rerun()

resultado = st.session_state.pop("conclusao_resultado", None)
if resultado:
    tipo, valor = resultado
    if tipo == "ok":
        st.success("✅ Conclusão registrada na blockchain e token CP enviado!")
        st.markdown(
            f"🔗 [Ver a transação no Polygonscan](https://amoy.polygonscan.com/tx/{valor})"
        )
    elif tipo == "sem_carteira":
        st.warning(
            "Ocorrência marcada como concluída, mas sem carteira informada — "
            "nenhuma transação de conclusão foi enviada."
        )
    else:
        st.error(
            f"⚠️ Falha ao registrar a conclusão on-chain: {valor}\n\n"
            "O status foi salvo como concluída mesmo assim. Selecione "
            "**Concluída** e clique em **Atualizar** de novo para tentar outra vez."
        )

st.markdown(
    "<p class='subtitulo-dashboard'>Ocorrências registradas</p>",
    unsafe_allow_html=True)

if registros:
    ativas_totais = [r for r in registros if not r.get("arquivada")]
    atrasadas = [r for r in ativas_totais if info_prazo(r)["atrasada"]]

    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.write(f"**{len(registros)} ocorrência(s) registrada(s)**")
    with col_b:
        if atrasadas:
            st.error(f"⏰ {len(atrasadas)} com prazo vencido")

    lats = [r["latitude"] for r in registros]
    lons = [r["longitude"] for r in registros]
    centro = [sum(lats) / len(lats), sum(lons) / len(lons)]

    mapa = folium.Map(location=centro, zoom_start=12)

    if len(registros) > 1:
        mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    for r in registros:
        status = r.get("status", "recebida")
        popup_html = f"""
        <b>{r.get('descricao', 'Sem descrição')}</b><br>
        Protocolo: {protocolo_de(r)}<br>
        Status: {STATUS_LABELS.get(status, status)}<br>
        Endereço: {r.get('endereco', 'N/A')}<br>
        Data: {r.get('data', 'N/A')}<br>
        CID: <a href='https://gateway.pinata.cloud/ipfs/{r.get("cid", "")}' target='_blank'>{r.get('cid', 'N/A')[:20]}...</a>
        """
        folium.Marker(
            location=[r["latitude"], r["longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(
                color=STATUS_CORES_MAPA.get(status, "gray"),
                icon="exclamation-sign"
            )
        ).add_to(mapa)

    st_folium(mapa, width=900, height=500, key="mapa_depin")

    st.markdown("### Ocorrências e status")
    # Texto normal em vez de legenda: esta instrução é operacional (explica o
    # que acontece ao concluir) e precisa ser lida sem esforço na projeção.
    st.markdown(
        "Atualize o status manualmente conforme o andamento. Ao passar para "
        "**Em andamento**, começa a contar o prazo de execução e o cidadão "
        "passa a ver a data prevista na consulta por protocolo. Ao marcar como "
        "**Concluída**, se a ocorrência tiver uma carteira informada, sai uma "
        "transação na blockchain que registra a conclusão e envia o token "
        "CP (Cidadão Participativo), tudo de uma vez."
    )

    def mostrar_ocorrencia(r):
        """Desenha o cartão de uma ocorrência, com os detalhes e os controles
        de atendimento. Usado pelos quatro grupos."""
        status_atual = r.get("status", "recebida")
        dados_prazo = info_prazo(r)

        # Protocolo e data vêm primeiro: identificam a ocorrência sem
        # ambiguidade. A descrição entra encurtada, só como pista — assim
        # todas as linhas ficam com a mesma altura, em vez de umas com uma
        # linha e outras com quatro.
        desc = r.get("descricao", "Sem descrição")
        if len(desc) > 40:
            desc = desc[:40].rstrip() + "…"

        # O aviso de atraso entra no título, não dentro do cartão: quem abre
        # o painel precisa ver o que está vencido sem ter que expandir tudo.
        alerta = "⏰ " if dados_prazo["atrasada"] else ""
        nao_lidas = sum(1 for m in r.get("mensagens", [])
                        if m.get("autor") == "cidadao")
        aviso_msg = f"  💬 {nao_lidas}" if nao_lidas else ""

        titulo = (f"{alerta}{STATUS_LABELS.get(status_atual, status_atual)}  "
                  f"{protocolo_de(r)}  ·  {data_curta(r)}  ·  {desc}{aviso_msg}")

        with st.expander(titulo):
            # ---- Prazo ----
            # publico=False: aqui quem lê é a equipe que atende, não o
            # cidadão. A frase explicativa sobre o que vai acontecer com a
            # ocorrência não faz sentido para quem é o responsável por
            # fazer isso acontecer.
            frase = texto_prazo(r, publico=False)
            if status_atual == "concluida":
                st.success(frase)
            elif dados_prazo["atrasada"]:
                st.error(frase)
            else:
                st.info(frase)

            st.write(f"**Protocolo:** `{protocolo_de(r)}`")
            st.write(f"**Nome:** {r.get('nome', 'N/A')}")
            if r.get("email"):
                st.write(f"**E-mail:** {r['email']}")
            st.write(f"**Endereço:** {r.get('endereco', 'N/A')}")
            st.write(f"**Descrição:** {r.get('descricao', 'N/A')}")
            st.write(f"**Data:** {r.get('data', 'N/A')}")
            st.write(f"**Carteira:** {r.get('wallet') or '_não informada_'}")
            st.write(f"**Equipe responsável:** {r.get('setor', 'Não atribuído')}")

            if r.get("cid"):
                link_foto = f"https://gateway.pinata.cloud/ipfs/{r['cid']}"
                st.image(link_foto, width=300)
                # O link fica sempre disponível: o gateway do IPFS às vezes
                # demora ou não responde, e nesse caso a imagem acima não
                # carrega. Com o link, a foto continua acessível.
                st.caption(
                    f"🔐 Impressão digital da foto: `{r['cid']}` — "
                    f"[abrir a imagem]({link_foto})")

            # Prova pública do registro. Se ela não existe, o dashboard diz
            # isso com todas as letras: uma ocorrência que ficou só no arquivo
            # local não tem o valor central que o projeto promete.
            if r.get("tx_registro"):
                st.markdown(
                    f"**Comprovante do registro:** "
                    f"[abrir no Polygonscan]"
                    f"(https://amoy.polygonscan.com/tx/{r['tx_registro']})"
                )
            elif not str(r.get("id", "")).startswith("legacy-"):
                st.warning(
                    "Esta ocorrência não tem prova on-chain: a gravação na "
                    "blockchain falhou no momento do envio. O registro existe "
                    "aqui, mas não é auditável publicamente."
                )

            if r.get("token_tx"):
                st.markdown(
                    f"**Comprovante de conclusão e recompensa:** "
                    f"[abrir no Polygonscan](https://amoy.polygonscan.com/tx/{r['token_tx']})"
                )
                st.caption(
                    "⛓️ A conclusão e o envio do token saíram na mesma operação — "
                    "uma não existe sem a outra."
                )

            # ---- Controles de atendimento ----
            st.markdown("---")
            st.markdown("**Atendimento**")

            col1, col2 = st.columns(2)
            with col1:
                label_escolhido = st.selectbox(
                    "Situação",
                    options=list(STATUS_LABELS.values()),
                    index=list(STATUS_LABELS.keys()).index(status_atual),
                    key=f"status_{r['id']}",
                )
                setor_atual = r.get("setor", SETORES[0])
                if setor_atual not in SETORES:
                    setor_atual = SETORES[0]
                setor_escolhido = st.selectbox(
                    "Equipe responsável",
                    options=SETORES,
                    index=SETORES.index(setor_atual),
                    key=f"setor_{r['id']}",
                )
            with col2:
                prazo_escolhido = st.number_input(
                    "Prazo de execução (dias úteis)",
                    min_value=1,
                    max_value=180,
                    value=int(r.get("prazo_dias") or PRAZO_PADRAO_DIAS),
                    step=1,
                    key=f"prazo_{r['id']}",
                )
                st.caption(
                    f"O padrão é {PRAZO_PADRAO_DIAS} dias úteis, contados do "
                    "encaminhamento à equipe. Ajuste quando o serviço exigir "
                    "mais ou menos tempo."
                )
                if r.get("data_andamento"):
                    st.caption(
                        "Encaminhada em "
                        f"**{formatar_data(r['data_andamento'])}**."
                    )

            atualizar = st.button("Atualizar", key=f"upd_{r['id']}")

            if atualizar:
                novo_status = LABEL_PARA_STATUS[label_escolhido]
                mudou_status = novo_status != status_atual
                mudou_setor = setor_escolhido != r.get("setor")
                mudou_prazo = int(prazo_escolhido) != int(
                    r.get("prazo_dias") or PRAZO_PADRAO_DIAS)
                precisa_tentar_onchain = (
                    novo_status == "concluida" and not r.get("token_tx")
                )

                if not (mudou_status or mudou_setor or mudou_prazo
                        or precisa_tentar_onchain):
                    st.info("Nada mudou nesta ocorrência.")
                else:
                    r["setor"] = setor_escolhido
                    r["prazo_dias"] = int(prazo_escolhido)
                    if mudou_status:
                        aplicar_status(r, novo_status)
                    salvar_registros(registros)

                    if precisa_tentar_onchain:
                        if r.get("wallet"):
                            st.session_state["conclusao_pendente"] = r["id"]
                        else:
                            st.session_state["conclusao_resultado"] = (
                                "sem_carteira", "")

                    st.rerun()

            # ---- Mensagens ----
            st.markdown("---")
            st.markdown("**Mensagens**")

            mensagens = r.get("mensagens", [])
            if mensagens:
                for m in mensagens:
                    quem = ("Cidadão" if m.get("autor") == "cidadao"
                            else "Equipe do município")
                    quando = data_curta({"data": m.get("data", "")})
                    st.markdown(f"**{quem}** · {quando}")
                    st.markdown(f"> {m.get('texto', '')}")
            else:
                st.caption("Nenhuma mensagem nesta ocorrência.")

            resposta = st.text_area(
                "Responder ao cidadão",
                key=f"resp_{r['id']}",
                height=90,
                placeholder="A equipe esteve no local hoje e o serviço foi "
                            "programado para a próxima semana.",
            )
            if st.button("Enviar resposta", key=f"envresp_{r['id']}"):
                if resposta.strip():
                    adicionar_mensagem(r, resposta, autor="municipio")
                    salvar_registros(registros)
                    st.rerun()
                else:
                    st.warning("Escreva a resposta antes de enviar.")

            # ---- Arquivar / restaurar ----
            # Arquivar em vez de excluir: nada é apagado, a ocorrência apenas
            # sai da vista do dia a dia. Isso é coerente com o próprio projeto,
            # em que o registro na blockchain é permanente por definição.
            st.markdown("---")
            if r.get("arquivada"):
                if st.button("↩️ Restaurar", key=f"rest_{r['id']}"):
                    r["arquivada"] = False
                    salvar_registros(registros)
                    st.rerun()
            else:
                if st.button("🗂️ Arquivar", key=f"arq_{r['id']}"):
                    r["arquivada"] = True
                    salvar_registros(registros)
                    st.rerun()

    ativas = [r for r in registros if not r.get("arquivada")]

    recebidas = ordenar_por_data(
        [r for r in ativas if r.get("status", "recebida") == "recebida"])
    em_andamento = ordenar_por_data(
        [r for r in ativas if r.get("status") == "em_andamento"])
    concluidas = ordenar_por_data(
        [r for r in ativas if r.get("status") == "concluida"])
    arquivadas = ordenar_por_data(
        [r for r in registros if r.get("arquivada")])

    # Lista vertical em vez de abas lado a lado: no celular, quatro abas
    # horizontais ficam apertadas e a contagem some. Empilhadas, cada grupo
    # ocupa uma linha inteira e o número fica sempre visível.
    GRUPOS = [
        (f"🔴 Recebidas ({len(recebidas)})", recebidas,
         "Nenhuma ocorrência aguardando atendimento.", "sucesso"),
        (f"🟠 Em andamento ({len(em_andamento)})", em_andamento,
         "Nenhuma ocorrência em andamento no momento.", "info"),
        (f"🟢 Concluídas ({len(concluidas)})", concluidas,
         "Nenhuma ocorrência concluída ainda.", "info"),
        (f"🗂️ Arquivadas ({len(arquivadas)})", arquivadas,
         "Nenhuma ocorrência arquivada ainda.", "info"),
    ]

    rotulos = [g[0] for g in GRUPOS]
    escolhido = st.radio("Ver:", rotulos, key="filtro_grupo",
                         label_visibility="collapsed")

    st.markdown("---")

    _, lista, vazio, tipo_vazio = next(g for g in GRUPOS if g[0] == escolhido)

    if escolhido.startswith("🗂️"):
        st.markdown(
            "Ocorrências já atendidas saem das listas do dia a dia e ficam "
            "guardadas aqui, mantendo o histórico do que a cidade resolveu. "
            "**Nada é apagado:** o registro de cada uma continua público e "
            "permanente na blockchain, e qualquer ocorrência pode ser "
            "restaurada a qualquer momento."
        )
        st.markdown("")

    if lista:
        for r in lista:
            mostrar_ocorrencia(r)
    elif tipo_vazio == "sucesso":
        st.success(vazio)
    else:
        st.info(vazio)
else:
    st.warning(
        "Nenhuma ocorrência registrada ainda. Envie pelo formulário primeiro!")
