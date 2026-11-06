"""Tool 1/3: read one cell's per-cycle CSV and extract clean capacity-vs-cycle points."""
import os

import numpy as np
import pandas as pd


def load_and_extract(path, eol_ah=0.88):
    """Return clean discharge-capacity-vs-cycle points plus data-quality facts
    (outliers removed, capacity-recovery jumps after rests)."""
    df = pd.read_csv(path)
    df.columns = [c.lower().strip() for c in df.columns]
    df = df.rename(columns={"qd": "discharge_capacity"})
    if "cycle_index" not in df.columns:
        df["cycle_index"] = np.arange(1, len(df) + 1)
    df = df[(df["cycle_index"] > 0)].dropna(subset=["discharge_capacity"])

    n_all = df["cycle_index"].to_numpy(float)
    q_all = df["discharge_capacity"].to_numpy(float)

    # ---- hard glitches: physically impossible capacities ----
    ok = (q_all > 0.5) & (q_all < 1.3)
    # ---- soft outliers: points far from a rolling median ----
    med = pd.Series(np.where(ok, q_all, np.nan)).rolling(21, center=True, min_periods=5).median().to_numpy()
    resid = q_all - med
    mad = np.nanmedian(np.abs(resid[ok] - np.nanmedian(resid[ok]))) * 1.4826
    ok &= np.abs(resid) <= max(6 * mad, 0.01)

    n, q = n_all[ok], q_all[ok]
    noise = float(np.median(np.abs(np.diff(q))) * 1.4826 / np.sqrt(2))      # cycle-to-cycle noise (Ah)

    # ---- capacity-recovery jumps (typical after rest periods / test pauses) ----
    smooth = pd.Series(q).rolling(5, center=True, min_periods=1).median().to_numpy()
    jumps = np.where(np.diff(smooth) > max(4 * noise, 0.004))[0]
    paused = int((df["paused"] > 0).sum()) if "paused" in df.columns else None

    below = np.where(q < eol_ah)[0]
    return {
        "cell_id": os.path.splitext(os.path.basename(path))[0],
        "n": n, "q": q,
        "outlier_n": n_all[~ok], "outlier_q": q_all[~ok],
        "facts": {
            "cycles": int(len(n)), "first_cycle": int(n[0]), "last_cycle": int(n[-1]),
            "q_start_Ah": round(float(np.median(q[:10])), 4), "q_end_Ah": round(float(np.median(q[-10:])), 4),
            "eol_cycle": int(n[below[0]]) if len(below) else None,
            "outliers_removed": int((~ok).sum()), "noise_Ah": round(noise, 5),
            "recovery_jumps": int(len(jumps)), "paused_cycles": paused,
        },
    }
