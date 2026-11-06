"""Investigator mode: fleet triage + tool-using LLM investigation of the shortlist.

    export GOOGLE_API_KEY=...                         # free key: https://aistudio.google.com/apikey
    python run_investigator.py                        # Gemini, high-priority shortlist
    python run_investigator.py --investigate labelled # the 10 hand-labelled cells, scored against the labels
    python run_investigator.py --investigate all      # every flagged cell
    python run_investigator.py --provider anthropic                 # Claude (ANTHROPIC_API_KEY)
    python run_investigator.py --provider groq --rpm 2              # free tier (GROQ_API_KEY)
    python run_investigator.py --provider ollama --model qwen2.5:14b --rpm 0   # local, free
    python run_investigator.py --skip-fit             # reuse fits from a previous run in --out
"""
import argparse
import os

import pandas as pd

from battery_fit_agent import Config
from battery_fit_agent.evaluate import evaluate
from battery_fit_agent.graph_v2 import run_fleet_agent
from battery_fit_agent.llm import DEFAULT_MODELS, PROVIDERS, get_chat_model, supports_images

LABELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "manual_labels.csv")


def main():
    cfg = Config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=cfg.data_store)
    ap.add_argument("--out", default="agent_outputs_investigator")
    ap.add_argument("--provider", default="gemini", choices=PROVIDERS)
    ap.add_argument("--model", default=None, help=f"default: {DEFAULT_MODELS}")
    ap.add_argument("--investigate", default="high", choices=["high", "all", "labelled"])
    ap.add_argument("--rpm", type=float, default=8, help="max LLM requests per minute (free tiers are rate limited)")
    ap.add_argument("--max-steps", type=int, default=6, help="max tool-calling rounds per cell")
    ap.add_argument("--no-plot", action="store_true", help="don't show the diagnostic plot to the model")
    ap.add_argument("--skip-fit", action="store_true", help="reuse fits already in --out")
    ap.add_argument("--cells", nargs="+", help="investigate only these cell ids (e.g. the ones skipped last time)")
    ap.add_argument("--shape-margin", type=float, default=10.0)
    a = ap.parse_args()

    cfg = Config(data_store=a.data, out_dir=a.out)
    cfg.make_dirs()
    llm = get_chat_model(a.provider, a.model, requests_per_minute=a.rpm)
    cells = a.cells or (pd.read_csv(LABELS)["cell_id"].tolist() if a.investigate == "labelled" else None)
    verdicts, report = run_fleet_agent(
        cfg, llm, which="cells" if cells else a.investigate, cells=cells, shape_margin=a.shape_margin,
        send_plot=supports_images(a.provider) and not a.no_plot, max_steps=a.max_steps, skip_fit=a.skip_fit)

    print("\n" + "=" * 80 + "\nREPORT\n" + "=" * 80 + "\n" + report)
    score, table = evaluate(verdicts, LABELS)
    if score and score.get("labelled_cells"):
        print(f"\nAgreement with hand labels: LLM {score['llm_agreement']}, "
              f"rule baseline {score['baseline_agreement']} ({score['labelled_cells']} labelled cells answered)")
        if score.get("skipped_api_errors"):
            print(f"Not scored (API errors): {', '.join(score['skipped_api_errors'])}")
        print(table.to_string(index=False))
        table.to_csv(os.path.join(cfg.out_dir, "evaluation.csv"), index=False)
    print(f"\nVerdicts, traces and report in {cfg.out_dir}/")


if __name__ == "__main__":
    main()