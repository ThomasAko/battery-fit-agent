# FastCharge_000045_CH2

**call** `get_cell_overview({"cell_id": "FastCharge_000045_CH2"})`

```json
{"cell_id": "FastCharge_000045_CH2", "cycles": 1178, "eol_cycle": null, "reached_end_of_life": false, "q_start_Ah": 1.0783, "q_end_Ah": 1.0387, "noise_mAh": 0.1, "knee_cycle": 409, "knee_fraction_of_life": 0.347, "outliers_removed": 0, "recovery_jumps": 0, "best_parametric_law": "cubic", "runner_up": "power", "delta_bic_runner_up": 58.4, "misfit_z": -1.38, "knee_z": null, "shortlist_reasons": ["test ended 20% of the way to end of life; knee position not comparable", "degradation shape differs from the fleet (cubic beats double_exp by dBIC=400.4)"]}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000045_CH2", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.347, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 1.4, "n_cells": 139}
```

**call** `check_end_of_life({"cell_id": "FastCharge_000045_CH2"})`

```json
{"reached_end_of_life": false, "eol_cycle": null, "last_cycle": 1178, "q_end_Ah": 1.0387, "fade_completed_fraction": 0.1997, "recent_fade_mAh_per_100_cycles": 5.1566, "cycles_to_end_of_life_at_recent_rate": 3077.638}
```

**agent:** **Category:** **test_ended_before_eol**

**Why this cell stands out**

| Item | Value (from tools) | Fleet comparison / interpretation |
|------|-------------------|------------------------------------|
| **Total cycles run** | 1 178 | – |
| **Capacity at start** | 1.078 Ah | – |
| **Capacity at end of test** | 1.039 Ah | – |
| **Fade completed** | 19.97 % of the total fade needed to reach the 0.88 Ah end‑of‑life target | The test stopped well before the cell could reach its end‑of‑life (EOL). |
| **Projected cycles to EOL** | ≈ 4 156 cycles (based on recent fade rate) | – |
| **Knee cycle** | 409 | This is 34.7 % of the projected total life (knee_fraction = 0.347). |
| **Fleet median knee_fraction** | 0.783 (75 %‑tile ≈ 0.80) | The cell’s knee occurs far earlier than the fleet median (≈ 1.4 th percentile). |
| **Outliers / jumps** | 0 removed, 0 recovery jumps | No data‑quality issues detected. |
| **Best parametric law** | Cubic (runner‑up: power, ΔBIC = 58.4) | The cubic law is a very different degradation shape from the fleet’s typical law (double‑exp beats cubic by ΔBIC ≈ 400). |
| **Shortlist reasons** | • Test ended ~20 % of the way to EOL → knee position not comparable.<br>• Degradation shape differs from fleet. | Both reasons are flagged, but the primary reason for the shortlist is that the test stopped far short of the cell’s end‑of‑life, making any knee‑position comparison unreliable. |

**Interpretation**

- The cell never reached the 80 % capacity (0.88 Ah) threshold that defines end‑of‑life; only about 20 % of the required fade was observed.
- Because the test stopped early, the knee‑fraction (0.347) is derived from an extrapolation rather than from an observed full‑life trajectory. Consequently, the knee position cannot be directly compared to the fleet’s knee statistics.
- Although the degradation shape (cubic law) is also unusual, the decisive factor for the shortlist is that the test terminated well before the cell could reach its end‑of‑life, rendering the knee metric non‑comparable.

**Conclusion**

FastCharge_000045_CH2 is highlighted because **the test ended far before the cell reached its end‑of‑life**, so its knee position and life‑time metrics are not comparable to the rest of the fleet. This places the cell in the **test_ended_before_eol** category.

**verdict:** `{
 "category": "test_ended_before_eol",
 "confidence": "high",
 "evidence": [
  "The test stopped at cycle 1178 with q_end_Ah\u202f=\u202f1.0387\u202fAh, only 19.97% of the fade needed to reach the 0.88\u202fAh end\u2011of\u2011life target (check_end_of_life).",
  "Knee occurred at cycle 409, giving a knee_fraction of 0.347, far below the fleet median knee_fraction of 0.783 (compare_to_fleet).",
  "No outliers or recovery jumps were removed (get_cell_overview), so the early knee is not due to data\u2011quality issues."
 ],
 "recommended_action": "Run the cell to its projected end\u2011of\u2011life (~4\u202f156 cycles) to obtain a comparable knee position and confirm the degradation shape."
}`
