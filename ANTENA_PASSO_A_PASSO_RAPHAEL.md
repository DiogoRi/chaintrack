# Antena DePIN — passo a passo completo

**Para o Raphael.** Do zero até a antena piscando sozinha quando alguém registra uma ocorrência pelo celular.

Este documento não pula nada e não manda você consultar outra seção. É só ir de cima para baixo. Não precisa saber nada de eletrônica.

**Tempo estimado:** 1 hora e meia na primeira vez, sendo que a maior parte é esperar download.

---

## Antes de começar: o que você está construindo

O sistema tem três partes que **não conversam entre si**:

- **O aplicativo**, que já está no ar em https://chaintrack.streamlit.app. Qualquer pessoa registra uma ocorrência pelo celular.
- **A blockchain**, onde esse registro fica gravado de forma pública e permanente.
- **A antena** (você), que fica lendo a blockchain e acende uma luz quando aparece algo novo.

O aplicativo **não manda nada** para a antena. Não existe fio nem conexão entre eles. A antena descobre sozinha, olhando o dado público.

**O que a placa faz:** recebe uma palavra pelo cabo USB e acende um LED. Quando chega a palavra `REGISTRO`, acende um LED. Quando chega `CONCLUIDA`, acende o outro. Só isso.

Toda a parte de blockchain acontece num programa Python rodando no computador. A placa nem fica sabendo que blockchain existe.

**Você não vai escrever nenhuma linha de código.** Tudo já está pronto no repositório.

---

## Material

- A placa **ESP32** (você já tem)
- **1 cabo USB** que sirva na placa — micro-USB ou USB-C, depende do modelo
- **2 LEDs** — sugestão: 1 vermelho e 1 verde
- **2 resistores** de 220Ω a 330Ω
- **1 protoboard** pequena
- **4 jumpers** macho-macho (fios com pino nas duas pontas)

Os LEDs, resistores, protoboard e jumpers custam uns R$ 20 no total em qualquer loja de eletrônica ou no Mercado Livre.

**Importante:** dá para fazer as Partes 1 a 4 **sem nenhum desses componentes**, só com a placa e o cabo. A placa tem um LED azul embutido que já serve para testar. Se os componentes ainda não chegaram, comece assim mesmo.

---

# PARTE 1 — Instalar o programa no computador

### 1.1

Baixe o Arduino IDE em **https://www.arduino.cc/en/software** e instale.

> O nome engana: "Arduino IDE" é só o nome do programa. Ele grava dezenas de marcas de placa, e a ESP32 é uma delas. Você vai configurar isso no passo 1.3.

### 1.2

Abra o Arduino IDE.

### 1.3

No menu de cima, vá em **File → Preferences**.

Procure o campo escrito **"Additional Board Manager URLs"** (fica na parte de baixo da janela). Cole exatamente isto dentro dele:

```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

Clique em **OK**.

> Isso ensina o programa onde encontrar o suporte para ESP32. É uma vez só, na vida.

### 1.4

Vá em **Tools → Board → Boards Manager**.

Abre uma barra de busca do lado esquerdo. Digite `esp32`.

Vai aparecer um item chamado **"esp32 by Espressif Systems"**. Clique em **Install**.

**Isso demora.** São uns 200 MB. Vá tomar um café.

### 1.5

Quando terminar, feche a janela do Boards Manager.

**Parte 1 concluída.** O computador já sabe conversar com ESP32.

---

# PARTE 2 — Baixar o projeto

### 2.1

Se você já tem a pasta do projeto no computador, pule para a Parte 3.

### 2.2

Se não tem: vá em **https://github.com/DiogoRi/chaintrack**

Clique no botão verde **"Code"** e depois em **"Download ZIP"**.

### 2.3

Descompacte o ZIP num lugar fácil de achar. Sugestão: direto em `C:\chaintrack`.

> Evite pastas com espaço ou acento no nome (`Meus Documentos`, `Área de Trabalho`). Isso costuma dar dor de cabeça depois, na Parte 6.

**Parte 2 concluída.**

---

# PARTE 3 — Plugar a placa e achar a porta

### 3.1

**Antes de plugar a placa**, abra o **Gerenciador de Dispositivos** do Windows.

Como abrir: clique no botão Iniciar, digite `gerenciador de dispositivos`, e abra.

### 3.2

Na lista, procure **"Portas (COM e LPT)"** e clique na setinha para expandir.

Anote o que já está ali. Pode estar vazio, pode ter uma ou duas coisas.

### 3.3

Agora **plugue a placa ESP32** no computador com o cabo USB.

Uma luzinha vermelha (ou o próprio LED da placa) deve acender, mostrando que ela tem energia.

### 3.4

Olhe de novo a lista de **Portas (COM e LPT)**. Deve ter aparecido uma linha nova, tipo:

- `Silicon Labs CP210x USB to UART Bridge (COM3)`
- ou `USB-SERIAL CH340 (COM5)`

**Anote esse `COMx`.** É o número da porta. Você vai precisar dele várias vezes.

### 3.5 — Se NÃO apareceu nada

Duas causas possíveis, nesta ordem:

**Primeiro: teste outro cabo.** Muitos cabos USB são só de carga — têm os fios de energia mas não os de dados. A placa acende, parece viva, e o computador não enxerga nada. Essa é de longe a causa mais comum. Pegue um cabo que você sabe que transfere arquivo (o de um celular que você já usou para passar foto para o PC, por exemplo).

**Segundo: falta o driver.** Olhe o chip retangular pequeno que fica perto do conector USB da placa. Está escrito o modelo nele:

- Se for **CP2102** ou **CP2104**: baixe o driver em https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
- Se for **CH340** ou **CH9102**: procure por "driver CH340 windows" e baixe do site do fabricante (wch.cn)

Instale, desplugue e plugue a placa de novo, e volte ao passo 3.4.

**Parte 3 concluída** quando você tiver o número `COMx` anotado.

---

# PARTE 4 — Gravar o programa na placa

### 4.1

No Arduino IDE, vá em **File → Open**.

Navegue até a pasta do projeto, entre na pasta `arduino`, e abra o arquivo **`antena_depin.ino`**.

### 4.2

Vá em **Tools → Board → esp32** e escolha **"ESP32 Dev Module"**.

> A lista é longa e em ordem alfabética. "ESP32 Dev Module" costuma estar bem no começo.

### 4.3

Vá em **Tools → Port** e escolha o `COMx` que você anotou na Parte 3.

### 4.4

Clique no botão **Upload** — é a setinha `→` no canto superior esquerdo.

Vai aparecer bastante texto na parte de baixo da tela. É normal.

### 4.5 — Se travar em "Connecting........"

Algumas placas ESP32 precisam de ajuda para entrar em modo de gravação:

Quando aparecer `Connecting....`, **segure o botão BOOT** da placa (fica ao lado do conector USB, escrito BOOT ou IO0) até a gravação começar. Aí solte.

### 4.6

No fim deve aparecer algo como:

```
Hard resetting via RTS pin...
Leaving...
```

**Isso é sucesso.** O programa está na placa.

**Parte 4 concluída.**

---

# PARTE 5 — Testar SEM montar nada

Esta é a parte mais importante do documento. Aqui você descobre se está tudo certo, **antes** de mexer com fios.

### 5.1

No Arduino IDE, clique no ícone de **lupa** no canto superior direito. Isso abre o **Serial Monitor**, uma janelinha na parte de baixo.

### 5.2

No canto direito dessa janelinha tem uma caixa de seleção com a velocidade. Mude para **9600 baud**.

> Se estiver em outra velocidade, vai aparecer texto embaralhado tipo `?¿?ÿ`. É só isso, não quebrou nada.

### 5.3

Aperte o botão **EN** (ou **RST**) da placa — é o botão que reinicia.

Deve aparecer no Serial Monitor:

```
ANTENA_PRONTA
```

### 5.4

Agora, na caixinha de digitar do Serial Monitor (em cima, onde está escrito "Message"), digite:

```
REGISTRO
```

e aperte **Enter**.

**O que deve acontecer:**

- O **LED azul da própria placa** pisca 3 vezes e fica aceso
- Aparece no monitor: `OK_REGISTRO`

### 5.5

Digite `RESET` e Enter. O LED apaga e aparece `OK_RESET`.

---

**Se isso funcionou, a parte difícil acabou.** A placa está gravada e respondendo. Todo o resto é fio e configuração.

> Aquele LED azul está ligado num pino chamado **GPIO2**, que já vem soldado de fábrica na maioria das placas ESP32. É por isso que dá para testar sem montar nada.

**Parte 5 concluída.**

---

# PARTE 6 — Montar os LEDs

Se os componentes ainda não chegaram, **pule para a Parte 7**. O sistema funciona com o LED azul da placa.

## 6.0 — O básico, para quem nunca mexeu

**O que é uma protoboard:** é aquela plaquinha branca cheia de furinhos. Ela serve para ligar componentes sem soldar nada. Você só espeta.

**O truque dela:** os furinhos são ligados entre si por dentro, **em fileiras de 5, na vertical**. Ou seja, tudo que você espetar na mesma coluna de 5 furinhos está eletricamente conectado. Colunas diferentes não se falam.

```
        a  b  c  d  e        f  g  h  i  j
   1    ○  ○  ○  ○  ○   |    ○  ○  ○  ○  ○
   2    ○  ○  ○  ○  ○   |    ○  ○  ○  ○  ○
   3    ○  ○  ○  ○  ○   |    ○  ○  ○  ○  ○

        └──ligados──┘         └──ligados──┘
         entre si              entre si
        (linha 1)             (linha 1)

   O canal do meio separa os dois lados.
```

Então: para ligar duas coisas, basta espetar as duas na mesma linha.

**O que é um resistor:** é o componentezinho com listras coloridas. Ele segura a corrente para o LED não queimar. **Não tem lado** — pode espetar em qualquer direção.

**O que é o LED:** é a luzinha. Ele **tem lado** e essa é a única coisa que você precisa acertar:

- A perna **LONGA** é o positivo (chamado ânodo)
- A perna **CURTA** é o negativo (chamado catodo)

Se inverter, ele simplesmente não acende. Não queima, não estraga nada. É só inverter e pronto.

**O que é GND:** é o "negativo", o retorno da corrente. Na placa ESP32 tem vários pinos escritos **GND**. Qualquer um serve.

**O que são GPIO2 e GPIO4:** são pinos da placa, identificados por número. O programa liga e desliga eles. Quando o pino liga, quem estiver espetado nele recebe energia.

## 6.1 — Montagem do primeiro LED (vermelho, "ocorrência registrada")

Faça na ordem:

1. Espete a **placa ESP32 na protoboard**, ou deixe ela ao lado — tanto faz, desde que você consiga alcançar os pinos com os jumpers.

2. Pegue um **resistor**. Espete uma perna dele na **linha 1** da protoboard e a outra perna na **linha 5**. (Qualquer par de linhas serve, desde que sejam diferentes.)

3. Pegue o **LED vermelho**. Espete a perna **LONGA** na **linha 5** — a mesma linha onde está a segunda perna do resistor. Espete a perna **CURTA** na **linha 10**.

4. Pegue um **jumper**. Ligue o pino **GPIO2** da placa até a **linha 1** da protoboard (onde está a primeira perna do resistor).

5. Pegue outro **jumper**. Ligue um pino **GND** da placa até a **linha 10** (onde está a perna curta do LED).

Pronto. O caminho ficou: `GPIO2 → resistor → LED → GND`.

## 6.2 — Montagem do segundo LED (verde, "ocorrência concluída")

Exatamente a mesma coisa, em linhas diferentes da protoboard, e usando o pino **GPIO4** em vez do GPIO2:

`GPIO4 → resistor → LED verde → GND`

## 6.3 — ⚠️ O único erro que estraga a placa

**Não use os pinos GPIO6, GPIO7, GPIO8, GPIO9, GPIO10 nem GPIO11.**

Eles existem fisicamente na placa, mas por dentro estão ligados na memória onde o programa fica guardado. Se você usar, a placa trava.

**Use apenas GPIO2 e GPIO4.** É o que o programa espera.

## 6.4 — Testar a montagem

Volte ao Serial Monitor (Parte 5), digite `REGISTRO` e Enter.

- O LED **vermelho** deve piscar 3 vezes e ficar aceso.

Digite `CONCLUIDA` e Enter.

- O LED **verde** deve acender.

Digite `RESET` e Enter. Os dois apagam.

**Se um LED não acendeu mas apareceu `OK_REGISTRO` na tela:** o LED está invertido. Puxe ele, gire 180 graus, espete de novo. É isso em 90% dos casos.

**Se apareceu `OK_REGISTRO` e nem o LED azul da placa acendeu:** aí é o jumper solto ou espetado na linha errada. Confira se cada peça está na linha que a anterior termina.

**Parte 6 concluída.**

---

# PARTE 7 — Fazer a antena reagir à blockchain sozinha

Aqui a antena para de depender de você digitar comandos e passa a reagir ao que acontece na internet.

## 7.1 — Instalar o Python

Se você já tem Python instalado, pule para 7.2.

Baixe em **https://www.python.org/downloads/** e instale.

⚠️ **Na primeira tela do instalador, marque a caixinha "Add Python to PATH"** antes de clicar em Install. Se esquecer, nada nas próximas etapas vai funcionar.

## 7.2 — Abrir o Prompt de Comando na pasta certa

1. Abra a pasta do projeto no Explorador de Arquivos (`C:\chaintrack`, ou onde você descompactou).
2. Clique na **barra de endereço** lá em cima (onde aparece o caminho da pasta).
3. Apague o que está escrito, digite `cmd` e aperte **Enter**.

Abre uma janela preta já dentro da pasta certa. É nela que você vai digitar os próximos comandos.

## 7.3 — Instalar as bibliotecas

Na janela preta, digite e dê Enter:

```
pip install -r requirements.txt
```

Demora uns minutos. Vai passar bastante texto. No fim deve aparecer `Successfully installed...`.

## 7.4 — Criar o arquivo de configuração

Este arquivo diz ao programa onde estão os contratos e em qual porta está a placa.

**Você NÃO precisa de nenhuma senha, chave privada ou credencial.** O programa só **lê** a blockchain — não assina nada, não gasta nada. Tudo de que ele precisa é informação pública.

Na mesma janela preta, digite:

```
notepad .env
```

Ele vai perguntar se quer criar o arquivo. Diga **Sim**.

Cole exatamente isto dentro:

```
CONTRACT_ADDRESS=0xd991cBD01c207a546D50798931Ec838417261E7a
TOKEN_CONTRACT_ADDRESS=0x54FD1b00D3B08c9fFFa3e6A20C9cb798aB3066F3
RPC_URL=https://polygon-amoy.drpc.org
SERIAL_PORT=COM3
BAUD_RATE=9600
```

**Troque o `COM3` pelo número que você anotou na Parte 3.**

Salve (Ctrl+S) e feche o Bloco de Notas.

> **Cuidado com o Bloco de Notas:** ele às vezes salva como `.env.txt` em vez de `.env`. Abrindo pelo comando `notepad .env` como acima, isso não acontece. Se ainda assim der problema, confira o nome do arquivo na pasta.

## 7.5 — Ligar o vigia

Com a placa plugada, digite na janela preta:

```
python vigia_antena.py
```

Deve aparecer:

```
Conectado à rede 80002 (80002 = Polygon Amoy)

Testando a antena...
✅ Antena respondeu — o LED deve ter piscado.

Ponto de partida: 14 ocorrências já registradas, 3 CP em circulação.
Verificando a cada 3 segundos.

>>> Pronto. Pode registrar pelo celular. (Control+C para encerrar)
```

**E o LED deve ter piscado**, porque ele testa a antena logo ao iniciar.

## 7.6 — O teste final

Com o programa rodando na janela preta:

1. Pegue o **celular** e abra **https://chaintrack.streamlit.app**
2. Registre uma ocorrência qualquer — pode ser uma foto do chão mesmo. **Preencha o campo de carteira** (pode ser este endereço: `0x54FD1b00D3B08c9fFFa3e6A20C9cb798aB3066F3`)
3. Envie.

Em uns 10 a 30 segundos, na janela preta aparece:

```
📍 NOVA OCORRÊNCIA detectada na blockchain (total: 15). Acendendo a antena...
```

**E o LED vermelho acende.**

Repare no que acabou de acontecer: o celular estava no 4G, o aplicativo está num servidor em outro país, e não existe nenhuma conexão entre eles e a sua placa. A antena descobriu sozinha, lendo o dado público.

**É isso que a gente vai mostrar para a banca.**

Para parar o programa: aperte **Control + C** na janela preta.

---

## Se algo der errado na Parte 7

| O que aparece | O que fazer |
|---|---|
| `could not open port COM3` | A porta está errada no `.env`, ou o Arduino IDE está com o Serial Monitor aberto segurando a porta. **Feche o Serial Monitor** e tente de novo |
| `⚠️ Antena não respondeu` | Cabo ou porta. O programa continua funcionando e avisando na tela, só não acende luz |
| `python não é reconhecido` | Faltou marcar "Add Python to PATH" na instalação. Reinstale o Python marcando a caixinha |
| `Faltam variáveis no .env` | O arquivo `.env` não foi salvo com o nome certo, ou foi salvo como `.env.txt` |
| Registrei e não acendeu | O vigia precisa estar rodando **antes** do registro. Ele usa o momento em que iniciou como ponto de partida. Reinicie e registre de novo |
| `Falha na leitura inicial` | O servidor de blockchain caiu. Troque a linha do `.env` para `RPC_URL=https://polygon-amoy-bor-rpc.publicnode.com` |

---

## Uma coisa importante

**Se a antena não funcionar no dia, a apresentação acontece do mesmo jeito.**

O aplicativo, o dashboard, o registro na blockchain e o envio do token funcionam sem ela. A gente perde a luz acendendo, que é bonito, mas não perde o projeto. Isso foi construído de propósito: a antena nunca pode ser o motivo de a demonstração travar.

Mas seria ótimo ter.

**Se você fizer só uma coisa hoje, faça as Partes 1 a 5.** São uns 40 minutos, quase tudo esperando download, e no fim você já sabe se a placa funciona. O resto pode ser amanhã.

O pior cenário é descobrir na véspera que o cabo não presta.

---

## Resumo de tudo, em uma tela

1. Instalar Arduino IDE, colar o link do ESP32, instalar o pacote
2. Baixar o projeto do GitHub
3. Plugar a placa, anotar o `COMx` no Gerenciador de Dispositivos
4. Abrir `arduino/antena_depin.ino`, escolher ESP32 Dev Module e a porta, clicar Upload
5. Serial Monitor a 9600, digitar `REGISTRO`, ver o LED azul piscar
6. Montar: `GPIO2 → resistor → LED (perna longa) → LED (perna curta) → GND`, e igual com GPIO4
7. Instalar Python, `pip install -r requirements.txt`, criar o `.env`, rodar `python vigia_antena.py`, registrar pelo celular

**Contatos úteis:**
- App: https://chaintrack.streamlit.app
- Repositório: https://github.com/DiogoRi/chaintrack
- Ver as transações: https://amoy.polygonscan.com
