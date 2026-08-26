"""
ocorrencias.py — DePIN Urbano, Fase 3

Regras de negócio das ocorrências, compartilhadas entre as páginas.

Existe para que o painel do município e a página de acompanhamento do cidadão
enxerguem exatamente a mesma coisa. Se o prazo fosse calculado em dois lugares
diferentes, bastaria uma linha divergente para o cidadão ver uma data e a
prefeitura ver outra — que é justamente o tipo de desencontro que o projeto
se propõe a eliminar.

Aqui não há nada de Streamlit nem de blockchain: são só dados e datas, o que
torna este arquivo fácil de testar isoladamente.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REGISTROS_PATH = BASE_DIR / "registros.json"

STATUS_LABELS = {
    "recebida": "🔴 Recebida",
    "em_andamento": "🟠 Em andamento",
    "concluida": "🟢 Concluída",
}
LABEL_PARA_STATUS = {v: k for k, v in STATUS_LABELS.items()}

STATUS_CORES_MAPA = {
    "recebida": "red",
    "em_andamento": "orange",
    "concluida": "green",
}

# Prazo padrão de execução, contado a partir do momento em que a ocorrência
# entra em andamento. Dez dias úteis é a ordem de grandeza usada por serviços
# de zeladoria urbana em prefeituras. O painel permite alterar caso a caso:
# trocar um poste não tem o mesmo prazo que recuperar uma calçada inteira.
PRAZO_PADRAO_DIAS = 10

# Quem executa. A lista é fixa de propósito: num sistema real, o setor sairia
# do tipo de ocorrência somado ao endereço (é assim que a subprefeitura
# competente é determinada). Aqui a escolha é manual, o que é suficiente para
# demonstrar o conceito sem inventar uma regra de encaminhamento que não
# corresponderia a nenhuma prefeitura de verdade.
SETORES = [
    "Não atribuído",
    "Zeladoria Urbana",
    "Obras e Pavimentação",
    "Iluminação Pública",
    "Água e Esgoto",
    "Limpeza Urbana",
    "Meio Ambiente e Poda",
    "Trânsito e Sinalização",
    "Fiscalização e Posturas",
    "Defesa Civil",
]


# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------
def _para_data(texto):
    """Converte 'AAAA-MM-DD HH:MM:SS' em date. Devolve None se não der."""
    if not texto:
        return None
    try:
        return datetime.strptime(str(texto)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def somar_dias_uteis(inicio: date, dias: int) -> date:
    """Soma dias úteis a uma data, pulando sábados e domingos.

    Feriados não entram na conta: exigiriam um calendário municipal, que
    muda de cidade para cidade. Como o prazo é editável no painel, um
    feriado pode ser absorvido manualmente quando fizer diferença.
    """
    atual = inicio
    restantes = int(dias)
    while restantes > 0:
        atual += timedelta(days=1)
        if atual.weekday() < 5:      # 0=segunda ... 4=sexta
            restantes -= 1
    return atual


def formatar_data(d) -> str:
    """date ou 'AAAA-MM-DD...' em 'DD/MM/AAAA'."""
    if isinstance(d, date):
        return d.strftime("%d/%m/%Y")
    convertida = _para_data(d)
    return convertida.strftime("%d/%m/%Y") if convertida else "—"


def data_curta(r) -> str:
    """'2026-08-22 21:25:12' vira '22/08/2026 21:25'."""
    bruta = str(r.get("data", ""))
    try:
        d, h = bruta.split(" ")
        ano, mes, dia = d.split("-")
        return f"{dia}/{mes}/{ano} {h[:5]}"
    except Exception:
        return bruta or "sem data"


# ---------------------------------------------------------------------------
# Prazo
# ---------------------------------------------------------------------------
def info_prazo(r, hoje=None):
    """Situação do prazo de uma ocorrência.

    O relógio só começa a correr quando a ocorrência entra em andamento —
    antes disso não existe equipe designada e um prazo seria fictício.

    Devolve um dicionário com:
        tem_prazo      há previsão calculável
        previsao       date da conclusão prevista (ou None)
        dias           dias úteis restantes (negativo = atrasada)
        atrasada       passou da previsão sem ter sido concluída
        concluida_em   date da conclusão, quando já concluída
    """
    hoje = hoje or date.today()
    status = r.get("status", "recebida")

    vazio = {"tem_prazo": False, "previsao": None, "dias": None,
             "atrasada": False, "concluida_em": _para_data(r.get("data_conclusao"))}

    if status == "concluida":
        return vazio

    inicio = _para_data(r.get("data_andamento"))
    if status != "em_andamento" or inicio is None:
        return vazio

    dias_prazo = int(r.get("prazo_dias") or PRAZO_PADRAO_DIAS)
    previsao = somar_dias_uteis(inicio, dias_prazo)

    # Dias úteis que ainda faltam. Contamos varrendo o intervalo em vez de
    # dividir por sete: são poucos dias, e assim o resultado bate exatamente
    # com o que a pessoa contaria no calendário.
    if previsao >= hoje:
        restantes = sum(
            1 for i in range((previsao - hoje).days)
            if (hoje + timedelta(days=i + 1)).weekday() < 5
        )
    else:
        restantes = -sum(
            1 for i in range((hoje - previsao).days)
            if (previsao + timedelta(days=i + 1)).weekday() < 5
        )

    return {
        "tem_prazo": True,
        "previsao": previsao,
        "dias": restantes,
        "atrasada": restantes < 0,
        "concluida_em": None,
    }


def texto_prazo(r, hoje=None, publico=True) -> str:
    """Frase curta sobre o prazo.

    O texto muda conforme quem está lendo. Para o cidadão, uma ocorrência
    ainda não encaminhada precisa de uma explicação: ele não sabe o que
    esperar nem quando. Para quem trabalha no município, essa mesma frase
    não informa nada, porque encaminhar é justamente o trabalho dele — ali
    o que interessa é que o relógio ainda não começou a correr.

    Use publico=False no painel do município.
    """
    status = r.get("status", "recebida")

    if status == "concluida":
        quando = _para_data(r.get("data_conclusao"))
        if quando:
            return f"Concluída em {formatar_data(quando)}."
        return "Concluída."

    if status == "recebida":
        if publico:
            return (f"Após o recebimento, a ocorrência é encaminhada à equipe "
                    f"responsável em até {PRAZO_PADRAO_DIAS} dias úteis. A "
                    f"partir desse encaminhamento, você passa a ver aqui a "
                    f"data prevista de conclusão.")
        return ("Aguardando encaminhamento. O prazo de execução começa a "
                "contar quando a situação passar para Em andamento.")

    info = info_prazo(r, hoje)
    if not info["tem_prazo"]:
        return "Em andamento."

    previsao = formatar_data(info["previsao"])
    dias = info["dias"]

    if dias > 1:
        return f"Conclusão prevista para {previsao} — faltam {dias} dias úteis."
    if dias == 1:
        return f"Conclusão prevista para {previsao} — falta 1 dia útil."
    if dias == 0:
        return f"Conclusão prevista para hoje, {previsao}."
    if dias == -1:
        return f"Prazo vencido em {previsao} — 1 dia útil de atraso."
    return f"Prazo vencido em {previsao} — {abs(dias)} dias úteis de atraso."


# ---------------------------------------------------------------------------
# Protocolo
# ---------------------------------------------------------------------------
def protocolo_de(r) -> str:
    """Número de protocolo exibido ao cidadão.

    Os registros feitos a partir da Fase 3 já nascem com um id curto que serve
    de protocolo. Os herdados da Fase 2 não tinham isso e recebem um rótulo
    próprio, para não aparecerem como 'LEGACY-3' na tela.
    """
    ident = str(r.get("id", ""))
    if ident.startswith("legacy-"):
        return f"FASE2-{ident.split('-')[-1].zfill(2)}"
    return ident.upper()


def normalizar_protocolo(texto: str) -> str:
    """Aceita o protocolo digitado de qualquer jeito.

    A pessoa vai copiar do comprovante, digitar com espaço, colar com quebra
    de linha, escrever minúsculo. Nada disso pode virar 'não encontrado'.
    """
    return "".join(str(texto).split()).upper().strip(".,;:")


def buscar_por_protocolo(registros, texto):
    """Devolve a ocorrência correspondente ao protocolo, ou None."""
    alvo = normalizar_protocolo(texto)
    if not alvo:
        return None
    for r in registros:
        if protocolo_de(r) == alvo:
            return r
    return None


# ---------------------------------------------------------------------------
# Leitura e gravação
# ---------------------------------------------------------------------------
def normalizar(r, indice=0):
    """Garante que todo registro tenha os campos que as telas esperam.

    Registros antigos foram gravados antes de vários desses campos existirem.
    Em vez de espalhar `.get(campo, padrão)` por toda parte, o preenchimento
    acontece num lugar só, na entrada.
    """
    r.setdefault("id", f"legacy-{indice}")
    r.setdefault("status", "recebida")
    r.setdefault("wallet", "")
    r.setdefault("token_tx", "")
    r.setdefault("arquivada", False)
    r.setdefault("tx_registro", "")
    if "onchain" not in r:
        r["onchain"] = bool(r.get("tx_registro"))

    # Campos da etapa de atendimento.
    r.setdefault("setor", SETORES[0])
    r.setdefault("prazo_dias", PRAZO_PADRAO_DIAS)
    r.setdefault("data_andamento", "")
    r.setdefault("data_conclusao", "")
    r.setdefault("mensagens", [])
    return r


def carregar_registros(caminho=None):
    caminho = caminho or REGISTROS_PATH
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = [json.loads(l) for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        linhas = []
    return [normalizar(r, i) for i, r in enumerate(linhas)]


def salvar_registros(registros, caminho=None):
    caminho = caminho or REGISTROS_PATH
    with open(caminho, "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def ordenar_por_data(lista):
    """Mais recentes primeiro. A data é gravada como 'AAAA-MM-DD HH:MM:SS',
    formato em que a ordem alfabética coincide com a cronológica."""
    return sorted(lista, key=lambda r: str(r.get("data", "")), reverse=True)


# ---------------------------------------------------------------------------
# Transições de status
# ---------------------------------------------------------------------------
def aplicar_status(r, novo_status, agora=None):
    """Muda o status e carimba a data do momento em que isso aconteceu.

    A data de entrada em andamento é o que ancora todo o prazo, então ela é
    gravada aqui e não é recalculada depois. Se a ocorrência voltar para
    'recebida' (um encaminhamento errado, por exemplo), o carimbo é apagado
    junto: um prazo não pode continuar correndo para uma ocorrência que não
    está mais com a equipe.
    """
    agora = agora or datetime.now()
    carimbo = agora.strftime("%Y-%m-%d %H:%M:%S")

    r["status"] = novo_status

    if novo_status == "em_andamento" and not r.get("data_andamento"):
        r["data_andamento"] = carimbo
    elif novo_status == "concluida" and not r.get("data_conclusao"):
        r["data_conclusao"] = carimbo
    elif novo_status == "recebida":
        r["data_andamento"] = ""
        r["data_conclusao"] = ""
    return r


def adicionar_mensagem(r, texto, autor="cidadao", agora=None):
    """Anexa uma mensagem à ocorrência.

    As mensagens ficam junto do registro, e não numa lista separada, porque
    o que dá sentido a elas é o contexto da ocorrência.
    """
    texto = str(texto).strip()
    if not texto:
        return r
    agora = agora or datetime.now()
    r.setdefault("mensagens", []).append({
        "autor": autor,
        "texto": texto[:1000],
        "data": agora.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return r
