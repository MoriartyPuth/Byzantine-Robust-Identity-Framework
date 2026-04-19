import logging
import os
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def krum_aggregate(updates: list, num_malicious: int = 1) -> int:
    """
    Krum Byzantine-robust aggregation.

    Selects the update whose sum of squared distances to its
    (n - num_malicious - 2) nearest neighbours is smallest.
    That update is considered the most trustworthy.

    Returns the index of the selected update.
    """
    n = len(updates)
    neighbours_to_keep = n - num_malicious - 2

    if neighbours_to_keep < 1:
        raise ValueError(
            f'Too few updates ({n}) for num_malicious={num_malicious}. '
            f'Need at least {num_malicious + 3} offices.'
        )

    scores = []
    for i in range(n):
        dists = sorted(
            np.linalg.norm(updates[i] - updates[j]) ** 2
            for j in range(n) if j != i
        )
        scores.append(sum(dists[:neighbours_to_keep]))

    os.makedirs('logs', exist_ok=True)
    pd.DataFrame({'office': range(n), 'krum_score': scores}).to_csv(
        'logs/krum_scores.csv', index=False
    )

    winner = int(np.argmin(scores))
    logger.debug('Krum scores: %s  →  winner=office-%d', [round(s, 2) for s in scores], winner)
    return winner
