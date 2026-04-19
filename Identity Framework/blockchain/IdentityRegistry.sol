// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract IdentityRegistry {
    address public admin;
    mapping(address => uint256) public reputation;
    mapping(bytes32 => bool) public idLedger;

    constructor() { admin = msg.sender; }

    function register(bytes32 h) external {
        require(reputation[msg.sender] >= 50, "Banned");
        idLedger[h] = true;
    }

    function slash(address node) external {
        require(msg.sender == admin, "Only HQ");
        reputation[node] -= 50;
    }
}