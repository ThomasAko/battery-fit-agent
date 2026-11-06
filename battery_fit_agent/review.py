"""LLM reviewer and report writer (local Llama via Ollama), each with a deterministic fallback."""
import json

REVIEW_PROMPT = """You are a battery test engineer reviewing automated curve fits of discharge capacity vs cycle
for one LFP/graphite cell (A123, nominal 1.1 Ah, end of life 0.88 Ah). Decide whether a human should look at this
cell closely. Interesting cells are ones where the fits do not explain the data, the best model is ambiguous,
the data has quality problems (many outliers, capacity-recovery jumps), or degradation is unusual (e.g. an early knee).
A clean curve that one model explains well is NOT interesting.

Reply with JSON only:
{"flag": true or false, "priority": "high" | "medium" | "low", "reasons": ["short reason", ...], "comment": "one sentence"}"""


class LLM:
    """Thin wrapper so the rest of the code runs (rules only) when Ollama/langchain-ollama is unavailable."""

    def __init__(self, model, base_url, enabled=True):
        self.json = self.text = None
        if not enabled:
            return
        try:
            from langchain_ollama import ChatOllama
            self.json = ChatOllama(model=model, temperature=0, format="json", base_url=base_url)  # decisions
            self.text = ChatOllama(model=model, temperature=0, base_url=base_url)                 # report
        except Exception as e:  # pragma: no cover
            print(f"LLM disabled ({type(e).__name__}: {e}); using rule-based review.")


def _rules_only(rules, why):
    return {"flag": bool(rules), "priority": "medium" if rules else "low", "reasons": rules,
            "comment": f"LLM review unavailable ({why}); rule-based decision.", "source": "rules"}


def llm_review(llm, cell_id, signals, table, rules):
    if llm.json is None:
        return _rules_only(rules, "disabled")
    from langchain_core.messages import HumanMessage, SystemMessage
    msg = (f"Cell: {cell_id}\nSignals: {json.dumps(signals)}\n"
           f"Fit table (sorted by BIC):\n{table[['rmse_mAh', 'r2', 'bic', 'delta_bic']].to_string()}\n"
           f"Rule-based checks triggered: {rules or 'none'}")
    try:
        out = json.loads(llm.json.invoke([SystemMessage(content=REVIEW_PROMPT), HumanMessage(content=msg)]).content)
        out["flag"] = bool(out.get("flag")); out.setdefault("reasons", rules); out["source"] = "llm"
        return out
    except Exception as e:                                   # unusable reply -> deterministic fallback
        return _rules_only(rules, type(e).__name__)


def llm_report(llm, prompt, wins, flagged):
    fallback = (f"Best-model counts: {wins}\n"
                f"Flagged ({len(flagged)}): {[f['cell_id'] for f in flagged]}")
    if llm.text is None:
        return "(LLM report disabled)\n" + fallback
    try:
        return llm.text.invoke(prompt).content
    except Exception as e:
        return f"(LLM report unavailable: {e})\n" + fallback
