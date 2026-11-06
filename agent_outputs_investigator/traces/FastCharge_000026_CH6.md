# FastCharge_000026_CH6

**call** `get_cell_overview({"cell_id": "FastCharge_000026_CH6"})`

```json
{"cell_id": "FastCharge_000026_CH6", "cycles": 483, "eol_cycle": 483, "reached_end_of_life": true, "q_start_Ah": 1.012, "q_end_Ah": 0.8813, "noise_mAh": 0.37, "knee_cycle": 168, "knee_fraction_of_life": 0.348, "outliers_removed": 0, "recovery_jumps": 0, "best_parametric_law": "cubic", "runner_up": "power", "delta_bic_runner_up": 707.4, "misfit_z": -1.38, "knee_z": -16.3, "shortlist_reasons": ["knee unusually early in life (at 35% of life, z=-16.3)", "degradation shape differs from the fleet (cubic beats double_exp by dBIC=1152.3)"]}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000026_CH6", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.348, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 2.2, "n_cells": 139}
```

**agent:** **Cell:** FastCharge_000026_CH6  

**Key facts (from `get_cell_overview`)**  

| Item | Value |
|------|-------|
| Total cycles run | **483** (test reached its end‑of‑life) |
| End‑of‑life cycle (80 % Q) | **483** (reached) |
| Start capacity | **1.012 Ah** |
| End capacity | **0.881 Ah** (≈ 87 % of start – the EOL definition) |
| Knee (onset of fast fade) | **cycle 168** |
| Knee fraction of life | **0.348** (34.8 % of total life) |
| Outliers removed | **0** (no data‑quality flags) |
| Best parametric law (by BIC) | **cubic** |
| Runner‑up law | **power** (ΔBIC = 707.4) |
| Misfit Z‑score | –1.38 (within normal range) |
| Knee Z‑score | **–16.3** (extremely low) |
| Shortlist reasons | 1. Knee unusually early (35 % of life, z = –16.3)  <br>2. Degradation shape differs from the fleet (cubic beats double‑exp by ΔBIC = 1152.3) |

**Fleet comparison (knee fraction)** – `compare_to_fleet`  

* Cell knee fraction: **0.348**  
* Fleet median knee fraction: **0.783** (≈ 78 % of life)  
* Fleet 25‑th / 75‑th percentiles: **0.7525 – 0.799**  
* Cell percentile in fleet: **2.2 %**  

The cell’s knee occurs **~35 %** into its life, whereas 95 % of the fleet does not show a knee until **≈ 78 %** of life. The knee Z‑score of –16.3 confirms this is far outside normal variation.

**Why the cell stands out**

1. **Real early ageing** – The test ran to its defined end‑of‑life (483 cycles, 0.88 Ah), so the early knee is not an artefact of a prematurely stopped test. The knee appears at cycle 168, i.e. only **34.8 %** of the total life, placing the cell in the **2 nd percentile** of the fleet. This is the classic “early knee / fast fade” pattern the shortlist flagged.

2. **Unusual degradation shape** – The best‑fit parametric model for this cell is a **cubic law**, which outperforms the fleet‑wide preferred double‑exponential model by a huge ΔBIC (≈ 1150). The runner‑up (power law) is still far worse (ΔBIC ≈ 707). This indicates the cell follows a degradation trajectory that is fundamentally different from the majority of the fleet.

3. **No data‑quality issues** – Zero outliers were removed and the misfit Z‑score (‑1.38) is within normal bounds, ruling out measurement artefacts.

**Conclusion / Category**

The cell is flagged primarily for **real_early_ageing** (the knee occurs far earlier than the fleet norm) and also exhibits an **unusual_shape** (cubic degradation law vs the fleet’s typical double‑exponential). Since the early knee is the most striking deviation and directly impacts lifetime, the dominant classification is **real_early_ageing**.

**verifier:** A consistency check found problems with your verdict:
- 'real_early_ageing' requires check_end_of_life, which you did not call
Use the tools as needed and reconsider.

**call** `check_end_of_life({"cell_id": "FastCharge_000026_CH6"})`

```json
{"reached_end_of_life": true, "eol_cycle": 483, "last_cycle": 483, "q_end_Ah": 0.8813, "fade_completed_fraction": 0.9902, "recent_fade_mAh_per_100_cycles": 41.542, "cycles_to_end_of_life_at_recent_rate": null}
```

**agent:** **Cell examined:** FastCharge_000026_CH6  

**Evidence**

| Source | Key result |
|--------|------------|
| `get_cell_overview` | • Test ran to end‑of‑life (483 cycles, 0.881 Ah ≈ 87 % of start)  <br>• Knee at cycle 168 → **knee fraction = 0.348** (34.8 % of life)  <br>• Knee Z‑score = ‑16.3 (far below fleet norm)  <br>• No outliers, misfit Z‑score = ‑1.38 (normal)  <br>• Best‑fit law = **cubic**, beating the fleet‑wide double‑exp model by ΔBIC ≈ 1150 |
| `check_end_of_life` | • `reached_end_of_life` = **true**  <br>• Fade completed ≈ 99 % of the total 80 %‑capacity loss (fade_completed_fraction = 0.9902)  <br>• No remaining cycles needed to reach EOL (cycles_to_end_of_life_at_recent_rate = null) |
| `compare_to_fleet` (knee_fraction) | • Cell knee fraction = 0.348  <br>• Fleet median knee fraction ≈ 0.783  <br>• Cell percentile ≈ 2 % (far in the low tail) |

**Interpretation**

* The test **did reach the defined end‑of‑life**, so the early knee is not an artefact of a prematurely stopped test.  
* The knee appears at **only 35 % of the cell’s total life**, whereas the fleet typically shows the knee at ~78 % of life. The knee Z‑score (‑16.3) confirms this is an extreme outlier.  
* No data‑quality flags (outliers, jumps) are present, and the overall fit quality is normal.  

**Conclusion**

The dominant reason the cell was shortlisted is that its **fast‑fade knee occurs unusually early in its life**, satisfying the definition of **real_early_ageing**. (The unusual cubic degradation shape is also noted, but the primary classification is real_early_ageing.)

**Category:** **real_early_ageing**

**verdict:** `{
 "category": "real_early_ageing",
 "confidence": "high",
 "evidence": [
  "Knee occurs at cycle 168, i.e. knee_fraction = 0.348 (34.8% of life) while fleet median is 0.783 (cell percentile 2.2%)",
  "Knee Z\u2011score = -16.3, far below the fleet distribution",
  "check_end_of_life reports reached_end_of_life = true (eol_cycle 483, q_end_Ah 0.8813)",
  "outliers_removed = 0 and misfit_z = -1.38, indicating no data\u2011quality issues"
 ],
 "recommended_action": "Perform a root\u2011cause analysis of the early knee (e.g., review formation, fast\u2011charge protocol, temperature history) and compare with similar cells to identify the ageing trigger."
}`
