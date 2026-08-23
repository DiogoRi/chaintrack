# Guia da Antena — ESP32

**Para o Raphael.** Este documento é o guia completo para conectar a antena física ao sistema. Tudo do lado do software já está pronto e testado; falta só a placa.

> Se você está lendo isto através do Claude analisando o repositório: este arquivo é a fonte de verdade sobre a antena. O `LEIA-ME_FASE3.md` é mais antigo e descreve uma arquitetura anterior em alguns trechos.

---

## 1. O que a antena faz no sistema (leia antes de mexer no hardware)

A arquitetura mudou em 23/08 e é importante entender **por quê**, porque muda o que você precisa fazer.

**Como era:** o aplicativo mandava um comando pela USB dizendo "acende o LED". Problema: o app agora está publicado na nuvem (https://chaintrack.streamlit.app), rodando num servidor remoto. Nenhum servidor remoto tem cabo USB ligado à maquete — a antena nunca acenderia na demo.

**Como é agora:** existe um programa separado, o **`vigia_antena.py`**, que roda no notebook do Diogo durante a apresentação. Ele fica consultando a blockchain a cada 3 segundos e acende os LEDs quando detecta atividade:

| O que ele observa na blockchain | Quando muda | LED |
|---|---|---|
| `total()` no contrato de ocorrências | Alguém registrou uma ocorrência nova | GPIO2 (LED_REGISTRO) |
| `totalSupply()` no contrato do token CP | Uma ocorrência foi concluída e o token foi enviado | GPIO4 (LED_CONCLUIDA) |

**Por que isso importa pro pitch:** a antena não sabe quem registrou nem de onde veio o registro. Ela só lê o dado público da blockchain e reage — que é literalmente o que um nó de uma rede descentralizada faz. É um argumento forte para a banca, e responde à pergunta clássica *"isso não poderia ser um banco de dados comum?"*.

**O que isso significa pra você:** o sketch da ESP32 **não precisa mudar**. Ele continua só ouvindo comandos pela serial. Quem mudou foi quem envia os comandos.

---

## 2. Material necessário

A placa ESP32 você já tem. O resto:

- 2x LED (sugestão: 1 vermelho para "registro", 1 verde para "concluída")
- 2x resistor de 220Ω a 330Ω
- 1x protoboard pequena
- ~6 jumpers macho-macho
- 1x cabo USB compatível com a placa (micro-USB ou USB-C, depende do modelo)

**Dá pra testar sem nenhum LED externo:** o GPIO2 é o LED azul embutido na maioria das placas ESP32 Dev Module. Ele pisca sozinho no comando REGISTRO. Use isso para validar tudo antes de montar o circuito.

---

## 3. Ligação

```
GPIO2  ──[resistor 220-330Ω]──▶|── GND     LED_REGISTRO   (ocorrência registrada)
GPIO4  ──[resistor 220-330Ω]──▶|── GND     LED_CONCLUIDA  (concluída + token enviado)
```

A perna **longa** do LED (ânodo) vai para o lado do resistor; a **curta** (catodo) vai para o GND.

⚠️ **Não use GPIO6 a GPIO11.** No ESP32 esses pinos estão ligados internamente à memória flash — usá-los como E/S trava a placa. Foi por isso que os pinos originais do sketch (8 e 9, pensados para Arduino Uno) foram trocados.

---

## 4. Gravar o sketch

O arquivo é **`arduino/antena_depin.ino`**, na raiz do repositório.

**4.1** No Arduino IDE, só na primeira vez: **File → Preferences → Additional Board Manager URLs**, cole:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

**4.2** **Tools → Board → Boards Manager**, procure `esp32`, instale o pacote da Espressif.

**4.3** Abra `arduino/antena_depin.ino`.

**4.4** **Tools → Board** → selecione **"ESP32 Dev Module"** (ou a variante exata da sua placa, se aparecer uma mais específica).

**4.5** **Tools → Port** → selecione a porta da placa.

**4.6** Clique em Upload.

**4.7** Abra o **Serial Monitor** a **9600 baud**. Ao reiniciar a placa, deve imprimir:
```
ANTENA_PRONTA
```

**4.8** Ainda no Serial Monitor, digite `REGISTRO` e dê Enter. O LED deve piscar 3x e ficar aceso, e a placa responde `OK_REGISTRO`.

Se chegou aqui, **o hardware está pronto**. O resto é configuração no notebook.

---

## 5. Comandos que o sketch entende

Uma linha por comando, terminada em `\n`:

| Comando | Efeito | Resposta |
|---|---|---|
| `REGISTRO` | Pisca o LED_REGISTRO 3x e deixa aceso | `OK_REGISTRO` |
| `CONCLUIDA` | Acende o LED_CONCLUIDA | `OK_CONCLUIDA` |
| `RESET` | Apaga os dois LEDs (usar entre um ensaio e outro) | `OK_RESET` |

---

## 6. Configurar o computador

> **Windows:** use `python` (ou `py`) nos comandos, não `python3`. Os arquivos
> `.command` são atalhos de Mac e não funcionam no Windows — rode os comandos
> direto no Prompt de Comando ou no PowerShell, dentro da pasta do projeto.

### 6.0 — O `.env` do Raphael (não precisa de senha nenhuma)

Você **não precisa** da `PRIVATE_KEY` nem das chaves da Pinata. O
`vigia_antena.py` apenas **lê** a blockchain: não assina transação, não gasta
gas, não sobe nada pro IPFS. Tudo que ele precisa é público.

Crie um arquivo chamado `.env` na raiz do projeto com exatamente isto:

```
CONTRACT_ADDRESS=0xd991cBD01c207a546D50798931Ec838417261E7a
TOKEN_CONTRACT_ADDRESS=0x54FD1b00D3B08c9fFFa3e6A20C9cb798aB3066F3
RPC_URL=https://polygon-amoy.drpc.org
SERIAL_PORT=COM3
BAUD_RATE=9600
```

Trocando `COM3` pela porta real da sua placa (passo 6.1).

> ⚠️ **Windows / Bloco de Notas:** ao salvar, ele costuma criar `.env.txt` em vez
> de `.env`. No diálogo de salvar, escolha "Tipo: Todos os arquivos" e escreva o
> nome entre aspas: `".env"`. Ou crie pelo PowerShell:
> `New-Item .env -ItemType File`

### 6.1 — Descobrir a porta serial

Com a ESP32 plugada:

- **Windows:** abra o **Gerenciador de Dispositivos** → **Portas (COM e LPT)**. Com a placa plugada aparece algo como `Silicon Labs CP210x (COM3)` ou `USB-SERIAL CH340 (COM5)`. O que interessa é o `COMx`. Truque: olhe a lista antes e depois de plugar — a linha que aparecer é a sua.
- **Mac:** `ls /dev/cu.*` — procure algo como `/dev/cu.usbserial-0001`
- **Linux:** `ls /dev/tty*` — geralmente `/dev/ttyUSB0`

> **Se nenhuma porta aparecer**, falta o driver USB-serial. Veja no chip da placa
> (perto do conector USB) se é **CP2102** (driver da Silicon Labs) ou **CH340**,
> instale o driver correspondente e reconecte.
>
> **Também pode ser o cabo.** Muito cabo USB é só de carga, sem os fios de dados.
> Se a placa acende mas não aparece porta nenhuma, teste outro cabo antes de
> caçar driver — é a causa mais comum e a mais fácil de descartar.

### 6.2 — Instalar as dependências

**Windows:**
```
pip install -r requirements.txt
```

**Mac/Linux:**
```
pip3 install -r requirements.txt
```

---

## 7. Testar

### Teste 1 — só a antena, sem blockchain

**Windows:** `python antena_serial.py`
**Mac/Linux:** `python3 antena_serial.py`

Esperado:
```
Antena respondeu: 'ANTENA_PRONTA'
```
e o LED_REGISTRO piscando 3x.

Se falhar aqui, o problema é cabo, porta ou driver — não é o sistema.

### Teste 2 — a antena reagindo à blockchain (o teste de verdade)

**Windows:** `python vigia_antena.py`
**Mac/Linux:** `python3 vigia_antena.py` (ou dois cliques em `iniciar_antena.command`)

Ele testa a antena ao iniciar e depois fica observando. Com ele rodando:

1. Registre uma ocorrência em https://chaintrack.streamlit.app (de qualquer celular, qualquer rede — pode ser pelo 4G)
2. Em poucos segundos: `📍 NOVA OCORRÊNCIA detectada` + **LED_REGISTRO acende**
3. No app, vá em "Dashboard da Prefeitura" e marque a ocorrência como **Concluída**
4. Em poucos segundos: `✅ CONCLUSÃO detectada` + **LED_CONCLUIDA acende**

> ⚠️ O LED de conclusão só acende se a ocorrência tiver uma **carteira preenchida** no momento do registro. Sem carteira, nenhum token é criado, e é a criação do token que o vigia detecta. Na demo, sempre preencher a carteira.

---

## 8. Se der problema

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `could not open port` | Porta errada no `.env`, cabo só de energia (sem dados), ou driver faltando | Rode `ls /dev/cu.*` com a placa plugada e ajuste `SERIAL_PORT`; teste outro cabo |
| Nenhuma porta aparece no Mac | Driver USB-serial ausente | Instale o driver CP2102 (Silicon Labs) ou CH340, conforme o chip da placa |
| `ANTENA_PRONTA` não aparece | Sketch não gravado, ou baud rate diferente de 9600 | Regrave e confirme 9600 no Serial Monitor |
| LED não acende, mas responde `OK_REGISTRO` | LED invertido ou resistor mal encaixado | Inverta o LED (perna longa no lado do resistor) |
| A placa trava ao ligar | Uso de GPIO6-GPIO11 | Use apenas GPIO2 e GPIO4 |
| O vigia diz "antena não respondeu" mas detecta os eventos | Só o cabo/porta estão errados; a lógica está certa | Corrija `SERIAL_PORT` — nada mais precisa mudar |
| O vigia não detecta nada | RPC fora do ar | Troque o `RPC_URL` no `.env` (ver seção 9) |

---

## 9. Referências rápidas

- **App publicado:** https://chaintrack.streamlit.app (republica sozinho a cada `git push`)
- **Contrato de ocorrências:** `0xd991cBD01c207a546D50798931Ec838417261E7a`
- **Contrato do token CP:** `0x54FD1b00D3B08c9fFFa3e6A20C9cb798aB3066F3`
- **Rede:** Polygon Amoy (chain id 80002)
- **RPC em uso:** `https://polygon-amoy.drpc.org`
  (o oficial `rpc-amoy.polygon.technology` caiu e derrubou tudo uma vez; alternativa: `https://polygon-amoy-bor-rpc.publicnode.com`)
- **Explorador:** https://amoy.polygonscan.com

### Arquivos que importam pra antena

| Arquivo | O que faz |
|---|---|
| `arduino/antena_depin.ino` | O sketch que roda na ESP32 |
| `antena_serial.py` | Conversa com a placa pela USB. Nunca lança exceção: se a antena não estiver lá, avisa e segue |
| `vigia_antena.py` | Observa a blockchain e dispara os sinais. É o que roda na apresentação |
| `iniciar_antena.command` | Atalho de dois cliques para o vigia |
| `.env` | Onde fica o `SERIAL_PORT` e os endereços dos contratos. **Não está no GitHub** — mas veja a seção 6.0: o seu não precisa de senha nenhuma, dá pra criar do zero |

---

## 10. Montagem na maquete — pontos de atenção

- **Meça o alcance do cabo USB** até onde o notebook vai ficar na mesa da FIAP. Cabo curto demais já estragou muita demo.
- **Fixe os LEDs de forma visível** para quem está sentado na banca, não só para quem apresenta.
- **Teste na posição final**, com tudo montado — não só na bancada.
- Leve um **cabo USB reserva**.
- Se sobrar tempo: teste com a placa alimentada e o notebook em modo de bateria, que é como vai estar no dia.
