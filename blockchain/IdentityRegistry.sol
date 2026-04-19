// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * IdentityRegistry
 * Tracks reputation of participating offices in the federated learning network.
 * Admin (HQ) can slash malicious nodes and reward honest ones.
 * Offices with reputation below BAN_THRESHOLD cannot register new identities.
 */
contract IdentityRegistry {
    address public admin;

    uint256 public constant MAX_REPUTATION   = 100;
    uint256 public constant BAN_THRESHOLD    = 50;
    uint256 public constant SLASH_AMOUNT     = 50;
    uint256 public constant REWARD_AMOUNT    = 5;

    mapping(address => uint256) public reputation;
    mapping(bytes32  => bool)   public idLedger;

    event NodeInitialised(address indexed node, uint256 initialReputation);
    event Registered(address indexed node, bytes32 idHash);
    event Slashed(address indexed node, uint256 newReputation, string reason);
    event Rewarded(address indexed node, uint256 newReputation);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin (HQ) can call this");
        _;
    }

    modifier notBanned(address node) {
        require(reputation[node] >= BAN_THRESHOLD, "Node is banned");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function initializeNode(address node) external onlyAdmin {
        reputation[node] = MAX_REPUTATION;
        emit NodeInitialised(node, MAX_REPUTATION);
    }

    function register(bytes32 h) external notBanned(msg.sender) {
        require(!idLedger[h], "Identity already registered");
        idLedger[h] = true;
        emit Registered(msg.sender, h);
    }

    /** Slash a malicious node. Reputation is floored at 0 (no underflow). */
    function slash(address node, string calldata reason) external onlyAdmin {
        uint256 current = reputation[node];
        uint256 newRep  = current >= SLASH_AMOUNT ? current - SLASH_AMOUNT : 0;
        reputation[node] = newRep;
        emit Slashed(node, newRep, reason);
    }

    /** Reward an honest node. Reputation is capped at MAX_REPUTATION. */
    function reward(address node) external onlyAdmin {
        uint256 current = reputation[node];
        uint256 newRep  = current + REWARD_AMOUNT > MAX_REPUTATION
                          ? MAX_REPUTATION
                          : current + REWARD_AMOUNT;
        reputation[node] = newRep;
        emit Rewarded(node, newRep);
    }

    function isBanned(address node) external view returns (bool) {
        return reputation[node] < BAN_THRESHOLD;
    }
}
