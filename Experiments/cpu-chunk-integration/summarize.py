"""Recompute all published medians and timing audits from retained raw JSON."""

from __future__ import annotations

import json
import statistics as stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def metric(values: list[float]) -> dict:
    return {
        "min": min(values), "median": stats.median(values), "max": max(values),
        "cv": (stats.pstdev(values) / stats.mean(values)
               if stats.mean(values) else 0.0),
        "samples": values,
    }


def solve_group(kind: str, workers: int) -> dict:
    samples = [read(RAW / f"{kind}-w{workers}" / f"baseline-w{workers}-s{i}.json")
               for i in (1, 2, 3)]
    for sample in samples:
        assert sample["batch_wall_seconds"] >= 10
        for solve in sample["solves"]:
            assert (solve["rounds"], solve["rows"], solve["objective"]) == (
                23, 5842, 12.217676366606236)
    def per_solve(key: str) -> list[float]:
        return [sum(run[key] for run in x["solves"]) / x["repeats"]
                for x in samples]
    return {
        "batch_seconds": metric([x["batch_wall_seconds"] for x in samples]),
        "wall_seconds": metric([x["normalized_batch_wall_seconds"] for x in samples]),
        "separation_seconds": metric(per_solve("separation_seconds")),
        "lp_seconds": metric(per_solve("lp_seconds")),
        "other_seconds": metric([
            x["normalized_batch_wall_seconds"]
            - sum(run["separation_seconds"] + run["lp_seconds"]
                  for run in x["solves"]) / x["repeats"]
            for x in samples
        ]),
        "round0_seconds": metric([
            sum(run["timings"][0]["separation_s"] + run["timings"][0]["lp_s"]
                for run in x["solves"]) / x["repeats"] for x in samples
        ]),
        "sample_files": [str((RAW / f"{kind}-w{workers}" /
                              f"baseline-w{workers}-s{i}.json").relative_to(ROOT))
                         for i in (1, 2, 3)],
    }


def replay_group(mode: str, workers: int, tag: str = "accepted") -> dict:
    samples = [read(RAW / f"separation-{mode}-w{workers}-{tag}-s{i}.json")
               for i in (1, 2, 3)]
    for sample in samples:
        assert sample["batch_wall_seconds"] >= 10
        assert all(len(replay["rounds"]) == 23 for replay in sample["replays"])
    wall = [x["normalized_wall_seconds"] for x in samples]
    cpu = [x["worker_cpu_seconds"] / x["repeats"] for x in samples]
    return {
        "batch_seconds": metric([x["batch_wall_seconds"] for x in samples]),
        "wall_seconds": metric(wall), "worker_cpu_seconds": metric(cpu),
        "parent_cpu_seconds": metric([x["parent_cpu_seconds"] / x["repeats"]
                                      for x in samples]),
        "effective_cores": metric([c / w for c, w in zip(cpu, wall, strict=True)]),
        "minor_faults_per_replay": metric([x["worker_minor_faults"] / x["repeats"]
                                           for x in samples]),
        "parent_wait_seconds": metric([
            sum(r["worker_wait_seconds"] for r in x["replays"]) / x["repeats"]
            for x in samples
        ]),
        "parent_result_seconds": metric([
            sum(r["parent_process_seconds"] for r in x["replays"]) / x["repeats"]
            for x in samples
        ]),
        "dispatch_seconds": metric([
            sum(r["dispatch_seconds"] for r in x["replays"]) / x["repeats"]
            for x in samples
        ]),
        "sample_files": [f"raw/separation-{mode}-w{workers}-{tag}-s{i}.json"
                         for i in (1, 2, 3)],
    }


def profile_group(workers: int) -> dict:
    samples = [read(RAW / f"profile-separation-w{workers}-s{i}.json")
               for i in (1, 2, 3)]
    for sample in samples:
        assert sample["batch_wall_seconds"] >= 10
    names = samples[0]["replays"][0]["worker_metrics"]
    phases = {}
    for name in names:
        if name in ("grid_cells", "grid_bytes", "compact_values", "compact_bytes",
                    "live_sites", "minor_faults", "pid", "task_start_at", "task_end_at"):
            continue
        phases[name] = metric([
            sum(r["worker_metrics"].get(name, 0) for r in x["replays"]) / x["repeats"]
            for x in samples
        ])
    critical_names = samples[0]["replays"][0]["rounds"][0]["last_worker_phase_seconds"]
    critical = {
        name: metric([
            sum(sum(round_["last_worker_phase_seconds"].get(name, 0)
                    for round_ in replay["rounds"]) for replay in x["replays"])
            / x["repeats"] for x in samples
        ]) for name in critical_names
    }
    return {
        "wall_seconds": metric([x["normalized_wall_seconds"] for x in samples]),
        "aggregate_worker_phase_seconds": phases,
        "last_worker_path_proxy_seconds": critical,
    }


def main() -> None:
    controls = {str(w): solve_group("control", w) for w in (1, 16)}
    accepted = {str(w): solve_group("candidate", w) for w in (1, 4, 8, 16)}
    scaling = {str(w): replay_group("chunk", w, "postprofile" if w == 16
                                    else "accepted") for w in (1, 4, 8, 16)}
    reference_replay = replay_group("reference", 16, "postprofile")
    profile = {str(w): profile_group(w) for w in (1, 16)}
    pairs = []
    for i in (1, 2, 3):
        ref = read(RAW / "paired" / f"reference-s{i}.json")
        chunk = read(RAW / "paired" / f"candidate-s{i}.json")
        assert ref["batch_wall_seconds"] >= 10 and chunk["batch_wall_seconds"] >= 10
        pairs.append({
            "sample": i, "reference_wall": ref["wall_per_solve_seconds"],
            "candidate_wall": chunk["wall_per_solve_seconds"],
            "saved_seconds": ref["wall_per_solve_seconds"] - chunk["wall_per_solve_seconds"],
            "reference_batch_seconds": ref["batch_wall_seconds"],
            "candidate_batch_seconds": chunk["batch_wall_seconds"],
        })
    serial = scaling["1"]
    for workers, item in scaling.items():
        count = int(workers)
        item["speedup"] = serial["wall_seconds"]["median"] / item["wall_seconds"]["median"]
        item["efficiency"] = item["speedup"] / count
        item["cpu_inflation"] = (item["worker_cpu_seconds"]["median"]
                                 / serial["worker_cpu_seconds"]["median"])
    timed = [read(path)["batch_wall_seconds"] for path in RAW.rglob("*.json")
             if "batch_wall_seconds" in read(path)]
    assert timed and min(timed) >= 10
    data = {
        "baseline_commit": "5f10bffeb207d5bc598a6244f11375cee3418d62",
        "accepted_commit": "011aa1b5f39457de1e2d9f5589b3df3f04e36575",
        "correctness": read(RAW / "correctness.json"),
        "profile_equivalence": read(RAW / "profile-equivalence.json"),
        "timed_sample_audit": {
            "count": len(timed), "minimum_seconds": min(timed),
            "maximum_seconds": max(timed), "all_at_least_10_seconds": True,
        },
        "control_solver": controls, "accepted_solver": accepted,
        "paired_solver": pairs, "separation_scaling": scaling,
        "reference_separation_16": reference_replay,
        "earlier_separation_16": {
            "chunk": replay_group("chunk", 16),
            "reference": replay_group("reference", 16),
        },
        "separation_profile": profile,
        "paired_saving_seconds": metric([x["saved_seconds"] for x in pairs]),
    }
    (ROOT / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({
        "paired_saving": data["paired_saving_seconds"],
        "accepted_w16": accepted["16"]["wall_seconds"],
        "replay_w16": scaling["16"]["wall_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
