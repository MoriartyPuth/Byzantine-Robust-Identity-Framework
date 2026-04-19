#!/usr/bin/env python3
"""
Byzantine-Robust Identity Framework
Main entry point — loads config.yaml and dispatches experiment modes.
"""

import argparse
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import yaml
    def _load_config(path='config.yaml'):
        with open(path) as f:
            return yaml.safe_load(f)
except ImportError:
    def _load_config(_path='config.yaml'):
        logging.warning('PyYAML not installed — using default config values.')
        return {}


def _setup_logging(cfg: dict):
    log_cfg = cfg.get('logging', {})
    level   = getattr(logging, log_cfg.get('level', 'INFO').upper(), logging.INFO)
    logfile = log_cfg.get('file', 'logs/run.log')
    os.makedirs('logs', exist_ok=True)

    handlers = [logging.StreamHandler(sys.stdout)]
    try:
        handlers.append(logging.FileHandler(logfile))
    except Exception:
        pass

    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S',
        handlers=handlers,
    )


def _build_fl(cfg: dict, attack_office=None):
    from data.loader import DataLoader
    from core.federated import FederatedLearning

    fl_cfg = cfg.get('federated_learning', {})
    dp_cfg = cfg.get('differential_privacy', {})
    da_cfg = cfg.get('data', {})

    loader = DataLoader(
        n_offices=fl_cfg.get('n_offices', 5),
        use_synthetic=da_cfg.get('use_synthetic', True),
    )
    return FederatedLearning(
        data_loader   = loader,
        n_offices     = fl_cfg.get('n_offices', 5),
        num_rounds    = fl_cfg.get('num_rounds', 10),
        local_epochs  = fl_cfg.get('local_epochs', 5),
        epsilon       = dp_cfg.get('epsilon_per_round', 0.5),
        clip_norm     = dp_cfg.get('clip_norm', 1.0),
        attack_office = attack_office,
    )


# ── Experiment modes ──────────────────────────────────────────────────────────

def run_baseline(cfg: dict):
    logger = logging.getLogger('baseline')
    logger.info('=== BASELINE EXPERIMENT (all honest offices) ===')
    fl = _build_fl(cfg, attack_office=None)
    metrics = fl.run()
    pd.DataFrame(metrics).to_csv('logs/baseline_metrics.csv', index=False)
    logger.info('Baseline complete. Final accuracy: %.4f', metrics[-1]['accuracy'])
    return metrics


def run_byzantine(cfg: dict):
    logger = logging.getLogger('byzantine')
    attack_office = cfg.get('byzantine', {}).get('attack_office', 4)
    logger.info('=== BYZANTINE EXPERIMENT (office %d attacks) ===', attack_office)
    fl = _build_fl(cfg, attack_office=attack_office)
    metrics = fl.run()
    pd.DataFrame(metrics).to_csv('logs/byzantine_metrics.csv', index=False)
    logger.info('Byzantine complete. Final accuracy: %.4f', metrics[-1]['accuracy'])
    return metrics


def run_dp_sensitivity(cfg: dict):
    logger = logging.getLogger('dp_sensitivity')
    logger.info('=== DIFFERENTIAL PRIVACY SENSITIVITY ANALYSIS ===')

    fl_cfg = cfg.get('federated_learning', {})
    da_cfg = cfg.get('data', {})
    dp_cfg = cfg.get('differential_privacy', {})

    from data.loader import DataLoader
    from core.federated import FederatedLearning

    results = []
    for eps in [1.0, 3.0, 5.0, 10.0]:
        logger.info('Testing epsilon=%.1f', eps)
        loader = DataLoader(
            n_offices=fl_cfg.get('n_offices', 5),
            use_synthetic=da_cfg.get('use_synthetic', True),
        )
        fl = FederatedLearning(
            data_loader  = loader,
            n_offices    = fl_cfg.get('n_offices', 5),
            num_rounds   = 8,
            local_epochs = fl_cfg.get('local_epochs', 20),
            epsilon      = eps,
            clip_norm    = dp_cfg.get('clip_norm', 5.0),
        )
        m = fl.run()
        results.append({
            'epsilon':        eps,
            'final_accuracy': m[-1]['accuracy'],
            'final_f1':       m[-1]['f1'],
        })
        logger.info('eps=%.1f -> acc=%.4f  f1=%.4f', eps, m[-1]['accuracy'], m[-1]['f1'])

    df = pd.DataFrame(results)
    df.to_csv('logs/dp_sensitivity.csv', index=False)
    logger.info('DP sensitivity results saved.')
    return results


def run_reputation_demo(cfg: dict):
    logger = logging.getLogger('reputation')
    logger.info('=== BLOCKCHAIN REPUTATION DEMO ===')

    from core.web3_client import ReputationManager, BlockchainClient
    bc_cfg = cfg.get('blockchain', {})
    client = BlockchainClient(
        provider_url     = bc_cfg.get('provider_url', ''),
        contract_address = bc_cfg.get('contract_address', ''),
    )
    rep = ReputationManager(client)
    rep.initialize_offices(5)

    logger.info('Initial reputations: %s', {i: rep.get_reputation(i) for i in range(5)})

    rep.slash_malicious(4, 'byzantine_poisoning')
    logger.info('Office 4 slashed. Reputation: %d', rep.get_reputation(4))
    logger.info('Office 4 banned: %s', rep.is_banned(4))

    for i in range(4):
        rep.reward_honest(i)

    logger.info('Final reputations: %s', {i: rep.get_reputation(i) for i in range(5)})
    rep.save_audit_log()


def run_full_suite(cfg: dict):
    logger = logging.getLogger('full')
    logger.info('=== FULL EXPERIMENT SUITE ===')

    baseline_metrics  = run_baseline(cfg)
    byzantine_metrics = run_byzantine(cfg)
    run_dp_sensitivity(cfg)
    run_reputation_demo(cfg)

    from reports.generator import ReportGenerator
    gen = ReportGenerator()
    gen.add_experiment('Baseline',  {'n_offices': 5}, baseline_metrics)
    gen.add_experiment('Byzantine', {'n_offices': 5, 'attack_office': 4}, byzantine_metrics)
    html_path = gen.generate_html_report()
    logger.info('HTML report saved to %s', html_path)

    logger.info('All experiments complete.')


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Byzantine-Robust Identity Framework')
    parser.add_argument('--mode', default='full',
                        choices=['baseline', 'byzantine', 'dp', 'reputation', 'full'])
    parser.add_argument('--config', default='config.yaml', help='Path to config.yaml')
    parser.add_argument('--rounds',        type=int,   help='Override num_rounds')
    parser.add_argument('--n-offices',     type=int,   help='Override n_offices')
    parser.add_argument('--epsilon',       type=float, help='Override epsilon_per_round')
    parser.add_argument('--attack-office', type=int,   help='Override attack_office')
    args = parser.parse_args()

    cfg = _load_config(args.config)
    _setup_logging(cfg)

    # CLI overrides
    if args.rounds:
        cfg.setdefault('federated_learning', {})['num_rounds'] = args.rounds
    if args.n_offices:
        cfg.setdefault('federated_learning', {})['n_offices'] = args.n_offices
    if args.epsilon:
        cfg.setdefault('differential_privacy', {})['epsilon_per_round'] = args.epsilon
    if args.attack_office is not None:
        cfg.setdefault('byzantine', {})['attack_office'] = args.attack_office

    dispatch = {
        'baseline':   run_baseline,
        'byzantine':  run_byzantine,
        'dp':         run_dp_sensitivity,
        'reputation': run_reputation_demo,
        'full':       run_full_suite,
    }
    dispatch[args.mode](cfg)


if __name__ == '__main__':
    main()
