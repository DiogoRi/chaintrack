# Prompts úteis — ChainTrack

Biblioteca pessoal de prompts reutilizáveis para trabalhar neste projeto com o
Claude. Este arquivo **não** é uma fonte de verdade do projeto: o `CLAUDE.md`
continua com as regras permanentes de trabalho, o `Fase 5 - Estado atual.md`
(no projeto do claude.ai) é a memória operacional curta do dia a dia, e o
`Fase 5 - Plano de execucao.md` continua sendo o histórico detalhado —
consultado só quando um detalhe específico de uma decisão ou bug antigo for
necessário, não lido nem reescrito por inteiro nas rotinas de abrir/encerrar
(ele já passou de 45 mil tokens; reler e regravar o documento inteiro toda
sessão é caro e foi o que travou a sessão de 27→28/09).

## 1. Iniciar uma nova conversa

```
Estou retomando o projeto DePIN Urbano / ChainTrack.
Antes de fazer qualquer alteração, leia primeiro o `CLAUDE.md` da raiz do projeto e depois leia o documento `Fase 5 - Estado atual.md` (no projeto do claude.ai) para entender o estado atual, as decisões já tomadas e as pendências.
NÃO leia o `Fase 5 - Plano de execucao.md` inteiro — ele é o histórico detalhado. Consulte-o só se precisar de um detalhe específico de uma decisão ou bug antigo que o Estado atual não cobre.
Verifique também os arquivos de código relevantes quando necessário, para confirmar que a documentação corresponde ao que realmente está implementado.
Não altere nenhum arquivo ainda.
Primeiro me diga, de forma resumida:

* Onde o projeto está agora.
* O que já está concluído.
* Quais são as pendências atuais.
* Qual seria o próximo passo recomendado.

Só execute alterações depois da minha confirmação.
```

## 2. Encerrar uma sessão

```
Antes de encerrarmos, atualize o `Fase 5 - Estado atual.md` com tudo o que foi feito nesta sessão e com as pendências que ficaram.
Confira o que realmente foi implementado, testado e publicado, distinguindo essas três situações.
Mantenha o Estado atual curto (2–3 páginas): resuma ou substitua entradas antigas da seção "Últimas atualizações" em vez de só acumular.
Só leia e atualize o `Fase 5 - Plano de execucao.md` (o histórico detalhado) se alguma decisão ou bug importante desta sessão merecer registro permanente e detalhado — não é obrigatório fazer isso em toda sessão. Quando precisar, preserve integralmente o conteúdo existente do Plano e não altere nada além do necessário.
Ao terminar, confirme resumidamente o que foi registrado (e em qual dos dois documentos) e se existe alguma pendência de commit, push, teste ou publicação.
```
