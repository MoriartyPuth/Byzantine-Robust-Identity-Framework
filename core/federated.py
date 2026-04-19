import logging
import os
import warnings
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning

warnings.filterwarnings('ignore', category=ConvergenceWarning)

from core.crypto_utils import PrivacyAccountant
from core.aggregation import krum_aggregate
from core.models import FederatedModel

logger = logging.getLogger(__name__)


class FederatedLearning:
    """
    FedKrum: Federated Learning with Krum Byzantine defence and Differential Privacy.

    Each round:
      1. Broadcast global weights to all offices.
      2. Each office trains locally from global weights (SGD steps).
      3. Compute update delta = local_weights - global_weights.
      4. Krum selects the most trustworthy delta (Byzantine filter).
      5. Server applies DP noise to the selected delta (central DP).
      6. Apply noised delta to global model.
      7. Evaluate global model on held-out test set.

    Central DP (noise applied once on server) gives far better utility than
    local DP (noise per office) for high-dimensional MLP weight vectors.
    """

    def __init__(
        self,
        data_loader,
        n_offices: int = 5,
        num_rounds: int = 10,
        epsilon: float = 0.5,
        clip_norm: float = 1.0,
        local_epochs: int = 5,
        attack_office: int = None,
    ):
        self.data_loader = data_loader
        self.n_offices = n_offices
        self.num_rounds = num_rounds
        self.local_epochs = local_epochs
        self.attack_office = attack_office

        self.privacy = PrivacyAccountant(
            epsilon_per_round=epsilon,
            clip_norm=clip_norm,
        )

        os.makedirs('logs', exist_ok=True)
        self.round_metrics = []
        self.attack_log = []

        # ── Initialise global model ──────────────────────────────────────────
        # Train on office 0's data to set up the MLP architecture (coefs_ shapes).
        # All office models are then seeded with these same initial weights so
        # every round starts from a consistent global state.
        self.global_model = FederatedModel()
        office0 = data_loader.get_office_data(0)
        logger.info('Initialising global model architecture on office-0 data ...')
        self.global_model.train(office0['X'], office0['y'], epochs=3)

        # ── Initialise office models ─────────────────────────────────────────
        self.office_models = []
        init_weights = self.global_model.get_weights()
        for i in range(n_offices):
            m = FederatedModel()
            office_data = data_loader.get_office_data(i)
            m.train(office_data['X'], office_data['y'], epochs=1)
            m.set_weights(init_weights.copy())
            self.office_models.append(m)

        logger.info(
            'FL initialised: %d offices, %d rounds, eps=%.2f, attack_office=%s',
            n_offices, num_rounds, epsilon, attack_office,
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _apply_attack(self, delta: np.ndarray) -> np.ndarray:
        """Scale delta by 10x and add large noise — simulates gradient poisoning."""
        return delta * 10.0 + np.random.randn(len(delta)) * 5.0

    def _train_office(self, office_id: int, global_weights: np.ndarray) -> np.ndarray:
        """Sync office model to global weights, run local SGD, return weight delta."""
        model = self.office_models[office_id]
        model.set_weights(global_weights.copy())

        office_data = self.data_loader.get_office_data(office_id)
        model.train(office_data['X'], office_data['y'], epochs=self.local_epochs)

        local_weights = model.get_weights()
        return local_weights - global_weights

    # ── Round ────────────────────────────────────────────────────────────────

    def run_round(self, round_num: int):
        global_weights = self.global_model.get_weights()
        raw_deltas = []

        for office_id in range(self.n_offices):
            delta = self._train_office(office_id, global_weights)

            if office_id == self.attack_office:
                delta = self._apply_attack(delta)
                self.attack_log.append({
                    'round': round_num,
                    'office': office_id,
                    'attack_type': 'gradient_poisoning',
                })
                logger.warning('Round %d: office %d launched gradient poisoning attack',
                               round_num, office_id)

            raw_deltas.append(delta)

        # Krum: select the most trustworthy delta
        try:
            winner = krum_aggregate(raw_deltas, num_malicious=1)
        except Exception:
            winner = int(np.argmin([np.linalg.norm(d) for d in raw_deltas]))

        attack_detected = (winner != self.attack_office) if self.attack_office is not None else False

        # Central DP: apply noise once on server to the selected delta
        private_delta = self.privacy.privatize(raw_deltas[winner])

        # Apply noised winner delta to global model
        new_weights = global_weights + private_delta
        self.global_model.set_weights(new_weights)

        X_test, y_test = self.data_loader.get_test_data()
        metrics = self.global_model.evaluate(X_test, y_test)

        self.round_metrics.append({
            'round':          round_num + 1,
            'accuracy':       metrics['accuracy'],
            'precision':      metrics['precision'],
            'recall':         metrics['recall'],
            'f1':             metrics['f1'],
            'winner_office':  int(winner),
            'attack_detected': attack_detected,
            'epsilon_spent':  round(self.privacy.total_epsilon_spent, 4),
        })

        logger.info(
            'Round %2d/%d | acc=%.4f f1=%.4f | winner=office-%d | eps_total=%.2f',
            round_num + 1, self.num_rounds,
            metrics['accuracy'], metrics['f1'],
            winner, self.privacy.total_epsilon_spent,
        )
        return winner, metrics

    # ── Full run ─────────────────────────────────────────────────────────────

    def run(self) -> list:
        logger.info('=== Starting Federated Learning: %d rounds, %d offices ===',
                    self.num_rounds, self.n_offices)
        if self.attack_office is not None:
            logger.info('Byzantine attack enabled: office %d', self.attack_office)

        for round_num in range(self.num_rounds):
            self.run_round(round_num)

        self._save_logs()
        budget = self.privacy.budget_summary()
        logger.info('Privacy budget used: %.4f epsilon over %d rounds',
                    budget['total_epsilon_spent'], budget['rounds_completed'])
        return self.round_metrics

    def _save_logs(self):
        pd.DataFrame(self.round_metrics).to_csv('logs/round_metrics.csv', index=False)
        if self.attack_log:
            pd.DataFrame(self.attack_log).to_csv('logs/attack_log.csv', index=False)

        budget = self.privacy.budget_summary()
        pd.DataFrame([budget]).to_csv('logs/privacy_budget.csv', index=False)
        logger.info('Logs saved to logs/')
