// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Deploy pelo Remix (remix.ethereum.org): cole este arquivo, compile e faça
// o deploy na rede Polygon Amoy via MetaMask — exatamente o mesmo fluxo já
// usado para o contrato de registro de ocorrências na Fase 2.
//
// O Remix busca o OpenZeppelin sozinho a partir do import abaixo (não
// precisa instalar nada localmente).
//
// "Token infinito": o dono do contrato (quem fez o deploy, ou seja, a
// wallet configurada no .env como WALLET_ADDRESS) pode chamar
// concluirOcorrencia() quantas vezes quiser, sem limite de quantidade —
// ideal para gerar recompensas na demonstração sem se preocupar em ficar
// sem saldo.
//
// Por que uma função só (e não "marcar concluída" + "mint" separados):
// isso garante que a prova de conclusão e o envio do token aconteçam na
// MESMA transação — uma só operação atômica e auditável no Polygonscan,
// em vez de duas transações que poderiam, em teoria, ficar dessincronizadas.

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract CidadaoParticipativoToken is ERC20, Ownable {
    /// @notice Emitido quando uma ocorrência é marcada como concluída.
    /// O `cid` é o mesmo identificador do IPFS usado no registro original
    /// da ocorrência — é o elo que liga essa conclusão à ocorrência certa.
    event OcorrenciaConcluida(
        string cid,
        address indexed destinatario,
        uint256 quantidade,
        uint256 timestamp
    );

    constructor() ERC20("Cidadao Participativo", "CP") Ownable(msg.sender) {}

    /// @notice Registra na blockchain que a ocorrência identificada por
    /// `cid` foi concluída, e no mesmo instante envia `quantidade` tokens
    /// (em wei, ou seja, já multiplicado por 10**18) para `destinatario`.
    /// Só a wallet dona do contrato pode chamar.
    function concluirOcorrencia(
        string memory cid,
        address destinatario,
        uint256 quantidade
    ) external onlyOwner {
        _mint(destinatario, quantidade);
        emit OcorrenciaConcluida(cid, destinatario, quantidade, block.timestamp);
    }
}
