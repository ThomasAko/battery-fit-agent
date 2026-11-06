# data

| Folder | Contents | In git? |
|---|---|---|
| `battery_data_store/` | one CSV per cell (`cycle_index`, `discharge_capacity`, `charge_capacity`, `dc_internal_resistance`, temperatures, `charge_duration`, `paused`), ~100 kB each; this is what the agent reads | yes |
| `FastCharge/` | the raw BEEP-structured `FastCharge_*_structure.json` files (100-200 MB each) | no |

The CSVs are per-cycle summaries extracted from the Severson et al. fast-charge dataset
(*Data-driven prediction of battery cycle life before capacity degradation*, Nature Energy 4, 383-391, 2019),
published at [data.matr.io/1](https://data.matr.io/1/). Please cite the paper if you use them.

To rebuild them from the raw files:

```bash
# put the downloaded JSONs in data/FastCharge/ (or pass --data_dir /path/to/FastCharge)
python scripts/extract_cycle_csvs.py            # all cells
python scripts/extract_cycle_csvs.py --n 20     # 20 cells spread across the batches
```
