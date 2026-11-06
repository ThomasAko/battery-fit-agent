"""Tool-using investigator: a small ReAct loop (LangGraph subgraph) that examines one shortlisted cell,
returns a structured verdict, and is checked by a deterministic verifier that can send it back once.

    agent <-> tools   (the LLM chooses which tools to call, up to max_steps rounds)
    agent -> conclude -> verify -(problems, first time)-> agent
                              \\-(ok or already revised)-> END
"""
import base64
import json
import os
from typing import Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .llm import structured

CATEGORIES = ("real_early_ageing", "unusual_shape", "test_ended_before_eol", "data_quality", "normal")


class Verdict(BaseModel):
    category: Literal["real_early_ageing", "unusual_shape", "test_ended_before_eol", "data_quality", "normal"] = \
        Field(description="the single best explanation of why this cell stands out")
    confidence: Literal["low", "medium", "high"]
    evidence: list[str] = Field(description="2-4 short findings, each quoting numbers returned by the tools")
    recommended_action: str = Field(description="one sentence: what a battery engineer should do next")


SYSTEM = """You are a battery test engineer investigating one LFP/graphite cell (A123 18650, nominal 1.1 Ah,
end of life 0.88 Ah) that an automated fleet screen put on a shortlist. Use the tools to find out WHY it stands out.
Never compute or guess numbers yourself; only use numbers returned by the tools.

Categories:
- real_early_ageing: the cell reached end of life and its knee / fast fade starts unusually early versus the fleet
- unusual_shape: degradation follows a different law than the fleet (or two laws tie), without data problems
- test_ended_before_eol: the test stopped far from end of life, so knee position and life metrics are not comparable
- data_quality: outliers, gaps or capacity jumps that look like measurement / equipment problems dominate
- normal: on inspection nothing is unusual

Start with get_cell_overview, then check whatever the shortlist reasons point to (check_end_of_life before calling
anything an early knee; locate_outliers when outliers or jumps are present; compare_to_fleet to judge "unusual").
Stop calling tools once you can decide."""


class InvState(TypedDict):
    cell_id: str
    messages: list
    steps: int
    verdict: dict
    revisions: int
    problems: list
    facts: dict          # tool results, collected for the verifier


def _image_message(path):
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}


def build_investigator(llm, tools, max_steps=6, send_plot=False, plot_dir=None):
    by_name = {t.name: t for t in tools}
    llm_tools = llm.bind_tools(tools)
    llm_verdict = structured(llm, Verdict)

    def start(state: InvState):
        text = f"Investigate cell {state['cell_id']}."
        content = text
        if send_plot and plot_dir and os.path.exists(p := os.path.join(plot_dir, f"{state['cell_id']}.png")):
            content = [{"type": "text", "text": text + " Its diagnostic plot is attached "
                        "(data, fitted laws, knee marker, 0.88 Ah end-of-life line, residuals)."}, _image_message(p)]
        return {"messages": [SystemMessage(content=SYSTEM), HumanMessage(content=content)],
                "steps": 0, "revisions": 0, "facts": {}}

    def agent(state: InvState):
        msg = llm_tools.invoke(state["messages"])
        return {"messages": state["messages"] + [msg]}

    def route_agent(state: InvState):
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) and state["steps"] < max_steps else "conclude"

    def run_tools(state: InvState):
        out, facts = [], dict(state["facts"])
        for call in state["messages"][-1].tool_calls:
            try:
                res = by_name[call["name"]].invoke(call["args"])
            except Exception as e:                                   # bad arguments -> tell the model
                res = json.dumps({"error": f"{type(e).__name__}: {e}"})
            facts[f"{call['name']}({json.dumps(call['args'], sort_keys=True)})"] = res
            out.append(ToolMessage(content=res, tool_call_id=call["id"], name=call["name"]))
        return {"messages": state["messages"] + out, "steps": state["steps"] + 1, "facts": facts}

    def conclude(state: InvState):
        msgs = list(state["messages"])
        pending = getattr(msgs[-1], "tool_calls", None) or []
        msgs += [ToolMessage(content='{"error": "step limit reached"}', tool_call_id=c["id"], name=c["name"])
                 for c in pending]                     # every tool call needs a reply before the next turn
        msgs.append(HumanMessage(content="Give your verdict now, using only numbers from the tools."))
        try:
            v = llm_verdict.invoke(msgs).model_dump()
        except Exception as e:
            v = {"category": "normal", "confidence": "low", "evidence": [f"verdict parsing failed: {e}"],
                 "recommended_action": "inspect manually"}
        return {"verdict": v, "messages": msgs[:-1]}

    def verify(state: InvState):
        """Deterministic consistency checks between the verdict and the tool results."""
        v, f = state["verdict"], state["facts"]
        eol = next((json.loads(r) for k, r in f.items() if k.startswith("check_end_of_life")), None)
        ov = next((json.loads(r) for k, r in f.items() if k.startswith("get_cell_overview")), None)
        problems = []
        if not ov:
            problems.append("you never called get_cell_overview")
        if v["category"] in ("real_early_ageing", "test_ended_before_eol") and not eol:
            problems.append(f"'{v['category']}' requires check_end_of_life, which you did not call")
        if eol and v["category"] == "real_early_ageing" and not eol["reached_end_of_life"]:
            problems.append("you called it real_early_ageing but check_end_of_life says the cell never reached end "
                            f"of life (fade completed {eol['fade_completed_fraction']:.0%})")
        if eol and v["category"] == "test_ended_before_eol" and eol["reached_end_of_life"]:
            problems.append("you called it test_ended_before_eol but the cell did reach end of life "
                            f"(cycle {eol['eol_cycle']})")
        if ov and v["category"] == "data_quality" and ov["outliers_removed"] < 3 and ov["recovery_jumps"] < 3:
            problems.append(f"you called it data_quality but only {ov['outliers_removed']} outliers and "
                            f"{ov['recovery_jumps']} recovery jumps were found")
        return {"problems": problems}

    def route_verify(state: InvState):
        return "revise" if state["problems"] and state["revisions"] < 1 else END

    def revise(state: InvState):
        note = ("A consistency check found problems with your verdict:\n- " + "\n- ".join(state["problems"])
                + "\nUse the tools as needed and reconsider.")
        return {"messages": state["messages"] + [HumanMessage(content=note)], "revisions": state["revisions"] + 1}

    g = StateGraph(InvState)
    for name, fn in [("start", start), ("agent", agent), ("tools", run_tools), ("conclude", conclude),
                     ("verify", verify), ("revise", revise)]:
        g.add_node(name, fn)
    g.add_edge(START, "start"); g.add_edge("start", "agent")
    g.add_conditional_edges("agent", route_agent, ["tools", "conclude"])
    g.add_edge("tools", "agent"); g.add_edge("conclude", "verify")
    g.add_conditional_edges("verify", route_verify, ["revise", END])
    g.add_edge("revise", "agent")
    return g.compile()


def rule_baseline(row):
    """Deterministic classifier over the same facts, as a baseline the LLM investigator must beat or match."""
    if row["outliers"] >= 10 or row["recovery_jumps"] >= 3:
        return "data_quality"
    if row.get("fade_completed", 1.0) < 0.7:
        return "test_ended_before_eol"
    kz = row["knee_z"]
    if kz == kz and kz < -3:                                   # kz == kz is False for NaN
        return "real_early_ageing"
    if row["flag"]:
        return "unusual_shape"
    return "normal"


def transcript(state):
    """Readable trace of one investigation (tool calls, results, verdict)."""
    lines = [f"# {state['cell_id']}\n"]
    for m in state["messages"]:
        if isinstance(m, AIMessage):
            if m.content:
                lines.append(f"**agent:** {m.content if isinstance(m.content, str) else m.content}\n")
            for c in m.tool_calls or []:
                lines.append(f"**call** `{c['name']}({json.dumps(c['args'])})`\n")
        elif isinstance(m, ToolMessage):
            lines.append(f"```json\n{m.content}\n```\n")
        elif isinstance(m, HumanMessage) and isinstance(m.content, str) and "consistency check" in m.content:
            lines.append(f"**verifier:** {m.content}\n")
    lines.append(f"**verdict:** `{json.dumps(state['verdict'], indent=1)}`\n")
    return "\n".join(lines)