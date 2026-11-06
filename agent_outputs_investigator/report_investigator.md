## Short‑list Summary (139 LFP/graphite cells)

| Category | Cells (evidence) |
|----------|------------------|
| **real_early_ageing** | • FastCharge_000008_CH47 – EOL 616 cycles, *q_end_Ah* 0.8841 Ah; knee 425 (0.69 life), percentile 5.8 %, z‑score ‑3.48  <br>• FastCharge_000026_CH5 – EOL 209 cycles, *fade_completed_fraction* 0.9855; knee 28 (0.134 life), z‑score ‑24.32  <br>• FastCharge_000026_CH6 – knee 168 (0.348 life), percentile 2.2 %, z‑score ‑16.3; EOL 483 cycles, *q_end_Ah* 0.8813 Ah, *misfit_z* ‑1.38  <br>• FastCharge_000041_CH10 – knee 93 (0.628 life), 5th percentile, z‑score ‑5.81; EOL 148 cycles, *q_end_Ah* 0.8407 Ah |
| **unusual_shape** | • FastCharge_000003_CH40 – knee 518 cycles (0.737 life) vs fleet median 0.783, percentile 18 %; ΔBIC 0.3 (tied)  <br>• FastCharge_000068_CH38 – best‑fit power law, ΔBIC 64.6; knee 0.789 (within IQR 0.7525‑0.799), 3 outliers, median deviation 22.2 mAh |
| **data_quality** | • FastCharge_000062_CH47 – 4 outliers (cycles 447‑450) after EOL 429, median deviation ‑28.3114 mAh |
| **test_ended_before_eol** | • FastCharge_000045_CH1 – *fade_completed_fraction* 0.2415, knee 76 (0.068 life), 1189 cycles run vs 1920.5 estimated, 67 outliers, 6 jumps  <br>• FastCharge_000045_CH2 – *q_end_Ah* 1.0387 Ah (19.97 % fade), knee 0.347, no outliers  <br>• FastCharge_000045_CH3 – *fade_completed_fraction* 0.1937, projected 3465.3 cycles to EOL, knee 0.362, stopped at 1176 cycles |

### Priority for Investigation
1. **real_early_ageing** – the most extreme early knees (e.g., 0.134 life, z‑scores ‑24.32/‑16.3) suggest fundamental degradation mechanisms (SEI growth, plating) that could affect the whole fleet.  
2. **unusual_shape** – cells with statistically distinct degradation laws (ΔBIC 64.6) may reveal alternative pathways worth probing.  
3. **data_quality** – the large outlier deviation (‑28.3114 mAh) could corrupt the tail‑end analysis and must be verified.  
4. **test_ended_before_eol** – while informative, the incomplete life limits comparability; extending these tests will be needed later.  

Focus first on the four early‑ageing cells to uncover root causes, then examine the two shape‑anomalous cells, followed by data‑quality checks and finally completing the truncated tests.