# DePIN Urbano — Fase 3 (Apresentação Presencial, 28/08)

> **Nota de correção:** a primeira versão desses arquivos foi montada em cima de
> uma cópia desatualizada de `app.py`/`dashboard.py`/`abi.json` que você tinha
> me mandado antes. Comparei com o repositório real
> (`github.com/DiogoRi/chaintrack`) e corrigi: o contrato de verdade usa
> `registrarOcorrencia(cid, descricao, lat, lng)` (lat/lng como string, sem
> campo de endereço no contrato), e o `dashboard.py` de vocês já tinha
> auto-refresh de 2s e ajuste automático de zoom (`fit_bounds`) — tudo isso
> foi preservado aqui. Também reparei que `streamlit-autorefresh` era usado
> no dashboard mas nunca tinha entrado no `requirements.txt`; já corrigi.
> **Use os arquivos desta entrega, não os da mensagem anterior.**
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

1. **Antena de verdade (ESP32 + LED via USB serial)** — quando alguém registra uma ocorrência, o app manda um sinal pela porta serial e o LED da antena acende. Quando uma ocorrência é marcada como concluída, um segundo LED acende.
2. **Status manual no dashboard** — cada ocorrência agora tem um status: Recebida → Em andamento → Concluída, alterado manualmente no painel do dashboard.
3. **Token "infinito" (DEPIN)** — ao marcar uma ocorrência como Concluída, se ela tiver uma carteira associada, o sistema minta e envia automaticamente tokens DEPIN pra essa carteira, na Polygon Amoy.
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
   python antena_serial.py
   ```
   Deve aparecer "Antena respondeu: 'ANTENA_PRONTA'" e o LED_REGISTRO piscar 3x.

## Deploy do token DEPIN (uma vez só)

1. Abra [remix.ethereum.org](https://remix.ethereum.org), crie um arquivo novo e cole o conteúdo de `DePinToken.sol`.
2. Compile (o Remix busca o OpenZeppelin sozinho pelo import).
3. Na aba "Deploy & Run", conecte a MetaMask na rede **Polygon Amoy** (mesma carteira que já é dona do contrato de registro da Fase 2) e faça o deploy.
4. Copie o endereço do contrato deployado e cole em `TOKEN_CONTRACT_ADDRESS` no `.env`.
5. Teste o mint manualmente antes da apresentação:
   ```
   python mint_token.py 0xSEU_ENDERECO_DE_TESTE
   ```
   Deve imprimir o hash da transação e um link do Polygonscan. Confira lá se o saldo do token realmente chegou na carteira de teste.

## Rodando tudo

Em terminais separados:
```
streamlit run app.py --server.port 8501        # formulário do cidadão
streamlit run dashboard.py --server.port 8502   # dashboard/admin
```

**Atenção:** evite atualizar o status no dashboard exatamente no mesmo segundo em que alguém está enviando um novo registro pelo app — os dois processos escrevem no mesmo `registros.json`, e uma escrita simultânea pode sobrescrever a outra. Na prática, com o ritmo humano de uma apresentação isso não costuma ser problema, mas vale coordenar durante a demo.

## Checklist antes do dia 28

- [ ] Arduino gravado com o sketch e testado (`python antena_serial.py` responde)
- [ ] Token DEPIN deployado e mint testado manualmente
- [ ] `.env` preenchido em todas as variáveis (Fase 2 + Fase 3)
- [ ] Pelo menos 1 registro de teste enviado pelo app.py com carteira preenchida
- [ ] Esse registro marcado como "Concluída" no dashboard e o token confirmado no Polygonscan
- [ ] Antena com os LEDs fixados na maquete física, testados na posição final (às vezes o fio USB é curto demais — meça a distância até o notebook)
- [ ] Ensaio completo do fluxo ao vivo pelo menos 2 vezes, cronometrado
