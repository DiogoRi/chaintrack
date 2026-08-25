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
| **Rede DePIN (antena)** | Nó físico que observa a blockchain por conta própria e sinaliza a atividade da rede. Nesta fase representa o nó; a evolução é transportar o registro por LoRaWAN. |
| **Armazenamento híbrido** | A imagem fica no IPFS; apenas os metadados vão para a blockchain. Guardar imagens on-chain seria caro e desnecessário. |
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
| **Fase 3** | Sistema integrado e funcionando ao vivo: aplicativo publicado, status de atendimento, token de recompensa emitido automaticamente e antena física reagindo à blockchain. |
""")

st.markdown("### Próximos passos")

st.markdown("""
- **Áudio e vídeo no registro** — há ocorrências que a foto não captura, como
  ruído excessivo ou vazamento audível.
- **LoRaWAN** — permitirá que a antena transmita o registro (o código da
  imagem, a localização e o horário) mesmo onde não há internet, deixando de
  representar um nó para se tornar um nó de fato. A antena não precisa
  carregar a foto: ela carrega o registro. A imagem vai por rede convencional
  quando houver, e é sincronizada depois — o LoRaWAN transporta pacotes
  pequenos, não fotos.
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
