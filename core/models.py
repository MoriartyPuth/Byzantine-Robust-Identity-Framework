import copy
import logging
import numpy as np
import pickle
import os
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class FederatedModel:
    """
    MLP-based federated model with proper weight extraction and injection.

    Weight vector layout (flat numpy array):
      [coef_layer0.flatten(), coef_layer1.flatten(), ...,
       intercept_layer0.flatten(), intercept_layer1.flatten(), ...]

    This layout is fixed after the first call to train() and must be
    consistent across all office models and the global model.
    """

    def __init__(self, n_features=41, hidden_layers=(64, 32), random_state=42):
        self.n_features = n_features
        self.hidden_layers = hidden_layers
        self.random_state = random_state
        self._coef_shapes = None      # set on first train()
        self._intercept_shapes = None
        self.model = self._build_model()

    def _build_model(self):
        return MLPClassifier(
            hidden_layer_sizes=self.hidden_layers,
            activation='relu',
            solver='sgd',
            learning_rate='constant',
            learning_rate_init=0.01,
            max_iter=5,
            warm_start=True,
            tol=1e-10,
            n_iter_no_change=1000,
            random_state=self.random_state,
        )

    def train(self, X, y, epochs=5):
        self.model.max_iter = epochs
        self.model.fit(X, y)
        if self._coef_shapes is None:
            self._coef_shapes = [c.shape for c in self.model.coefs_]
            self._intercept_shapes = [b.shape for b in self.model.intercepts_]
        return self

    def get_weights(self):
        if not hasattr(self.model, 'coefs_'):
            raise RuntimeError('Model has not been trained yet.')
        parts = [c.flatten() for c in self.model.coefs_] + \
                [b.flatten() for b in self.model.intercepts_]
        return np.concatenate(parts)

    def set_weights(self, flat_weights):
        """Inject a flat weight vector back into the model's coefs_ and intercepts_."""
        if not hasattr(self.model, 'coefs_'):
            raise RuntimeError('Model must be trained at least once before set_weights().')
        idx = 0
        for i, shape in enumerate(self._coef_shapes):
            size = shape[0] * shape[1]
            self.model.coefs_[i] = flat_weights[idx:idx + size].reshape(shape)
            idx += size
        for i, shape in enumerate(self._intercept_shapes):
            size = shape[0]
            self.model.intercepts_[i] = flat_weights[idx:idx + size].reshape(shape)
            idx += size

    def copy_from(self, other):
        self.model = copy.deepcopy(other.model)
        self._coef_shapes = other._coef_shapes
        self._intercept_shapes = other._intercept_shapes

    def weight_size(self):
        if self._coef_shapes is None:
            raise RuntimeError('Model not yet trained.')
        coef_total = sum(s[0] * s[1] for s in self._coef_shapes)
        bias_total = sum(s[0] for s in self._intercept_shapes)
        return coef_total + bias_total

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]

    def evaluate(self, X, y):
        y_pred = self.predict(X)
        return {
            'accuracy':  accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall':    recall_score(y, y_pred, zero_division=0),
            'f1':        f1_score(y, y_pred, zero_division=0),
        }

    def save(self, path):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            return pickle.load(f)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    np.random.seed(42)
    X = np.random.randn(1000, 41)
    y = np.random.randint(0, 2, 1000)

    model = FederatedModel()
    model.train(X, y, epochs=3)

    w = model.get_weights()
    logger.info('Weight vector size: %d', w.shape[0])

    model2 = FederatedModel()
    model2.train(X, y, epochs=1)
    model2.set_weights(w)

    assert np.allclose(model.get_weights(), model2.get_weights()), 'set_weights roundtrip failed'
    logger.info('get_weights / set_weights roundtrip: OK')

    metrics = model.evaluate(X, y)
    logger.info('Metrics: %s', metrics)
