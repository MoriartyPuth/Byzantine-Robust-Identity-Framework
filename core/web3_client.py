import hashlib
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ABI_PATH = os.path.join(_BASE_DIR, 'blockchain', 'IdentityRegistry.abi')


class BlockchainClient:
    """
    Wraps the IdentityRegistry smart contract.

    Connects to a live node (Ganache or testnet) when WEB3_PROVIDER_URL is set.
    Falls back to a pure-Python simulation so the rest of the system always works.

    To run locally with Ganache:
        ganache --port 8545
        export WEB3_PROVIDER_URL=http://127.0.0.1:8545
        export WEB3_CONTRACT_ADDRESS=<deployed address>
        export WEB3_PRIVATE_KEY=<account private key>
    """

    def __init__(self, provider_url=None, contract_address=None, private_key=None):
        self.provider_url     = provider_url     or os.environ.get('WEB3_PROVIDER_URL', '')
        self.contract_address = contract_address or os.environ.get('WEB3_CONTRACT_ADDRESS', '')
        self.private_key      = private_key      or os.environ.get('WEB3_PRIVATE_KEY', '')
        self.w3               = None
        self.contract         = None
        self.connected        = False

        if HAS_WEB3 and self.provider_url:
            self._connect()
        else:
            logger.info('BlockchainClient: running in simulation mode (no provider URL or web3)')

    def _connect(self):
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.provider_url))
            self.connected = self.w3.is_connected()
            if self.connected:
                logger.info('Connected to blockchain at %s', self.provider_url)
                self._load_contract()
            else:
                logger.warning('Could not reach %s — falling back to simulation', self.provider_url)
        except Exception as exc:
            logger.warning('Blockchain connection error: %s — simulation mode', exc)
            self.connected = False

    def _load_contract(self):
        if not os.path.exists(_ABI_PATH):
            logger.warning('ABI not found at %s — contract calls disabled', _ABI_PATH)
            return
        if not self.contract_address:
            logger.warning('WEB3_CONTRACT_ADDRESS not set — contract calls disabled')
            return
        try:
            with open(_ABI_PATH) as f:
                abi = json.load(f)
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=abi,
            )
            logger.info('Contract loaded at %s', self.contract_address)
        except Exception as exc:
            logger.warning('Failed to load contract: %s', exc)

    # ── Public API ────────────────────────────────────────────────────────────

    def register_identity(self, office_id: int, identity_hash: str) -> str:
        if self.connected and self.contract:
            try:
                tx = self.contract.functions.register(
                    bytes.fromhex(identity_hash)
                ).transact({'from': self.w3.eth.accounts[0]})
                return tx.hex()
            except Exception as exc:
                logger.warning('register() failed on-chain: %s', exc)
        return self._sim_hash(f'register:{office_id}:{identity_hash}')

    def slash(self, office_address: str, reason: str = 'byzantine_attack') -> str:
        if self.connected and self.contract:
            try:
                tx = self.contract.functions.slash(
                    Web3.to_checksum_address(office_address), reason
                ).transact({'from': self.w3.eth.accounts[0]})
                return tx.hex()
            except Exception as exc:
                logger.warning('slash() failed on-chain: %s', exc)
        return self._sim_hash(f'slash:{office_address}')

    def reward(self, office_address: str) -> str:
        if self.connected and self.contract:
            try:
                tx = self.contract.functions.reward(
                    Web3.to_checksum_address(office_address)
                ).transact({'from': self.w3.eth.accounts[0]})
                return tx.hex()
            except Exception as exc:
                logger.warning('reward() failed on-chain: %s', exc)
        return self._sim_hash(f'reward:{office_address}')

    def get_reputation(self, office_address: str) -> int:
        if self.connected and self.contract:
            try:
                return self.contract.functions.reputation(
                    Web3.to_checksum_address(office_address)
                ).call()
            except Exception as exc:
                logger.warning('get_reputation() failed on-chain: %s', exc)
        return 100  # simulation default

    @staticmethod
    def _sim_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()


class ReputationManager:
    """
    Manages office reputation locally and optionally mirrors to the blockchain.

    Local state is the source of truth in simulation mode.
    When connected, on-chain state is authoritative.
    """

    def __init__(self, blockchain_client: BlockchainClient = None):
        self.blockchain  = blockchain_client or BlockchainClient()
        self._reputation = {}   # office_id (int) -> score
        self._audit_log  = []

    def initialize_offices(self, n_offices: int):
        for i in range(n_offices):
            self._reputation[i] = 100
        logger.info('Initialised %d offices at reputation=100', n_offices)

    def slash_malicious(self, office_id: int, reason: str = 'byzantine_attack') -> int:
        old = self._reputation.get(office_id, 100)
        new = max(0, old - 50)
        self._reputation[office_id] = new
        self._record('SLASH', office_id, old, new, reason)
        self.blockchain.slash(str(office_id), reason)
        logger.warning('Office %d slashed (%s): %d → %d', office_id, reason, old, new)
        return new

    def reward_honest(self, office_id: int) -> int:
        old = self._reputation.get(office_id, 100)
        new = min(100, old + 5)
        self._reputation[office_id] = new
        self._record('REWARD', office_id, old, new, 'honest_contribution')
        self.blockchain.reward(str(office_id))
        return new

    def get_reputation(self, office_id: int) -> int:
        return self._reputation.get(office_id, 100)

    def is_banned(self, office_id: int) -> bool:
        return self._reputation.get(office_id, 100) < 50

    def save_audit_log(self, path: str = None):
        if path is None:
            path = os.path.join(_BASE_DIR, 'logs', 'blockchain_audit.csv')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import pandas as pd
        pd.DataFrame(self._audit_log).to_csv(path, index=False)
        logger.info('Blockchain audit log saved to %s', path)

    def _record(self, action, office_id, old_rep, new_rep, reason):
        self._audit_log.append({
            'timestamp':      datetime.now().isoformat(),
            'office_id':      office_id,
            'action':         action,
            'old_reputation': old_rep,
            'new_reputation': new_rep,
            'reason':         reason,
        })
