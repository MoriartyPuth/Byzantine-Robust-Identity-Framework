"""
Tests for the PrivacyAccountant (gradient clipping + Laplace DP).
"""
import numpy as np
import pytest
from core.crypto_utils import PrivacyAccountant


class TestPrivacyAccountant:

    def test_clips_large_delta(self):
        """After clipping, the L2 norm of the (pre-noise) delta must be <= clip_norm."""
        pa = PrivacyAccountant(epsilon_per_round=1.0, clip_norm=1.0)
        large = np.full(50, 100.0)
        # Run many times — noise can push norm slightly above clip_norm,
        # so we test the clipping step by zeroing noise: use very high epsilon.
        pa2 = PrivacyAccountant(epsilon_per_round=1e6, clip_norm=1.0)
        result = pa2.privatize(large.copy())
        # With near-zero noise, result ≈ clipped vector with norm ~1
        assert np.linalg.norm(result) < 2.0, 'Clipping did not reduce the large delta'

    def test_small_delta_not_clipped(self):
        """A delta already within clip_norm should not be scaled down."""
        pa = PrivacyAccountant(epsilon_per_round=1e6, clip_norm=10.0)
        small = np.array([0.1, 0.2, 0.3])
        original_norm = np.linalg.norm(small)
        result = pa.privatize(small.copy())
        # With near-zero noise and no clipping, result ≈ small
        result_norm = np.linalg.norm(result)
        assert abs(result_norm - original_norm) < 0.01

    def test_budget_accumulates(self):
        pa = PrivacyAccountant(epsilon_per_round=0.5, clip_norm=1.0)
        delta = np.ones(10)
        for _ in range(4):
            pa.privatize(delta.copy())
        assert pa.rounds_completed == 4
        assert abs(pa.total_epsilon_spent - 2.0) < 1e-9

    def test_budget_summary_keys(self):
        pa = PrivacyAccountant(epsilon_per_round=0.3, clip_norm=0.5)
        pa.privatize(np.ones(5))
        summary = pa.budget_summary()
        for key in ('epsilon_per_round', 'clip_norm', 'rounds_completed', 'total_epsilon_spent'):
            assert key in summary

    def test_invalid_epsilon_raises(self):
        with pytest.raises(ValueError):
            PrivacyAccountant(epsilon_per_round=0.0)

    def test_invalid_clip_norm_raises(self):
        with pytest.raises(ValueError):
            PrivacyAccountant(epsilon_per_round=1.0, clip_norm=-1.0)

    def test_output_shape_preserved(self):
        pa = PrivacyAccountant(epsilon_per_round=1.0, clip_norm=1.0)
        delta = np.random.randn(200)
        result = pa.privatize(delta)
        assert result.shape == delta.shape
