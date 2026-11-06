"""Score investigator verdicts (and the rule baseline) against hand labels."""
import pandas as pd


def evaluate(verdicts: pd.DataFrame, labels_csv: str):
    lab = pd.read_csv(labels_csv)
    alt = lab.get("acceptable_alternative", pd.Series([""] * len(lab))).fillna("")
    lab = lab.assign(acceptable=[{a} | ({b} if b else set()) for a, b in zip(lab["label"], alt)])
    m = verdicts.merge(lab[["cell_id", "label", "acceptable"]], on="cell_id", how="inner")
    errored = m[m["category"] == "error"]["cell_id"].tolist()   # API failures are not wrong answers
    m = m[m["category"] != "error"]
    if m.empty:
        return {"labelled_cells": 0, "skipped_api_errors": errored}, m
    m["llm_correct"] = [c in acc for c, acc in zip(m["category"], m["acceptable"])]
    m["baseline_correct"] = [c in acc for c, acc in zip(m["baseline"], m["acceptable"])]
    score = {"labelled_cells": len(m), "llm_agreement": f"{m['llm_correct'].sum()}/{len(m)}",
             "baseline_agreement": f"{m['baseline_correct'].sum()}/{len(m)}", "skipped_api_errors": errored}
    return score, m[["cell_id", "label", "category", "confidence", "baseline", "llm_correct", "baseline_correct"]]