"""
Sobre o Projeto — DePIN Urbano, Fase 3

Terceira página do app. Serve a três públicos ao mesmo tempo:

1. A banca avaliadora, que na demonstração não consegue ver tudo.
2. Quem apresenta: se der branco, esta página tem a ordem do que dizer.
3. Qualquer pessoa que encontrar o app publicado e não souber do que se trata.

O texto é o documento "Sobre o Projeto v7", convertido para a web. Duas
diferenças em relação ao PDF, ambas ganhos do formato: os endereços dos
contratos aqui são links clicáveis, e os dois parágrafos que descreviam o uso
do token CP foram fundidos, porque diziam a mesma coisa em sequência.

Toda sigla é explicada na primeira aparição, e há um glossário no fim.

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

# ===========================================================================
# ABERTURA
# ===========================================================================
st.markdown("<p class='titulo-sobre'>📖 Sobre o projeto</p>",
            unsafe_allow_html=True)
st.markdown("<p class='subtitulo-sobre'>Sistema descentralizado para registro "
            "e acompanhamento de ocorrências urbanas</p>",
            unsafe_allow_html=True)

st.caption("Projeto de Iniciação Científica · Fase 3 · Agosto de 2026 · "
           "Diogo Ricci e Raphael Herkmann")

st.info("**DePIN Urbano** é o projeto de pesquisa. **ChainTrack** é a "
        "aplicação desenvolvida para demonstrar seu funcionamento.")

st.markdown("""
Uma proposta para tornar ocorrências urbanas mais fáceis de acompanhar, com
uma prova pública que, uma vez confirmada na blockchain, não pode ser apagada,
e mais simples de auditar, ao mesmo tempo em que recompensa a participação do
cidadão.
""")

# ===========================================================================
# O PROBLEMA
# ===========================================================================
st.markdown("### O problema que queremos resolver")

st.markdown("""
Quem registra um problema urbano, como barulho recorrente de um
estabelecimento, um buraco na via, um vazamento de água, iluminação pública
sem funcionar, uma calçada quebrada ou outra ocorrência semelhante, muitas
vezes não consegue acompanhar o que aconteceu depois do envio.

As dúvidas são simples, mas importantes: alguém analisou? Qual equipe ficou
responsável? O atendimento começou? Existe prazo? Foi realmente concluído?
Quando o processo acontece apenas dentro de sistemas fechados, o cidadão
depende da informação fornecida pelo próprio órgão que está sendo cobrado.

O DePIN Urbano foi criado para adicionar uma camada pública de prova e
acompanhamento. O registro original da ocorrência passa a ter uma evidência
verificável fora do sistema interno do município. Assim, o cidadão consegue
acompanhar o atendimento, o município ganha uma visão organizada das demandas
e qualquer pessoa pode conferir a existência do registro público.

Com os registros organizados, o município também passa a produzir dados úteis
para a gestão: quais bairros concentram mais ocorrências, quais problemas
aparecem com maior frequência, quanto tempo cada tipo de atendimento leva e
como as equipes estão respondendo às demandas.

Isso também aumenta a auditabilidade. O projeto não elimina corrupção ou
falhas de gestão, mas reduz uma fragilidade importante: a possibilidade de um
registro simplesmente desaparecer ou ter sua data de entrada alterada sem
deixar rastro.

Há ainda um objetivo social: estimular participação cívica. A proposta é fazer
com que o cidadão deixe de enxergar a cidade apenas como algo administrado por
terceiros e passe a participar da conservação do lugar onde vive. Quando uma
contribuição gera acompanhamento, resultado e reconhecimento, aumenta a
chance de a pessoa participar novamente.
""")

st.info("**Ideia central:** transformar uma ocorrência urbana em um registro "
        "público, acompanhável e verificável, conectando cidadão, município e "
        "infraestrutura digital.")

# ===========================================================================
# O FLUXO
# ===========================================================================
st.markdown("### Como funciona, do celular até a conclusão")

st.markdown("""
**1. O cidadão registra a ocorrência.**
Pelo celular, tira ou envia uma foto, descreve o problema e informa o
endereço. Se quiser receber recompensa, pode informar também uma carteira
Web3 (carteira digital compatível com blockchain).

**2. A foto é enviada pelo Pinata para o IPFS.**
IPFS (*InterPlanetary File System*, ou Sistema de Arquivos Interplanetário) é
uma rede distribuída de arquivos. Pinata é o serviço usado pelo projeto para
enviar a imagem ao IPFS e mantê-la disponível.

**3. A imagem recebe um CID.**
CID (*Content Identifier*, ou Identificador de Conteúdo) é um código ligado ao
conteúdo da imagem. Ele funciona como uma impressão digital: se a foto for
alterada, o CID também muda.

**4. O registro vai para a blockchain.**
O CID da imagem, a descrição, o endereço e as coordenadas são registrados na
Polygon Amoy. A foto inteira não vai para a blockchain; vai apenas a
referência verificável dela.

**5. A antena detecta a mudança.**
O aplicativo não manda a antena acender. Um programa no computador consulta a
blockchain e, quando percebe uma nova ocorrência, envia um comando pela USB
para a ESP32 acender o LED de registro.

**6. O cidadão recebe protocolo e comprovante.**
O comprovante reúne o protocolo, o CID e o link da transação na blockchain.
Com o protocolo, o cidadão pode acompanhar o andamento sem precisar fazer
login.

**7. O município encaminha e acompanha.**
No Dashboard do Município, a ocorrência passa por Recebida → Em andamento →
Concluída. Quando entra em andamento, pode ser atribuída a uma equipe
responsável e a um prazo.

**8. O cidadão acompanha o atendimento.**
Na página de acompanhamento, ele vê situação, equipe responsável, previsão de
conclusão e pode acrescentar informações ao caso.

**9. A conclusão também gera uma prova pública.**
Quando a ocorrência é concluída e há uma carteira Web3 informada, uma nova
transação registra a conclusão e envia a recompensa em token CP (Cidadão
Participativo).

**10. A antena sinaliza novamente.**
O programa percebe que novos tokens CP foram emitidos e aciona o segundo LED,
indicando que uma ocorrência foi concluída e recompensada.
""")

st.success("Foto → IPFS/Pinata → Blockchain → Antena → Município → "
           "Conclusão → Token CP")

# ===========================================================================
# IPFS E PINATA
# ===========================================================================
st.markdown("### Onde entram IPFS e Pinata?")

st.markdown("""
Os dois trabalham juntos, mas não são a mesma coisa.

| Tecnologia | Função no projeto |
| --- | --- |
| **IPFS** (*InterPlanetary File System*) | É o sistema distribuído onde a imagem fica identificada pelo seu conteúdo, e não apenas por um endereço de servidor. |
| **Pinata** | É o serviço usado pelo ChainTrack para enviar a foto ao IPFS e mantê-la disponível. |
| **Pinning** | É a ação de manter um arquivo armazenado e disponível em um nó do IPFS, evitando que ele seja descartado. |
| **CID** (*Content Identifier*) | É o identificador do conteúdo da imagem. Se o conteúdo mudar, o CID muda. |
| **Hash da transação** | É o identificador da operação registrada na blockchain. Ele não é o CID da imagem. |
""")

st.success("Foto → Pinata → IPFS → CID → Blockchain guarda o CID e os dados "
           "do registro")

st.info("**Por que não guardar a foto inteira na blockchain?** Porque imagens "
        "são arquivos grandes. Guardar apenas o CID torna o registro mais "
        "leve, mais barato e ainda permite conferir se a imagem continua "
        "sendo exatamente a mesma.")

# ===========================================================================
# POR QUE BLOCKCHAIN
# ===========================================================================
st.markdown("### Por que blockchain e não um sistema comum?")

st.markdown("""
Um sistema comum já consegue receber e acompanhar ocorrências. A blockchain
entra porque o objetivo não é apenas armazenar informações, mas criar uma
prova que não dependa exclusivamente de quem administra o sistema. O município
continua usando sua aplicação normalmente, enquanto os registros essenciais
também ficam em uma blockchain pública, criando uma camada independente de
verificação e auditoria.

Na prática, essa camada acrescenta três propriedades importantes:

- **Imutável:** depois de confirmado, o registro não pode ser apagado ou
  reescrito retroativamente pelo município.
- **Independente:** a prova não existe apenas dentro do banco de dados da
  própria instituição que administra o serviço.
- **Publicamente auditável:** qualquer pessoa pode verificar o registro
  diretamente na blockchain, sem precisar de acesso ao sistema interno do
  município.

A diferença não é apenas guardar o dado, mas permitir que sua existência e seu
histórico sejam verificados fora do sistema de quem administra o serviço.
""")

# ===========================================================================
# ONDE ESTÁ O DEPIN
# ===========================================================================
st.markdown("### Onde está o DePIN?")

st.markdown("""
DePIN (*Decentralized Physical Infrastructure Network*, ou Rede Descentralizada
de Infraestrutura Física) conecta o mundo físico a redes digitais
descentralizadas. No DePIN Urbano, o cidadão e seu celular funcionam como
pontos distribuídos de coleta: registram uma situação real da cidade e enviam
essa evidência para uma infraestrutura verificável. A ESP32 acrescenta uma
demonstração física dessa integração ao reagir a eventos confirmados na
blockchain. Em uma evolução com LoRaWAN, dispositivos também poderão
transmitir pequenos pacotes de dados por rádio.
""")

# ===========================================================================
# A ANTENA
# ===========================================================================
st.markdown("### Como a antena funciona hoje, e o que mudaria com LoRaWAN")

st.markdown("""
**Hoje: a antena observa**

A ESP32 não acessa a blockchain diretamente. Um programa Python no computador
consulta a Polygon Amoy a cada poucos segundos. Quando detecta uma nova
ocorrência, envia pela porta USB a palavra `REGISTRO`; quando detecta uma
conclusão com emissão de CP, envia `CONCLUIDA`. A ESP32 recebe o comando e
acende o LED correspondente.
""")

st.success("Blockchain → programa Python → USB → ESP32 → LED")

st.markdown("""
**Futuro com LoRaWAN: a infraestrutura também transporta dados**

LoRaWAN (*Long Range Wide Area Network*, ou rede de rádio de longo alcance e
baixo consumo) é indicada para transmitir pequenos pacotes de dados a longas
distâncias. Ela não foi criada para transportar fotos ou vídeos pesados.

Nesse cenário, informações leves, como identificador da ocorrência,
localização, horário, tipo de evento ou CID, poderiam seguir por rádio até um
gateway. A foto continuaria sendo enviada pela internet para o Pinata e o IPFS
quando houvesse conexão disponível.
""")

st.success("Dados pequenos → LoRaWAN por rádio  ·  Foto → internet → "
           "Pinata/IPFS")

st.info("A antena atual é principalmente uma demonstração física do conceito "
        "DePIN. Em uma evolução com LoRaWAN, ela deixa de apenas observar e "
        "passa a participar do transporte de dados. Em um produto final, essa "
        "infraestrutura física só faria sentido onde trouxesse benefício real.")

# ===========================================================================
# ACOMPANHAMENTO
# ===========================================================================
st.markdown("### O acompanhamento pelo município e pelo cidadão")

st.markdown("""
| 🔴 Recebida | 🟠 Em andamento | 🟢 Concluída |
| --- | --- | --- |
| O registro entrou no sistema e aguarda encaminhamento. | Uma equipe pode ser definida e o prazo de execução começa a ser acompanhado. | O atendimento foi encerrado. Quando há carteira Web3 informada, a conclusão e a recompensa CP são registradas em uma transação. |

O Dashboard do Município também reúne mapa, protocolo, descrição, foto, equipe
responsável, prazo, mensagens e links das provas públicas. Para o cidadão, a
consulta é feita pelo protocolo e traduz a informação técnica da blockchain
para uma linguagem simples.
""")

# ===========================================================================
# TOKEN CP
# ===========================================================================
st.markdown("### Token CP e participação cívica")

st.markdown("""
CP significa **Cidadão Participativo**. Ele é o token de recompensa do
projeto. A ideia não é criar um ativo especulativo, e sim representar
participação cívica: uma forma de reconhecer quem contribui para identificar
problemas e, futuramente, também para confirmar soluções.

Em uma implementação municipal futura, os tokens CP poderiam ser convertidos
em benefícios definidos pelo próprio município, como créditos de Zona Azul,
passagens de transporte público ou descontos em determinados tributos e
serviços municipais. Esses usos são possibilidades futuras do projeto e não
fazem parte da versão atual.

O incentivo é importante porque o projeto não quer apenas digitalizar
reclamações. Ele pretende estimular uma mudança de comportamento: mais pessoas
observando, cuidando, acompanhando e ajudando a verificar a qualidade do
espaço urbano.
""")

# ===========================================================================
# TRANSPARÊNCIA E PRIVACIDADE
# ===========================================================================
st.markdown("### Transparência, auditabilidade e privacidade")

st.markdown("""
O registro público cria uma referência que não depende somente do sistema
interno do município. Isso facilita auditoria e permite conferir quando uma
ocorrência foi registrada e quais dados foram associados àquela transação.

Ao mesmo tempo, dados pessoais não devem ser gravados de forma permanente em
uma blockchain pública. Nome, e-mail e uma futura identificação por CPF ou
gov.br devem permanecer em sistemas protegidos do município. A blockchain deve
guardar apenas o que realmente precisa ser público e verificável.
""")

st.markdown(f"""
**Rede utilizada nesta fase:** Polygon Amoy (rede de testes)

- **Contrato de ocorrências:** [`{CONTRATO_OCORRENCIAS}`]({EXPLORADOR}/{CONTRATO_OCORRENCIAS})
- **Contrato do token CP:** [`{CONTRATO_TOKEN}`]({EXPLORADOR}/{CONTRATO_TOKEN})
- **Código-fonte:** [github.com/DiogoRi/chaintrack](https://github.com/DiogoRi/chaintrack)
""")

# ===========================================================================
# PRÓXIMOS PASSOS
# ===========================================================================
st.markdown("### Próximos passos")

st.markdown("""
- **Avisos por e-mail:** informar o cidadão quando a ocorrência mudar de
  situação ou for concluída, usando o e-mail fornecido no registro.
- **Pedido de informações adicionais:** o município poderá entrar em contato
  quando precisar de mais detalhes, imagens ou esclarecimentos sobre a
  ocorrência.
- **Feedback após a conclusão:** depois que o município marcar uma ocorrência
  como concluída, o cidadão poderá ser convidado, por exemplo dentro de uma
  janela de até 10 dias, a confirmar se o serviço realmente foi executado e se
  ficou adequado.
- **Recompensa pelo feedback:** quem participar da verificação da solução
  também poderá receber CP, evitando que o incentivo exista apenas para
  relatar coisas quebradas ou problemas.
- **Foto e geolocalização na verificação:** no feedback de campo, a pessoa
  poderá enviar uma nova foto e a localização do aparelho. Uma margem de
  distância, como até 100 metros, pode ser usada para compensar a imprecisão
  normal do GPS.
- **Identidade adequada ao contexto governamental:** em uma versão de
  produção, CPF verificado ou autenticação gov.br pode limitar participações
  por pessoa. A carteira Web3 permanece como endereço para receber o token, e
  não como prova de identidade.
- **LoRaWAN:** onde fizer sentido, pequenos dados poderão ser transportados
  por rádio de longo alcance. Fotos e vídeos continuam por conexão de internet
  convencional e IPFS/Pinata.
- **Infraestrutura de produção:** substituir o arquivo local por banco de
  dados, adicionar autenticação robusta, histórico de alterações, backup,
  notificações e separação de permissões.
""")

st.info("A evolução mais importante é fechar o ciclo: não apenas registrar o "
        "problema, mas permitir que a própria população também ajude a "
        "confirmar se a solução foi realmente entregue.")

# ===========================================================================
# GLOSSÁRIO
# ===========================================================================
st.markdown("### Glossário rápido")

st.markdown("""
**DePIN** — *Decentralized Physical Infrastructure Network* (Rede de
Infraestrutura Física Descentralizada): modelo em que participantes e
dispositivos distribuídos ajudam a fornecer ou verificar uma infraestrutura
física.

**Blockchain** — registro compartilhado entre vários computadores, no qual
transações confirmadas ficam públicas e difíceis de alterar retroativamente.

**IPFS** — *InterPlanetary File System* (Sistema de Arquivos Interplanetário):
sistema distribuído de arquivos identificado pelo conteúdo.

**Pinata** — serviço usado para enviar arquivos ao IPFS e mantê-los
disponíveis por meio de pinning.

**Pinning** — ação de manter um arquivo armazenado e disponível em um nó IPFS.

**CID** — *Content Identifier* (Identificador de Conteúdo): código associado
ao conteúdo do arquivo.

**Polygon Amoy** — rede de testes da Polygon usada pelo projeto para registrar
transações sem custo econômico real.

**Carteira Web3** — aplicativo ou endereço usado para receber e movimentar
ativos em blockchain, como o token CP.

**CP** — Cidadão Participativo: token de recompensa do projeto.

**ESP32** — placa eletrônica programável usada na demonstração física da
antena.

**LoRaWAN** — *Long Range Wide Area Network*: rede de rádio de longo alcance e
baixo consumo para pequenos pacotes de dados.

**LGPD** — Lei Geral de Proteção de Dados: legislação brasileira que
estabelece regras para tratamento de dados pessoais.
""")

# ===========================================================================
# EQUIPE
# ===========================================================================
st.markdown("### Equipe do projeto")

st.markdown("""
Projeto de Iniciação Científica do programa **Future Makers — FIAP**,
desenvolvido por estudantes do **primeiro ano de Análise e Desenvolvimento de
Sistemas**.

- **Diogo Ricci**
- **Raphael Herkmann**

O desenvolvimento do sistema, a integração com blockchain e IPFS, a construção
da demonstração física e a pesquisa foram conduzidos em conjunto pela dupla.
""")
