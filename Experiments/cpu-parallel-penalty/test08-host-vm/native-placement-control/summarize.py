"""Verify physical pin/restore and summarize native placement controls."""

import hashlib
import json
import statistics as st
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FULL = ROOT / "full-solver-placement"


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


def native(source, workers):
    records = [json.loads((source / f"sample{i}-w{workers}.json").read_text())
               for i in (1, 2, 3)]
    repeats = 350 if workers == 8 else 620
    checksum = "6dcf5659d2bc7924" if workers == 8 else "9f46094101fd3341"
    assert all(x["native"]["repeats"] == repeats for x in records)
    assert all(x["native"]["checksum"] == checksum for x in records)
    assert all(10 <= x["native"]["wall"] <= 60 for x in records)
    assert all(min(v["running_percent"] for v in x["perf_counters"].values())
               >= 99.5 for x in records)
    output = {"batch_wall": stats([x["native"]["wall"] for x in records]),
              "wall_per_replay": stats([x["native"]["wall"] / repeats for x in records]),
              "worker_cpu_per_replay": stats([x["native"]["worker_cpu"] / repeats
                                              for x in records]),
              "checksum": checksum, "repeats": repeats}
    for event in ("instructions", "cycles", "ls_any_fills_from_sys.all_dram_io"):
        output[event + "_per_replay"] = stats([
            x["perf_counters"][event]["count"] / repeats for x in records])
    return output


def solver(source, workers):
    records = [json.loads((source / f"baseline-w{workers}-s{i}.json").read_text())
               for i in (1, 2, 3)]
    runs = [run for record in records for run in record["solves"]]
    assert all(run["rounds"] == 23 and run["rows"] == 5842 for run in runs)
    assert all(run["objective"] == 12.217676366606236 for run in runs)
    assert all(run["stopped"] == "converged: every placement covers mass 1"
               for run in runs)
    assert all(record["batch_wall_seconds"] >= 10 for record in records)
    trajectory_keys = ("index", "rows_held", "rows_added", "violated",
                       "support", "objective")
    trajectories = [tuple(tuple(round_[key] for key in trajectory_keys)
                          for round_ in run["timings"]) for run in runs]
    assert all(trajectory == trajectories[0] for trajectory in trajectories)
    trajectory_sha256 = hashlib.sha256(
        json.dumps(trajectories[0], separators=(",", ":")).encode()).hexdigest()
    return {"batch_wall": stats([x["batch_wall_seconds"] for x in records]),
            "wall_per_solve": stats([x["normalized_batch_wall_seconds"] for x in records]),
            "separation_per_solve": stats([
                st.mean(run["separation_seconds"] for run in x["solves"])
                for x in records]),
            "lp_per_solve": stats([
                st.mean(run["lp_seconds"] for run in x["solves"])
                for x in records]),
            "correct_solves": len(runs),
            "trajectory_sha256": trajectory_sha256,
            "repeats_per_batch": [x["repeats"] for x in records]}


def affinity(directory):
    before = [line.split("\t") for line in (directory / "before.tsv").read_text().splitlines()]
    pinned = (directory / "after-taskset.txt").read_text().splitlines()
    assert len(before) == len(pinned) == 16
    assert all(int(line[0]) == i and line[2] == "0-31" for i, line in enumerate(before))
    assert all(line.endswith(": " + str(i)) for i, line in enumerate(pinned))
    assert "RESTORED_OK" in (directory / "log.txt").read_text()
    return {"original_verified": True, "pinned_verified": True,
            "restored_verified": True,
            "pinned_at": (directory / "PINNED").read_text().strip(),
            "restored_at": (directory / "RESTORED").read_text().strip()}


def main():
    result = {"native": {}, "solver": {}, "affinity": {}}
    for workers in (8, 16):
        result["native"][str(workers)] = {
            "vm_unpinned": native(ROOT / "tail-retest" / "vm-results", workers),
            "vm_pinned": native(HERE / "vm-results", workers),
            "physical_pve": native(ROOT / "tail-retest" / "host-results", workers)}
    result["affinity"]["native"] = affinity(HERE / "host-evidence")
    result["affinity"]["full_solver"] = affinity(FULL / "host-evidence")
    result["solver"] = {
        "w8_default": solver(HERE / "full-solver-unpinned-w8", 8),
        "w8_guest_affinity_only": solver(FULL / "full-solver-guest-affinity-only-w8", 8),
        "w8_host_and_guest_pinned": solver(FULL / "full-solver-pinned-w8", 8),
        "w16_default": solver(HERE / "full-solver-unpinned-w16", 16)}
    assert len({x["trajectory_sha256"] for x in result["solver"].values()}) == 1
    result["solver_trajectory_identical_across_all_66_solves"] = True
    a = result["native"]["8"]
    result["derived"] = {
        "native_w8_wall_speedup_pinned_vs_unpinned":
            a["vm_unpinned"]["wall_per_replay"]["median"] /
            a["vm_pinned"]["wall_per_replay"]["median"],
        "native_w8_cpu_saving_fraction":
            1 - a["vm_pinned"]["worker_cpu_per_replay"]["median"] /
            a["vm_unpinned"]["worker_cpu_per_replay"]["median"],
        "solver_w8_wall_saving_vs_default":
            result["solver"]["w8_default"]["wall_per_solve"]["median"] -
            result["solver"]["w8_host_and_guest_pinned"]["wall_per_solve"]["median"],
        "solver_w8_wall_saving_vs_guest_affinity_only":
            result["solver"]["w8_guest_affinity_only"]["wall_per_solve"]["median"] -
            result["solver"]["w8_host_and_guest_pinned"]["wall_per_solve"]["median"],
        "solver_pinned_w8_minus_default_w16":
            result["solver"]["w8_host_and_guest_pinned"]["wall_per_solve"]["median"] -
            result["solver"]["w16_default"]["wall_per_solve"]["median"]}
    out = HERE / "processed"
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["derived"], indent=2))


if __name__ == "__main__":
    main()
