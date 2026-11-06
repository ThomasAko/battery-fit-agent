# FastCharge_000008_CH47

**call** `get_cell_overview({"cell_id": "FastCharge_000008_CH47"})`

```json
{"cell_id": "FastCharge_000008_CH47", "cycles": 616, "eol_cycle": 616, "reached_end_of_life": true, "q_start_Ah": 1.0874, "q_end_Ah": 0.8841, "noise_mAh": 0.16, "knee_cycle": 425, "knee_fraction_of_life": 0.69, "outliers_removed": 0, "recovery_jumps": 0, "best_parametric_law": "cubic", "runner_up": "power", "delta_bic_runner_up": 112.4, "misfit_z": 0.73, "knee_z": -3.48, "shortlist_reasons": ["knee unusually early in life (at 69% of life, z=-3.48)", "degradation shape differs from the fleet (cubic beats double_exp by dBIC=189.4)"]}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000008_CH47", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.69, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 5.8, "n_cells": 139}
```

**agent:** **Category:** real_early_ageing  

**Why this cell stands out**

- The test reached the end‑of‑life definition (capacity ≈ 0.884 Ah, 80 % of nominal) after 616 cycles.  
- Its capacity‑fade “knee” occurs at cycle 425, which is only **69 % of its total life**.  
- Compared with the fleet (median knee ≈ 78 % of life, 25‑75 % range ≈ 75‑80 %), this cell’s knee is in the **5.8 th percentile** of the fleet, and its knee‑z‑score is **‑3.48**, indicating a statistically early onset of rapid fade.  
- The cell’s overall fit quality (misfit z ≈ 0.73) is normal, and there are **no outliers or measurement jumps**.  

Thus the cell is flagged because it **reached end‑of‑life but its fast‑fade knee appeared unusually early**, matching the “real_early_ageing” category.

**verifier:** A consistency check found problems with your verdict:
- 'real_early_ageing' requires check_end_of_life, which you did not call
Use the tools as needed and reconsider.

**call** `check_end_of_life({"cell_id": "FastCharge_000008_CH47"})`

```json
{"reached_end_of_life": true, "eol_cycle": 616, "last_cycle": 616, "q_end_Ah": 0.8841, "fade_completed_fraction": 0.9802, "recent_fade_mAh_per_100_cycles": 103.1976, "cycles_to_end_of_life_at_recent_rate": null}
```

**agent:** **Category:** real_early_ageing  

**Why this cell stands out**

- **End‑of‑life reached:** The test completed 616 cycles, ending at 0.884 Ah (≈ 80 % of the nominal 1.087 Ah). The `check_end_of_life` call confirms the cell reached EOL, with 98 % of the total capacity fade already completed (`fade_completed_fraction = 0.9802`).  
- **Early knee:** The capacity‑fade knee occurs at cycle 425, which is only **69 % of the cell’s total life**. Compared with the fleet (median knee ≈ 78 % of life, 25‑75 % range ≈ 75‑80 %), this places the cell in the **5.8 th percentile** (`cell_percentile = 5.8`) and gives a knee‑z‑score of **‑3.48**, indicating a statistically early onset of rapid degradation.  
- **No data‑quality issues:** There are **0 outliers** and **0 recovery jumps**, and the overall fit quality (`misfit_z ≈ 0.73`) is normal.  

Thus the cell is flagged because it **reached end‑of‑life but its rapid‑fade knee appeared unusually early**, matching the **real_early_ageing** category.

**verdict:** `{
 "category": "real_early_ageing",
 "confidence": "high",
 "evidence": [
  "EOL reached at cycle 616 with q_end_Ah = 0.8841\u202fAh (check_end_of_life)",
  "Knee at cycle 425 = 0.69 of life (knee_fraction), fleet median 0.783, cell percentile 5.8\u202f% (compare_to_fleet)",
  "Knee z\u2011score = -3.48, indicating statistically early fast fade (overview)",
  "No outliers or recovery jumps (overview: outliers_removed = 0, recovery_jumps = 0)"
 ],
 "recommended_action": "Review formation and early\u2011cycle protocols for this cell to identify factors causing the premature knee."
}`
