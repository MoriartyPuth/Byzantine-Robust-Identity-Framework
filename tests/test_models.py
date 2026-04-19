"""
Tests for FederatedModel — weight extraction, injection, and roundtrip correctness.
"""
import numpy as np
import pytest
from core.models import FederatedModel


def _trained_model(seed=0):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((300, 41))
    y = rng.integers(0, 2, 300)
    m = FederatedModel(random_state=seed)
    m.train(X, y, epochs=2)
    return m, X, y


class TestFederatedModel:

    def test_get_weights_returns_flat_array(self):
        m, _, _ = _trained_model()
        w = m.get_weights()
        assert isinstance(w, np.ndarray)
        assert w.ndim == 1
        assert len(w) > 0

    def test_set_weights_roundtrip(self):
        m, X, y = _trained_model(seed=1)
        original = m.get_weights().copy()

        # Corrupt weights, then restore
        m.set_weights(np.zeros_like(original))
        assert not np.allclose(m.get_weights(), original)

        m.set_weights(original)
        assert np.allclose(m.get_weights(), original)

    def test_set_weights_changes_predictions(self):
        # Use balanced classes and more epochs so the trained model predicts both classes
        rng = np.random.default_rng(42)
        X = rng.standard_normal((400, 41))
        y = np.array([0] * 200 + [1] * 200)
        m = FederatedModel(random_state=42)
        m.train(X, y, epochs=10)
        preds_before = m.predict(X).copy()

        # Large random weights are guaranteed to shift network output
        rng2 = np.random.default_rng(999)
        m.set_weights(rng2.standard_normal(m.weight_size()) * 50)
        preds_after = m.predict(X)

        assert not np.array_equal(preds_before, preds_after)

    def test_copy_from_is_independent(self):
        m1, X, y = _trained_model(seed=3)
        m2 = FederatedModel(random_state=99)
        m2.train(X, y, epochs=1)
        m2.copy_from(m1)

        assert np.allclose(m1.get_weights(), m2.get_weights())

        # Mutating m2 must not affect m1
        m2.set_weights(np.zeros_like(m2.get_weights()))
        assert not np.allclose(m1.get_weights(), m2.get_weights())

    def test_evaluate_returns_all_metrics(self):
        m, X, y = _trained_model(seed=4)
        metrics = m.evaluate(X, y)
        for key in ('accuracy', 'precision', 'recall', 'f1'):
            assert key in metrics
            assert 0.0 <= metrics[key] <= 1.0

    def test_weight_size_consistent(self):
        m, _, _ = _trained_model(seed=5)
        assert m.weight_size() == len(m.get_weights())

    def test_raises_before_training(self):
        m = FederatedModel()
        with pytest.raises(RuntimeError):
            m.get_weights()
