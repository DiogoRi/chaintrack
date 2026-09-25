"""
ocorrencias.py — DePIN Urbano, Fase 5

Regras de negócio das ocorrências, compartilhadas entre as páginas.

Existe para que o painel do município e a página de acompanhamento do cidadão
enxerguem exatamente a mesma coisa. Se o prazo fosse calculado em dois lugares
diferentes, bastaria uma linha divergente para o cidadão ver uma data e a
prefeitura ver outra — que é justamente o tipo de desencontro que o projeto
se propõe a eliminar.

MUDANÇA DA FASE 5: até a Fase 3, este arquivo lia e gravava um arquivo
`registros.json` na pasta do projeto. Isso funcionava no Mac, mas não
sobrevive ao servidor da Streamlit, que reinicia sozinho de vez em quando
(depois de um tempo sem visita, depois de uma publicação nova, em
manutenções). Um reinício apaga tudo que só existia no disco daquele
servidor — no meio do Talent Summit isso seria catastrófico.

A partir de agora, quem guarda os dados é o Supabase. As funções abaixo
mudaram por dentro, mas mantêm exatamente os mesmos nomes e o mesmo formato
de dados que usavam antes — então nenhuma das duas páginas que consomem este
arquivo precisou mudar uma linha sequer. A "gaveta" trocou; a etiqueta da
gaveta continua a mesma.

Duas gavetas dividem a mesma tabela `ocorrencias` no banco: as ocorrências
normais do dia a dia (origem='normal', o que este arquivo cuida) e as da
gincana do evento (origem='evento', que o app do Raphael e o worker cuidam
através de outras funções). Elas nunca se misturam.
"""

import json
import os
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# não é mais usado para ler/gravar;
REGISTROS_PATH = BASE_DIR / "registros.json"
# fica só de referência histórica.

load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError(
        "Faltam SUPABASE_URL e/ou SUPABASE_SECRET_KEY no .env. "
        "Sem eles este arquivo não consegue falar com o banco de dados. "
        "Confira o .env na raiz do projeto (veja .env.example)."
    )

_REST = f"{SUPABASE_URL}/rest/v1/ocorrencias"
_REST_ANTENAS = f"{SUPABASE_URL}/rest/v1/antenas"
# BLOCO 9: as duas funções de identidade do cidadão (criar_participante,
# recuperar_participante) já existem no Supabase desde a Fase 5 inicial,
# criadas para o app em React do Raphael chamar diretamente. Aqui elas são
# chamadas por REST simples, do mesmo jeito que o resto deste arquivo já
# fala com o banco — são funções (RPC), não tabelas, por isso o endereço
# é /rest/v1/rpc/<nome-da-funcao> em vez de /rest/v1/<tabela>.
_RPC_CRIAR_PARTICIPANTE = f"{SUPABASE_URL}/rest/v1/rpc/criar_participante"
_RPC_RECUPERAR_PARTICIPANTE = f"{SUPABASE_URL}/rest/v1/rpc/recuperar_participante"
# BLOCO 9 (vitrine, 25/09 — corrigido mais tarde no mesmo dia): a área
# pessoal do cidadão comum (obter_painel_cidadao, mais abaixo) tentou
# primeiro reaproveitar a função `painel(p_id)` que o Rafa já usa no React
# desde 18/09. Só que `painel()` filtra `origem = 'evento'` em tudo o que
# devolve — de propósito, para o ranking da gincana nunca se misturar com
# ocorrências do fluxo normal (ver o comentário na própria função, no
# Supabase). Resultado: para o cidadão comum (origem sempre 'normal'),
# `painel()` sempre devolvia 0 CP e 0 ocorrências, mesmo com tudo certo no
# banco — só descoberto testando de ponta a ponta e comparando com o banco
# linha por linha.
#
# A correção consulta as tabelas direto (constante logo abaixo), com o
# filtro ESPELHADO: `origem = 'normal'` em vez de `'evento'`. `painel()`
# em si não foi tocada — o Rafa continua recebendo dela exatamente o que
# sempre recebeu (REGRA QUE NÃO SE QUEBRA). Os dois painéis leem a MESMA
# tabela `ocorrencias`, cada um só a fatia dele; não criamos nenhuma
# função nova no banco.
_REST_PARTICIPANTES = f"{SUPABASE_URL}/rest/v1/participantes"
# Pedido do Rafa (23/09): um jeito de ver, do celular, há quanto tempo o
# worker parou — em vez de descobrir só quando alguém percebe. A tabela
# worker_lease já é atualizada a cada volta do laço do worker desde o Bloco
# 5 (campo visto_em); só faltava um jeito de ler isso de fora. Usa a mesma
# chave secreta e o mesmo padrão REST do resto deste arquivo — não é uma
# função nova no Postgres, então não mexe em nada que o Rafa consome.
_REST_WORKER_LEASE = f"{SUPABASE_URL}/rest/v1/worker_lease"
_HEADERS = {
    "apikey": SUPABASE_SECRET_KEY,
    "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
    "Content-Type": "application/json",
}
_TIMEOUT = 15   # segundos. Mais que isso e algo está muito errado com a rede.

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

# O banco fala outro dialeto: 'registrado'/'em_andamento'/'concluido' — porque
# esse é o vocabulário exato que está prometido ao Raphael no tipos.ts, e a
# mesma tabela também guarda as ocorrências da gincana. Essa troca de palavras
# acontece só aqui, na fronteira com o banco; o resto deste arquivo e as duas
# páginas continuam falando 'recebida'/'em_andamento'/'concluida' como sempre.
_STATUS_PARA_BANCO = {
    "recebida": "registrado",
    "em_andamento": "em_andamento",
    "concluida": "concluido",
}
_STATUS_DO_BANCO = {v: k for k, v in _STATUS_PARA_BANCO.items()}

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
# Leitura e gravação — FASE 5: fala com o Supabase, não mais com o arquivo
# ---------------------------------------------------------------------------
def normalizar(r, indice=0):
    """Garante que todo registro tenha os campos que as telas esperam.

    Registros antigos (ou linhas incompletas vindas do banco) podem não ter
    todos os campos ainda. Em vez de espalhar `.get(campo, padrão)` por toda
    parte, o preenchimento acontece num lugar só, na entrada.
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


def _carimbo_para_iso(carimbo):
    """'2026-09-12 14:23:01' -> '2026-09-12T14:23:01' (o que o Postgres aceita)."""
    if not carimbo:
        return None
    return str(carimbo).replace(" ", "T", 1)


def _iso_para_carimbo(iso):
    """O que volta do Postgres (ex: '2026-09-12T14:23:01.83+00:00') vira
    '2026-09-12 14:23:01' — o formato que o resto deste arquivo já entende.

    Nota sobre fuso: para não complicar um protótipo com conversão de fuso
    horário, os carimbos são gravados e lidos como texto puro, sem tradução
    de UTC para horário de Brasília. Isso preserva exatamente os dígitos que
    o próprio app escreveu — o que basta para ordenar e exibir. Não é usado
    para nenhum cálculo entre sistemas diferentes.
    """
    if not iso:
        return ""
    return str(iso)[:19].replace("T", " ")


def _para_banco(r):
    """Um registro no formato usado pelas telas -> uma linha da tabela `ocorrencias`."""
    return {
        "protocolo": r.get("id"),
        "origem": r.get("origem", "normal"),
        "antena_numero": r.get("antena_numero"),
        "participante_id": r.get("participante_id") or None,
        "tipo": r.get("tipo", "outro"),
        "nome": r.get("nome") or None,
        "email": r.get("email") or None,
        "endereco": r.get("endereco") or None,
        "descricao": r.get("descricao") or None,
        "foto_cid": r.get("cid") or None,
        "lat": r.get("latitude"),
        "lng": r.get("longitude"),
        "status": _STATUS_PARA_BANCO.get(r.get("status", "recebida"), "registrado"),
        "wallet": r.get("wallet") or None,
        "tx_hash_registro": r.get("tx_registro") or None,
        "tx_hash_conclusao": r.get("token_tx") or None,
        "setor": r.get("setor", SETORES[0]),
        "prazo_dias": int(r.get("prazo_dias") or PRAZO_PADRAO_DIAS),
        "mensagens": r.get("mensagens", []),
        "arquivada": bool(r.get("arquivada", False)),
        "em_andamento_em": _carimbo_para_iso(r.get("data_andamento")),
        "concluido_em": _carimbo_para_iso(r.get("data_conclusao")),
    }


def _do_banco(row):
    """Uma linha vinda do Supabase -> o formato que as telas já conhecem."""
    return normalizar({
        "id": row.get("protocolo") or f"db-{row.get('id')}",
        "nome": row.get("nome") or "",
        "email": row.get("email") or "",
        "endereco": row.get("endereco") or "",
        "descricao": row.get("descricao") or "",
        "latitude": row.get("lat"),
        "longitude": row.get("lng"),
        "cid": row.get("foto_cid") or "",
        "data": _iso_para_carimbo(row.get("criado_em")),
        "status": _STATUS_DO_BANCO.get(row.get("status"), "recebida"),
        "wallet": row.get("wallet") or "",
        "token_tx": row.get("tx_hash_conclusao") or "",
        "tx_registro": row.get("tx_hash_registro") or "",
        "onchain": bool(row.get("tx_hash_registro")),
        "setor": row.get("setor") or SETORES[0],
        "prazo_dias": row.get("prazo_dias") or PRAZO_PADRAO_DIAS,
        "data_andamento": _iso_para_carimbo(row.get("em_andamento_em")),
        "data_conclusao": _iso_para_carimbo(row.get("concluido_em")),
        "mensagens": row.get("mensagens") or [],
        "arquivada": bool(row.get("arquivada", False)),
    })


def buscar_antena_por_slug(slug):
    """Devolve o numero da antena ativa correspondente ao slug, ou None.
    Usado no bloco 3: quando o cidadao chega pela URL da gincana (?a=<slug>),
    confirmamos que a antena existe e esta ativa ANTES de mostrar o formulario.
    """
    if not slug:
        return None
    try:
        resp = requests.get(
            _REST_ANTENAS,
            headers=_HEADERS,
            params={"slug": f"eq.{slug}",
                    "ativa": "eq.true", "select": "numero"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        linhas = resp.json()
    except Exception:
        return None
    if not linhas:
        return None
    return linhas[0]["numero"]


def criar_participante_automatico():
    """BLOCO 9: cria um participante novo para o cidadão do fluxo normal
    (fora da gincana), usando um apelido interno gerado pelo próprio
    código — nunca escolhido nem visto pela pessoa, e nunca exibido em
    nenhuma tela (o telão só soma ocorrências com origem='evento', então
    esse apelido nunca aparece lá).

    Existe só para satisfazer a função criar_participante() do Supabase,
    que foi desenhada pensando na gincana e por isso exige um apelido.

    Devolve {"id":..., "apelido":..., "codigo_recup":...} do novo
    participante, ou None se não conseguir depois de algumas tentativas
    (por exemplo, sem conexão com o Supabase).
    """
    for _ in range(3):
        apelido_interno = "cidadao_" + uuid.uuid4().hex[:10]
        try:
            resp = requests.post(
                _RPC_CRIAR_PARTICIPANTE,
                headers=_HEADERS,
                json={"p_apelido": apelido_interno},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            resultado = resp.json()
        except Exception:
            return None
        if resultado.get("ok"):
            return resultado["participante"]
        if resultado.get("erro") != "apelido_em_uso":
            # "apelido_curto" não deveria acontecer (o texto gerado sempre
            # tem bem mais de 2 caracteres) e "tente_de_novo" é raríssimo —
            # mas se vier, tentar de novo com o mesmo motivo não ajudaria.
            return None
    return None


def recuperar_participante_por_codigo(codigo):
    """BLOCO 9: confere um código de recuperação e devolve o participante
    correspondente, ou None se o código não existir ou algo falhar.
    Usado quando o cidadão do fluxo normal cola o código de um painel que
    já tinha (por exemplo, vindo de outro aparelho).
    """
    if not codigo or not codigo.strip():
        return None
    try:
        resp = requests.post(
            _RPC_RECUPERAR_PARTICIPANTE,
            headers=_HEADERS,
            json={"p_codigo": codigo.strip()},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        resultado = resp.json()
    except Exception:
        return None
    if resultado.get("ok"):
        return resultado["participante"]
    return None


def obter_painel_cidadao(participante_id):
    """BLOCO 9 (vitrine): dados da área pessoal do cidadão comum — CP
    acumulado, apelido interno (nunca mostrado) e a lista de ocorrências
    dele, com status já traduzido para o vocabulário do app
    ('recebida'/'em_andamento'/'concluida', o mesmo de STATUS_LABELS).

    ATUALIZADO em 25/09 (correção, mais tarde no mesmo dia): não usa mais a
    RPC `painel()` — ela filtra `origem = 'evento'` em tudo (decisão certa
    para a gincana, ver comentário da função no Supabase), então nunca
    devolvia nada para o cidadão comum, cujas ocorrências são sempre
    'normal'. Agora consulta `participantes` e `ocorrencias` direto, com o
    filtro espelhado (`origem = 'normal'`). Não cria função nova no banco,
    e `painel()` continua intocada — o que o Rafa consome dela não muda em
    nada (REGRA QUE NÃO SE QUEBRA). `pontos_gincana` fica sempre 0 aqui de
    propósito: pontos de gincana são assunto do `painel()`, não deste
    painel.

    Devolve:
        {"ok": True, "codigo_recup": "...", "cp": 3, "pontos_gincana": 0,
         "ocorrencias": [{"tipo":..., "status":..., "cp_ganho":...,
                           "tx_hash":..., "criado_em": "AAAA-MM-DD HH:MM:SS"},
                          ...]}   # mais recente primeiro
    ou {"ok": False, "erro": "..."} se o id não existir ou a consulta falhar.
    """
    if not participante_id:
        return {"ok": False, "erro": "sem participante_id"}

    try:
        resp_participante = requests.get(
            _REST_PARTICIPANTES,
            headers=_HEADERS,
            params={
                "id": f"eq.{participante_id}",
                "select": "id,codigo_recup",
            },
            timeout=_TIMEOUT,
        )
        resp_participante.raise_for_status()
        linhas_participante = resp_participante.json()
    except Exception as e:
        return {"ok": False, "erro": f"não foi possível consultar: {e}"}

    if not linhas_participante:
        return {"ok": False, "erro": "participante não encontrado"}
    participante = linhas_participante[0]

    try:
        resp_ocorrencias = requests.get(
            _REST,
            headers=_HEADERS,
            params={
                "participante_id": f"eq.{participante_id}",
                "origem": "eq.normal",
                "select": ("tipo,status,cp_ganho,tx_hash_registro,"
                           "tx_hash_conclusao,criado_em"),
                "order": "criado_em.desc",
            },
            timeout=_TIMEOUT,
        )
        resp_ocorrencias.raise_for_status()
        brutas = resp_ocorrencias.json()
    except Exception as e:
        return {"ok": False, "erro": f"não foi possível consultar: {e}"}

    ocorrencias = [
        {
            "tipo": o.get("tipo"),
            "status": _STATUS_DO_BANCO.get(o.get("status"), o.get("status")),
            "cp_ganho": o.get("cp_ganho") or 0,
            "tx_hash": o.get("tx_hash_conclusao") or o.get("tx_hash_registro"),
            "criado_em": _iso_para_carimbo(o.get("criado_em")),
        }
        for o in brutas
    ]

    return {
        "ok": True,
        "codigo_recup": participante.get("codigo_recup"),
        "cp": sum(o["cp_ganho"] for o in ocorrencias),
        "pontos_gincana": 0,
        "ocorrencias": ocorrencias,
    }


def buscar_endereco_por_coordenada(lat, lon):
    """Traduz uma coordenada (latitude, longitude) vinda do GPS do navegador
    em um endereco legivel (rua, bairro, cidade), usando o servico gratuito
    Nominatim (OpenStreetMap).
    Usado no bloco 3-b: quando o cidadao aperta 'Usar minha localizacao'.
    Se qualquer coisa der errado, devolve None e o formulario cai no
    preenchimento manual, sem travar o cadastro.
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            headers={"User-Agent": "DePIN-Urbano-FIAP/1.0"},
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        dados = resp.json()
    except Exception:
        return None

    endereco = dados.get("address", {})
    resultado = {
        "via": endereco.get("road") or endereco.get("pedestrian") or "",
        "bairro": endereco.get("suburb") or endereco.get("neighbourhood") or "",
        "cidade": endereco.get("city") or endereco.get("town") or endereco.get("municipality") or "",
        "estado": endereco.get("state") or "",
        "cep": endereco.get("postcode") or "",
        "numero": endereco.get("house_number") or "",
    }

    # Em areas rurais, o Nominatim (OpenStreetMap) costuma saber o CEP mas
    # nao sabe o nome da cidade ou do bairro -- isso depende de voluntarios
    # terem mapeado aquele trecho, o que raramente acontece no interior. Os
    # Correios, por outro lado, sempre sabem a qual cidade um CEP pertence.
    # Por isso, se faltar a cidade mas tivermos um CEP, completamos com o
    # ViaCEP -- sem sobrescrever o que o Nominatim ja sabia.
    if not resultado["cidade"] and resultado["cep"]:
        dados_cep = buscar_endereco_por_cep(resultado["cep"])
        if dados_cep:
            for campo in ("via", "bairro", "cidade"):
                if not resultado[campo] and dados_cep[campo]:
                    resultado[campo] = dados_cep[campo]

    return resultado


def buscar_endereco_por_cep(cep):
    """Consulta o CEP no ViaCEP (o webservice dos Correios) e devolve o que
    encontrar (via, bairro, cidade, estado), ou None se o CEP nao existir ou
    o servico falhar.
    """
    cep_limpo = "".join(c for c in (cep or "") if c.isdigit())
    if len(cep_limpo) != 8:
        return None
    try:
        resp = requests.get(
            f"https://viacep.com.br/ws/{cep_limpo}/json/",
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        dados = resp.json()
    except Exception:
        return None
    if dados.get("erro"):
        return None
    return {
        "via": dados.get("logradouro") or "",
        "bairro": dados.get("bairro") or "",
        "cidade": dados.get("localidade") or "",
        "estado": dados.get("uf") or "",
    }


def carregar_registros(caminho=None):
    """Lê do Supabase todas as ocorrências do fluxo normal (não-evento).

    `caminho` não é mais usado — o parâmetro fica só para não quebrar quem
    ainda chamar esta função como antes, passando um caminho de arquivo.
    """
    resp = requests.get(
        _REST,
        headers=_HEADERS,
        params={"origem": "eq.normal", "order": "id.desc"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [_do_banco(row) for row in resp.json()]


def salvar_registros(registros, caminho=None):
    """Grava a lista inteira de volta no Supabase.

    Mantida com o mesmo nome e a mesma ideia de sempre — "aqui está a lista
    inteira, guarda ela" — para que as duas páginas continuem chamando
    exatamente como chamavam quando isto escrevia num arquivo. Por baixo,
    virou um upsert: o Supabase encontra cada linha pelo protocolo (que é
    único) e atualiza os campos daquela linha, sem duplicar nada.
    """
    if not registros:
        return
    payload = [_para_banco(r) for r in registros]
    resp = requests.post(
        _REST,
        headers={**_HEADERS, "Prefer": "resolution=merge-duplicates"},
        params={"on_conflict": "protocolo"},
        json=payload,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()


def criar_registro(dados):
    """Grava uma ocorrência NOVA e devolve ela já normalizada, com protocolo.

    Chamada pelo app.py assim que os dados do formulário são válidos —
    ANTES da foto subir para o IPFS. Se a foto (ou, mais tarde, a
    blockchain) falhar depois, a ocorrência já existe e não se perde: é
    exatamente o problema que esta troca resolve.
    """
    protocolo = uuid.uuid4().hex[:8]
    registro = normalizar(
        {**dados, "id": protocolo, "status": dados.get("status", "recebida")})
    linha = _para_banco(registro)
    resp = requests.post(_REST, headers=_HEADERS, json=[
                         linha], timeout=_TIMEOUT)
    resp.raise_for_status()
    return registro


def atualizar_registro(protocolo, **campos):
    """Atualiza só os campos passados de uma ocorrência já existente.

    Usado, por exemplo, depois que a foto sobe para o IPFS (para gravar o
    CID) — sem precisar carregar e regravar a lista inteira só para mudar
    uma linha.
    """
    traducao = {
        "cid": "foto_cid",
        "latitude": "lat",
        "longitude": "lng",
        "tx_registro": "tx_hash_registro",
        "token_tx": "tx_hash_conclusao",
        "data_andamento": "em_andamento_em",
        "data_conclusao": "concluido_em",
    }
    corpo = {}
    for chave, valor in campos.items():
        chave_banco = traducao.get(chave, chave)
        if chave_banco in ("em_andamento_em", "concluido_em"):
            valor = _carimbo_para_iso(valor)
        corpo[chave_banco] = valor

    resp = requests.patch(
        _REST,
        headers=_HEADERS,
        params={"protocolo": f"eq.{protocolo}"},
        json=corpo,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()


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


def obter_status_worker():
    """Pedido do Rafa (23/09): um "sinal de vida" do worker, legível de
    qualquer lugar (inclusive do celular, numa página do Streamlit), pra
    responder "há quanto tempo ele parou" em vez de só descobrir isso
    quando alguém percebe que ocorrências pararam de sair da fila.

    Lê a linha `worker_blockchain` da tabela `worker_lease`, que já é
    renovada a cada volta do laço do worker desde o Bloco 5 (campo
    `visto_em`) — nada precisou mudar no worker em si pra isso funcionar.

    Devolve um dicionário:
        {
            "ok": True,
            "owner": "...",              # qual processo/máquina é o dono
            "visto_em": datetime,        # última vez que o worker se
                                          # provou vivo (fuso do servidor)
            "segundos_desde_ultima_volta": 12.3,
        }
    ou {"ok": False, "erro": "..."} se a linha não existir ou a consulta
    falhar (por exemplo, Supabase fora do ar — que é, ele mesmo, um sinal
    de alerta, só que sobre o banco, não sobre o worker).
    """
    try:
        resp = requests.get(
            _REST_WORKER_LEASE,
            headers=_HEADERS,
            params={
                "nome": "eq.worker_blockchain",
                "select": "owner,visto_em,lease_ate",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        linhas = resp.json()
    except Exception as e:
        return {"ok": False, "erro": f"não foi possível consultar: {e}"}

    if not linhas:
        return {"ok": False, "erro": "linha 'worker_blockchain' não encontrada"}

    linha = linhas[0]
    visto_em_texto = linha.get("visto_em")
    if not visto_em_texto:
        return {"ok": False, "erro": "worker nunca registrou um heartbeat"}

    try:
        visto_em = datetime.fromisoformat(visto_em_texto.replace("Z", "+00:00"))
        agora = datetime.now(visto_em.tzinfo)
        segundos = (agora - visto_em).total_seconds()
    except Exception as e:
        return {"ok": False, "erro": f"data inválida vinda do banco: {e}"}

    return {
        "ok": True,
        "owner": linha.get("owner"),
        "visto_em": visto_em,
        "segundos_desde_ultima_volta": segundos,
    }
