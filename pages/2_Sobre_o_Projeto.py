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

st.markdown("<p class='titulo-dashboard'>📖 Sobre o projeto</p>",
            unsafe_allow_html=True)
st.markdown(
    "<p class='frase-impacto'>Sistema DePIN para monitoramento urbano</p>",
    unsafe_allow_html=True)

st.markdown("""
Quando um cidadão registra um buraco na calçada, um poste apagado ou um
vazamento, esse pedido costuma desaparecer dentro de um sistema fechado.
Não há como saber se ele foi recebido, se está sendo tratado, nem provar
depois que ele existiu.

**Este projeto torna esse registro público, permanente e auditável** — e
recompensa quem contribui.
""")

st.markdown("### Como funciona")

st.markdown("""
1. **O cidadão registra** uma ocorrência pelo celular: foto, descrição e endereço.
2. **A foto vai para o IPFS**, uma rede distribuída de arquivos, e recebe um
   código calculado a partir da própria imagem. Se a foto for trocada, o
   código muda e a alteração fica evidente.
3. **Os dados vão para a blockchain** (Polygon Amoy). A partir daí ninguém
   pode apagar ou alterar o registro — nem a prefeitura, nem quem
   desenvolveu o sistema.
4. **A antena física acende**, sinalizando que a rede recebeu a ocorrência.
5. **A prefeitura acompanha** pelo painel: Recebida → Em andamento → Concluída.
6. **Ao concluir**, uma única operação registra publicamente o atendimento
   **e** envia os tokens ao cidadão. As duas coisas ficam inseparáveis.
""")

st.markdown("### Arquitetura em três camadas")

st.markdown("""
| Camada | Função |
| --- | --- |
| **Coleta** | Interface web acessada pelo celular, onde o cidadão envia foto, descrição e localização. |
| **Rede DePIN (antena)** | Nó físico que observa a blockchain e sinaliza a atividade da rede. Nesta fase representa o nó; a evolução é transportar o dado por LoRaWAN. |
| **Armazenamento híbrido** | A imagem fica no IPFS; apenas os metadados vão para a blockchain. Guardar imagens on-chain seria caro e desnecessário. |
""")

st.markdown("### O incentivo")

st.markdown("""
Ao ter sua ocorrência resolvida, o cidadão recebe o token **CP — Cidadão
Participativo**, na proporção de um token por ocorrência atendida. O saldo
funciona, assim, como a própria contagem de contribuições da pessoa à cidade.

A emissão é ilimitada e ocorre **somente** quando um problema é resolvido.
Não há pré-venda, reserva nem distribuição inicial: é um crédito cívico,
não um ativo especulativo. A aplicação prevista é o uso em serviços e
benefícios municipais.
""")

st.markdown("### Privacidade")

st.markdown("""
**O nome do cidadão não vai para a blockchain.** Foi uma decisão de projeto,
não uma limitação técnica: dado pessoal em registro imutável e público
conflita com a LGPD, inclusive com o direito à exclusão.

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

st.markdown("### Evolução do projeto")

st.markdown("""
| Fase | Entrega |
| --- | --- |
| **Fase 1** | Concepção: o problema, a proposta e a arquitetura pretendida. |
| **Fase 2** | Primeiro protótipo: coleta, IPFS, prova on-chain e dashboard com mapa, demonstrados em vídeo. |
| **Fase 3** | Sistema integrado e funcionando ao vivo: aplicativo publicado, status de atendimento, token de recompensa emitido automaticamente e antena física reagindo à blockchain. |
""")

st.markdown("### Próximos passos")

st.markdown("""
- **Áudio e vídeo no registro** — há ocorrências que a foto não captura, como
  ruído excessivo ou vazamento audível.
- **LoRaWAN** — fará a antena transportar o dado de fato, deixando de ser a
  representação de um nó para se tornar um nó da rede.
- **Token intransferível** *(soulbound)* — reforça que o CP é crédito cívico,
  e não algo negociável.
- **Selos de reputação por NFT** — Bronze, Prata e Ouro conforme o volume de
  contribuições do cidadão.
- **Carteira conectada via MetaMask**, dispensando a digitação do endereço.
- **Validação de veracidade** dos registros, com verificação cruzada de
  metadados das imagens.
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
