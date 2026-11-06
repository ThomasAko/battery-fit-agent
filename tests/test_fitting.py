import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from make_synthetic_cells import cell_curve  # noqa: E402

from battery_fit_agent.extract import load_and_extract  # noqa: E402
from battery_fit_agent.fitting import compute_signals, fit_all, rank_fits, rule_flags  # noqa: E402


def _cell(tmp_path, glitches=0):
    rng = np.random.default_rng(0)
    n, q = cell_curve(rng, 800, knee_frac=0.72, noise=2e-4)
    if glitches:
        q[[100, 300, 500][:glitches]] = 0.2
    p = tmp_path / "c.csv"
    pd.DataFrame({"cycle_index": n, "QD": q}).to_csv(p, index=False)   # "QD" alias is accepted
    return load_and_extract(str(p))


def test_extract_removes_glitches(tmp_path):
    cell = _cell(tmp_path, glitches=3)
    assert cell["facts"]["outliers_removed"] >= 3
    assert cell["q"].min() > 0.5


def test_fit_ranks_flexible_law_above_linear(tmp_path):
    cell = _cell(tmp_path)
    fits = fit_all(cell["n"], cell["q"])
    table = rank_fits(fits)
    assert {"linear", "cubic", "double_exp", "piecewise_1break"} <= set(table.index)
    assert table.index[0] != "linear"
    assert table.loc["linear", "delta_bic"] > 10


def test_deep_dive_adds_models_and_signals_are_complete(tmp_path):
    cell = _cell(tmp_path)
    fits = fit_all(cell["n"], cell["q"], extended=True)
    assert {"piecewise_2break", "smoothing_spline"} <= set(fits)
    table = rank_fits(fits)
    s = compute_signals(cell["facts"], fits, table)
    assert s["knee_cycle"] is not None and 300 < s["knee_cycle"] < 800
    assert isinstance(rule_flags(s), list)
