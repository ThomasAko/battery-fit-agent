"""
extract_cycle_csvs.py — build the agent's battery_data_store from the BEEP FastCharge JSONs.

Download the BEEP-structured FastCharge files (Severson et al., Nature Energy 2019) from
https://data.matr.io/1/. For each structured JSON this keeps only the per-cycle summary columns the agent
needs and writes one small CSV per cell (~2,000 rows, ~100 kB), so the 27 GB dataset becomes a few MB.
The JSONs contain bare NaN/Infinity tokens, so they are read with a NaN-safe loader.

USAGE (JSONs in data/FastCharge/, CSVs written to data/battery_data_store/):
    python scripts/extract_cycle_csvs.py                # all cells
    python scripts/extract_cycle_csvs.py --n 20         # 20 cells spread across the dataset
    python scripts/extract_cycle_csvs.py --data_dir /elsewhere/FastCharge   # JSONs kept outside the repo
(or set FASTCHARGE_DIR instead of passing --data_dir)
"""
import os, re, json, argparse
import numpy as np
import pandas as pd

DATA_DIR  = os.getenv("FASTCHARGE_DIR", "data/FastCharge")

OUT_STORE = "data/battery_data_store"

KEEP = ["cycle_index", "discharge_capacity", "charge_capacity", "dc_internal_resistance",
        "temperature_maximum", "temperature_average", "charge_duration", "paused"]
ALIASES = {"qd": "discharge_capacity", "qc": "charge_capacity", "ir": "dc_internal_resistance",
           "tmax": "temperature_maximum", "tavg": "temperature_average", "chargetime": "charge_duration"}


def read_nan_json(filepath):
    """Replace bare NaN/Infinity tokens (invalid JSON), then json.loads."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = re.sub(r"\bNaN\b", "null", raw)
    raw = re.sub(r"-?\bInfinity\b", "null", raw)
    return json.loads(raw)


def extract_one(filepath):
    data = read_nan_json(filepath)
    summary = next((data[k] for k in ["structured_summary", "summary", "structured_data"] if k in data), None)
    if summary is None:
        return None
    df = pd.DataFrame(summary)
    df.columns = [c.lower().strip() for c in df.columns]
    df = df.rename(columns=ALIASES)
    df = df[[c for c in KEEP if c in df.columns]]
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "cycle_index" in df.columns:
        df = df.sort_values("cycle_index").reset_index(drop=True)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default=DATA_DIR, help="folder of FastCharge *_structure.json files")
    ap.add_argument("--out", default=OUT_STORE)
    ap.add_argument("--n", type=int, default=0, help="number of cells (0 = all)")
    args = ap.parse_args()

    if not os.path.isdir(args.data_dir):
        raise SystemExit(f"FastCharge folder not found: {args.data_dir} (use --data_dir or FASTCHARGE_DIR)")
    files = sorted(f for f in os.listdir(args.data_dir)
                   if f.endswith(".json") and os.path.getsize(os.path.join(args.data_dir, f)) > 1e6)
    if args.n and args.n < len(files):                       # evenly spaced subset across batches
        files = [files[i] for i in np.linspace(0, len(files) - 1, args.n).astype(int)]
    os.makedirs(args.out, exist_ok=True)
    print(f"Extracting {len(files)} cells -> {args.out}/")

    for i, fname in enumerate(files, 1):
        cell_id = fname.replace("_structure.json", "").replace(".json", "")
        try:
            df = extract_one(os.path.join(args.data_dir, fname))
            if df is None or len(df) < 50:
                print(f"  [{i:3d}] {cell_id}: skipped (no usable summary)")
                continue
            df.to_csv(os.path.join(args.out, f"{cell_id}.csv"), index=False)
            print(f"  [{i:3d}] {cell_id}: {len(df)} cycles, columns={list(df.columns)}")
        except Exception as e:
            print(f"  [{i:3d}] {cell_id}: FAILED ({e})")
    print("Done.")
