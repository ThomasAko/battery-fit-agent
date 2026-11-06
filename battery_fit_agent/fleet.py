"""Post-hoc, fleet-relative review of a finished run (no re-fitting, no LLM).

The per-cell criterion "RMSE >> own noise" flags nearly every long, low-noise Severson cell, because no
3-4 parameter law tracks ~1000 cycles at the 0.1 mAh noise floor. Judging each cell against the rest of
the fleet instead ("is this cell's misfit / knee / shape unusual?") produces a shortlist a human can use.
"""
import glob
import os

import numpy as np
import pandas as pd

from .fitting import PARAMETRIC


def best_parametric(out_dir):
    """Best parametric law per cell, read back from the saved *_fits.csv tables
    (deep-dive spline / 2-break excluded, since those are flexible, not physical laws)."""
    rows = []
    for f in sorted(glob.glob(os.path.join(out_dir, "*_fits.csv"))):
        t = pd.read_csv(f, index_col=0)
        t = t[t.index.isin(PARAMETRIC)].sort_values("bic")
        rows.append({"cell_id": os.path.basename(f).replace("_fits.csv", ""),
                     "best_parametric": t.index[0], "rmse_mAh": t.iloc[0]["rmse_mAh"],
                     "runner_up": t.index[1], "delta_bic_runner_up": round(t.iloc[1]["bic"] - t.iloc[0]["bic"], 1)})
    return pd.DataFrame(rows)


def robust_z(s):
    """How unusual each cell is relative to the fleet (median/MAD version of a z-score)."""
    s = s.astype(float); med = s.median(); mad = 1.4826 * (s - med).abs().median()
    return (s - med) / (mad if mad > 0 else 1e-9)


def fade_progress(data_store, cell_ids, eol_ah=0.88):
    """How far each test got towards end of life: 0 = no fade yet, 1 = reached 80 % capacity."""
    from .extract import load_and_extract
    rows = []
    for c in cell_ids:
        f = load_and_extract(os.path.join(data_store, f"{c}.csv"), eol_ah=eol_ah)["facts"]
        span = max(f["q_start_Ah"] - eol_ah, 1e-6)
        rows.append({"cell_id": c, "q_start_Ah": f["q_start_Ah"], "q_end_Ah": f["q_end_Ah"],
                     "fade_completed": round(min((f["q_start_Ah"] - f["q_end_Ah"]) / span, 1.5), 3)})
    return pd.DataFrame(rows)


def fleet_review(out_dir, shape_margin=0.0, data_store=None, min_fade=0.7, eol_ah=0.88, write=True):
    """Re-score every cell against the fleet.

    Defaults reproduce the original post-hoc review. The investigator mode tightens it:
      shape_margin  only call a shape "different" if the fleet law loses by at least this many BIC units
      data_store    if given, cells whose test stopped well short of end of life (fade_completed < min_fade)
                    are excluded from the knee comparison, since their knee is measured against test length
    """
    summ = pd.read_csv(os.path.join(out_dir, "summary.csv"))
    param = best_parametric(out_dir)
    wf = summ[["cell_id", "cycles", "eol_cycle", "noise_mAh", "knee_cycle", "knee_fraction",
               "outliers", "recovery_jumps"]].merge(param, on="cell_id")

    majority = wf["best_parametric"].mode()[0]                 # the fleet's typical degradation law
    wf["misfit_z"] = robust_z(wf["rmse_mAh"]).round(2)          # misfit vs. the other cells, not vs. own noise
    comparable = pd.Series(True, index=wf.index)
    if data_store:
        wf = wf.merge(fade_progress(data_store, wf["cell_id"], eol_ah), on="cell_id")
        comparable = wf["fade_completed"] >= min_fade
    wf["knee_z"] = np.nan
    wf.loc[comparable, "knee_z"] = robust_z(wf.loc[comparable, "knee_fraction"]).round(2)  # knee as fraction of life

    # how much the fleet law loses by, when it is not the winner (read from the fit tables)
    def majority_gap(cell):
        t = pd.read_csv(os.path.join(out_dir, f"{cell}_fits.csv"), index_col=0)
        t = t[t.index.isin(PARAMETRIC)]
        return round(float(t.loc[majority, "bic"] - t["bic"].min()), 1) if majority in t.index else np.inf
    wf["majority_gap_bic"] = [majority_gap(c) for c in wf["cell_id"]]

    def reasons(r):
        out = []
        if r.misfit_z > 2.5:
            out.append(f"misfit unusually large for this fleet (RMSE {r.rmse_mAh} mAh, z={r.misfit_z})")
        if data_store and r.fade_completed < min_fade:
            out.append(f"test ended {r.fade_completed:.0%} of the way to end of life; knee position not comparable")
        elif r.knee_z < -3:
            out.append(f"knee unusually early in life (at {r.knee_fraction:.0%} of life, z={r.knee_z})")
        if r.delta_bic_runner_up < 2:
            out.append(f"{r.best_parametric} and {r.runner_up} statistically tied (dBIC={r.delta_bic_runner_up})")
        if r.best_parametric != majority and r.majority_gap_bic >= shape_margin:
            out.append(f"degradation shape differs from the fleet ({r.best_parametric} beats {majority}"
                       + (f" by dBIC={r.majority_gap_bic})" if shape_margin else ")"))
        if r.outliers >= 3:                                     # 1 is usually just the incomplete last cycle
            out.append(f"{r.outliers} outlier cycles removed")
        if r.recovery_jumps >= 3:
            out.append(f"{r.recovery_jumps} capacity-recovery jumps")
        return out

    wf["reasons"] = wf.apply(reasons, axis=1)
    wf["flag"] = wf["reasons"].str.len() > 0
    wf["priority"] = np.where(wf["reasons"].str.len() >= 2, "high", np.where(wf["flag"], "medium", "-"))
    if write:
        wf.to_csv(os.path.join(out_dir, "summary_fleet.csv"), index=False)
    return wf, majority, summ
