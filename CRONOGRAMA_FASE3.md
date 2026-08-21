# Cronograma — Fase 3 DePIN Urbano (21/08 → 28/08)

Apresentação presencial na FIAP: **28/08/2026**. Faltam 7 dias a partir de hoje (21/08).

## Sexta 21/08 (hoje) — comprar e preparar
- Comprar hardware (Arduino Uno, 2 LEDs, resistores, protoboard, jumpers) — de preferência loja física.
- Deploy do contrato `DePinToken.sol` no Remix (Polygon Amoy), igual ao fluxo já feito na Fase 2.
- Preencher o `.env` com `TOKEN_CONTRACT_ADDRESS`.

## Sábado 22/08 e Domingo 23/08 — hardware + integração
- Gravar o sketch `antena_depin.ino` no Arduino e testar com `python antena_serial.py`.
- Rodar `app.py` localmente e confirmar que o campo de carteira aparece e valida corretamente.
- Testar `mint_token.py` manualmente com uma carteira de teste; confirmar recebimento no Polygonscan.

## Segunda 24/08 — ponta a ponta
- Rodar o fluxo completo pelo menos uma vez: registrar ocorrência com carteira → antena acende → dashboard mostra "Recebida" → marcar "Concluída" → token chega na carteira → segundo LED acende.
- Anotar qualquer travamento e corrigir.

## Terça 25/08 — maquete física
- Fixar o Arduino e os LEDs dentro/na maquete da antena (a que já está sendo impressa).
- Testar a distância do cabo USB até o notebook na posição real da apresentação.
- Carregar de 3 a 5 registros de contingência no `registros.json` (com fotos reais, sem rostos/placas), caso a rede falhe no dia.

## Quarta 26/08 — ensaio 1
- Ensaio completo da apresentação com o hardware real, cronometrado.
- Ajustar o que travar ou demorar demais.

## Quinta 27/08 — ensaio 2 + buffer
- Segundo ensaio completo.
- Dia de reserva para qualquer imprevisto técnico (peça de hardware quebrada, contrato com bug, etc.).
- Confirmar com a coordenação da FIAP o formato exato da apresentação do dia 28 (tempo disponível, se é só demo ou também slides).

## Sexta 28/08 — apresentação presencial
- Chegar com antecedência para testar a conexão USB e a rede Wi-Fi/dados no local.
- Ter o `registros.json` de contingência pronto, caso algo falhe ao vivo.

## Pendências em aberto para além da Fase 3 (já mapeadas desde a Fase 2)
- Veracidade dos dados (validação de EXIF, validação cruzada).
- Sustentabilidade do modelo de tokens em produção (hoje é "infinito" só para a demo).
- Privacidade/LGPD — manter o cuidado de não usar fotos com rostos/placas.
- Evolução da antena para LoRaWAN real (fora do escopo da Fase 3).
- Conexão de carteira real via MetaMask/WalletConnect (hoje é um campo de texto simples).
