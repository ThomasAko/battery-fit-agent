# FastCharge_000041_CH10

**call** `get_cell_overview({"cell_id": "FastCharge_000041_CH10"})`

```json
{"cell_id": "FastCharge_000041_CH10", "cycles": 169, "eol_cycle": 148, "reached_end_of_life": true, "q_start_Ah": 1.0714, "q_end_Ah": 0.8407, "noise_mAh": 1.66, "knee_cycle": 93, "knee_fraction_of_life": 0.628, "outliers_removed": 2, "recovery_jumps": 0, "best_parametric_law": "cubic", "runner_up": "double_exp", "delta_bic_runner_up": 6.5, "misfit_z": -1.02, "knee_z": -5.81, "shortlist_reasons": ["knee unusually early in life (at 63% of life, z=-5.81)"]}
```

**call** `check_end_of_life({"cell_id": "FastCharge_000041_CH10"})`

```json
{"reached_end_of_life": true, "eol_cycle": 148, "last_cycle": 169, "q_end_Ah": 0.8407, "fade_completed_fraction": 1.2053, "recent_fade_mAh_per_100_cycles": 209.6146, "cycles_to_end_of_life_at_recent_rate": null}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000041_CH10", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.628, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 5.0, "n_cells": 139}
```

**call** `locate_outliers({"cell_id": "FastCharge_000041_CH10"})`

```json
{"outliers": 2, "per_quarter_of_test": [0, 0, 0, 0], "first_cycle": 170.0, "last_cycle": 171.0, "fraction_below_trend": 1.0, "median_deviation_mAh": -23.2692, "recovery_jumps": 0}
```

**agent:** **Category:** **real_early_ageing**

**Why this cell stands out**

- **Knee timing:** The capacity‑fade knee occurs at cycle 93, which is only **62.8 % of the cell’s total life** (knee_fraction = 0.628).  
- **Fleet comparison:** The fleet median knee fraction is 0.783 (75 %‑25 % interquartile range 0.7525‑0.799). This cell is at the **5th percentile**, i.e., the knee appears far earlier than almost all other cells. Its knee‑z‑score is –5.81, confirming an extreme early‑knee outlier.  
- **End‑of‑life reached:** The test continued past the 80 % capacity end‑of‑life point (EOL cycle = 148). The cell’s final capacity is 0.8407 Ah, well below the 0.88 Ah EOL threshold (fade_completed_fraction = 1.205). Thus the early knee is not an artifact of the test stopping early.  
- **Outliers:** Only two outlier points are present, both at cycles 170‑171 (after the recorded test end). They are far below the trend but occur **after** the cell has already passed EOL, so they do not explain the early knee.  

**Conclusion:** The cell’s capacity‑fade accelerates unusually early in its life, well before the fleet’s typical knee point, and the test reached true end‑of‑life. This makes it a genuine early‑ageing case, matching the “real_early_ageing” category.

**verdict:** `{
 "category": "real_early_ageing",
 "confidence": "high",
 "evidence": [
  "Knee at cycle 93 \u2192 knee_fraction 0.628 (5th percentile of fleet, fleet median 0.783, fleet IQR 0.7525\u20110.799)",
  "Knee z\u2011score = -5.81, far below typical values",
  "Test reached true end\u2011of\u2011life: eol_cycle 148, reached_end_of_life true, q_end_Ah 0.8407\u202fAh (<0.88\u202fAh)",
  "Only 2 outliers (cycles 170\u2011171) after EOL, not affecting early knee"
 ],
 "recommended_action": "Perform detailed post\u2011mortem analysis (e.g., microscopy, impedance) to identify the root cause of the unusually early capacity\u2011fade knee."
}`
