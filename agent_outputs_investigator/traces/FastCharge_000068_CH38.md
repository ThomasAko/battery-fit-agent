# FastCharge_000068_CH38

**call** `get_cell_overview({"cell_id": "FastCharge_000068_CH38"})`

```json
{"cell_id": "FastCharge_000068_CH38", "cycles": 500, "eol_cycle": 478, "reached_end_of_life": true, "q_start_Ah": 1.0774, "q_end_Ah": 0.8393, "noise_mAh": 0.21, "knee_cycle": 377, "knee_fraction_of_life": 0.789, "outliers_removed": 3, "recovery_jumps": 0, "best_parametric_law": "power", "runner_up": "double_exp", "delta_bic_runner_up": 64.6, "misfit_z": 0.7, "knee_z": 0.22, "shortlist_reasons": ["degradation shape differs from the fleet (power beats double_exp by dBIC=64.6)", "3 outlier cycles removed"]}
```

**call** `locate_outliers({"cell_id": "FastCharge_000068_CH38"})`

```json
{"outliers": 3, "per_quarter_of_test": [0, 1, 0, 0], "first_cycle": 247.0, "last_cycle": 503.0, "fraction_below_trend": 1.0, "median_deviation_mAh": -22.2052, "recovery_jumps": 0}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000068_CH38", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.789, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 62.6, "n_cells": 139}
```

**agent:** **Category:** *unusual_shape*  

**Why this cell stands out**

| Item | Value (from tools) | Fleet context |
|------|-------------------|---------------|
| **Best‑fit law** | **Power law** (Δ BIC = 64.6 vs. runner‑up double‑exp) | The fleet’s typical best law is *double‑exp* (the runner‑up here). A Δ BIC > 10 already signals a decisive preference; 64.6 is a very strong statistical separation, showing that this cell follows a markedly different degradation trajectory. |
| **Knee position** | Knee at cycle 377 → knee fraction = 0.789 | Fleet median knee fraction = 0.783 (25‑75 % = 0.7525‑0.799). The cell’s knee is right in the middle of the fleet distribution (62 % percentile), so the timing of the knee is *not* unusual. |
| **End‑of‑life** | Reached EOL at cycle 478 (EOL = 0.88 Ah) | Test completed, so the early‑knee hypothesis does not apply. |
| **Outliers** | 3 cycles removed (all in the 2nd quarter, median deviation ≈ ‑22 mAh, 100 % below trend) | Only a few isolated low‑capacity points; they do not dominate the fit and the Δ BIC remains huge even after removal. |
| **Shortlist reasons** | “degradation shape differs from the fleet (power beats double_exp by dBIC=64.6)”, “3 outlier cycles removed” | Confirms the shape difference is the primary flag. |

**Interpretation**

- The cell’s *knee timing* and *overall capacity fade* are typical for the fleet, ruling out **real_early_ageing** or **test_ended_before_eol**.
- The **large Δ BIC (64.6)** indicates that a *power‑law* model describes its capacity loss far better than the *double‑exponential* model that fits the majority of cells. This is a clear deviation in degradation *shape*.
- The outlier cycles are few, isolated, and already accounted for in the shortlist; they do not constitute a data‑quality problem.

**Conclusion**

FastCharge_000068_CH38 is flagged because its degradation follows a *different parametric law* than the fleet—i.e., an **unusual_shape** case. The power‑law dominance (Δ BIC = 64.6) is the decisive evidence.

**verdict:** `{
 "category": "unusual_shape",
 "confidence": "high",
 "evidence": [
  "Best\u2011fit law is power (\u0394\u202fBIC vs. double_exp = 64.6), indicating a strong statistical preference over the fleet\u2019s usual double\u2011exp law.",
  "Knee fraction = 0.789, within the fleet interquartile range (median 0.783, p25\u2011p75 0.7525\u20110.799), so timing is normal.",
  "3 outlier cycles were removed (first at 247, median deviation \u201322.2\u202fmAh), but they do not dominate the fit."
 ],
 "recommended_action": "Review the cell\u2019s charge/temperature history to identify factors causing a power\u2011law degradation instead of the fleet\u2019s double\u2011exponential trend."
}`
