import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.dirname(__file__))
from fake_llm import FakeToolLLM  # noqa: E402
from make_synthetic_cells import main as make_cells  # noqa: E402

from battery_fit_agent import Config  # noqa: E402
from battery_fit_agent.graph_v2 import run_fleet_agent  # noqa: E402


def _run(tmp_path, llm, which="all"):
    data, out = tmp_path / "data", tmp_path / "out"
    make_cells(str(data))
    cfg = Config(data_store=str(data), out_dir=str(out)); cfg.make_dirs()
    verdicts, report = run_fleet_agent(cfg, llm, which=which)
    return verdicts, report, out


def test_investigator_classifies_planted_anomalies(tmp_path):
    v, report, out = _run(tmp_path, FakeToolLLM())
    cat = dict(zip(v["cell_id"], v["category"]))
    assert cat.get("SYNTH_010") == "test_ended_before_eol"     # stopped at 35 % of life
    assert "SYNTH_005" in cat                                  # glitchy logger is shortlisted
    assert cat.get("SYNTH_003") == "real_early_ageing"         # early knee
    assert (v["tool_calls"] >= 4).all()
    assert os.path.exists(out / "traces" / "SYNTH_010.md") and os.path.exists(out / "verdicts.csv")
    assert report == "(fake report)"


def test_verifier_sends_inconsistent_verdict_back(tmp_path):
    v, _, _ = _run(tmp_path, FakeToolLLM(wrong_first=True))
    assert v["revised"].all()
    assert (v["unresolved_problems"].str.len() == 0).all()
    assert dict(zip(v["cell_id"], v["category"]))["SYNTH_010"] == "test_ended_before_eol"


def test_step_limit_pads_pending_tool_calls(tmp_path):
    from langchain_core.messages import ToolMessage
    from battery_fit_agent.fleet import fleet_review
    from battery_fit_agent.investigator import build_investigator
    from battery_fit_agent.tools import CellStore, make_tools
    _, _, out = _run(tmp_path, FakeToolLLM(), which="high")
    wf, _, _ = fleet_review(str(out), shape_margin=10, data_store=str(tmp_path / "data"), write=False)
    inv = build_investigator(FakeToolLLM(), make_tools(CellStore(wf, str(out), str(tmp_path / "data"))), max_steps=1)
    res = inv.invoke({"cell_id": "SYNTH_010"})
    ids = {c["id"] for m in res["messages"] for c in (getattr(m, "tool_calls", None) or [])}
    answered = {m.tool_call_id for m in res["messages"] if isinstance(m, ToolMessage)}
    assert ids <= answered
