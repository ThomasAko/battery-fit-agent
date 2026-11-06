# FastCharge_000003_CH40

**call** `get_cell_overview({"cell_id": "FastCharge_000003_CH40"})`

```json
{"cell_id": "FastCharge_000003_CH40", "cycles": 703, "eol_cycle": 703, "reached_end_of_life": true, "q_start_Ah": 1.0734, "q_end_Ah": 0.8845, "noise_mAh": 0.15, "knee_cycle": 518, "knee_fraction_of_life": 0.737, "outliers_removed": 0, "recovery_jumps": 0, "best_parametric_law": "exponential", "runner_up": "double_exp", "delta_bic_runner_up": 0.3, "misfit_z": 0.21, "knee_z": -1.72, "shortlist_reasons": ["exponential and double_exp statistically tied (dBIC=0.3)"]}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000003_CH40", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.737, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 18.0, "n_cells": 139}
```

**agent:** **Category:** *unusual_shape*

**Why this cell stands out**

| Item | Value (cell) | Fleet reference |
|------|--------------|-----------------|
| **Best parametric law** | exponential | – |
| **Runner‑up law** | double‑exp | – |
| **Δ BIC (runner‑up)** | **0.3** | – (Δ BIC < 1 means the two models are statistically indistinguishable) |
| **Knee cycle** | 518 cycles | – |
| **Knee fraction of life** | **0.737** | median 0.783, 25 %‑tile 0.7525, 75 %‑tile 0.799 |
| **Outliers removed** | 0 | – |
| **Reached end‑of‑life?** | Yes (703 cycles, 0.884 Ah) | – |

The automated fleet screen flagged **FastCharge_000003_CH40** because its degradation can be described equally well by two different parametric laws (exponential and double‑exponential) with a Δ BIC of only 0.3. In the fleet, a single law usually dominates (Δ BIC ≫ 1). This statistical tie indicates that the cell’s capacity‑fade pattern does not follow the usual single‑law behavior seen in the rest of the population, i.e., its degradation follows an *unusual shape*.

The earlier‑than‑average knee (0.737 × life vs. fleet median 0.783) is consistent with the ambiguous law fit, but the primary reason the cell was shortlisted is the **law‑tie** evidence, not simply an early knee. No outliers, gaps, or measurement issues were detected.

**verdict:** `{
 "category": "unusual_shape",
 "confidence": "high",
 "evidence": [
  "Best parametric law = exponential, runner\u2011up = double_exp with \u0394\u202fBIC = 0.3 (statistically tied)",
  "Knee fraction of life = 0.737, below fleet median 0.783 (cell percentile 18\u202f%)",
  "Outliers_removed = 0, recovery_jumps = 0 (no data quality issues)",
  "Reached end\u2011of\u2011life at 703 cycles, knee at 518 cycles (knee_fraction = 0.737)"
 ],
 "recommended_action": "Perform deeper post\u2011mortem analysis (e.g., impedance spectroscopy) to understand why two degradation laws fit equally well."
}`
