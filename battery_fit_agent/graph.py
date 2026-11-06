"""The LangGraph workflow: one loop over the data store, one pass of the graph body per cell.

    next_file -> load_extract -> fit_models -> review -(flag)-> deep_dive -> plot -> record -> next_file
                                                     \\-(no flag)----------/
    next_file -(queue empty)-> summarize -> END
"""
import json
import os
from typing import TypedDict

import pandas as pd
from langgraph.graph import END, START, StateGraph

from .config import Config
from .extract import load_and_extract
from .fitting import compute_signals, fit_all, rank_fits, rule_flags
from .plotting import plot_cell
from .review import LLM, llm_report, llm_review


class BatchState(TypedDict):
    queue: list          # files still to process
    current: dict        # the cell being processed (data, fits, table, signals, review)
    results: list        # one summary row per finished cell
    report: str


def build_agent(cfg: Config):
    cfg.make_dirs()
    llm = LLM(cfg.model, cfg.ollama_url, enabled=cfg.use_llm)

    def next_file(state: BatchState):
        return {}                                                   # routing happens in the edge

    def route_next(state: BatchState):
        return "load_extract" if state["queue"] else "summarize"

    def load_extract(state: BatchState):
        path, rest = state["queue"][0], state["queue"][1:]
        cell = load_and_extract(path, eol_ah=cfg.eol_ah)
        print(f"\n[{cell['cell_id']}] {cell['facts']['cycles']} cycles, "
              f"{cell['facts']['outliers_removed']} outliers removed, "
              f"{cell['facts']['recovery_jumps']} recovery jumps")
        return {"queue": rest, "current": {"cell": cell}}

    def fit_models(state: BatchState):
        cur = dict(state["current"])
        cur["fits"] = fit_all(cur["cell"]["n"], cur["cell"]["q"])
        cur["table"] = rank_fits(cur["fits"])
        cur["signals"] = compute_signals(cur["cell"]["facts"], cur["fits"], cur["table"])
        s = cur["signals"]
        print(f"  best: {s['best_model']} (RMSE {s['best_rmse_mAh']} mAh, noise {s['noise_mAh']} mAh), "
              f"runner-up {s['runner_up']} dBIC={s['runner_up_delta_bic']}, knee ~cycle {s['knee_cycle']}")
        return {"current": cur}

    def review(state: BatchState):
        cur = dict(state["current"])
        rules = rule_flags(cur["signals"])
        cur["review"] = llm_review(llm, cur["cell"]["cell_id"], cur["signals"], cur["table"], rules)
        r = cur["review"]
        print(f"  review ({r['source']}): flag={r['flag']} priority={r.get('priority')} reasons={r.get('reasons')}")
        return {"current": cur}

    def route_review(state: BatchState):
        return "deep_dive" if state["current"]["review"]["flag"] else "plot"

    def deep_dive(state: BatchState):
        """Flagged cells only: try more flexible models and check whether they resolve the issue."""
        cur = dict(state["current"])
        cur["fits"] = fit_all(cur["cell"]["n"], cur["cell"]["q"], extended=True)
        cur["table"] = rank_fits(cur["fits"])
        new_best = cur["table"].index[0]
        ratio = cur["table"].iloc[0]["rmse_mAh"] / max(cur["signals"]["noise_mAh"], 1e-3)
        note = (f"deep-dive best: {new_best} (RMSE/noise {ratio:.2f})"
                + ("; flexible model resolves the misfit" if ratio <= 2.5 else "; still unexplained -> inspect manually"))
        cur["review"] = {**cur["review"], "deep_dive": note}
        if "breaks" in cur["fits"].get("piecewise_2break", {}):
            cur["review"]["deep_dive"] += f"; 2-break piecewise breaks at {cur['fits']['piecewise_2break']['breaks']}"
        print("  " + cur["review"]["deep_dive"])
        return {"current": cur}

    def plot(state: BatchState):
        cur = state["current"]
        path = os.path.join(cfg.plot_dir, f"{cur['cell']['cell_id']}.png")
        plot_cell(cur["cell"], cur["fits"], cur["table"], cur["review"], path, eol_ah=cfg.eol_ah)
        return {"current": {**cur, "plot": path}}

    def record(state: BatchState):
        cur = state["current"]; s = cur["signals"]; r = cur["review"]; f = cur["cell"]["facts"]
        row = {"cell_id": cur["cell"]["cell_id"], "cycles": f["cycles"], "eol_cycle": f["eol_cycle"],
               "best_model": cur["table"].index[0], "best_rmse_mAh": float(cur["table"].iloc[0]["rmse_mAh"]),
               "noise_mAh": s["noise_mAh"], "knee_cycle": s["knee_cycle"],
               "outliers": f["outliers_removed"], "recovery_jumps": f["recovery_jumps"],
               "flag": r["flag"], "priority": r.get("priority"), "reasons": "; ".join(r.get("reasons", [])),
               "comment": r.get("comment", ""), "deep_dive": r.get("deep_dive", ""), "plot": cur["plot"]}
        cur["table"].to_csv(os.path.join(cfg.out_dir, f"{row['cell_id']}_fits.csv"))
        return {"results": state["results"] + [row], "current": {}}

    def summarize(state: BatchState):
        df = pd.DataFrame(state["results"])
        # fleet-level check: cells whose knee comes unusually early *relative to their own life*
        df["knee_fraction"] = (df["knee_cycle"] / df["eol_cycle"].fillna(df["cycles"])).round(3)
        if df["knee_fraction"].notna().sum() >= 5:
            k = df["knee_fraction"].astype(float)
            z = (k - k.median()) / (1.4826 * (k - k.median()).abs().median() + 1e-9)
            for i in df.index[z < -3]:
                df.loc[i, "flag"] = True
                df.loc[i, "reasons"] = (df.loc[i, "reasons"] + "; " if df.loc[i, "reasons"] else "") + \
                                       "knee much earlier than the other cells"
        df.to_csv(os.path.join(cfg.out_dir, "summary.csv"), index=False)
        wins = df["best_model"].value_counts().to_dict()
        flagged = df[df["flag"]][["cell_id", "priority", "reasons", "deep_dive"]].to_dict("records")
        prompt = (f"Write a short report (max 200 words, plain text) for a battery scientist. {len(df)} cells were "
                  f"processed. Best-model counts by BIC: {wins}. Median knee cycle: {df['knee_cycle'].median()}. "
                  f"Flagged cells: {json.dumps(flagged)}. Say which functions best explain the data overall and "
                  f"which cells to inspect first and why.")
        report = llm_report(llm, prompt, wins, flagged)
        with open(os.path.join(cfg.out_dir, "report.md"), "w") as fh:
            fh.write(report)
        return {"results": df.to_dict("records"), "report": report}

    g = StateGraph(BatchState)
    for name, fn in [("next_file", next_file), ("load_extract", load_extract), ("fit_models", fit_models),
                     ("review", review), ("deep_dive", deep_dive), ("plot", plot), ("record", record),
                     ("summarize", summarize)]:
        g.add_node(name, fn)
    g.add_edge(START, "next_file")
    g.add_conditional_edges("next_file", route_next, ["load_extract", "summarize"])
    g.add_edge("load_extract", "fit_models")
    g.add_edge("fit_models", "review")
    g.add_conditional_edges("review", route_review, ["deep_dive", "plot"])
    g.add_edge("deep_dive", "plot")
    g.add_edge("plot", "record")
    g.add_edge("record", "next_file")
    g.add_edge("summarize", END)
    return g.compile()


def run(files, cfg: Config):
    agent = build_agent(cfg)
    final = agent.invoke({"queue": list(files), "current": {}, "results": [], "report": ""},
                         {"recursion_limit": 10 * len(files) + 20})
    return pd.DataFrame(final["results"]), final["report"]
