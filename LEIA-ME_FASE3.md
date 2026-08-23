# DePIN Urbano — Fase 3 (Apresentação Presencial, 28/08)

> **Estado atual (23/08) — leia isto primeiro.** A arquitetura evoluiu depois
> que este documento foi escrito. O que vale hoje:
>
> - O app está **publicado em https://chaintrack.streamlit.app** e tem **duas
>   páginas**: o formulário do cidadão (principal) e o Dashboard da Prefeitura
>   (`pages/1_Dashboard_da_Prefeitura.py`). O arquivo `dashboard.py` não existe
>   mais — virou essa página.
> - Rodando localmente, sobe tudo com **um comando só**:
>   `streamlit run app.py` (ou dois cliques em `iniciar_demo.command`).
> - **A antena não é mais acionada pelo app.** Um programa separado,
>   `vigia_antena.py`, observa a blockchain e acende os LEDs. Isso permite que
>   o registro venha da nuvem, de qualquer celular e qualquer rede.
> - **Para tudo sobre a antena, use o `ANTENA_GUIA_RAPHAEL.md`**, que está
>   atualizado. As seções sobre antena aqui embaixo são de referência histórica.

> ⚠️ **Correção importante sobre o contrato (23/08).** Uma versão anterior deste
> documento afirmava que o contrato usava `registrarOcorrencia(cid, descricao,
> lat, lng)` com lat/lng como string. **Isso estava errado** e fez toda transação
> reverter até ser descoberto. A função correta, no contrato realmente publicado
> em `0xd991cBD01c207a546D50798931Ec838417261E7a`, é:
>
> ```
> registrar(string cid, string descricao, string endereco, int256 lat, int256 lng)
> ```
>
> com latitude e longitude como **inteiros multiplicados por 1.000.000**
> (ex: -23.5505 vira -23550500). O `abi.json` do repositório já está correto;
> o `abi_original_fase2.json` guarda a mesma referência.
> Se voltar a aparecer "execution reverted", é o primeiro lugar a conferir —
> rode `python3 diagnostico_registro.py`, que testa isso automaticamente.
>
> **Atualização 21/08:** o Raphael confirmou que a placa é uma **ESP32**
> (não um Arduino Uno). Já corrigi o `arduino/antena_depin.ino` pra usar
> pinos seguros de ESP32 (GPIO2 e GPIO4 — evite GPIO6 a GPIO11, que no
> ESP32 costumam estar ligados à memória flash). A comunicação continua
> sendo por **cabo USB** (a mesma ideia de antes) — o Wi-Fi de 2.4GHz da
> placa é um recurso a mais que ela tem, mas **não precisamos usar agora**;
> ligar por USB é mais simples e mais confiável pra demonstração ao vivo.
> Se sobrar tempo depois da Fase 3, dá pra evoluir pra usar o Wi-Fi, mas
> isso fica de bônus, fora do caminho crítico desta semana.

O que mudou em relação à Fase 2:

1. **Antena de verdade (ESP32 + LED via USB serial)** — o programa `vigia_antena.py` observa a blockchain e acende o LED quando detecta uma ocorrência nova; um segundo LED acende quando detecta uma conclusão. A antena reage ao registro público, não a um comando do app.
2. **Status manual no dashboard** — cada ocorrência agora tem um status: Recebida → Em andamento → Concluída, alterado manualmente no painel do dashboard.
3. **Token "infinito" (CP — Cidadão Participativo)** — ao marcar uma ocorrência como Concluída, se ela tiver uma carteira associada, o sistema minta e envia automaticamente tokens CP pra essa carteira, na Polygon Amoy.
4. **Campo de carteira no formulário** — o cidadão pode (opcionalmente) colar o endereço da sua wallet ao registrar, pra receber o token depois.

## Lista de compras (hardware) — comprar HOJE se possível

A placa ESP32 (o Raphael já tem) dispensa o item "Arduino Uno" abaixo. Como faltam poucos dias, prefira uma loja física de eletrônica (ex: Santa Efigênia em SP) a comprar online, pra garantir que chega a tempo — só se faltar algum item da lista.

- ~~1x Arduino Uno R3~~ — não precisa, já tem a ESP32
- 2x LED (qualquer cor, sugestão: 1 vermelho + 1 verde ou azul) — opcional: o GPIO2 já aciona o LED embutido da própria placa, então dá pra testar sem LED externo nenhum
- 2x resistor de 220Ω a 330Ω (para proteger os LEDs, se forem usar externos)
- 1x protoboard pequena (breadboard)
- ~6 jumpers macho-macho
- 1x cabo USB compatível com a entrada da ESP32 (costuma ser micro-USB ou USB-C, dependendo do modelo)

Se só der pra usar o LED embutido da placa (sem LED externo), sem problema — o sistema funciona só com ele piscando pra "registro recebido"; o "concluída" (GPIO4) simplesmente fica sem efeito visível até ligarem um LED externo nesse pino.

## Como ligar a ESP32

Veja os comentários no topo de `arduino/antena_depin.ino` — resumindo:

- GPIO2 → resistor → LED (perna longa) → LED (perna curta) → GND — **LED_REGISTRO** (esse pino já é o LED azul embutido em muitas placas ESP32 — funciona mesmo sem nada ligado)
- GPIO4 → resistor → LED (perna longa) → LED (perna curta) → GND — **LED_CONCLUIDA**

## Passo a passo para configurar

1. No Arduino IDE, instale o suporte a ESP32 (só na primeira vez): **File → Preferences → Additional Board Manager URLs**, cole `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`, depois vá em **Tools → Board → Boards Manager**, procure "esp32" e instale o pacote da Espressif.
2. Abra `arduino/antena_depin.ino`, em **Tools → Board** selecione **"ESP32 Dev Module"** (ou o nome exato da variante da placa do Raphael, se aparecer uma mais específica), selecione a porta certa, e grave (upload).
3. Descubra o nome da porta serial:
   - Windows: Gerenciador de Dispositivos → Portas (COM e LPT) → algo como "COM3"
   - Mac: no Terminal, rode `ls /dev/cu.*` com a ESP32 plugada
   - Linux: rode `ls /dev/tty*` com a ESP32 plugada (geralmente `/dev/ttyUSB0`)
4. Copie `.env.example` para `.env` e preencha `SERIAL_PORT` com o valor encontrado, além das variáveis que já existiam da Fase 2.
5. Instale as dependências novas: `pip install -r requirements.txt` (inclui `pyserial` agora).
6. Teste a antena isoladamente, sem precisar do Streamlit:
   ```
   python3 antena_serial.py
   ```
   Deve aparecer "Antena respondeu: 'ANTENA_PRONTA'" e o LED_REGISTRO piscar 3x.

## Deploy do token CP — Cidadão Participativo (uma vez só)

1. Abra [remix.ethereum.org](https://remix.ethereum.org), crie um arquivo novo e cole o conteúdo de `CidadaoParticipativoToken.sol`.
2. Compile (o Remix busca o OpenZeppelin sozinho pelo import).
3. Na aba "Deploy & Run", conecte a MetaMask na rede **Polygon Amoy** (mesma carteira que já é dona do contrato de registro da Fase 2) e faça o deploy.
4. Copie o endereço do contrato deployado e cole em `TOKEN_CONTRACT_ADDRESS` no `.env`.
5. Teste a conclusão + mint manualmente antes da apresentação:
   ```
   python3 mint_token.py QmCIDdeTeste123 0xSEU_ENDERECO_DE_TESTE
   ```
   (o primeiro argumento pode ser qualquer texto de teste — na demo de verdade, o dashboard passa o CID real da ocorrência).
   Deve imprimir o hash da transação e um link do Polygonscan. Confira lá se o evento `OcorrenciaConcluida` e o saldo do token realmente chegaram na carteira de teste.

## Testando o fluxo completo sem a antena

Isso é 100% possível e não depende de nenhum hardware — o Raphael pode testar
a ESP32 depois, em paralelo:

1. Rode `streamlit run app.py` (ou abra https://chaintrack.streamlit.app), preencha o formulário (foto, nome, endereço,
   descrição) e cole um endereço de carteira de teste no campo de carteira.
2. Envie — o registro aparece na blockchain (prova original da ocorrência)
   e cai no `registros.json` com status "Recebida".
3. No menu lateral do app, abra o **Dashboard da Prefeitura**, encontre essa
   ocorrência e mude o status pra "Em andamento" (fica só local, não gera
   transação — a prova de existência já saiu no passo 2).
4. Mude para "Concluída" — isso dispara a transação `concluirOcorrencia` de
   verdade na Polygon Amoy (se o `TOKEN_CONTRACT_ADDRESS` já estiver
   configurado), aparecendo o link pro Polygonscan mostrando a conclusão
   e o token enviado juntos. Sem antena nenhuma conectada, o app só avisa
   que o sinal físico não foi enviado — o resto funciona normalmente.

## Rodando tudo

**Na nuvem (recomendado para a demo):** basta abrir https://chaintrack.streamlit.app
em qualquer navegador ou celular. Nada para instalar ou iniciar. Não aciona a antena.

**Localmente (único jeito de acender a antena):**
```
streamlit run app.py
```
ou dois cliques em `iniciar_demo.command`. As duas telas ficam no mesmo app —
use o menu na barra lateral esquerda para alternar entre o formulário e o
Dashboard da Prefeitura.

Para a antena, em paralelo:
```
python3 vigia_antena.py
```
ou dois cliques em `iniciar_antena.command`.

## Checklist antes do dia 28

- [ ] ESP32 gravada com o sketch e testada (`python3 antena_serial.py` responde)
- [ ] Token CP deployado e mint testado manualmente
- [ ] `.env` preenchido em todas as variáveis (Fase 2 + Fase 3)
- [ ] Pelo menos 1 registro de teste enviado pelo app.py com carteira preenchida
- [ ] Esse registro marcado como "Concluída" no dashboard e o token confirmado no Polygonscan
- [ ] Antena com os LEDs fixados na maquete física, testados na posição final (às vezes o fio USB é curto demais — meça a distância até o notebook)
- [ ] `vigia_antena.py` testado: registrar pelo celular e ver o LED acender
- [ ] Decidido se a demo será pela nuvem (robusta, sem antena) ou local (com antena)
- [ ] Ensaio completo do fluxo ao vivo pelo menos 2 vezes, cronometrado
