# Byzantine-Robust Identity Framework

A federated learning system with Byzantine fault tolerance, differential privacy, and blockchain-based reputation tracking — built for the Ministry of Interior identity verification use case.

---

## Architecture

```
                    GLOBAL COORDINATOR
                   ┌─────────────────────┐
                   │  MLP Global Model   │
                   │  FedKrum Aggregation│
                   │  DP Privacy Budget  │
                   └──────────┬──────────┘
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  Office 0   │    │  Office 1   │    │  Office N   │
   │  Local MLP  │    │  Local MLP  │    │  Local MLP  │
   │  SGD steps  │    │  SGD steps  │    │  SGD steps  │
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          └───────────────────┼───────────────────┘
                              │  weight deltas (DP-noised)
                   ┌──────────▼──────────┐
                   │   BLOCKCHAIN LAYER  │
                   │  IdentityRegistry   │
                   │  Slash / Reward     │
                   │  Audit Trail        │
                   └─────────────────────┘
```

### How FedKrum works

1. Global model broadcasts its weights to all offices.
2. Each office trains locally (SGD steps) starting from global weights.
3. Each office computes a **weight delta** = local weights − global weights.
4. Delta is **clipped** (L2 norm ≤ `clip_norm`) then **Laplace noise** is added → (ε, 0)-DP per round.
5. **Krum** selects the delta with the lowest Byzantine score (most trustworthy).
6. The selected delta is applied to the global model.
7. Global model is evaluated on the held-out test set.

---

## Setup

### Requirements
- Python 3.9+
- See `requirements.txt` for all packages

```bash
pip install -r requirements.txt
```

Optional: install [GNU Make](https://gnuwin32.sourceforge.net/packages/make.htm) (Git Bash includes it) to use the `Makefile` shortcuts.

---

## Usage

### Run experiments

```bash
# Full suite (baseline + byzantine + DP sensitivity + reputation demo)
python main.py --mode full

# Individual modes
python main.py --mode baseline
python main.py --mode byzantine
python main.py --mode dp
python main.py --mode reputation
```

### CLI overrides

```bash
python main.py --mode byzantine --rounds 20 --epsilon 0.3 --attack-office 2
```

### Launch dashboard

```bash
streamlit run dashboard.py
```

### Run tests

```bash
pytest tests/ -v
```

### Make shortcuts (Git Bash / WSL)

```bash
make install
make run-full
make dashboard
make test
make coverage
```

---

## Configuration

All hyperparameters live in `config.yaml`:

```yaml
federated_learning:
  n_offices: 5
  num_rounds: 10
  local_epochs: 5

differential_privacy:
  epsilon_per_round: 0.5   # privacy budget per round
  clip_norm: 1.0            # gradient clipping threshold

byzantine:
  attack_office: 4          # which office launches the attack

blockchain:
  provider_url: ""          # leave empty for simulation mode
  contract_address: ""      # fill after deploying IdentityRegistry.sol
```

---

## Blockchain (optional)

The smart contract is in `blockchain/IdentityRegistry.sol`. To run it on a local testnet:

```bash
# Install Ganache
npm install -g ganache

# Start local blockchain
ganache --port 8545

# Deploy contract (requires Hardhat or Remix IDE), then set env vars:
export WEB3_PROVIDER_URL=http://127.0.0.1:8545
export WEB3_CONTRACT_ADDRESS=<deployed address>
```

Without these env vars, the system runs in **simulation mode** (pure Python reputation tracking) — all experiments still work.

---

## Project Structure

```
Identity Framework/
├── main.py                   # CLI entry point
├── config.yaml               # All hyperparameters
├── dashboard.py              # Streamlit dashboard
├── requirements.txt
├── Makefile
│
├── core/
│   ├── models.py             # FederatedModel (MLP) — get/set weights
│   ├── federated.py          # FedKrum training loop
│   ├── aggregation.py        # Krum Byzantine-robust aggregation
│   ├── crypto_utils.py       # PrivacyAccountant (clip + Laplace DP)
│   ├── evaluation.py         # ExperimentEvaluator, ReputationTracker
│   └── web3_client.py        # Blockchain client + ReputationManager
│
├── data/
│   └── loader.py             # NSL-KDD download / synthetic data / partitioning
│
├── blockchain/
│   ├── IdentityRegistry.sol  # Solidity smart contract
│   └── IdentityRegistry.abi  # Contract ABI for web3.py
│
├── reports/
│   └── generator.py          # HTML / PDF report generation
│
├── tests/
│   ├── test_aggregation.py   # Krum unit tests
│   ├── test_dp.py            # PrivacyAccountant unit tests
│   └── test_models.py        # FederatedModel unit tests
│
└── logs/                     # Generated at runtime
    ├── round_metrics.csv
    ├── baseline_metrics.csv
    ├── byzantine_metrics.csv
    ├── attack_log.csv
    ├── krum_scores.csv
    ├── privacy_budget.csv
    ├── dp_sensitivity.csv
    └── blockchain_audit.csv
```

---

## Privacy Guarantee

Each FL round applies **(ε, 0)-DP** via the Laplace mechanism:
- Gradient clipping bounds sensitivity to `clip_norm`
- Noise scale = `clip_norm / epsilon_per_round`
- After R rounds: total privacy cost = **R × ε** (sequential composition)

The privacy budget is tracked and saved to `logs/privacy_budget.csv` after every run.
