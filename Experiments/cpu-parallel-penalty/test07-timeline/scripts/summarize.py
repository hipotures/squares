"""Reduce long timeline batches and quantify overlapping wall-tail mechanisms."""

import gzip
import json
import statistics as st
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"


def read(mode, pair):
    with gzip.open(RAW / f"{mode}-w16-pair{pair}-s1.json.gz", "rt") as handle:
        return json.load(handle)


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


def quantile(values, fraction):
    seq = sorted(values)
    return seq[min(len(seq) - 1, int(fraction * (len(seq) - 1)))]


def one_trace(trace):
    totals = defaultdict(float)
    per_round = []
    delays = []
    correlations = []
    for round_data in trace:
        chunks = sorted(round_data["chunks"], key=lambda c: c["chunk"])
        first = min(c["worker_start"] for c in chunks)
        last = max(c["worker_finish"] for c in chunks)
        span = last - first
        worker_busy = sum(c["worker_finish"] - c["worker_start"] for c in chunks)
        worker_cpu = sum(c["worker_cpu"] for c in chunks)
        by_worker = defaultdict(list)
        for chunk in chunks:
            by_worker[chunk["worker_pid"]].append(chunk)
            delays.append(chunk["consume_start"] - chunk["result_ready"])
        final_finishes = sorted(max(c["worker_finish"] for c in group)
                                for group in by_worker.values())
        half_done = final_finishes[len(final_finishes) // 2 - 1]
        tail_after_half = last - half_done
        hol = 0.0
        for index, chunk in enumerate(chunks[:-1]):
            next_ready = min(c["result_ready"] for c in chunks[index + 1:])
            hol += max(0.0, chunk["received"] - max(chunk["wait_start"], next_ready))
        events = []
        for chunk in chunks:
            events.append((chunk["worker_start"], 1))
            events.append((chunk["worker_finish"], -1))
        events.sort(key=lambda x: (x[0], x[1]))
        histogram = defaultdict(float)
        active = 0
        previous = first
        for now, delta in events:
            histogram[str(active)] += max(0.0, now - previous)
            active += delta
            previous = now
        predicted = [c["predicted_cells"] for c in chunks]
        observed = [c["worker_finish"] - c["worker_start"] for c in chunks]
        if st.pstdev(predicted) and st.pstdev(observed):
            correlations.append(st.correlation(predicted, observed))
        row = {"round": round_data["round"], "round_wall": round_data["end"] - round_data["start"],
               "worker_first_start": first, "worker_last_finish": last,
               "worker_average_finish": st.mean(c["worker_finish"] for c in chunks),
               "worker_active_span": span, "worker_busy_sum": worker_busy,
               "worker_cpu_sum": worker_cpu,
               "worker_utilization": worker_busy / (16 * span),
               "tail_after_half_workers_finish": tail_after_half,
               "head_of_line_wait": hol,
               "parent_wait": round_data["parent_wait"],
               "parent_process": round_data["parent_process"],
               "slowest_chunk": max(observed),
               "active_worker_seconds_by_count": dict(histogram),
               "chunks": len(chunks), "workers_used": len(by_worker)}
        per_round.append(row)
        for key in ("round_wall", "worker_active_span", "worker_busy_sum",
                    "worker_cpu_sum", "tail_after_half_workers_finish",
                    "head_of_line_wait", "parent_wait", "parent_process"):
            totals[key] += row[key]
    totals["worker_utilization_weighted"] = (
        totals["worker_busy_sum"] / (16 * totals["worker_active_span"]))
    totals["result_ready_to_consume_median"] = st.median(delays)
    totals["result_ready_to_consume_p95"] = quantile(delays, 0.95)
    totals["predictor_cell_duration_correlation_median"] = (
        st.median(correlations) if correlations else None)
    return dict(totals), per_round


result = {"modes": {}, "pairs": [], "trace_metrics": {}, "rounds": {}}
source = {}
for mode in ("production", "ordered", "cost-first"):
    xs = [read(mode, pair) for pair in (1, 2, 3)]
    source[mode] = xs
    assert all(10 <= x["batch_wall"] <= 60 for x in xs)
    assert all(x["rows"] == 5842 and x["rounds"] == 23 for x in xs)
    result["modes"][mode] = {
        "batch_wall": stats([x["batch_wall"] for x in xs]),
        "wall_per_replay": stats([x["wall_per_replay"] for x in xs]),
        "worker_cpu_per_replay": stats([x["worker_cpu_per_replay"] for x in xs]),
        "parent_cpu_per_replay": stats([x["parent_cpu_per_replay"] for x in xs]),
        "replays_per_sample": [x["repeats"] for x in xs],
        "hashes": xs[0]["hashes"],
    }
    if mode != "production":
        trace_values = [one_trace(x["first_replay_trace"]) for x in xs]
        result["trace_metrics"][mode] = {
            key: stats([value[0][key] for value in trace_values])
            for key in trace_values[0][0]
            if trace_values[0][0][key] is not None
        }
        result["rounds"][mode] = trace_values[0][1]
for pair in (1, 2, 3):
    current = source["ordered"][pair - 1]["wall_per_replay"]
    candidate = source["cost-first"][pair - 1]["wall_per_replay"]
    result["pairs"].append({"pair": pair, "ordered_wall": current,
                            "cost_first_wall": candidate,
                            "saving": current - candidate})
assert result["modes"]["ordered"]["hashes"] == result["modes"]["cost-first"]["hashes"]
result["balanced_comparison"] = {"modes": {}, "pairs": [], "trace_metrics": {}}
balanced_source = {}
for mode in ("ordered", "balanced"):
    xs = []
    for pair in (1, 2, 3):
        with gzip.open(RAW / f"{mode}-w16-balance{pair}-s1.json.gz", "rt") as handle:
            xs.append(json.load(handle))
    balanced_source[mode] = xs
    assert all(10 <= x["batch_wall"] <= 60 for x in xs)
    result["balanced_comparison"]["modes"][mode] = {
        "batch_wall": stats([x["batch_wall"] for x in xs]),
        "wall_per_replay": stats([x["wall_per_replay"] for x in xs]),
        "worker_cpu_per_replay": stats([x["worker_cpu_per_replay"] for x in xs]),
        "hashes": xs[0]["hashes"],
    }
    traces = [one_trace(x["first_replay_trace"])[0] for x in xs]
    result["balanced_comparison"]["trace_metrics"][mode] = {
        key: stats([x[key] for x in traces])
        for key in ("round_wall", "worker_active_span", "worker_busy_sum",
                    "worker_cpu_sum", "tail_after_half_workers_finish",
                    "worker_utilization_weighted", "parent_wait", "parent_process")}
for pair in (1, 2, 3):
    current = balanced_source["ordered"][pair - 1]["wall_per_replay"]
    candidate = balanced_source["balanced"][pair - 1]["wall_per_replay"]
    result["balanced_comparison"]["pairs"].append(
        {"pair": pair, "ordered_wall": current, "balanced_wall": candidate,
         "saving": current - candidate})
assert (result["balanced_comparison"]["modes"]["ordered"]["hashes"] ==
        result["balanced_comparison"]["modes"]["balanced"]["hashes"])
(ROOT / "processed").mkdir(exist_ok=True)
(ROOT / "processed" / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
for mode, x in result["modes"].items():
    print(mode, "wall", round(x["wall_per_replay"]["median"], 3),
          "worker CPU", round(x["worker_cpu_per_replay"]["median"], 3))
print("paired savings", [round(x["saving"], 3) for x in result["pairs"]])
print("balanced paired savings", [round(x["saving"], 3)
                                  for x in result["balanced_comparison"]["pairs"]])
