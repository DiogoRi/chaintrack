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
// wallet configurada no .env como WALLET_ADDRESS) pode chamar mint()
// quantas vezes quiser, sem limite de quantidade — ideal para gerar
// recompensas na demonstração sem se preocupar em ficar sem saldo.

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DePinToken is ERC20, Ownable {
    constructor() ERC20("DePin Token", "DEPIN") Ownable(msg.sender) {}

    /// @notice Cria `amount` tokens (em wei, ou seja, já multiplicado por
    /// 10**18) e envia para `to`. Só a wallet dona do contrato pode chamar.
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
