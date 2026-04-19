import logging
import os
import urllib.request

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

logger = logging.getLogger(__name__)

NSL_KDD_URLS = {
    'train': 'https://raw.githubusercontent.com/sebastianairrott/NSL-KDD/master/KDDTrain%2B.txt',
    'test':  'https://raw.githubusercontent.com/sebastianairrott/NSL-KDD/master/KDDTest%2B.txt',
}

COLUMNS = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'label', 'difficulty',
]

CATEGORICAL_COLS = ['protocol_type', 'service', 'flag']


def download_nsl_kdd(data_dir='data/nsl_kdd'):
    os.makedirs(data_dir, exist_ok=True)
    train_path = os.path.join(data_dir, 'KDDTrain+.txt')
    test_path  = os.path.join(data_dir, 'KDDTest+.txt')

    if os.path.exists(train_path) and os.path.exists(test_path):
        logger.info('NSL-KDD dataset already present in %s', data_dir)
        return train_path, test_path

    logger.info('Downloading NSL-KDD dataset ...')
    try:
        urllib.request.urlretrieve(NSL_KDD_URLS['train'], train_path)
        urllib.request.urlretrieve(NSL_KDD_URLS['test'],  test_path)
        logger.info('Download complete.')
        return train_path, test_path
    except Exception as exc:
        logger.warning('Download failed (%s) — falling back to synthetic data.', exc)
        return None, None


def generate_synthetic_data(n_samples=50000, test_size=10000, random_state=42):
    logger.info('Generating synthetic network traffic data (n=%d) ...', n_samples)
    np.random.seed(random_state)

    n_normal = int(n_samples * 0.7)
    n_attack = n_samples - n_normal

    def _make_features(n, is_attack):
        return pd.DataFrame({
            'duration':       np.random.exponential(5 if is_attack else 50, n),
            'protocol_type':  np.random.choice(['tcp', 'udp', 'icmp'], n),
            'service':        np.random.choice(['http', 'ftp', 'smtp', 'dns', 'ssh', 'other'], n),
            'flag':           np.random.choice(['SF', 'S0', 'REJ', 'RSTR', 'OTH'], n),
            'src_bytes':      np.random.lognormal(12 if is_attack else 8, 2 if is_attack else 1.5, n),
            'dst_bytes':      np.random.lognormal(4  if is_attack else 8, 2 if is_attack else 1.5, n),
            'land':           np.random.choice([0, 1], n, p=[0.99, 0.01]),
            'wrong_fragment': np.random.choice([0, 1, 2, 3], n, p=[0.9, 0.05, 0.03, 0.02]),
            'urgent':         np.zeros(n, dtype=int),
            'hot':            np.random.poisson(0.1, n),
            'num_failed_logins':  np.random.poisson(0.05, n),
            'logged_in':      np.zeros(n, dtype=int) if is_attack else np.ones(n, dtype=int),
            'num_compromised':    np.random.poisson(0.1, n),
            'root_shell':         np.random.choice([0, 1], n, p=[0.98, 0.02]),
            'su_attempted':       np.random.choice([0, 1, 2], n, p=[0.95, 0.03, 0.02]),
            'num_root':           np.random.poisson(0.05, n),
            'num_file_creations': np.random.poisson(0.1, n),
            'num_shells':         np.random.poisson(0.02, n),
            'num_access_files':   np.random.poisson(0.05, n),
            'num_outbound_cmds':  np.zeros(n, dtype=int),
            'is_host_login':      np.zeros(n, dtype=int),
            'is_guest_login':     np.random.choice([0, 1], n, p=[0.9, 0.1]),
            'count':          np.random.poisson(50 if is_attack else 10, n),
            'srv_count':      np.random.poisson(10, n),
            'serror_rate':    np.random.beta(5, 2, n) if is_attack else np.random.beta(1, 10, n),
            'srv_serror_rate':    np.random.beta(1, 10, n),
            'rerror_rate':        np.random.beta(1, 20, n),
            'srv_rerror_rate':    np.random.beta(1, 20, n),
            'same_srv_rate':      np.random.beta(8, 2, n),
            'diff_srv_rate':  np.random.beta(5, 2, n) if is_attack else np.random.beta(2, 5, n),
            'srv_diff_host_rate': np.random.beta(1, 10, n),
            'dst_host_count':     np.random.poisson(10, n),
            'dst_host_srv_count': np.random.poisson(10, n),
            'dst_host_same_srv_rate':      np.random.beta(8, 2, n),
            'dst_host_diff_srv_rate':      np.random.beta(1, 10, n),
            'dst_host_same_src_port_rate': np.random.beta(5, 5, n),
            'dst_host_srv_diff_host_rate': np.random.beta(1, 10, n),
            'dst_host_serror_rate':        np.random.beta(5, 2, n) if is_attack else np.random.beta(1, 10, n),
            'dst_host_srv_serror_rate':    np.random.beta(1, 10, n),
            'dst_host_rerror_rate':        np.random.beta(1, 20, n),
            'dst_host_srv_rerror_rate':    np.random.beta(1, 20, n),
            'label':      np.full(n, 'attack' if is_attack else 'normal'),
            'difficulty': np.random.choice(range(1, 43), n),
        })

    train_df = pd.concat([_make_features(n_normal, False), _make_features(n_attack, True)],
                         ignore_index=True).sample(frac=1, random_state=random_state).reset_index(drop=True)

    np.random.seed(random_state + 1)
    n_test_normal = int(test_size * 0.6)
    test_df = pd.concat([_make_features(n_test_normal, False),
                         _make_features(test_size - n_test_normal, True)],
                        ignore_index=True).sample(frac=1, random_state=random_state + 1).reset_index(drop=True)

    return train_df, test_df


def load_data(data_dir='data/nsl_kdd', use_synthetic=True):
    if not use_synthetic:
        train_path, test_path = download_nsl_kdd(data_dir)
        if train_path and os.path.exists(train_path):
            logger.info('Loading NSL-KDD from %s ...', data_dir)
            train_df = pd.read_csv(train_path, header=None, names=COLUMNS)
            test_df  = pd.read_csv(test_path,  header=None, names=COLUMNS)
            return train_df, test_df

    return generate_synthetic_data()


def preprocess_data(df, label_encoders=None, scaler=None, fit=True):
    df = df.copy()
    df['binary_label'] = (df['label'] != 'normal').astype(int)

    if label_encoders is None:
        label_encoders = {}

    for col in CATEGORICAL_COLS:
        if fit:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
        else:
            le = label_encoders[col]
            df[col] = df[col].astype(str).apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else -1
            )

    feature_cols = [c for c in COLUMNS[:41] if c not in CATEGORICAL_COLS] + CATEGORICAL_COLS
    X = df[feature_cols].values.astype(float)
    y = df['binary_label'].values

    if fit:
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)
    else:
        X = scaler.transform(X)

    return X, y, label_encoders, scaler


def partition_for_offices(X, y, n_offices=5, random_state=42):
    np.random.seed(random_state)
    indices        = np.random.permutation(len(X))
    partition_size = len(X) // n_offices
    partitions = []
    for i in range(n_offices):
        start = i * partition_size
        end   = start + partition_size if i < n_offices - 1 else len(X)
        idx   = indices[start:end]
        partitions.append({'X': X[idx], 'y': y[idx]})
    return partitions


class DataLoader:
    def __init__(self, data_dir='data/nsl_kdd', n_offices=5, use_synthetic=True):
        self.n_offices = n_offices
        train_df, test_df = load_data(data_dir, use_synthetic)

        self.X_train, self.y_train, self.label_encoders, self.scaler = \
            preprocess_data(train_df, fit=True)
        self.X_test, self.y_test, _, _ = \
            preprocess_data(test_df, self.label_encoders, self.scaler, fit=False)

        self.partitions = partition_for_offices(self.X_train, self.y_train, n_offices)

        logger.info('DataLoader ready — train=%d  test=%d  offices=%d  attack_ratio=%.2f%%',
                    len(self.X_train), len(self.X_test), n_offices,
                    self.y_train.mean() * 100)

    def get_office_data(self, office_id: int) -> dict:
        if office_id >= self.n_offices:
            raise ValueError(f'Office {office_id} does not exist (n_offices={self.n_offices})')
        return self.partitions[office_id]

    def get_test_data(self):
        return self.X_test, self.y_test
