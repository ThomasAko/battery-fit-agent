"""Investigation tools. Every number the investigator sees comes from one of these functions;
the LLM decides which to call and how to interpret the results, but never computes anything itself."""
import json
import os

import numpy as np
import pandas as pd
from langchain_core.tools import tool

from .extract import load_and_extract
from .fitting import PARAMETRIC, fit_all, rank_fits

FLEET_METRICS = ["knee_fraction", "rmse_mAh", "noise_mAh", "cycles", "eol_cycle", "fade_rate_mAh_per_100",
                 "outliers"]


class CellStore:
    """Read-only access to one finished run: fleet table, per-cell fit tables, raw per-cell data."""

    def __init__(self, fleet_df, out_dir, data_store, eol_ah=0.88):
        self.fleet = fleet_df.set_index("cell_id")
        self.out_dir, self.data_store, self.eol_ah = out_dir, data_store, eol_ah
        self._cells = {}
        self.fleet["fade_rate_mAh_per_100"] = [self._fade_rate(c) for c in self.fleet.index]

    def cell(self, cell_id):
        if cell_id not in self._cells:
            self._cells[cell_id] = load_and_extract(os.path.join(self.data_store, f"{cell_id}.csv"), self.eol_ah)
        return self._cells[cell_id]

    def _fade_rate(self, cell_id):
        c = self.cell(cell_id)
        k = min(100, len(c["n"]) // 3)
        return round(1e5 * float(np.median(c["q"][:k]) - np.median(c["q"][-k:])) / max(c["n"][-1] - c["n"][0], 1), 3)

    def fits(self, cell_id):
        return pd.read_csv(os.path.join(self.out_dir, f"{cell_id}_fits.csv"), index_col=0)

    def check(self, cell_id):
        if cell_id not in self.fleet.index:
            raise KeyError(f"unknown cell_id {cell_id!r}")


def _clean(o):
    """JSON-safe, rounded copy: numpy -> python, NaN -> None, floats to 4 significant decimals."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)):
        return [_clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else round(float(o), 4)
    return o if o is None or isinstance(o, str) else str(o)


def _j(d):
    return json.dumps(_clean(d))


def make_tools(store: CellStore):
    @tool
    def get_cell_overview(cell_id: str) -> str:
        """Key facts for one cell: cycles, end-of-life cycle, start/end capacity, noise, knee, outliers,
        best parametric law and runner-up, fleet z-scores and the reasons it was shortlisted."""
        store.check(cell_id)
        r = store.fleet.loc[cell_id]; f = store.cell(cell_id)["facts"]
        return _j({"cell_id": cell_id, "cycles": f["cycles"], "eol_cycle": f["eol_cycle"],
                   "reached_end_of_life": f["eol_cycle"] is not None,
                   "q_start_Ah": f["q_start_Ah"], "q_end_Ah": f["q_end_Ah"], "noise_mAh": 1e3 * f["noise_Ah"],
                   "knee_cycle": r.get("knee_cycle"), "knee_fraction_of_life": r.get("knee_fraction"),
                   "outliers_removed": f["outliers_removed"], "recovery_jumps": f["recovery_jumps"],
                   "best_parametric_law": r.get("best_parametric"), "runner_up": r.get("runner_up"),
                   "delta_bic_runner_up": r.get("delta_bic_runner_up"), "misfit_z": r.get("misfit_z"),
                   "knee_z": r.get("knee_z"), "shortlist_reasons": r.get("reasons")})

    @tool
    def check_end_of_life(cell_id: str) -> str:
        """Did the test reach end of life (80 % capacity, 0.88 Ah)? Returns how much of the fade to end of life
        was completed and the recent fade rate, to tell an early knee apart from a test that simply stopped early."""
        store.check(cell_id)
        c = store.cell(cell_id); f = c["facts"]; n, q = c["n"], c["q"]
        span = f["q_start_Ah"] - store.eol_ah
        done = (f["q_start_Ah"] - f["q_end_Ah"]) / span if span > 0 else None
        k = min(100, len(n) // 3)
        slope = np.polyfit(n[-k:], q[-k:], 1)[0] if k >= 10 else np.nan     # Ah per cycle near the end
        to_go = (f["q_end_Ah"] - store.eol_ah) / -slope if slope < 0 and f["eol_cycle"] is None else None
        return _j({"reached_end_of_life": f["eol_cycle"] is not None, "eol_cycle": f["eol_cycle"],
                   "last_cycle": f["last_cycle"], "q_end_Ah": f["q_end_Ah"],
                   "fade_completed_fraction": done, "recent_fade_mAh_per_100_cycles": -1e5 * slope,
                   "cycles_to_end_of_life_at_recent_rate": to_go})

    @tool
    def locate_outliers(cell_id: str) -> str:
        """Where the removed outlier cycles sit (by quarter of the test), whether they cluster, and how far
        they fall from the trend. Clustered, one-sided dips suggest a measurement or equipment problem."""
        store.check(cell_id)
        c = store.cell(cell_id); n = c["n"]; on, oq = c["outlier_n"], c["outlier_q"]
        if len(on) == 0:
            return _j({"outliers": 0})
        edges = np.linspace(n.min(), n.max(), 5)
        per_q = np.histogram(on, edges)[0].tolist()
        trend = np.interp(on, n, pd.Series(c["q"]).rolling(31, center=True, min_periods=1).median())
        dev = 1e3 * (oq - trend)
        return _j({"outliers": int(len(on)), "per_quarter_of_test": per_q,
                   "first_cycle": on.min(), "last_cycle": on.max(),
                   "fraction_below_trend": float(np.mean(dev < 0)), "median_deviation_mAh": float(np.median(dev)),
                   "recovery_jumps": c["facts"]["recovery_jumps"]})

    @tool
    def compare_to_fleet(cell_id: str, metric: str) -> str:
        """Compare one metric of this cell with the whole fleet (median, quartiles, percentile of this cell).
        metric is one of: knee_fraction, rmse_mAh, noise_mAh, cycles, eol_cycle, fade_rate_mAh_per_100, outliers."""
        store.check(cell_id)
        if metric not in FLEET_METRICS:
            return _j({"error": f"metric must be one of {FLEET_METRICS}"})
        s = store.fleet[metric].astype(float); v = s.loc[cell_id]
        return _j({"metric": metric, "cell_value": v, "fleet_median": s.median(),
                   "fleet_p25": s.quantile(0.25), "fleet_p75": s.quantile(0.75),
                   "cell_percentile": None if np.isnan(v) else round(100 * float((s.dropna() < v).mean()), 1),
                   "n_cells": int(s.notna().sum())})

    @tool
    def get_fit_table(cell_id: str) -> str:
        """All candidate laws fitted to the whole test, ranked by BIC (RMSE in mAh, R2, BIC, delta BIC)."""
        store.check(cell_id)
        t = store.fits(cell_id)
        t = t[t.index.isin(PARAMETRIC)].sort_values("bic")
        t["delta_bic"] = (t["bic"] - t["bic"].min()).round(1)
        return _j(t[["rmse_mAh", "r2", "bic", "delta_bic"]].to_dict(orient="index"))

    @tool
    def refit_window(cell_id: str, start_cycle: int, end_cycle: int) -> str:
        """Refit all candidate laws on a window of cycles only (e.g. before or after the knee, or excluding a
        suspicious stretch) and rank them by BIC. Needs at least 50 cycles in the window."""
        store.check(cell_id)
        c = store.cell(cell_id); m = (c["n"] >= start_cycle) & (c["n"] <= end_cycle)
        if m.sum() < 50:
            return _j({"error": f"only {int(m.sum())} cycles in window; need at least 50"})
        t = rank_fits(fit_all(c["n"][m], c["q"][m]))
        return _j({"window": [int(c["n"][m].min()), int(c["n"][m].max())], "cycles": int(m.sum()),
                   "ranking": t[["rmse_mAh", "bic", "delta_bic"]].head(4).to_dict(orient="index")})

    return [get_cell_overview, check_end_of_life, locate_outliers, compare_to_fleet, get_fit_table, refit_window]
