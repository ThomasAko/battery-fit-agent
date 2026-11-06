"""Tool 3/3: per-cell diagnostic plot (data, all fits, knee, EOL line, residuals of the best fit)."""
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def plot_cell(cell, fits, table, review, path, eol_ah=0.88):
    n, q = cell["n"], cell["q"]
    best = table.index[0]
    fig, (ax, axr) = plt.subplots(2, 1, figsize=(8, 6.8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax.scatter(n, q, s=6, color="0.6", label="extracted points")
    if len(cell["outlier_n"]):
        ax.scatter(cell["outlier_n"], np.clip(cell["outlier_q"], 0.8, 1.15), marker="x", s=25,
                   color="crimson", label=f"outliers removed ({len(cell['outlier_n'])})")
    for m in table.index:
        ax.plot(n, fits[m]["yhat"], lw=2.6 if m == best else 1.0, alpha=1 if m == best else 0.6,
                label=f"{m}  RMSE={table.loc[m, 'rmse_mAh']:.1f} mAh" + ("  <- best (BIC)" if m == best else ""))
    knee = fits.get("piecewise_1break", {}).get("knee_cycle")
    if knee:
        ax.axvline(knee, color="k", ls=":", lw=1); ax.text(knee, ax.get_ylim()[1], " knee", va="top", fontsize=8)
    ax.axhline(eol_ah, color="crimson", ls="--", lw=0.8)
    ax.set_ylabel("Discharge capacity (Ah)"); ax.legend(fontsize=7, loc="lower left")
    status = "FLAGGED: " + "; ".join(review.get("reasons", [])) if review.get("flag") else "not flagged"
    ax.set_title(textwrap.shorten(f"{cell['cell_id']}  |  {status}", 200, placeholder=" ..."), fontsize=9,
                 wrap=True)
    axr.scatter(n, 1e3 * (q - fits[best]["yhat"]), s=4, color="0.4")
    axr.axhline(0, color="k", lw=0.8); axr.set_ylabel(f"resid. {best}\n(mAh)"); axr.set_xlabel("Cycle")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close(fig)
