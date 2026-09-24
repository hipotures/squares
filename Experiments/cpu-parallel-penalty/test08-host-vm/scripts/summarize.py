"""Normalize identical-iteration native host/VM samples per 181 directions."""

import argparse
import json
import statistics as st
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "package" / "plan.json").read_text())
COUNTS = (1, 2, 4, 8, 16)
EVENTS = ("instructions", "cycles", "ls_any_fills_from_sys.all_dram_io")


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


def machine(directory):
    env = json.loads((directory / "environment.json").read_text())
    cases = {}
    for workers in COUNTS:
        xs = [json.loads((directory / f"sample{i}-w{workers}.json").read_text())
              for i in (1, 2, 3)]
        repeats = PLAN["repeats"][str(workers)]
        assert all(x["native"]["repeats"] == repeats for x in xs)
        assert all(x["native"]["checksum"] == PLAN["expected_checksums"][str(workers)]
                   for x in xs)
        assert all(10 <= x["native"]["wall"] <= 60 for x in xs)
        assert all(min(v.get("running_percent", 0) for v in x["perf_counters"].values()) >= 99.5
                   for x in xs)
        item = {"repeats": repeats,
                "batch_wall": stats([x["native"]["wall"] for x in xs]),
                "wall_per_replay": stats([x["native"]["wall"] / repeats for x in xs]),
                "worker_cpu_per_replay": stats([x["native"]["worker_cpu"] / repeats for x in xs]),
                "effective_cores": stats([x["native"]["worker_cpu"] /
                                          x["native"]["wall"] for x in xs]),
                "checksum": xs[0]["native"]["checksum"]}
        for event in EVENTS:
            item[event + "_per_replay"] = stats([
                x["perf_counters"][event]["count"] / repeats for x in xs])
        item["ipc"] = stats([
            x["perf_counters"]["instructions"]["count"] /
            x["perf_counters"]["cycles"]["count"] for x in xs])
        item["load_before"] = [x["load_before"] for x in xs]
        cases[str(workers)] = item
    one_wall = cases["1"]["wall_per_replay"]["median"]
    one_cpu = cases["1"]["worker_cpu_per_replay"]["median"]
    one_instr = cases["1"]["instructions_per_replay"]["median"]
    one_cycles = cases["1"]["cycles_per_replay"]["median"]
    one_fills = cases["1"]["ls_any_fills_from_sys.all_dram_io_per_replay"]["median"]
    for workers in COUNTS:
        c = cases[str(workers)]
        c["speedup"] = one_wall / c["wall_per_replay"]["median"]
        c["efficiency"] = c["speedup"] / workers
        c["cpu_inflation"] = c["worker_cpu_per_replay"]["median"] / one_cpu
        c["instructions_ratio"] = c["instructions_per_replay"]["median"] / one_instr
        c["cycles_ratio"] = c["cycles_per_replay"]["median"] / one_cycles
        c["dram_fills_ratio"] = c["ls_any_fills_from_sys.all_dram_io_per_replay"]["median"] / one_fills
    return {"environment": env, "workers": cases}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host-dir", type=Path)
    args = p.parse_args()
    result = {"plan": PLAN, "vm": machine(ROOT / "vm-results")}
    if args.host_dir:
        result["host"] = machine(args.host_dir)
        vm, host = result["vm"], result["host"]
        assert vm["environment"]["source_sha256"] == host["environment"]["source_sha256"]
        assert vm["environment"]["data_sha256"] == host["environment"]["data_sha256"]
        assert vm["environment"]["build_flags"] == host["environment"]["build_flags"]
        result["comparison"] = {}
        for workers in COUNTS:
            v = vm["workers"][str(workers)]
            h = host["workers"][str(workers)]
            assert v["checksum"] == h["checksum"]
            result["comparison"][str(workers)] = {
                "host_vs_vm_wall_ratio": h["wall_per_replay"]["median"] /
                                          v["wall_per_replay"]["median"],
                "host_vs_vm_cpu_ratio": h["worker_cpu_per_replay"]["median"] /
                                         v["worker_cpu_per_replay"]["median"],
                "host_vs_vm_inflation_ratio": h["cpu_inflation"] / v["cpu_inflation"]}
    out = ROOT / "processed"
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    for machine_name in ("vm", "host"):
        if machine_name not in result:
            continue
        print(machine_name)
        for workers in COUNTS:
            x = result[machine_name]["workers"][str(workers)]
            print(workers, round(x["wall_per_replay"]["median"], 4),
                  round(x["worker_cpu_per_replay"]["median"], 4),
                  round(x["cpu_inflation"], 3), round(x["ipc"]["median"], 3))


if __name__ == "__main__":
    main()
