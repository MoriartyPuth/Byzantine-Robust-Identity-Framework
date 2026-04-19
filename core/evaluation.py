import os
import numpy as np
import pandas as pd
import time
from datetime import datetime


class ExperimentEvaluator:
    def __init__(self, output_dir='logs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.experiments = []
        self.current_experiment = None
    
    def start_experiment(self, name, config):
        self.current_experiment = {
            'name': name,
            'config': config,
            'start_time': time.time(),
            'metrics': []
        }
    
    def log_round(self, round_num, metrics):
        if self.current_experiment:
            self.current_experiment['metrics'].append({
                'round': round_num,
                **metrics
            })
    
    def end_experiment(self):
        if self.current_experiment:
            self.current_experiment['end_time'] = time.time()
            self.current_experiment['duration'] = (
                self.current_experiment['end_time'] - 
                self.current_experiment['start_time']
            )
            self.experiments.append(self.current_experiment)
            self._save_experiment(self.current_experiment)
            self.current_experiment = None
    
    def _save_experiment(self, exp):
        df = pd.DataFrame(exp['metrics'])
        filename = self.output_dir + '/' + exp['name'] + '_metrics.csv'
        df.to_csv(filename, index=False)
        
        config_file = self.output_dir + '/' + exp['name'] + '_config.txt'
        with open(config_file, 'w') as f:
            for k, v in exp['config'].items():
                f.write(k + ': ' + str(v) + '\n')
            f.write('duration: ' + str(round(exp['duration'], 2)) + 's\n')
    
    def get_summary(self):
        summary = []
        for exp in self.experiments:
            metrics = exp['metrics']
            if metrics:
                summary.append({
                    'experiment': exp['name'],
                    'rounds': len(metrics),
                    'initial_acc': metrics[0]['accuracy'],
                    'final_acc': metrics[-1]['accuracy'],
                    'best_acc': max(m['accuracy'] for m in metrics),
                    'avg_f1': np.mean([m['f1'] for m in metrics]),
                    'duration': exp['duration']
                })
        return pd.DataFrame(summary)


class AttackAnalyzer:
    def __init__(self):
        self.attack_log = []
    
    def log_attack(self, round_num, office_id, attack_type, detected, 
                   accuracy_before, accuracy_after):
        self.attack_log.append({
            'round': round_num,
            'office': office_id,
            'attack_type': attack_type,
            'detected': detected,
            'accuracy_before': accuracy_before,
            'accuracy_after': accuracy_after,
            'impact': accuracy_before - accuracy_after
        })
    
    def get_detection_rate(self):
        if not self.attack_log:
            return 0.0
        detected = sum(1 for a in self.attack_log if a['detected'])
        return detected / len(self.attack_log)
    
    def get_avg_impact(self):
        if not self.attack_log:
            return 0.0
        return np.mean([a['impact'] for a in self.attack_log])
    
    def save(self, path='logs/attack_analysis.csv'):
        df = pd.DataFrame(self.attack_log)
        df.to_csv(path, index=False)
        return df


class ReputationTracker:
    def __init__(self, n_offices=5, initial_reputation=100):
        self.n_offices = n_offices
        self.reputation = {i: initial_reputation for i in range(n_offices)}
        self.history = []
    
    def slash(self, office_id, amount=50):
        self.reputation[office_id] = max(0, self.reputation[office_id] - amount)
        self.history.append({
            'office': office_id,
            'action': 'slash',
            'amount': amount,
            'new_reputation': self.reputation[office_id]
        })
    
    def reward(self, office_id, amount=5):
        self.reputation[office_id] = min(100, self.reputation[office_id] + amount)
        self.history.append({
            'office': office_id,
            'action': 'reward',
            'amount': amount,
            'new_reputation': self.reputation[office_id]
        })
    
    def is_banned(self, office_id):
        return self.reputation[office_id] < 50
    
    def get_all(self):
        return self.reputation.copy()
    
    def save(self, path='logs/reputation_history.csv'):
        df = pd.DataFrame(self.history)
        df.to_csv(path, index=False)
        return df


if __name__ == '__main__':
    print('Testing Evaluation Module...')
    evaluator = ExperimentEvaluator()
    evaluator.start_experiment('test', {'rounds': 5})
    for i in range(5):
        evaluator.log_round(i, {'accuracy': 0.7 + i*0.03, 'f1': 0.65 + i*0.03})
    evaluator.end_experiment()
    print(evaluator.get_summary())
