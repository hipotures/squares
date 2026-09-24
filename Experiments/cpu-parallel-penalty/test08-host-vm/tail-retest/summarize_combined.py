"""Combine original 1/2/4 and revised 8/16 native host/VM samples."""

import json
import statistics as st
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ORIGINAL_PLAN = json.loads((ROOT / "package" / "plan.json").read_text())
TAIL_PLAN = json.loads((HERE / "package" / "plan.json").read_text())
COUNTS = (1, 2, 4, 8, 16)
EVENTS = ("instructions", "cycles", "ls_any_fills_from_sys.all_dram_io")


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


def dataset(machine):
    old = ROOT / (machine + "-results")
    new = HERE / (machine + "-results")
    environment = json.loads((old / "environment.json").read_text())
    tail_environment = json.loads((new / "environment.json").read_text())
    for key in ("source_sha256", "data_sha256", "build_flags", "compiler"):
        assert environment[key] == tail_environment[key], (machine, key)
    cases = {}
    for workers in COUNTS:
        source = old if workers <= 4 else new
        plan = ORIGINAL_PLAN if workers <= 4 else TAIL_PLAN
        repeats = plan["repeats"][str(workers)]
        records = [json.loads((source / f"sample{i}-w{workers}.json").read_text())
                   for i in (1, 2, 3)]
        assert all(x["native"]["workers"] == workers for x in records)
        assert all(x["native"]["repeats"] == repeats for x in records)
        assert all(x["native"]["checksum"] ==
                   plan["expected_checksums"][str(workers)] for x in records)
        assert all(10 <= x["native"]["wall"] <= 60 for x in records)
        assert all(min(v["running_percent"] for v in x["perf_counters"].values())
                   >= 99.5 for x in records)
        case = {"source": str(source.relative_to(ROOT)), "repeats": repeats,
                "checksum": records[0]["native"]["checksum"],
                "batch_wall": stats([x["native"]["wall"] for x in records]),
                "wall_per_replay": stats([x["native"]["wall"] / repeats for x in records]),
                "worker_cpu_per_replay": stats([x["native"]["worker_cpu"] / repeats
                                                for x in records]),
                "effective_cores": stats([x["native"]["worker_cpu"] /
                                           x["native"]["wall"] for x in records]),
                "ipc": stats([x["perf_counters"]["instructions"]["count"] /
                              x["perf_counters"]["cycles"]["count"] for x in records]),
                "load_before": [x["load_before"] for x in records]}
        for event in EVENTS:
            case[event + "_per_replay"] = stats([
                x["perf_counters"][event]["count"] / repeats for x in records])
        cases[str(workers)] = case
    one = cases["1"]
    for workers in COUNTS:
        case = cases[str(workers)]
        case["speedup"] = one["wall_per_replay"]["median"] / case["wall_per_replay"]["median"]
        case["efficiency"] = case["speedup"] / workers
        case["cpu_inflation"] = case["worker_cpu_per_replay"]["median"] / one["worker_cpu_per_replay"]["median"]
        for event in EVENTS:
            case[event + "_ratio"] = (case[event + "_per_replay"]["median"] /
                                       one[event + "_per_replay"]["median"])
    return {"environment_original": environment,
            "environment_tail": tail_environment, "workers": cases}


def main():
    vm, host = dataset("vm"), dataset("host")
    for key in ("source_sha256", "data_sha256", "build_flags"):
        assert vm["environment_original"][key] == host["environment_original"][key]
    comparison = {}
    for workers in COUNTS:
        v, h = vm["workers"][str(workers)], host["workers"][str(workers)]
        assert v["repeats"] == h["repeats"] and v["checksum"] == h["checksum"]
        comparison[str(workers)] = {
            "host_vs_vm_wall_ratio": h["wall_per_replay"]["median"] /
                                     v["wall_per_replay"]["median"],
            "host_vs_vm_cpu_ratio": h["worker_cpu_per_replay"]["median"] /
                                    v["worker_cpu_per_replay"]["median"],
            "host_vs_vm_instruction_ratio": h["instructions_per_replay"]["median"] /
                                            v["instructions_per_replay"]["median"],
            "host_vs_vm_cycle_ratio": h["cycles_per_replay"]["median"] /
                                      v["cycles_per_replay"]["median"]}
    output = {"method": "original plan 1/2/4; matched revised plan 8/16",
              "excluded_receipt": "host-results/perf-sample1-w8.csv; "
                                  "7.902868434-second batch, no valid sample JSON",
              "original_plan": ORIGINAL_PLAN, "tail_plan": TAIL_PLAN,
              "vm": vm, "host": host, "comparison": comparison}
    path = ROOT / "processed" / "summary-complete.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(path)
    for workers in COUNTS:
        v, h = vm["workers"][str(workers)], host["workers"][str(workers)]
        print(workers, "VM", round(v["wall_per_replay"]["median"], 5),
              "host", round(h["wall_per_replay"]["median"], 5),
              "VM infl", round(v["cpu_inflation"], 3),
              "host infl", round(h["cpu_inflation"], 3))


if __name__ == "__main__":
    main()
