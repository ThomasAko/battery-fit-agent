"""Run the curve-fitting agent over a folder of per-cell CSVs.

    python run_agent.py                                  # data/battery_data_store -> agent_outputs
    python run_agent.py --data my_cells --out results
    python run_agent.py --no-llm                         # rule-based review only (no Ollama needed)
    python run_agent.py --model llama3.1:8b --ollama-url http://localhost:11434
"""
import argparse
import glob
import os
import sys

from battery_fit_agent import Config, fleet_review, run


def main():
    cfg = Config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=cfg.data_store, help="folder of per-cell CSVs")
    ap.add_argument("--out", default=cfg.out_dir, help="output folder (plots, fit tables, summaries, report)")
    ap.add_argument("--model", default=cfg.model, help="Ollama model tag")
    ap.add_argument("--ollama-url", default=cfg.ollama_url)
    ap.add_argument("--no-llm", action="store_true", help="skip the LLM; use the rule-based reviewer")
    ap.add_argument("--limit", type=int, default=None, help="process only the first N cells")
    a = ap.parse_args()

    cfg = Config(data_store=a.data, out_dir=a.out, model=a.model, ollama_url=a.ollama_url, use_llm=not a.no_llm)
    files = sorted(glob.glob(os.path.join(cfg.data_store, "*.csv")))[: a.limit]
    if not files:
        sys.exit(f"No CSVs found in '{cfg.data_store}'. See README -> Data.")
    print(f"{len(files)} cell files in {cfg.data_store}")

    summary, report = run(files, cfg)
    print("\n" + "=" * 80 + "\nREPORT\n" + "=" * 80 + "\n" + report)
    print("\nBest model per cell (by BIC, after deep dive):")
    print(summary["best_model"].value_counts().to_string())

    if len(summary) >= 5:
        wf, majority, summ = fleet_review(cfg.out_dir)
        print(f"\nPer-cell criteria: {int(summ['flag'].sum())}/{len(summ)} flagged  |  "
              f"fleet-relative criteria: {int(wf['flag'].sum())}/{len(wf)} flagged  (fleet law: {majority})")
        for _, r in wf[wf["flag"]].sort_values("priority").iterrows():
            print(f"  {r.cell_id} [{r.priority}]: " + "; ".join(r.reasons))
    print(f"\nOutputs written to {cfg.out_dir}/")


if __name__ == "__main__":
    main()
