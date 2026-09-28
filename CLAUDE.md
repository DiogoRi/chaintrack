# CLAUDE.md — DePIN Urbano (ChainTrack)

Guia permanente de trabalho para qualquer sessão do Claude neste projeto. É **enxuto de propósito**:
não repete o conteúdo dos documentos, só diz **onde está a verdade** de cada assunto e **quais regras não
mudam**. Se algo aqui divergir de um documento mais novo ou do código, **investigue antes de agir** e
avise o Diogo; não corrija este arquivo por conta própria sem registrar o motivo.

> **Este arquivo é a referência principal** sempre que a sessão tiver acesso à pasta/repositório. Não
> existe cópia dele no claude.ai, de propósito (duas cópias acabariam divergindo).
>
> Repositório **público** (`github.com/DiogoRi/chaintrack`): **todo conteúdo versionado é público**,
> inclusive este arquivo. Regra absoluta: nunca colocar aqui nem em nenhum arquivo do repo senhas,
> chaves privadas, secrets, conteúdo do `.env`, slugs das antenas, códigos de recuperação ou qualquer
> credencial.

---

## 1. Antes de começar qualquer tarefa

1. Leia o **"Fase 5 - Plano de execucao.md"** (documento do projeto no claude.ai, ver §5): o topo tem
   as atualizações por data; a seção "Ordem do dia — o que falta" tem as pendências abertas.
2. Leia **"Como trabalhar com o Diogo.md"** (mesmo lugar): como explicar, em que ritmo, o que evitar.
3. Confira o estado real no **código e no Git** antes de afirmar qualquer coisa (último commit,
   `main` vs `origin/main`, arquivo no disco). Pasta certa no Mac: `/Users/diogo/Desktop/depin-urbano`
   (desde 25/09; antes era `/Users/diogo/depin-urbano`, que não existe mais).

---

## 2. Regras permanentes de trabalho

### Verificar antes de agir
- Antes de sugerir, implementar ou alterar qualquer coisa, consulte os documentos, o código e, quando
  necessário, o histórico (Git, conversas anteriores) relevante.
- Não presuma que uma funcionalidade, arquivo, serviço, tabela, coluna, função, endpoint ou componente
  existe. **Verifique primeiro.** (Já aconteceu: documentação dizia que algo tinha sido feito no
  `app.py` e não tinha; documentação dizia que `painel()` precisava de ajuste e já estava pronta.)
- Não invente arquitetura, funcionalidades, decisões ou requisitos que não estejam documentados ou
  confirmados pelo Diogo.
- Nunca invente informação para preencher uma lacuna. O que só o Diogo (ou o Rafa) pode confirmar fica
  marcado explicitamente como **"pendente de confirmação"**.
- **Conflito entre fontes** (conversa, documentos, Git, código, banco): a data sozinha não basta para
  concluir qual está certa, e nenhuma fonte vence automaticamente. Consulte o Plano de execução, o
  código/infraestrutura atual e o histórico relevante. Se ainda houver ambiguidade, **pergunte ao Diogo
  antes de alterar**. Divergência encontrada é registrada, não ignorada.
- Documento antigo com decisão superada: não apagar o histórico; acrescentar nota de "superado"
  apontando para o Plano de execução, **só** quando houver decisão posterior confirmada.
- Se um `git status`/`git push` mostrar algo estranho, rode `pwd` antes de suspeitar de bug de Git.

### Dizer o estado com precisão
- Sempre diferencie: **implementado** (confirmado no código/Git/banco), **planejado**, **pendente de
  confirmação** e **apenas sugestão**.
- Antes de afirmar que algo está concluído, confirme no código, no Git, nos arquivos ou na
  infraestrutura. "Rodou sem erro" não é "funciona": todo bloco precisa de um teste que **chame** o que
  foi criado.
- **Editar o arquivo no Mac não é publicar.** O `chaintrack.streamlit.app` redeploya a partir da `main`
  no GitHub: só está no ar depois de commit + push (e do redeploy automático). Confirmar o push por
  `main` == `origin/main`.
- Ao testar localmente depois de editar um módulo importado (ex.: `ocorrencias.py`), reinicie o processo
  do `streamlit run`: o processo antigo continua com o código velho em memória.

### Preservar o que existe
- Preserve as decisões arquiteturais já tomadas (§4). Se houver motivo técnico para mudar, **explique e
  discuta com o Diogo antes** de qualquer mudança estrutural.
- Trabalhe incrementalmente e preserve o que já funciona.
- Antes de remover ou substituir algo, verifique dependências e impacto no restante do projeto
  (inclusive no lado do Rafa).
- **Regra que não se quebra (contrato com o React):** antes de qualquer mudança, pergunte: *isso muda o
  que sai de `painel()`, `telao()`, `chegada()`, `apelido_disponivel()`, `criar_participante()` ou
  `recuperar_participante()`?* Não → pode tocar. Sim → para, avisa o Rafa, e só então muda.
- Constantes espelhadas precisam mudar juntas: `RETRIES_MAX` (`worker_blockchain.py`) ==
  `_RETRIES_MAX_WORKER` (`ocorrencias.py`); faixas de status do worker espelham `INTERVALO_LOOP_SEG` e
  `DURACAO_LEASE_SEG`.
- **Se uma ferramenta de edição/escrita falhar ou ficar sem progresso por tempo anormal, não insista
  nem entre em loop de arquivos intermediários.** Pare, releia o estado real do arquivo (a "falha" pode
  ser só a ferramenta recusando uma edição vazia/mal direcionada, sem ter mudado nada) e diagnostique a
  causa antes de tentar de novo. Para documentos do projeto Claude.ai — que não têm edição incremental,
  só leem e regravam tudo —, usar uma cópia temporária para preservar o original e validar que nada foi
  perdido antes de regravar **é permitido e correto**; isso não é o problema. O que não pode acontecer é
  repetir a mesma operação, empilhar cópias em cascata (`original.md`, `plano.md`, `_correto.md`...) ou
  trocar de estratégia sozinho sem diagnosticar — **pare e pergunte ao Diogo antes** (decidido 27/09,
  depois de três tentativas de escrever um arquivo grande travarem em sequência).

### Documentação
- Não recrie documentos inteiros quando uma atualização incremental basta.
- Não crie documentos paralelos ou duplicados para substituir documentos oficiais sem necessidade.
- Depois de mudanças relevantes, verifique quais documentos precisam ser atualizados. O **Plano de
  execução** é atualizado **sem esperar pedido**, assim que uma decisão fecha ou um achado importante
  aparece (pedido explícito do Diogo, 18/09).

### Com as pessoas
- Detalhes em "Como trabalhar com o Diogo.md". Resumo: explicar sempre o quê **e por quê**; linguagem
  simples (termo técnico traduzido na primeira vez); **um passo de cada vez** quando ele está executando,
  esperando o resultado ou o print; quando faltar base para uma decisão, recomendar uma com o raciocínio
  à mostra; assumir erro próprio na hora.
- **Nada de crítica ao Rafa**: levar solução, não apontamento. Mensagens para o Rafa escritas na voz do
  Diogo, prontas para copiar.

---

## 3. Arquitetura atual (resumo; detalhes nas fontes do §5)

```
Cidadão (fluxo normal) ─────────────┐
                                    ▼
QR na miniantena → React (Vercel) → Streamlit `app.py` → Supabase (Postgres) ← worker_blockchain.py (Mac)
   depinurbano.vercel.app/a/:slug     chaintrack.streamlit.app      │                 │
   /eu?p=<id> (painel), telão         formulário, Pinata (foto)     │                 ▼
                                                                    │        Polygon Amoy (2 contratos)
React lê o Supabase só por funções ◄────────────────────────────────┘        registro + mint do CP
                                                                              (carteira de custódia)
vigia_antena.py (Mac, USB) → ESP32 → LEDs da antena grande
```

- **Streamlit** (este repo) escreve: formulário (`app.py`), foto no Pinata, gravação no Supabase.
  Páginas: acompanhar ocorrência, Dashboard do Município (com senha; aba de status do worker desde
  26/09), Sobre, Meu Painel (cidadão comum).
- **React** (repo do Rafa) só lê, chamando funções do Supabase; nunca lê tabela direto.
- **Supabase** é a fonte dos dados; a blockchain é a prova. O cidadão nunca espera a blockchain.
- **Worker** roda no Mac do Diogo; deve subir com `caffeinate -s ./iniciar_worker.command` (auto-reinício
  e Mac acordado, ver checklist do dia 30 no Plano): registra on-chain, avança
  sozinho o status das ocorrências da gincana, e minta 1 CP na conclusão. Uma transação por vez; lease
  em `worker_lease` impede dois workers simultâneos.

---

## 4. Decisões arquiteturais vigentes (não mudar sem discutir)

Motivos e datas estão no Plano de execução; aqui só a lista.

- **Supabase primeiro, blockchain depois** (Bloco 2): a ocorrência é salva na hora; o worker grava o hash
  depois. Ordem real: foto no Pinata → linha no Supabase (decisão consciente do Bloco 2).
- **Sem carteira Web3 para o cidadão** (16/09): nenhum campo de carteira em nenhum fluxo. Todo CP vai
  para a **carteira de custódia do projeto**; o vínculo CP↔pessoa existe só no Supabase.
- **CP só é creditado pelo worker**, no momento em que a conclusão é confirmada on-chain; nunca pelo
  botão do Dashboard (16/09).
- **Privacidade on-chain** (22/09): vai para a blockchain só o CID da foto e o protocolo. Nada de nome,
  descrição, endereço ou coordenadas (LGPD).
- **`origem = 'evento'` (gincana) e `origem = 'normal'` (cidadão comum) nunca se misturam**: ranking e
  `painel()` só veem evento; Dashboard do Município e Meu Painel só veem normal.
- **Identidade do cidadão** (16/09 e 23/09): `participante_id` persistente (`p_...`) + código de
  recuperação, reconhecido por sessão → localStorage → código. Login com e-mail/senha é evolução futura
  possível, sem refazer a base.
- **Contratos definitivos na Amoy; sem redeploy** (08/09). Endereços públicos no Plano de execução
  ("DECISÃO 08/09").
- **Domínio `depinurbano.vercel.app` e o caminho `/a/:slug` são fixos**: o QR está gravado na geometria
  impressa das antenas (21/09).
- **Divisão pelo verbo**: tudo que lê → React; tudo que escreve → Python/Streamlit.
- **Ligar/desligar antena** é feito no banco (`antenas.ativa`), não no código.
- **A antena não é "nó blockchain"**: um agente (`vigia_antena.py`) lê o estado e aciona o ESP32. Ela é
  maquete em escala de um gateway LoRaWAN futuro.

---

## 5. Mapa das fontes de verdade

"Projeto" = documentos do projeto **IC/Future Makers** no claude.ai. "Repo" = `DiogoRi/chaintrack`.

| Assunto | Fonte de verdade | Observação |
|---|---|---|
| Estado atual, decisões, histórico e pendências da Fase 5 | Projeto: `Fase 5 - Plano de execucao.md` | Fonte vigente das decisões; em conflito, aplicar a regra de conflito do §2 |
| Como trabalhar com o Diogo | Projeto: `Como trabalhar com o Diogo.md` | |
| Escopo e regras do evento (Talent Summit, 30/09) | Projeto: `Fase 5 - Talent Summit - decisoes e escopo ate 30-09.md` | Detalhes técnicos posteriores estão no Plano |
| Custódia do CP e o que o certificado prova | Projeto: `Fase 5 - Custodia do token CP e o que prova o certificado.md` | Ver §6 (trecho da carteira no fluxo normal superado) |
| Banco de dados (tabelas, funções, RLS) | **O banco real** (Supabase SQL Editor; `pg_get_functiondef`) → Plano de execução → `Fase 5 - Esquema do Supabase (para executar).md` | O doc do esquema é a versão de 06/09; várias partes mudaram (§6) |
| Contrato React ↔ Supabase | `tipos.ts` (revisão 8), no repo do Rafa | Não acessível daqui; resumo no Plano, seção "Troca com o Rafa — 17 e 18/09" |
| Regras de negócio Python / acesso ao Supabase | Repo: `ocorrencias.py` | Telas só chamam funções daqui |
| Formulário do cidadão e da gincana | Repo: `app.py` | |
| Páginas Streamlit | Repo: `pages/` (1 Acompanhar, 2 Dashboard do Município, 3 Sobre, 5 Meu Painel) | `4_Status_do_Worker.py` foi removida em 26/09 |
| Blockchain / worker | Repo: `worker_blockchain.py`, `mint_token.py`, `abi.json`, `token_abi.json`, `CidadaoParticipativoToken.sol`, `iniciar_worker.command` | Endereços dos contratos: Plano, "DECISÃO 08/09" |
| Frontend React (chegada, painel, telão, certificado) | Repo do Rafa (branch `main` → Vercel) | Estratégia em `Fase 5 - Plano do frontend React (Rafa).md`; detalhes técnicos desse doc estão superados (§6) |
| Hardware / antenas | Repo: `vigia_antena.py`, `antena_serial.py`, `arduino/antena_depin.ino`, `ANTENA_GUIA_RAPHAEL.md`, `ANTENA_PASSO_A_PASSO_RAPHAEL.md`, `iniciar_antena.command`; Plano, seção "Mini-antenas" | Docs do projeto sobre antena são da Fase 3 |
| Deploy e operação | Streamlit Cloud observa a `main` do repo; Secrets na Streamlit Cloud; `.env` local (fora do Git); `requirements.txt`; Plano, "Checklist da manhã do dia 30" | Slugs das antenas: arquivo `.sql` no Desktop do Diogo, **fora do repo** de propósito |
| Apresentação / pitch | Projeto: `Roteiro da apresentacao - 28-08.md`; `ROTEIRO_APRESENTACAO.md` local (fora do Git) | Roteiro ainda cita a MetaMask (§6) |
| Proposta da IC e regras do programa | Projeto: PDF da proposta; `Guia_Participante_Future_Makers.pdf` | O PDF da proposta tem o domínio errado (com hífen) |
| Histórico da Fase 3 e anteriores | Projeto: `Estado Fase3...`, `Cronograma Fase3...`, `Fase 4 - ideias...`, `Antena no Mac...`; repo: `LEIA-ME_FASE3.md` | Só histórico; não usar como estado atual |

---

## 6. Trechos conhecidos como desatualizados (não seguir sem conferir)

- **Esquema do Supabase (06/09)**: o `auto_conclusao.py` separado virou parte do `worker_blockchain.py`
  (18/09); previa a linha no banco antes da foto (a ordem real é o contrário, Bloco 2); o texto de
  `painel()`/`telao()` é anterior à revisão 8; o domínio está com hífen; e a "rotação de chaves e
  carteira nova" foi **cancelada** em 08/09. **Onde o worker roda:** o esquema previa a nuvem; hoje roda
  no Mac; levar para a nuvem está **em avaliação para o NEXT** (Diogo, 27/09). Não é decisão fechada.
- **Custódia do CP (05/09)**: dizia que o campo de carteira continuaria no fluxo normal. Foi **removido
  de todos os fluxos** em 16/09.
- **Plano do frontend React (05/09)**: parâmetros de URL (`?antena=&apelido=`), tabelas e calendário
  superados. O formato real é `?a=<slug>&p=<id>` e `/eu?p=<id>`.
- **Roteiro da apresentação (28/08)**: a fala "mostre a MetaMask com o saldo de CP" não vale mais.
  Também não vale mais "concluir e recompensar são a mesma transação".
- **Plano de execução, "Em paralelo"**: o item "encurtar a URL da Vercel antes de gerar QR" é anterior à
  trava de domínio de 21/09.
- **Documentos da Fase 3** (`Cronograma Fase3`, `Estado Fase3`, `Antena no Mac`): a pasta certa mudou
  para `/Users/diogo/Desktop/depin-urbano` (25/09); `registros.json` virou Supabase; carteira do
  cidadão, pausa do auto-refresh do dashboard e rotação de chaves não valem mais.

Cada documento do projeto listado acima tem, no topo, uma nota "⚠️ Nota de 27/09/2026: trechos superados" com os trechos
superados.
