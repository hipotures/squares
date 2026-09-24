"""Reduce adjacent verified-THP pairs and retain per-sample hardware counters."""

import json
import statistics as st
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
EVENTS = ("instructions", "cycles", "ls_any_fills_from_sys.all_dram_io",
          "ls_l1_d_tlb_miss.all_l2_miss")


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


result = {}
for workers in (1, 16):
    cases = {}
    for mode in ("normal", "huge"):
        samples = [json.loads((RAW / f"{mode}-w{workers}-pair{i}-s1.json").read_text())
                   for i in (1, 2, 3)]
        assert all(x["hugepages_confirmed_before_timing"] for x in samples)
        assert all(min(v["running_percent"] for v in x["counters"].values()) >= 99.5
                   for x in samples)
        endpoint = {
            "cpu_per_call": stats([x["median_cpu_per_call"] for x in samples]),
            "huge_kib_min": min(min(x["huge_kib_before_by_worker"]) for x in samples),
            "minor_faults_per_call": stats([
                sum(r["minor_faults"] for r in x["records"]) /
                sum(r["calls"] for r in x["records"]) for x in samples]),
        }
        for event in EVENTS:
            endpoint[event + "_per_worker_call"] = stats([
                x["counters"][event]["count"] /
                sum(r["calls"] for r in x["records"]) for x in samples])
        cases[mode] = endpoint
    result[str(workers)] = {"cases": cases, "pairs": [
        {"pair": i,
         "normal_cpu_per_call": json.loads((RAW / f"normal-w{workers}-pair{i}-s1.json").read_text())["median_cpu_per_call"],
         "huge_cpu_per_call": json.loads((RAW / f"huge-w{workers}-pair{i}-s1.json").read_text())["median_cpu_per_call"]}
        for i in (1, 2, 3)]}
    a, b = cases["normal"], cases["huge"]
    result[str(workers)]["huge_vs_normal_cpu_ratio"] = (
        b["cpu_per_call"]["median"] / a["cpu_per_call"]["median"])
    result[str(workers)]["huge_vs_normal_dtlb_miss_ratio"] = (
        b["ls_l1_d_tlb_miss.all_l2_miss_per_worker_call"]["median"] /
        a["ls_l1_d_tlb_miss.all_l2_miss_per_worker_call"]["median"])

(ROOT / "processed").mkdir(exist_ok=True)
(ROOT / "processed" / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
for workers, row in result.items():
    print(workers, "CPU ratio", round(row["huge_vs_normal_cpu_ratio"], 3),
          "DTLB ratio", round(row["huge_vs_normal_dtlb_miss_ratio"], 3))
