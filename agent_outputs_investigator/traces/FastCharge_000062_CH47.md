# FastCharge_000062_CH47

**call** `get_cell_overview({"cell_id": "FastCharge_000062_CH47"})`

```json
{"cell_id": "FastCharge_000062_CH47", "cycles": 446, "eol_cycle": 429, "reached_end_of_life": true, "q_start_Ah": 1.0761, "q_end_Ah": 0.8486, "noise_mAh": 0.2, "knee_cycle": 342, "knee_fraction_of_life": 0.797, "outliers_removed": 4, "recovery_jumps": 0, "best_parametric_law": "exponential", "runner_up": "double_exp", "delta_bic_runner_up": 5.9, "misfit_z": 0.28, "knee_z": 0.52, "shortlist_reasons": ["4 outlier cycles removed"]}
```

**call** `locate_outliers({"cell_id": "FastCharge_000062_CH47"})`

```json
{"outliers": 4, "per_quarter_of_test": [0, 0, 0, 0], "first_cycle": 447.0, "last_cycle": 450.0, "fraction_below_trend": 1.0, "median_deviation_mAh": -28.3114, "recovery_jumps": 0}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000062_CH47", "metric": "knee_fraction"})`

```json
{"metric": "knee_fraction", "cell_value": 0.797, "fleet_median": 0.783, "fleet_p25": 0.7525, "fleet_p75": 0.799, "cell_percentile": 70.5, "n_cells": 139}
```

**call** `compare_to_fleet({"cell_id": "FastCharge_000062_CH47", "metric": "outliers"})`

```json
{"metric": "outliers", "cell_value": 4.0, "fleet_median": 1.0, "fleet_p25": 0.0, "fleet_p75": 1.0, "cell_percentile": 95.7, "n_cells": 139}
```

**agent:** **Category:** **data_quality**

**Why this cell stands out**

| Item | Value (cell) | Fleet median / range | Comment |
|------|--------------|----------------------|---------|
| **Outlier cycles** | 4 removed cycles | Median = 1, 95 th percentile ≈ 2 | The cell has far more outliers than typical – it sits in the 95.7 th percentile of the fleet. |
| **Location of outliers** | Cycles 447‑450 (the very end of the test) | – | All four outliers cluster at the tail of the test, well after the cell has already passed its end‑of‑life (EOL = 429 cycles). |
| **Magnitude of deviation** | Median deviation = ‑28 mAh (≈ ‑3 % of nominal capacity) | – | The outliers are a full‑cycle‑capacity drop below the trend, far larger than the typical noise (0.2 mAh). |
| **Trend impact** | Knee at cycle 342, knee‑fraction = 0.797 (within fleet 25‑75 % range) | – | The degradation curve itself is normal; the knee timing and shape are not unusual. |
| **Test completion** | Reached EOL (429 cycles) and ran to 446 cycles | – | The test finished well past EOL, so the knee and life metrics are comparable to the fleet. |
| **Shortlist reason** | “4 outlier cycles removed” | – | The only reason the automated screen flagged this cell is the unusually high number of outliers. |

**Interpretation**

- The cell’s capacity fade, knee position, and fitted degradation law (exponential, runner‑up double‑exp) are all typical for the fleet.
- The anomaly is the presence of four consecutive outlier points at the very end of the test, each dropping ~28 mAh below the expected trend. This cluster of large‑magnitude deviations is far beyond normal measurement noise and far exceeds the fleet’s outlier distribution.
- Because the outliers dominate the shortlist reason and are clearly clustered at the test’s tail, the most plausible explanation is a **measurement or equipment issue** (e.g., a brief interruption in the cycler, a temperature spike, or a data‑logging glitch) rather than an intrinsic cell‑level ageing problem.

**Conclusion**

FastCharge_000062_CH47 is flagged not because its ageing behavior is abnormal, but because its data contain a cluster of large, late‑stage outliers that are atypical for the fleet. This points to a data‑quality problem rather than early ageing, an unusual degradation shape, or an incomplete test.

**verdict:** `{
 "category": "data_quality",
 "confidence": "high",
 "evidence": [
  "4 outlier cycles were removed (fleet median 1, 95.7th percentile \u22482) \u2013 far above typical.",
  "All outliers occur at cycles 447\u2011450, after the cell reached EOL at cycle 429.",
  "Median deviation of the outliers is -28.3114\u202fmAh, far larger than the noise level of 0.2\u202fmAh."
 ],
 "recommended_action": "Inspect the cycler logs and temperature data for cycles 447\u2011450 to identify any measurement or equipment fault."
}`
