import hashlib
import numpy as np

def generate_id_hash(biometrics, office_id):
    """SHA-3 Salted Hashing for Identity Commitment."""
    salt = f"OFFICE_{office_id}_SECRET_SALT_2026"
    data = f"{biometrics}{salt}".encode()
    return hashlib.sha3_256(data).hexdigest()

def apply_laplace_dp(weights, epsilon=0.5):
    """Adds Differential Privacy noise to model weights."""
    sensitivity = 1.0
    beta = sensitivity / epsilon
    noise = np.random.laplace(0, beta, weights.shape)
    return weights + noise