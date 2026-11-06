"""Tool 2/3: candidate degradation functions, fitting, goodness-of-fit and rule checks."""
import warnings

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
from scipy.optimize import OptimizeWarning, curve_fit

warnings.filterwarnings("ignore", category=OptimizeWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

PARAMETRIC = ["linear", "quadratic", "cubic", "power", "exponential", "double_exp", "piecewise_1break"]


def _metrics(y, yhat, k):
    rss = float(np.sum((y - yhat) ** 2)); m = len(y)
    return {"rmse_mAh": 1e3 * np.sqrt(rss / m),
            "r2": 1 - rss / float(np.sum((y - y.mean()) ** 2)),
            "aic": m * np.log(rss / m) + 2 * k,
            "bic": m * np.log(rss / m) + k * np.log(m), "k": k}


def _hinge(x, y, breaks):
    """Continuous piecewise-linear fit with fixed breakpoints (linear least squares)."""
    X = np.column_stack([np.ones_like(x), x] + [np.maximum(0, x - b) for b in breaks])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return X @ coef, coef


def fit_piecewise(x, y, n_breaks=1):
    """Grid-search the breakpoint(s); returns the best continuous piecewise-linear fit."""
    grid = np.quantile(x, np.linspace(0.05, 0.97, 60 if n_breaks == 1 else 25))
    best = None
    cands = [(b,) for b in grid] if n_breaks == 1 else [(a, b) for a in grid for b in grid if b > a + 0.05]
    for br in cands:
        yhat, coef = _hinge(x, y, br)
        rss = np.sum((y - yhat) ** 2)
        if best is None or rss < best[0]:
            best = (rss, yhat, br, coef)
    return best[1], best[2], best[3]


def fit_all(n, q, extended=False):
    """Fit every candidate function to capacity-vs-cycle. x is cycle scaled to [0,1] for stability.
    extended=True adds the deep-dive models (2-break piecewise, smoothing spline)."""
    x = (n - n.min()) / (n.max() - n.min())
    y0, y1 = q[:10].mean(), q[-10:].mean()
    fits = {}

    def add(name, yhat, k, **extra):
        if yhat is not None and np.all(np.isfinite(yhat)):
            fits[name] = {"yhat": yhat, **_metrics(q, yhat, k), **extra}

    # polynomials
    for deg, name in [(1, "linear"), (2, "quadratic"), (3, "cubic")]:
        add(name, np.polyval(np.polyfit(x, q, deg), x), deg + 1)
    # non-linear parametric models
    models = {
        "power":       (lambda x, a, b, c: a - b * np.power(x + 1e-9, c), [y0, max(y0 - y1, 1e-3), 1.5],
                        ([0, 0, 0.1], [2, 2, 15])),
        "exponential": (lambda x, a, b, c: a - b * np.exp(c * x), [y0 + 0.005, 0.005, 4.0],
                        ([0, 1e-9, 0.01], [2, 2, 60])),
        "double_exp":  (lambda x, a, b, c, d: a * np.exp(b * x) + c * np.exp(d * x), [y0, -0.05, -1e-3, 6.0],
                        ([0, -10, -2, 0], [2, 1, 0, 60])),
    }
    for name, (f, p0, bounds) in models.items():
        try:
            p, _ = curve_fit(f, x, q, p0=p0, bounds=bounds, maxfev=20000)
            add(name, f(x, *p), len(p))
        except Exception:
            pass
    # piecewise linear with one breakpoint -> the knee
    yhat, br, coef = fit_piecewise(x, q, 1)
    knee = float(n.min() + br[0] * (n.max() - n.min()))
    add("piecewise_1break", yhat, 4, knee_cycle=round(knee), slope_change=float(coef[2]))

    if extended:   # deep-dive models, only for flagged cells
        yhat, br, _ = fit_piecewise(x, q, 2)
        add("piecewise_2break", yhat, 6,
            breaks=[round(float(n.min() + b * (n.max() - n.min()))) for b in br])
        noise = np.median(np.abs(np.diff(q))) * 1.4826 / np.sqrt(2)
        spl = UnivariateSpline(x, q, s=len(q) * noise ** 2 * 1.5)
        add("smoothing_spline", spl(x), len(spl.get_knots()) + 3)
    return fits


def rank_fits(fits):
    table = pd.DataFrame({m: {k: v for k, v in f.items() if k in ("rmse_mAh", "r2", "aic", "bic", "k")}
                          for m, f in fits.items()}).T
    table["delta_bic"] = table["bic"] - table["bic"].min()
    return table.sort_values("bic").round({"rmse_mAh": 2, "r2": 4, "aic": 1, "bic": 1, "delta_bic": 1})


def compute_signals(facts, fits, table):
    """Deterministic evidence the reviewer (LLM) reasons over."""
    best = table.index[0]
    pw = fits.get("piecewise_1break", {})
    knee_gain = float(table.loc["linear", "bic"] - table.loc["piecewise_1break", "bic"]) \
        if "linear" in table.index and "piecewise_1break" in table.index else 0.0
    return {
        "best_model": best,
        "best_rmse_mAh": float(table.iloc[0]["rmse_mAh"]),
        "noise_mAh": round(1e3 * facts["noise_Ah"], 2),
        "fit_to_noise_ratio": round(float(table.iloc[0]["rmse_mAh"]) / max(1e3 * facts["noise_Ah"], 1e-3), 2),
        "runner_up": table.index[1], "runner_up_delta_bic": float(table.iloc[1]["delta_bic"]),
        "knee_cycle": pw.get("knee_cycle"),
        "knee_bic_gain_vs_linear": round(knee_gain, 1),
        "fade_accelerates_after_knee": bool(pw.get("slope_change", 0) < 0),
        "outliers_removed": facts["outliers_removed"], "recovery_jumps": facts["recovery_jumps"],
        "eol_cycle": facts["eol_cycle"], "cycles": facts["cycles"],
    }


def rule_flags(s):
    """Baseline flags: shown to the LLM, and used on their own if the LLM is off or its reply is unusable."""
    r = []
    if s["fit_to_noise_ratio"] > 2.5:          r.append("no candidate explains the curve (RMSE >> noise)")
    if s["runner_up_delta_bic"] < 2:           r.append("two models fit equally well (ambiguous)")
    if s["outliers_removed"] >= 5:             r.append(f"{s['outliers_removed']} outlier cycles removed")
    if s["recovery_jumps"] >= 3:               r.append(f"{s['recovery_jumps']} capacity-recovery jumps")
    if s["knee_cycle"] and s["fade_accelerates_after_knee"] and s["knee_bic_gain_vs_linear"] > 10 \
       and s["knee_cycle"] < 0.4 * (s["eol_cycle"] or s["cycles"]):
        r.append(f"early knee at cycle {s['knee_cycle']}")
    return r
