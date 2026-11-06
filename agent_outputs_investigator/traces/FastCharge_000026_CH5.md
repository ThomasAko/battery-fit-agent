# FastCharge_000026_CH5

**call** `get_cell_overview({"cell_id": "FastCharge_000026_CH5"})`

```json
{"cell_id": "FastCharge_000026_CH5", "cycles": 209, "eol_cycle": 209, "reached_end_of_life": true, "q_start_Ah": 0.9697, "q_end_Ah": 0.8813, "noise_mAh": 0.49, "knee_cycle": 28, "knee_fraction_of_life": 0.134, "outliers_removed": 0, "recovery_jumps": 0, "best_parametric_law": "cubic", "runner_up": "piecewise_1break", "delta_bic_runner_up": 149.0, "misfit_z": -1.64, "knee_z": -24.32, "shortlist_reasons": ["knee unusually early in life (at 13% of life, z=-24.32)", "degradation shape differs from the fleet (cubic beats double_exp by dBIC=314.2)"]}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000026_CH5", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.134, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 0.7, "n_cells": 139}
```

**agent:** **Category:** real_early_ageing  

**Why this cell stands out**

- The test **reached end‑of‑life** (capacity fell to 0.881 Ah, the 0.88 Ah EOL threshold) after **209 cycles** – the full life was completed.  
- Its **knee** (the point where capacity fade accelerates) occurred at **cycle 28**, which is only **13 % of its total life** (`knee_fraction_of_life = 0.134`).  
- Compared with the fleet, the median knee occurs at **≈78 % of life** (`fleet_median knee_fraction = 0.783`). The cell’s knee is therefore **extremely early**, with a **z‑score of –24.32**.  
- No outliers or measurement jumps were detected (`outliers_removed = 0`).  
- The degradation shape is also atypical: the **cubic law** fits best, beating the next‑best piecewise law by a large BIC margin, confirming a different degradation trajectory from the fleet.

Because the cell **reached its end‑of‑life** yet shows a **knee far earlier than any other cell in the fleet**, the primary reason it was shortlisted is **real early ageing**.

**verifier:** A consistency check found problems with your verdict:
- 'real_early_ageing' requires check_end_of_life, which you did not call
Use the tools as needed and reconsider.

**call** `check_end_of_life({"cell_id": "FastCharge_000026_CH5"})`

```json
{"reached_end_of_life": true, "eol_cycle": 209, "last_cycle": 209, "q_end_Ah": 0.8813, "fade_completed_fraction": 0.9855, "recent_fade_mAh_per_100_cycles": 45.5617, "cycles_to_end_of_life_at_recent_rate": null}
```

**agent:** **Re‑evaluated category:** **real_early_ageing**

**Evidence**

| Item | Value (cell) | Fleet reference / interpretation |
|------|--------------|-----------------------------------|
| **End‑of‑life reached?** | `reached_end_of_life = true` (209 cycles) | The test ran to the 0.88 Ah EOL threshold. |
| **Fade completed** | `fade_completed_fraction = 0.9855` (≈98 % of the total capacity loss) | Confirms the cell truly completed its life, not stopped early. |
| **Knee cycle** | `knee_cycle = 28` | Occurs at **13 %** of the total life (`knee_fraction_of_life = 0.134`). |
| **Fleet knee position** | Median knee fraction ≈ 0.78 (≈78 % of life) | The cell’s knee is **far earlier** than the fleet median. |
| **Knee z‑score** | `knee_z = -24.32` | Extremely low; the shortlist flagged this as “knee unusually early”. |
| **Outliers / data gaps** | `outliers_removed = 0`, `recovery_jumps = 0` | No data‑quality issues. |
| **Degradation shape** | Best law = **cubic** (beats the runner‑up by ΔBIC = 149) | Indicates a different degradation law, but the primary abnormality is the early knee. |

**Why the other categories do not apply**

- **test_ended_before_eol:** The `check_end_of_life` call shows the cell *did* reach EOL (fade ≈ 98 % completed).  
- **data_quality:** No outliers or capacity jumps were detected.  
- **unusual_shape:** While the cubic law is atypical, the defining factor for shortlisting is the *early* knee; the shape difference is secondary.  
- **normal:** The knee occurs far earlier than any fleet cell, so the cell is not normal.

**Conclusion**

The cell **FastCharge_000026_CH5** completed its full life but exhibited a **knee at only 13 % of its lifespan**, an extreme outlier compared with the fleet (median ≈ 78 %). This satisfies the definition of **real_early_ageing**: an early‑onset rapid fade that occurs despite the test reaching true end‑of‑life.

**verdict:** `{
 "category": "real_early_ageing",
 "confidence": "high",
 "evidence": [
  "Reached end\u2011of\u2011life: true (eol_cycle = 209) \u2013 fade_completed_fraction = 0.9855",
  "Knee at cycle 28, which is 0.134 of life (knee_fraction_of_life = 0.134) vs fleet median 0.783",
  "Knee z\u2011score = -24.32, far below fleet distribution",
  "No outliers removed (outliers_removed = 0) and no recovery jumps"
 ],
 "recommended_action": "Investigate early\u2011knee mechanisms (e.g., SEI growth, lithium plating) and compare formation/fast\u2011charge protocols to the fleet."
}`
