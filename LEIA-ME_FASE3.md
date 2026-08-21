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

O que mudou em relação à Fase 2:

1. **Antena de verdade (Arduino + LED via USB serial)** — quando alguém registra uma ocorrência, o app manda um sinal pela porta serial e o LED da antena acende. Quando uma ocorrência é marcada como concluída, um segundo LED acende.
2. **Status manual no dashboard** — cada ocorrência agora tem um status: Recebida → Em andamento → Concluída, alterado manualmente no painel do dashboard.
3. **Token "infinito" (DEPIN)** — ao marcar uma ocorrência como Concluída, se ela tiver uma carteira associada, o sistema minta e envia automaticamente tokens DEPIN pra essa carteira, na Polygon Amoy.
4. **Campo de carteira no formulário** — o cidadão pode (opcionalmente) colar o endereço da sua wallet ao registrar, pra receber o token depois.

## Lista de compras (hardware) — comprar HOJE se possível

Como faltam poucos dias, prefira uma loja física de eletrônica (ex: Santa Efigênia em SP) a comprar online, pra garantir que chega a tempo.

- 1x Arduino Uno R3 (ou clone tipo "Uno compatível") — já vem com cabo USB na maioria dos kits, confirme antes de comprar
- 2x LED (qualquer cor, sugestão: 1 vermelho + 1 verde ou azul)
- 2x resistor de 220Ω a 330Ω (para proteger os LEDs)
- 1x protoboard pequena (breadboard)
- ~6 jumpers macho-macho
- Se o Arduino não vier com cabo: 1x cabo USB-A para USB-B

Se só der pra conseguir 1 LED, sem problema — o sistema funciona com só o LED de "registro recebido" (o segundo, de "concluída", simplesmente fica sem efeito até vocês conseguirem o segundo LED).

## Como ligar o Arduino

Veja os comentários no topo de `arduino/antena_depin.ino` — resumindo:

- Pino 8 → resistor → LED (perna longa) → LED (perna curta) → GND — **LED_REGISTRO**
- Pino 9 → resistor → LED (perna longa) → LED (perna curta) → GND — **LED_CONCLUIDA**

## Passo a passo para configurar

1. Abra `arduino/antena_depin.ino` na Arduino IDE, selecione a placa e a porta certa, e grave (upload) no Arduino.
2. Descubra o nome da porta serial:
   - Windows: Gerenciador de Dispositivos → Portas (COM e LPT) → algo como "COM3"
   - Mac: no Terminal, rode `ls /dev/cu.*` com o Arduino plugado
   - Linux: rode `ls /dev/tty*` com o Arduino plugado (geralmente `/dev/ttyUSB0` ou `/dev/ttyACM0`)
3. Copie `.env.example` para `.env` e preencha `SERIAL_PORT` com o valor encontrado, além das variáveis que já existiam da Fase 2.
4. Instale as dependências novas: `pip install -r requirements.txt` (inclui `pyserial` agora).
5. Teste a antena isoladamente, sem precisar do Streamlit:
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
