"""Recompute the published profile statistics directly from retained raw JSON."""

from __future__ import annotations

import hashlib
import json
import statistics as stats
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"


def read(name: str) -> dict:
    return json.loads((RAW / name).read_text())


def summary(values: list[float]) -> dict[str, float]:
    assert len(values) == 3
    return {
        "min": min(values), "median": stats.median(values), "max": max(values),
        "cv_percent": (
            100 * stats.stdev(values) / abs(stats.mean(values))
            if stats.mean(values) else 0.0
        ),
    }


def baseline() -> dict:
    output = {}
    for workers in (1, 4, 8, 16):
        samples = [read(f"baseline-w{workers}-s{i}.json") for i in (1, 2, 3)]
        metric = {
            "batch_wall_seconds": [x["batch_wall_seconds"] for x in samples],
            "wall_per_solve_seconds": [x["normalized_batch_wall_seconds"] for x in samples],
            "separation_per_solve_seconds": [
                sum(y["separation_seconds"] for y in x["solves"]) / x["repeats"]
                for x in samples
            ],
            "lp_per_solve_seconds": [
                sum(y["lp_seconds"] for y in x["solves"]) / x["repeats"]
                for x in samples
            ],
            "round0_per_solve_seconds": [
                sum(y["timings"][0]["separation_s"] + y["timings"][0]["lp_s"]
                    for y in x["solves"]) / x["repeats"]
                for x in samples
            ],
            "parent_cpu_per_solve_seconds": [
                x["parent_cpu_seconds"] / x["repeats"] for x in samples
            ],
        }
        metric["other_per_solve_seconds"] = [
            a - b - c for a, b, c in zip(
                metric["wall_per_solve_seconds"],
                metric["separation_per_solve_seconds"],
                metric["lp_per_solve_seconds"], strict=True
            )
        ]
        output[str(workers)] = {
            "samples": [f"raw/baseline-w{workers}-s{i}.json" for i in (1, 2, 3)],
            "repeats_per_sample": samples[0]["repeats"],
            "statistics": {name: summary(values) for name, values in metric.items()},
            "peak_parent_rss_kib_observed": [x["peak_parent_rss_kib"] for x in samples],
        }
    return output


def scaling() -> dict:
    output = {}
    for workers in (1, 2, 4, 8, 16):
        tag = "-long" if workers == 16 else ""
        samples = [read(f"separation-w{workers}{tag}-s{i}.json") for i in (1, 2, 3)]
        values = {
            "batch_wall_seconds": [x["batch_wall_seconds"] for x in samples],
            "wall_per_replay_seconds": [x["normalized_wall_seconds"] for x in samples],
            "worker_cpu_per_replay_seconds": [
                x["worker_cpu_seconds"] / x["repeats"] for x in samples
            ],
            "parent_cpu_per_replay_seconds": [
                x["parent_cpu_seconds"] / x["repeats"] for x in samples
            ],
        }
        for name, key in (
            ("parent_wait_per_replay_seconds", "worker_wait_seconds"),
            ("parent_process_per_replay_seconds", "parent_process_seconds"),
            ("dispatch_per_replay_seconds", "dispatch_seconds"),
        ):
            values[name] = [
                sum(r[key] for r in x["replays"]) / x["repeats"] for x in samples
            ]
        output[str(workers)] = {
            "samples": [f"raw/separation-w{workers}{tag}-s{i}.json" for i in (1, 2, 3)],
            "repeats_per_sample": samples[0]["repeats"],
            "statistics": {name: summary(array) for name, array in values.items()},
            "worker_rss_pages_last_sample": samples[-1]["worker_rss_pages"],
        }
    serial_wall = output["1"]["statistics"]["wall_per_replay_seconds"]["median"]
    serial_cpu = output["1"]["statistics"]["worker_cpu_per_replay_seconds"]["median"]
    for key, entry in output.items():
        workers = int(key)
        wall = entry["statistics"]["wall_per_replay_seconds"]["median"]
        cpu = entry["statistics"]["worker_cpu_per_replay_seconds"]["median"]
        entry["speedup_vs_one"] = serial_wall / wall
        entry["parallel_efficiency"] = serial_wall / wall / workers
        entry["effective_worker_cores"] = cpu / wall
        entry["worker_cpu_inflation"] = cpu / serial_cpu
    return output


def separation_profile() -> dict:
    output = {}
    for workers in (1, 16):
        samples = [read(f"profile-separation-w{workers}-s{i}.json")
                   for i in (1, 2, 3)]
        keys = sorted(samples[0]["replays"][0]["worker_metrics"])
        aggregate = {
            name: summary([
                sum(r["worker_metrics"].get(name, 0.0) for r in x["replays"])
                / x["repeats"] for x in samples
            ]) for name in keys
        }
        critical_names = samples[0]["replays"][0]["rounds"][0]["last_worker_phase_seconds"]
        critical = {
            name: summary([
                sum(sum(round_["last_worker_phase_seconds"].get(name, 0.0)
                        for round_ in r["rounds"]) for r in x["replays"])
                / x["repeats"] for x in samples
            ]) for name in critical_names
        }
        output[str(workers)] = {
            "samples": [f"raw/profile-separation-w{workers}-s{i}.json"
                        for i in (1, 2, 3)],
            "wall_per_replay_seconds": summary([x["normalized_wall_seconds"]
                                                 for x in samples]),
            "aggregate_worker_metrics_per_replay": aggregate,
            "last_worker_phase_seconds_per_replay": critical,
        }
    return output


def lp_profile() -> dict:
    output = {}
    for mode in ("reference", "profile"):
        samples = [read(f"lp-{mode}-s{i}.json") for i in (1, 2, 3)]
        entry = {
            "samples": [f"raw/lp-{mode}-s{i}.json" for i in (1, 2, 3)],
            "wall_per_sequence_seconds": summary([x["normalized_wall_seconds"]
                                                   for x in samples]),
        }
        if mode == "profile":
            names = samples[0]["sequences"][0]["phases"]
            entry["phase_seconds_per_sequence"] = {
                name: summary([
                    sum(seq["phases"][name] for seq in x["sequences"]) / x["repeats"]
                    for x in samples
                ]) for name in names
            }
        output[mode] = entry
    cpu_samples = [read(f"lp-cpu-s{i}.json") for i in (1, 2, 3)]
    output["direct_parent_cpu"] = {
        "samples": [f"raw/lp-cpu-s{i}.json" for i in (1, 2, 3)],
        "parent_cpu_per_sequence_seconds": summary([
            x["parent_cpu_per_sequence_seconds"] for x in cpu_samples
        ]),
        "wall_per_sequence_seconds": summary([
            x["wall_per_sequence_seconds"] for x in cpu_samples
        ]),
    }
    return output


def experiments() -> dict:
    output = {}
    for variant in ("vectorized", "prefix"):
        if not (RAW / f"{variant}-candidate-w16-s3.json").exists():
            continue
        endpoints = {}
        for workers in (1, 16):
            paired = {
                mode: [read(f"{variant}-{mode}-w{workers}-s{i}.json")
                       for i in (1, 2, 3)]
                for mode in ("reference", "candidate")
            }
            endpoints[str(workers)] = {
                mode: {
                    "files": [f"raw/{variant}-{mode}-w{workers}-s{i}.json"
                              for i in (1, 2, 3)],
                    "batch_wall_seconds": summary([x["batch_wall_seconds"] for x in data]),
                    "wall_per_solve_seconds": summary([
                        x["normalized_wall_seconds"] for x in data
                    ]),
                    "separation_per_solve_seconds": summary([
                        sum(r["separation_seconds"] for r in x["solves"]) / x["repeats"]
                        for x in data
                    ]),
                    "lp_per_solve_seconds": summary([
                        sum(r["lp_seconds"] for r in x["solves"]) / x["repeats"]
                        for x in data
                    ]),
                } for mode, data in paired.items()
            }
            diffs = [a["normalized_wall_seconds"] - b["normalized_wall_seconds"]
                     for a, b in zip(paired["reference"], paired["candidate"], strict=True)]
            endpoints[str(workers)]["paired_saved_seconds"] = summary(diffs)
            endpoints[str(workers)]["paired_reduction_percent"] = summary([
                100 * diff / a["normalized_wall_seconds"]
                for diff, a in zip(diffs, paired["reference"], strict=True)
            ])
        output[variant] = endpoints
    return output


def main() -> None:
    artifacts = {}
    for name in ("current-states.npz", "current-rows-csr.npz", "libprefix_rows.so"):
        payload = (RAW / name).read_bytes()
        artifacts[f"raw/{name}"] = {
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()
        }
    data = {
        "input_main_sha": json.loads((ROOT / "environment.json").read_text())["main_sha"],
        "case": "n=12, outer_side=99/25, square_side=9977/10000",
        "environment": "environment.json",
        "baseline": baseline(), "scaling": scaling(),
        "separation_profile": separation_profile(), "lp_profile": lp_profile(),
        "memory_probe": "raw/memory-probe.json",
        "baseline_correctness": "raw/baseline-correctness.json",
        "accepted_state_identity": "raw/current-identity.json",
        "binary_artifacts": artifacts,
        "research_experiments": experiments(),
    }
    (ROOT / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({
        "baseline_16_wall": data["baseline"]["16"]["statistics"]["wall_per_solve_seconds"],
        "experiments": {
            variant: {
                workers: {
                    "saved": endpoint["paired_saved_seconds"]["median"],
                    "reduction_percent": endpoint["paired_reduction_percent"]["median"],
                }
                for workers, endpoint in values.items()
            }
            for variant, values in data["research_experiments"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
