"""Audit long samples and reduce selected causal controls."""

import json
import statistics as st
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
matrix = json.loads((ROOT / "processed" / "matrix.json").read_text())


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


def triplet(target, background, n, tag):
    values = [json.loads((RAW / f"{target}-{background}-n{n}-{tag}-s{i}.json").read_text())
              for i in (1, 2, 3)]
    assert all(10 <= x["wall"] <= 60 for x in values)
    assert all(min(v["running_percent"] for v in x["counters"].values()) >= 99.5
               for x in values)
    measures = {"wall_per_call": stats([x["wall_per_call"] for x in values]),
                "cpu_per_call": stats([x["cpu_per_call"] for x in values]),
                "ipc": stats([x["ipc"] for x in values])}
    for event in ("instructions", "cycles", "ls_any_fills_from_sys.all_dram_io"):
        measures[event + "_per_call"] = stats([
            x["counters"][event]["count"] / x["calls"] for x in values])
    return measures


result = {"repeat_conditions": {}, "distinct_inputs": {}, "register_controls": {},
          "screen_cells": matrix["screen_cells"],
          "repeated_cells": matrix["repeated_cells"],
          "sample_target_seconds": 20}
for target in ("prefix", "slab", "top13", "direction", "register"):
    result["repeat_conditions"][f"{target}:idle"] = triplet(target, "sleep", 0, "repeat")
for row in matrix["repeated"]:
    target, background, n = row["target"], row["background"], row["bg_count"]
    key = f"{target}:{background}:{n}"
    result["repeat_conditions"][key] = triplet(target, background, n, "repeat")
for target in ("prefix", "slab", "top13"):
    result["distinct_inputs"][f"{target}:{target}:14"] = triplet(
        target, target, 14, "distinct")
for background in ("stream", "prefix", "slab", "top13"):
    result["register_controls"][background] = triplet(
        "register", background, 14, "register-control")
idle = result["repeat_conditions"]
for group in (result["repeat_conditions"], result["distinct_inputs"],
              result["register_controls"]):
    for key, value in group.items():
        target = "register" if group is result["register_controls"] else key.split(":")[0]
        value["wall_inflation_vs_idle"] = (
            value["wall_per_call"]["median"] /
            idle[f"{target}:idle"]["wall_per_call"]["median"])

(ROOT / "processed" / "final.json").write_text(json.dumps(result, indent=2) + "\n")
for key in ("prefix:stream:8", "slab:slab:14", "direction:prefix:8",
            "top13:stream:14"):
    print(key, round(result["repeat_conditions"][key]["wall_inflation_vs_idle"], 2))
