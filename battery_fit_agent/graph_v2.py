"""Investigator mode: fit the whole fleet, triage against the fleet, then let a tool-using LLM investigate
each shortlisted cell and write a report grounded in the verdicts.

    fit_fleet -> triage -> next_cell -(more cells)-> investigate -> next_cell
                                     \\-(done)-----> report -> END
"""
import glob
import json
import os
import time
from typing import TypedDict

import pandas as pd
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from .config import Config
from .fleet import fleet_review
from .graph import run as run_fit_pipeline
from .investigator import build_investigator, rule_baseline, transcript
from .tools import CellStore, make_tools

REPORT_PROMPT = """You are writing a short report (max 250 words, markdown) for a battery scientist about a fleet of
{n} LFP/graphite cells. An automated screen shortlisted {k} cells and an investigator classified each one.
Verdicts (JSON): {verdicts}
Fleet: the double-exponential-type law '{law}' is the best parametric fit for {law_count} of {n} cells.
Group the shortlisted cells by category, say which to look at first and why, and quote only numbers that appear
in the verdict evidence. Do not invent cells or numbers."""


class FleetState(TypedDict):
    queue: list
    verdicts: list
    report: str
    shortlist: list


def build_fleet_agent(cfg: Config, llm, which="high", shape_margin=10.0, send_plot=False, max_steps=6,
                      cells=None, skip_fit=False, retries=3, retry_wait=30):
    """which: "high" (high-priority shortlist), "all" (every flagged cell) or "cells" (the list in `cells`)."""
    trace_dir = os.path.join(cfg.out_dir, "traces")
    os.makedirs(trace_dir, exist_ok=True)
    ctx = {}

    def fit_fleet(state: FleetState):
        if skip_fit and os.path.exists(os.path.join(cfg.out_dir, "summary.csv")):
            print("Reusing fits in", cfg.out_dir); return {}
        files = sorted(glob.glob(os.path.join(cfg.data_store, "*.csv")))
        fit_cfg = Config(data_store=cfg.data_store, out_dir=cfg.out_dir, use_llm=False)
        run_fit_pipeline(files, fit_cfg)                      # deterministic: extract, fit, rule flags, plots
        return {}

    def triage(state: FleetState):
        wf, majority, _ = fleet_review(cfg.out_dir, shape_margin=shape_margin, data_store=cfg.data_store,
                                       eol_ah=cfg.eol_ah, write=False)
        wf.to_csv(os.path.join(cfg.out_dir, "summary_triage.csv"), index=False)
        ctx.update(wf=wf, majority=majority,
                   store=CellStore(wf, cfg.out_dir, cfg.data_store, cfg.eol_ah))
        ctx["investigator"] = build_investigator(llm, make_tools(ctx["store"]), max_steps=max_steps,
                                                 send_plot=send_plot, plot_dir=cfg.plot_dir)
        pick = (wf[wf["flag"]] if which == "all" else wf[wf["cell_id"].isin(cells or [])] if which == "cells"
                else wf[wf["priority"] == "high"])
        print(f"\nTriage: {int(wf['flag'].sum())}/{len(wf)} flagged, {int((wf['priority'] == 'high').sum())} high "
              f"priority (fleet law: {majority}); investigating {len(pick)} cells")
        return {"queue": pick["cell_id"].tolist(), "shortlist": pick["cell_id"].tolist()}

    def next_cell(state: FleetState):
        return {}

    def route(state: FleetState):
        return "investigate" if state["queue"] else "report"

    def investigate(state: FleetState):
        cell_id, rest = state["queue"][0], state["queue"][1:]
        row = ctx["wf"].set_index("cell_id").loc[cell_id]
        base = {"cell_id": cell_id, "baseline": rule_baseline(row.to_dict() | {"cell_id": cell_id}),
                "triage_reasons": "; ".join(row["reasons"])}
        out, err = None, None
        for attempt in range(retries + 1):              # API overload (503) or rate limit (429): wait and retry
            try:
                out = ctx["investigator"].invoke({"cell_id": cell_id}, {"recursion_limit": 4 * max_steps + 20})
                break
            except Exception as e:
                err = e
                if attempt < retries:
                    wait = retry_wait * (attempt + 1)
                    print(f"  {cell_id}: API error ({str(e)[:80]}...); retrying in {wait}s")
                    time.sleep(wait)
        if out is None:                                 # give up on this cell, keep going with the others
            print(f"  {cell_id}: skipped after {retries + 1} attempts")
            v = {**base, "category": "error", "confidence": "low", "evidence": [str(err)[:300]],
                 "recommended_action": "re-run this cell", "tool_calls": 0, "revised": False,
                 "unresolved_problems": []}
            return {"queue": rest, "verdicts": state["verdicts"] + [v]}
        with open(os.path.join(trace_dir, f"{cell_id}.md"), "w") as fh:
            fh.write(transcript(out))
        v = {**base, **out["verdict"], "tool_calls": sum(len(getattr(m, "tool_calls", []) or [])
                                                         for m in out["messages"]),
             "revised": out["revisions"] > 0, "unresolved_problems": out["problems"]}
        print(f"  {cell_id}: {v['category']} ({v['confidence']}), {v['tool_calls']} tool calls"
              + (", revised after verifier" if v["revised"] else "") + f" | baseline: {v['baseline']}")
        return {"queue": rest, "verdicts": state["verdicts"] + [v]}

    def report(state: FleetState):
        vs = pd.DataFrame(state["verdicts"])
        vs.to_csv(os.path.join(cfg.out_dir, "verdicts.csv"), index=False)
        wf = ctx["wf"]
        slim = [{k: v[k] for k in ("cell_id", "category", "confidence", "evidence", "recommended_action")}
                for v in state["verdicts"] if v["category"] != "error"]
        prompt = REPORT_PROMPT.format(n=len(wf), k=len(slim), verdicts=json.dumps(slim), law=ctx["majority"],
                                      law_count=int((wf["best_parametric"] == ctx["majority"]).sum()))
        try:
            text = llm.invoke([HumanMessage(content=prompt)]).content
            text = text if isinstance(text, str) else " ".join(p.get("text", "") for p in text if isinstance(p, dict))
        except Exception as e:
            text = f"(report generation failed: {e})\n\n" + vs[["cell_id", "category", "confidence"]].to_string(index=False)
        with open(os.path.join(cfg.out_dir, "report_investigator.md"), "w") as fh:
            fh.write(text)
        return {"report": text}

    g = StateGraph(FleetState)
    for name, fn in [("fit_fleet", fit_fleet), ("triage", triage), ("next_cell", next_cell),
                     ("investigate", investigate), ("report", report)]:
        g.add_node(name, fn)
    g.add_edge(START, "fit_fleet"); g.add_edge("fit_fleet", "triage"); g.add_edge("triage", "next_cell")
    g.add_conditional_edges("next_cell", route, ["investigate", "report"])
    g.add_edge("investigate", "next_cell"); g.add_edge("report", END)
    return g.compile()


def run_fleet_agent(cfg: Config, llm, **kw):
    agent = build_fleet_agent(cfg, llm, **kw)
    final = agent.invoke({"queue": [], "verdicts": [], "report": "", "shortlist": []}, {"recursion_limit": 500})
    return pd.DataFrame(final["verdicts"]), final["report"]