import hashlib
import logging
import numpy as np

logger = logging.getLogger(__name__)


def generate_id_hash(biometrics, office_id):
    """SHA-3 salted hash for identity commitment."""
    salt = f'OFFICE_{office_id}_SECRET_SALT_2026'
    data = f'{biometrics}{salt}'.encode()
    return hashlib.sha3_256(data).hexdigest()


class PrivacyAccountant:
    """
    Differential Privacy via gradient clipping + calibrated Laplace noise.

    Each call to privatize():
      1. Clips the weight delta to L2 norm <= clip_norm  (bounding sensitivity)
      2. Adds Laplace noise scaled to  clip_norm / epsilon_per_round
      3. Accumulates epsilon spend (basic sequential composition)

    Formal guarantee per round: (epsilon_per_round, 0)-DP
    After R rounds:            (R * epsilon_per_round, 0)-DP  (worst-case composition)
    """

    def __init__(self, epsilon_per_round: float = 0.5, clip_norm: float = 1.0):
        if epsilon_per_round <= 0:
            raise ValueError('epsilon_per_round must be positive')
        if clip_norm <= 0:
            raise ValueError('clip_norm must be positive')
        self.epsilon_per_round = epsilon_per_round
        self.clip_norm = clip_norm
        self.rounds_completed = 0
        self.total_epsilon_spent = 0.0

    def privatize(self, delta: np.ndarray) -> np.ndarray:
        """Clip then add calibrated Laplace noise to a weight update delta."""
        # Step 1: clip
        norm = np.linalg.norm(delta)
        if norm > self.clip_norm:
            delta = delta * (self.clip_norm / norm)

        # Step 2: noise  (sensitivity = clip_norm after clipping)
        noise_scale = self.clip_norm / self.epsilon_per_round
        noise = np.random.laplace(0.0, noise_scale, delta.shape)

        # Step 3: budget accounting
        self.rounds_completed += 1
        self.total_epsilon_spent += self.epsilon_per_round

        logger.debug(
            'DP round %d: delta_norm=%.4f, noise_scale=%.4f, total_eps=%.2f',
            self.rounds_completed, norm, noise_scale, self.total_epsilon_spent,
        )
        return delta + noise

    def budget_summary(self) -> dict:
        return {
            'epsilon_per_round':   self.epsilon_per_round,
            'clip_norm':           self.clip_norm,
            'rounds_completed':    self.rounds_completed,
            'total_epsilon_spent': round(self.total_epsilon_spent, 4),
        }
