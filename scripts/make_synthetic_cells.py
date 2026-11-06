"""Generate a small fleet of synthetic capacity-fade curves so the agent can be tried without the dataset.

    python scripts/make_synthetic_cells.py demo_data
    python run_agent.py --data demo_data --out demo_outputs --no-llm

Curves follow the double-exponential "slow fade, then knee" shape seen in LFP/graphite cells, with
cell-to-cell variation, measurement noise, and a few planted anomalies (early knee, glitches, rest-recovery jumps, a test stopped early).
"""
import os
import sys

import numpy as np
import pandas as pd


def cell_curve(rng, life, knee_frac=0.7, noise=2e-4, q0=1.07):
    n = np.arange(1, life + 1)
    x = n / life
    slow = 0.03 * x
    fast = 0.16 * np.exp((x - 1) / (1 - knee_frac) * 2.5)
    q = q0 - slow - fast + rng.normal(0, noise, n.size)
    return n, q


def main(dst, n_cells=12, seed=7):
    rng = np.random.default_rng(seed)
    os.makedirs(dst, exist_ok=True)
    for i in range(n_cells):
        life = int(rng.integers(500, 1100))
        knee = 0.45 if i == 3 else rng.uniform(0.68, 0.78)          # one early-knee cell
        n, q = cell_curve(rng, life, knee_frac=knee, noise=rng.uniform(1e-4, 4e-4))
        if i == 5:                                                   # glitchy logger
            q[rng.choice(life, 6, replace=False)] = rng.choice([0.2, 1.6, 0.95], 6)
        if i == 8:                                                   # rest periods -> capacity recovery
            for c in rng.choice(np.arange(100, life - 100), 3, replace=False):
                q[c:c + 15] += 0.006 * np.exp(-np.arange(15) / 4)
        if i == 10:                                                  # test stopped long before end of life
            keep = int(0.35 * life); n, q = n[:keep], q[:keep]
        pd.DataFrame({"cycle_index": n, "discharge_capacity": q}).to_csv(
            os.path.join(dst, f"SYNTH_{i:03d}.csv"), index=False)
    print(f"wrote {n_cells} synthetic cells to {dst}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "demo_data")
