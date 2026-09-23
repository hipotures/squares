#!/usr/bin/env python3
"""Reduce full solver traces without adding overlapping worker times as wall."""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def read(name):
    return json.loads((RESULTS / name).read_text())


def seconds(ns):
    return ns / 1e9


def union_ns(items):
    intervals = sorted((x["start_ns"], x["end_ns"]) for x in items)
    total = 0
    lo = hi = None
    for start, end in intervals:
        if lo is None:
            lo, hi = start, end
        elif start <= hi:
            hi = max(hi, end)
        else:
            total += hi - lo
            lo, hi = start, end
    return total + (hi - lo if lo is not None else 0)


EVENT_PARTS = ("project_u", "project_v", "live_filter", "live_gather",
    "event_construct_u", "event_construct_v", "unique_u", "unique_v",
    "searchsorted", "grid_alloc", "add_at", "cumsum_1", "cumsum_2",
    "v_range", "reachable")


def categories(profile):
    c = Counter(profile["parts_ns"])
    result = {
        "projection": c["project_u"] + c["project_v"],
        "live_filter_and_gather": c["live_filter"] + c["live_gather"],
        "event_construction": c["event_construct_u"] + c["event_construct_v"],
        "unique": c["unique_u"] + c["unique_v"],
        "searchsorted": c["searchsorted"],
        "grid_allocation": c["grid_alloc"],
        "add_at": c["add_at"],
        "double_cumsum": c["cumsum_1"] + c["cumsum_2"],
        "domain_v_range": c["v_range"],
        "reachable": c["reachable"],
        "event_grid_other": c["event_grid_total"] - sum(c[k] for k in EVENT_PARTS),
        "scored_where": c["scored_where"],
        "candidate_selection": c["selector_total"],
        "candidate_reconstruction": c["reconstruct"],
        "coverage_mask": c["coverage_mask"],
        "weight_sum": c["weight_sum"],
        "candidate_sort": c["found_sort"],
    }
    result["placement_other"] = profile["cpu_ns"] - sum(result.values())
    return result


def phase(round_index):
    return "round0" if round_index == 0 else "steady"


def main():
    base = {w: [read(f"baseline-w{w}-r{i}.json") for i in range(1, 4)] for w in (1, 16)}
    median = {}
    for w, runs in base.items():
        median[str(w)] = {key: statistics.median(x["row_run"][key] for x in runs)
                          for key in ("seconds", "separation_seconds", "lp_seconds",
                                      "rounds", "rows", "objective")}
        median[str(w)]["round0_separation_seconds"] = statistics.median(
            x["round_timings_exact"][0]["separation_seconds"] for x in runs)
        median[str(w)]["least_covered"] = statistics.median(x["least_covered"] for x in runs)
        median[str(w)]["pricing_seconds"] = statistics.median(x["pricing"]["total_s"] for x in runs)
    traces = {w: read("profile-serial.json" if w == 1 else "profile-16.json") for w in (1, 16)}
    phase_summary = {}
    op_serial_ns = Counter()
    op_parallel_wall_ns = Counter()
    op_parallel_cpu_ns = Counter()
    phase_op = defaultdict(Counter)
    phase_sep = defaultdict(float)
    for w, trace in traces.items():
        groups = defaultdict(list)
        for p in trace["profiles"]:
            groups[p["round"]].append(p)
        total_profile_sep = trace["row_run"]["separation_seconds"]
        scale = median[str(w)]["separation_seconds"] / total_profile_sep
        for timing in trace["round_timings_exact"]:
            index = timing["index"]
            entries = groups[index]
            ph = phase(index)
            counts = Counter()
            for p in entries:
                counts.update(categories(p))
            cpu = sum(p["cpu_ns"] for p in entries)
            if w == 1:
                op_serial_ns.update(counts)
                phase_op[(w, ph)].update(counts)
                phase_sep[(w, ph)] += timing["separation_seconds"]
            else:
                active = union_ns(entries)
                round_ns = timing["separation_seconds"] * 1e9
                if active > round_ns + 1e6:
                    raise RuntimeError(f"worker intervals exceed round {index} separation wall")
                for key, value in counts.items():
                    op_parallel_cpu_ns[key] += value
                    wall = active * value / cpu * scale
                    op_parallel_wall_ns[key] += wall
                    phase_op[(w, ph)][key] += wall
                parent = max(0, round_ns - active) * scale
                op_parallel_wall_ns["parent_gaps"] += parent
                phase_op[(w, ph)]["parent_gaps"] += parent
                phase_sep[(w, ph)] += timing["separation_seconds"] * scale
    serial_row_ns = traces[1]["row_run"]["separation_seconds"] * 1e9 - sum(
        p["cpu_ns"] for p in traces[1]["profiles"])
    serial_row_ns *= median["1"]["separation_seconds"] / traces[1]["row_run"]["separation_seconds"]
    op_serial_ns["row_bookkeeping"] = serial_row_ns
    # Serial operation measurements are direct profiled seconds; the row
    # residual is scaled to the unprofiled median only for presentation.
    table = {}
    for key in sorted(set(op_serial_ns) | set(op_parallel_wall_ns)):
        table[key] = dict(serial_seconds=seconds(op_serial_ns[key]),
                          serial_pct=100 * seconds(op_serial_ns[key]) /
                                     traces[1]["row_run"]["separation_seconds"],
                          parallel_wall_seconds=seconds(op_parallel_wall_ns[key]),
                          parallel_aggregate_worker_cpu_seconds=seconds(op_parallel_cpu_ns[key]),
                          concurrency_inflation=(op_parallel_cpu_ns[key] / op_serial_ns[key]
                                                  if op_serial_ns[key] else None))
    whole = median["16"]["seconds"]
    sep = median["16"]["separation_seconds"]
    nonsep = whole - sep
    gpu_ops = ("double_cumsum", "reachable", "scored_where", "candidate_selection")
    gpu_group = sum(table[k]["parallel_wall_seconds"] for k in gpu_ops)
    steady_gpu_group = sum(seconds(phase_op[(16, "steady")][k]) for k in gpu_ops)
    factors = (2, 5, 10, 20)
    amdahl = {
        "all_separation": {str(f): dict(total_seconds=nonsep + sep/f, speedup=whole/(nonsep+sep/f)) for f in factors},
        "measured_gpu_group_only": {str(f): dict(total_seconds=whole-gpu_group+gpu_group/f, speedup=whole/(whole-gpu_group+gpu_group/f)) for f in factors},
        "gpu_group_operations": gpu_ops,
        "gpu_group_wall_seconds": gpu_group,
        "steady_gpu_group_wall_seconds": steady_gpu_group,
        "all_separation_infinite": dict(total_seconds=nonsep, speedup=whole/nonsep),
        "gpu_group_infinite": dict(total_seconds=whole-gpu_group, speedup=whole/(whole-gpu_group)),
        "steady_gpu_group_infinite": dict(total_seconds=whole-steady_gpu_group, speedup=whole/(whole-steady_gpu_group)),
        "nonseparation_seconds": nonsep,
    }
    thresholds = {str(f): whole/f-nonsep for f in (1, 1.25, 1.5, 2)}
    replay = read("replay-round18.json")
    replay_summary = {}
    for op in ("selector", "double_cumsum"):
        replay_summary[op] = {}
        for w in (1, 16):
            runs = [r for r in replay["runs"] if r["op"] == op and r["workers"] == w]
            replay_summary[op][str(w)] = {
                "wall_seconds": statistics.median(r["wall_ns"] for r in runs)/1e9,
                "worker_cpu_seconds": statistics.median(r["worker_cpu_ns"] for r in runs)/1e9,
            }
    result = dict(baseline_medians=median, trace_overhead={str(w): traces[w]["row_run"]["seconds"]-median[str(w)]["seconds"] for w in (1,16)},
                  profile_run_seconds={str(w): traces[w]["row_run"]["seconds"] for w in (1,16)},
                  operation_table=table, phase_operations={f"{w}_{ph}": {k:seconds(v) if w==1 else seconds(v) for k,v in vals.items()} for (w,ph),vals in phase_op.items()},
                  phase_separation_seconds={f"{w}_{ph}":v for (w,ph),v in phase_sep.items()},
                  amdahl=amdahl, gpu_separation_thresholds=thresholds,
                  replay_summary=replay_summary)
    (RESULTS / "summary.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: result[k] for k in ("baseline_medians", "operation_table", "amdahl", "gpu_separation_thresholds", "replay_summary")}, indent=2))


if __name__ == "__main__":
    main()
