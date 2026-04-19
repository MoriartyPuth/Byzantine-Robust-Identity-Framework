import numpy as np
import pandas as pd
import os

def krum_aggregate(updates, num_malicious=1):
    """Selects the most honest model update and logs Krum scores."""
    n = len(updates)
    scores = []
    
    for i in range(n):
        distances = [np.linalg.norm(updates[i] - updates[j])**2 for j in range(n) if i != j]
        distances.sort()
        # Krum score: sum of n-f-2 closest neighbors
        score = sum(distances[:n - num_malicious - 2])
        scores.append(score)
    
    # Save scores for the Dashboard to read
    if not os.path.exists('logs'): os.makedirs('logs')
    k_df = pd.DataFrame({'office': range(n), 'krum_score': scores})
    k_df.to_csv("logs/krum_scores.csv", index=False)
            
    return np.argmin(scores)