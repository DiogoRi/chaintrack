"""
Sobre o Projeto — DePIN Urbano, Fase 3

Terceira página do app. Serve a três públicos ao mesmo tempo:

1. A banca avaliadora, que em 5 minutos de apresentação não consegue ver
   tudo — aqui ficam a arquitetura, as tecnologias e os endereços dos
   contratos, disponíveis para conferência.
2. Quem apresenta: se der branco, esta página tem a estrutura do que
   precisa ser dito, na ordem certa.
3. Qualquer pessoa que encontrar o app publicado na internet e não souber
   do que se trata.

É só conteúdo: não lê nem grava nada, não acessa a blockchain.
"""

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tema_visual import aplicar_tema  # noqa: E402

st.set_page_config(
    page_title="Sobre o Projeto — DePIN Urbano",
    page_icon="📖",
    initial_sidebar_state="expanded",
)
aplicar_tema()

CONTRATO_OCORRENCIAS = "0xd991cBD01c207a546D50798931Ec838417261E7a"
CONTRATO_TOKEN = "0x54FD1b00D3B08c9fFFa3e6A20C9cb798aB3066F3"
EXPLORADOR = "https://amoy.polygonscan.com/address"

# Título com tamanho próprio (menor que o do dashboard) para caber numa
# linha só, e com espaço definido antes do subtítulo — a classe
# 'frase-impacto' usa margem negativa, que aqui colaria os dois.
st.markdown("<p class='titulo-sobre'>📖 Sobre o projeto</p>",
            unsafe_allow_html=True)
st.markdown("<p class='subtitulo-sobre'>Sistema DePIN para monitoramento "
            "urbano</p>", unsafe_allow_html=True)

st.markdown("""
Quando um cidadão registra um buraco na calçada, um poste apagado, um
vazamento ou um ruído que não deixa a vizinhança dormir, esse pedido
costuma desaparecer dentro de um sistema fechado. Não há como saber se ele
foi recebido, se está sendo tratado, nem provar depois que ele existiu.

**Este projeto torna esse registro público, permanente e auditável, e
recompensa quem contribui.**
""")

st.markdown("### Como funciona")

st.markdown("""
1. **O cidadão registra** uma ocorrência pelo celular: foto, descrição e endereço.
2. **A foto vai para o IPFS** (*InterPlanetary File System*, um sistema
   distribuído de arquivos) e recebe um código calculado a partir da própria
   imagem. Se a foto for trocada, o código muda e a alteração fica evidente.
3. **Os dados vão para a blockchain** (Polygon Amoy). A partir daí ninguém
   pode apagar ou alterar o registro: nem a prefeitura, nem quem atende as
   ocorrências, nem quem desenvolveu o sistema.
4. **A antena física observa a blockchain** e acende ao detectar o novo
   registro. Ela não é avisada pelo aplicativo: lê o contrato por conta
   própria. É essa independência que a torna um nó da rede, e não um
   acessório do sistema.
5. **O município acompanha** pelo painel: Recebida → Em andamento → Concluída.
   Ao encaminhar a ocorrência a uma equipe, começa a correr um prazo de
   execução, e fica registrado qual setor ficou responsável.
6. **O cidadão acompanha** pelo número de protocolo, sem precisar de login.
   Ele vê a situação, a equipe responsável, a data prevista de conclusão e
   pode enviar mensagens complementares.
7. **Ao concluir**, uma única operação registra publicamente o atendimento e
   envia os tokens ao cidadão. As duas coisas ficam inseparáveis.
""")

st.markdown("### Prazo e responsabilidade")

st.markdown("""
Registrar não basta: o que a população cobra é previsibilidade. Por isso cada
ocorrência carrega, além da situação, **quem é o responsável e até quando**.

O prazo só começa a correr quando a ocorrência é encaminhada a uma equipe.
Antes disso não há responsável designado, e um prazo seria fictício. A partir
do encaminhamento são **dez dias úteis** por padrão, ajustáveis caso a caso:
recolocar uma lâmpada não leva o mesmo tempo que recuperar uma calçada
inteira.

O detalhe que muda tudo: **a data de abertura está na blockchain.** O
município pode atualizar a situação e até revisar o prazo, mas não pode fazer
a ocorrência ter entrado depois do que entrou. O relógio corre contra um marco
que não pertence a quem é cobrado por ele.
""")

st.markdown("### Arquitetura em três camadas")

st.markdown("""
| Camada | Função |
| --- | --- |
| **Coleta** | Interface web acessada pelo celular, onde o cidadão envia foto, descrição e localização, e depois acompanha o atendimento pelo protocolo. |
| **Rede DePIN (antena)** | Nó físico que observa a blockchain por conta própria e sinaliza a atividade da rede. Nesta fase representa o nó; a evolução é transportar o registro por rádio de longo alcance (LoRaWAN). |
| **Armazenamento híbrido** | A imagem fica no IPFS; para a blockchain vão apenas os dados do registro (o código da imagem, o endereço, a data). Guardar a foto inteira na blockchain seria caro e desnecessário. |
""")

st.markdown("### Por que DePIN")

st.markdown("""
**DePIN** — *Decentralized Physical Infrastructure Network* — descreve redes
em que a infraestrutura física não pertence a uma empresa central, e sim aos
próprios participantes, que são remunerados por mantê-la.

Aqui isso aparece em duas frentes. O cidadão é **quem fiscaliza**: são os
olhos dele que encontram o problema, e o celular dele que registra. E o
cidadão é também **quem sustenta a rede**: as antenas ficam espalhadas pela
cidade, operadas por moradores, e não numa central da prefeitura.

É essa dupla função que separa o modelo de um canal de denúncias comum. Não
existe um dono da rede a quem pedir permissão.
""")

st.markdown("### O incentivo")

st.markdown("""
Ao ter sua ocorrência resolvida, o cidadão recebe o token **CP — Cidadão
Participativo**, na proporção de um token por ocorrência atendida. Assim, o
saldo de tokens mostra quantas vezes aquela pessoa já ajudou a cidade.

A emissão é ilimitada e ocorre **somente** quando um problema é resolvido.
Não há pré-venda, reserva nem distribuição inicial: é um crédito cívico,
não um ativo especulativo. A aplicação prevista é o uso em serviços e
benefícios municipais.
""")

st.markdown("### Privacidade")

st.markdown("""
**O nome do cidadão não vai para a blockchain.** Foi uma decisão de projeto,
não uma limitação técnica: dado pessoal em registro imutável e público
conflita com a **LGPD** (*Lei Geral de Proteção de Dados*), inclusive com o
direito à exclusão.

O vínculo entre a ocorrência e quem a registrou é feito pelo endereço da
carteira, que é pseudônimo. O nome permanece apenas no sistema da
prefeitura, onde pode ser corrigido ou apagado.
""")

st.markdown("### Registros públicos")

st.markdown(f"""
Qualquer pessoa pode conferir os contratos, a qualquer momento:

- **Contrato de ocorrências:** [`{CONTRATO_OCORRENCIAS}`]({EXPLORADOR}/{CONTRATO_OCORRENCIAS})
- **Contrato do token CP:** [`{CONTRATO_TOKEN}`]({EXPLORADOR}/{CONTRATO_TOKEN})
- **Rede:** Polygon Amoy (rede de testes)
- **Código-fonte:** [github.com/DiogoRi/chaintrack](https://github.com/DiogoRi/chaintrack)
""")

st.markdown("### Tecnologias")

st.markdown("""
| Camada | Tecnologia |
| --- | --- |
| Interface | Python + Streamlit |
| Armazenamento de imagens | IPFS, via Pinata |
| Blockchain | Polygon Amoy, contratos em Solidity |
| Integração | web3.py |
| Hardware | ESP32, comunicação por USB serial |
| Mapa | Folium / OpenStreetMap |
""")

st.markdown("### O que é protótipo e o que seria produção")

st.markdown("""
Este é um protótipo funcional, e algumas simplificações foram escolhas
conscientes, não descuidos. Vale dizer quais são e o que mudaria numa versão
de produção.

| Simplificação atual | Por que agora | O que mudaria em produção |
| --- | --- | --- |
| A lista de ocorrências fica num arquivo local | Basta para demonstrar o fluxo, e a prova que importa já está na blockchain | Banco de dados, com histórico de atendimento e backup |
| O painel da prefeitura não exige login por padrão | Facilita a demonstração ao vivo | Login por servidor, com registro de quem alterou cada status |
| Uma única carteira assina as operações | Simplifica o protótipo | Separação de papéis e assinatura múltipla para emitir tokens |
| O contrato não impede recompensar a mesma ocorrência duas vezes | Não acontece no uso normal do painel | Trava no próprio contrato, marcando cada ocorrência já paga |
| Rede de testes (Polygon Amoy) | Permite testar sem custo real | Rede principal, com custo por transação previsto no orçamento |
| O setor responsável é escolhido à mão | A lista de setores basta para demonstrar | Encaminhamento automático pelo tipo de ocorrência e pelo endereço, como fazem as subprefeituras |
| O prazo não notifica ninguém | O painel já destaca o que venceu | Aviso por e-mail ou SMS ao cidadão e ao setor, como no SP156 |

O ponto central é que **nenhuma dessas simplificações afeta a garantia
principal do projeto**: a ocorrência registrada na blockchain continua
pública, permanente e verificável por qualquer pessoa.
""")

st.markdown("### Evolução do projeto")

st.markdown("""
| Fase | Entrega |
| --- | --- |
| **Fase 1** | Concepção: o problema, a proposta e a arquitetura pretendida. |
| **Fase 2** | Primeiro protótipo: coleta, IPFS, prova on-chain e dashboard com mapa, demonstrados em vídeo. |
| **Fase 3** | Sistema integrado e funcionando ao vivo: aplicativo publicado, acompanhamento pelo cidadão, prazo com responsável, token de recompensa emitido automaticamente e antena física reagindo à blockchain. |
| **Fase 4** *(projetada)* | Confirmação da obra pelo cidadão que passa pelo local, com foto e localização, também recompensada. Identidade verificada por gov.br ou CPF. |
""")

st.markdown("### O próximo passo: quem confirma que a obra foi feita?")

st.markdown("""
O sistema atual tem um ponto aberto, e vale nomeá-lo com clareza: **quem
declara que o serviço foi concluído é o próprio município** — a mesma parte
que está sendo cobrada pelo prazo. A blockchain garante que a data de abertura
não pode ser adulterada, mas não garante que a árvore foi de fato retirada.

A Fase 4 fecha esse ciclo. A ideia é simples: **quem confirma é quem passa
pelo local.**

Ao concluir uma ocorrência, ela entra numa lista aberta de confirmação por
alguns dias. Qualquer cidadão que esteja ali pode dizer se o serviço foi
mesmo feito, e recebe token por isso. O cidadão deixa de ser apenas quem
reporta e passa a ser **quem audita**.
""")

st.markdown("""
| Regra | Por que existe |
| --- | --- |
| **Foto obrigatória** | Sem ela a confirmação pode ser feita de casa. A foto é o que prova que alguém esteve no local. |
| **Localização exigida, com raio de tolerância** | O aparelho precisa estar a poucas dezenas de metros da ocorrência. O raio existe porque o GPS do celular erra: sem tolerância, quem está de fato na esquina certa seria recusado. |
| **Uma confirmação por pessoa** | Impede que a mesma pessoa multiplique a recompensa confirmando a mesma obra várias vezes. |
| **Janela de alguns dias** | Concentra as confirmações no período em que o serviço ainda pode ser conferido, e dá previsibilidade a quem executou. |
""")

st.markdown("""
Isso muda o desenho do incentivo, e essa é a parte mais importante.

Recompensar apenas quem **relata** cria um incentivo torto: em tese, alguém
poderia danificar algo para depois registrar. Recompensar também quem
**confirma a resolução** desloca parte do valor para o lado construtivo da
rede, e cria um segundo grupo de participantes cujo interesse é que o
problema seja de fato resolvido.
""")

st.markdown("### Por que a localização vale diferente em cada momento")

st.markdown("""
A mesma informação — onde a pessoa está — serve a dois propósitos distintos,
e por isso o sistema a trata de dois jeitos.

**Ao registrar uma ocorrência, a localização ajuda mas não trava.** O ganho
principal aqui nem é comprovar presença: é **acabar com a digitação do
endereço**, que hoje é a parte mais cansativa do formulário. O aplicativo
preenche sozinho e a pessoa só corrige se for preciso.

E ela não pode ser obrigatória nesse momento. Quem viu um buraco de manhã e
só foi registrar à noite, em casa, seria bloqueado — e essa pessoa está
fazendo exatamente o que o sistema quer que ela faça.

**Ao confirmar uma obra, a localização é obrigatória.** Aqui a afirmação é
sobre o **estado atual** do lugar: dizer que o serviço foi feito só significa
alguma coisa se quem diz está vendo. É a diferença entre relatar uma lembrança
e atestar o presente.
""")

st.markdown("### O que este sistema não é")

st.markdown("""
**Não é canal de emergência.** Vazamento de gás, fio de energia caído,
princípio de incêndio, risco imediato a alguém: nesses casos a pessoa deve
ligar para os bombeiros ou para a concessionária **na hora**, e não abrir uma
ocorrência aqui. Um registro que espera atendimento em dias não serve para
o que precisa de minutos, e o aplicativo deixa isso claro para quem usa.

O terreno deste projeto é o da zeladoria urbana: buraco na via, calçada
quebrada, poste apagado, entulho, árvore caída, pintura de faixa. Coisas que
incomodam muita gente por muito tempo, e que hoje desaparecem dentro de
sistemas fechados.

**Nem tudo é responsabilidade da prefeitura.** Água que sai do bueiro é da
companhia de saneamento; fio partido é da distribuidora de energia. Nesses
casos o município encaminha a ocorrência ao órgão competente — e é aí que
mora um problema conhecido de quem já tentou resolver alguma coisa: cada um
diz que a responsabilidade é do outro, e o cidadão fica no meio.

**O encaminhamento também vira um registro público.** Fica gravado quando a
ocorrência saiu da prefeitura, para quem foi, e a partir de que momento o
prazo passa a correr contra a concessionária. A responsabilidade é
transferida com prova, e ninguém pode alegar depois que nunca recebeu.
""")

st.markdown("### O limite que essa etapa não resolve sozinha")

st.markdown("""
**Identidade.** Hoje quem identifica um participante é o endereço da carteira,
e isso não é identidade de verdade: nada impede que uma mesma pessoa crie
várias carteiras e finja ser várias pessoas. Isso tem nome — **ataque sybil**
— e é um problema central em qualquer rede que distribui recompensa sem saber
quem é quem.

A exigência de foto e de localização já torna a fraude trabalhosa: para
confirmar uma obra é preciso estar fisicamente no lugar, e a recompensa por
confirmação é pequena por definição. Isso desestimula o esforço de burlar,
mas não elimina a possibilidade.

Num sistema com uso governamental, o caminho natural é a autenticação por
**gov.br** ou por CPF verificado, ligando uma pessoa real a uma participação —
mantendo a carteira apenas como endereço de recebimento, e não como documento.
""")

st.markdown("### Outros passos previstos")

st.markdown("""
- **Áudio e vídeo no registro** — há ocorrências que a foto não captura, como
  ruído excessivo ou vazamento audível.
- **LoRaWAN** (*Long Range Wide Area Network*, uma rede de rádio de longo
  alcance e baixo consumo, feita para enviar pouquíssimos dados a vários
  quilômetros) — permitirá que a antena transmita o registro (o código da
  imagem, a localização e o horário) mesmo onde não há internet, deixando de
  representar um nó para se tornar um nó de fato. A antena não precisa
  carregar a foto: ela carrega o registro. A imagem vai por rede convencional
  quando houver, e é sincronizada depois — o LoRaWAN transporta pacotes
  pequenos, não fotos.
- **Token intransferível** — um token que fica preso à carteira que o recebeu
  e não pode ser vendido nem repassado (em inglês, *soulbound*). Reforça que o
  CP é crédito cívico, e não algo negociável.
- **Selos de reputação por NFT** (*Non-Fungible Token*, um token único, que
  representa um item específico em vez de um valor) — Bronze, Prata e Ouro
  conforme o volume de contribuições do cidadão.
- **Carteira conectada via MetaMask**, dispensando a digitação do endereço.
- **Endereço preenchido pela localização do aparelho**, eliminando os campos
  de rua, número, bairro e CEP no momento do registro.
""")

st.markdown("### Equipe")

st.markdown("""
Projeto de Iniciação Científica do programa **Future Makers — FIAP**,
desenvolvido por estudantes do **primeiro ano de Análise e Desenvolvimento
de Sistemas**.

- **Diogo Ricci**
- **Raphael Herkmann**

O desenvolvimento do sistema, a integração com blockchain e IPFS, a
construção da antena física e a pesquisa foram conduzidos em conjunto pela
dupla.
""")

st.markdown("---")
st.caption(
    "DePIN — *Decentralized Physical Infrastructure Network*: redes em que a "
    "infraestrutura física é distribuída entre os próprios participantes, "
    "que são remunerados por contribuir com ela."
)
