import sys
import os
import time
import numpy as np
import random

# Add parent directory to path to import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crypto_utils import generate_id_hash, apply_laplace_dp
from core.aggregation import krum_aggregate

class MoISimulator:
    def __init__(self):
        self.num_offices = 5
        self.reputation = {i: 100 for i in range(self.num_offices)}
        self.log_file = "logs/moi_simulation.log"
        self.global_model = np.array([0.15, 0.42, 0.88, 0.21])

    def write_log(self, office, status, msg):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f'time="{timestamp}", office={office}, status="{status}", reputation={self.reputation[office]}, msg="{msg}"\n'
        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def run_cycle(self, attack=False):
        updates = []
        for i in range(self.num_offices):
            # 1. Identity Phase
            cid = f"CITIZEN_{random.randint(1000, 9999)}"
            h = generate_id_hash(cid, i)
            
            # 2. ML Phase
            if i == 4 and attack:
                local_weights = np.array([10.0, 10.0, 10.0, 10.0]) # Poison
                self.write_log(i, "ALERT", "Data poisoning attempt detected")
            else:
                local_weights = apply_laplace_dp(self.global_model + np.random.normal(0, 0.02, 4))
                self.write_log(i, "SUCCESS", f"Registered ID: {h[:8]}...")
            
            updates.append(local_weights)

        # 3. Aggregation & Slashing
        winner = krum_aggregate(updates)
        if attack:
            self.reputation[4] -= 25
            self.write_log(4, "SLASHED", "Byzantine behavior punished by Blockchain")
        
        return winner

if __name__ == "__main__":
    if not os.path.exists('logs'): os.makedirs('logs')
    sim = MoISimulator()
    print("Simulation started. Office 4 will attack in 5 seconds...")
    time.sleep(2)
    sim.run_cycle(attack=False)
    time.sleep(3)
    sim.run_cycle(attack=True)
    print("Simulation cycle complete. Logs updated.")