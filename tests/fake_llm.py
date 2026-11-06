"""A scripted stand-in for a tool-calling chat model, so the investigator graph can be tested offline."""
import json

from langchain_core.messages import AIMessage, ToolMessage


class FakeToolLLM:
    """Calls overview + end-of-life + outliers, then classifies from the tool results.
    If `wrong_first` is set, the first verdict is deliberately inconsistent to exercise the verifier."""

    def __init__(self, wrong_first=False):
        self.wrong_first, self.calls = wrong_first, 0

    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema):
        llm = self

        class _S:
            def invoke(self, messages):
                res = {m.name: json.loads(m.content) for m in messages if isinstance(m, ToolMessage)}
                ov, eol = res["get_cell_overview"], res["check_end_of_life"]
                revised = any("consistency check" in str(getattr(m, "content", "")) for m in messages)
                if llm.wrong_first and not revised:
                    cat = "real_early_ageing" if not eol["reached_end_of_life"] else "test_ended_before_eol"
                elif ov["outliers_removed"] >= 10 or ov["recovery_jumps"] >= 3:
                    cat = "data_quality"
                elif not eol["reached_end_of_life"] and eol["fade_completed_fraction"] < 0.7:
                    cat = "test_ended_before_eol"
                elif ov["knee_z"] is not None and ov["knee_z"] < -3:
                    cat = "real_early_ageing"
                else:
                    cat = "unusual_shape"
                return schema(category=cat, confidence="medium",
                              evidence=[f"knee_z={ov['knee_z']}", f"reached_eol={eol['reached_end_of_life']}"],
                              recommended_action="inspect")
        return _S()

    def invoke(self, messages):
        self.calls += 1
        first = next(m.content for m in messages if m.type == "human")
        first = first if isinstance(first, str) else first[0]["text"]
        if first.startswith("You are writing a short report"):
            return AIMessage(content="(fake report)")
        cell = first.split()[2].rstrip(".")
        done = {m.name for m in messages if isinstance(m, ToolMessage)}
        for name in ("get_cell_overview", "check_end_of_life", "locate_outliers"):
            if name not in done:
                return AIMessage(content="", tool_calls=[{"name": name, "args": {"cell_id": cell},
                                                          "id": f"c{self.calls}"}])
        if "compare_to_fleet" not in done:
            return AIMessage(content="", tool_calls=[{"name": "compare_to_fleet",
                                                      "args": {"cell_id": cell, "metric": "knee_fraction"},
                                                      "id": f"c{self.calls}"}])
        return AIMessage(content="I have enough information.")
