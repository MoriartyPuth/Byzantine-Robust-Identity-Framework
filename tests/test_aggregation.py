"""
Tests for Krum Byzantine-robust aggregation.
"""
import numpy as np
import pytest
from core.aggregation import krum_aggregate


def _honest(n=4, dim=10, seed=0):
    rng = np.random.default_rng(seed)
    return [rng.normal(0, 0.01, dim) for _ in range(n)]


class TestKrumAggregate:

    def test_selects_integer_index(self):
        updates = _honest(5)
        winner = krum_aggregate(updates, num_malicious=1)
        assert isinstance(winner, int)
        assert 0 <= winner < 5

    def test_rejects_poisoned_office(self):
        """Krum must never select the office with a clearly poisoned update."""
        honest   = _honest(4, dim=20, seed=42)
        poisoned = [np.full(20, 1000.0)]   # wildly different from honest cluster
        updates  = honest + poisoned        # poisoned is index 4

        for _ in range(10):                 # repeat to rule out luck
            winner = krum_aggregate(updates, num_malicious=1)
            assert winner != 4, 'Krum selected the poisoned office'

    def test_all_honest_selects_central_update(self):
        """With all-honest updates near zero, the winner should have the smallest norm."""
        rng = np.random.default_rng(7)
        updates = [rng.normal(0, 0.01, 10) for _ in range(5)]
        winner = krum_aggregate(updates, num_malicious=1)
        assert 0 <= winner < 5

    def test_raises_when_too_few_offices(self):
        updates = [np.ones(5), np.ones(5)]   # only 2 offices, need ≥ 4 for f=1
        with pytest.raises(ValueError):
            krum_aggregate(updates, num_malicious=1)

    def test_scores_saved_to_csv(self, tmp_path, monkeypatch):
        import os, pandas as pd
        monkeypatch.chdir(tmp_path)
        os.makedirs('logs', exist_ok=True)
        updates = _honest(5)
        krum_aggregate(updates, num_malicious=1)
        df = pd.read_csv('logs/krum_scores.csv')
        assert len(df) == 5
        assert 'krum_score' in df.columns
