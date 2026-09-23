"""Check retained samples, durations, and correctness evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    results = read(ROOT / "results.json")
    checks = {}
    groups = {
        "baseline": sorted(RAW.glob("baseline-w*-s*.json")),
        "scaling": sorted(RAW.glob("separation-w*-s*.json")),
        "profile_separation": sorted(RAW.glob("profile-separation-w*-s*.json")),
        "profile_lp": [RAW / f"lp-{mode}-s{i}.json"
                       for mode in ("reference", "profile") for i in (1, 2, 3)],
        "lp_cpu": sorted(RAW.glob("lp-cpu-s*.json")),
        "prototypes": sorted(RAW.glob("vectorized-*-s*.json"))
        + sorted(RAW.glob("prefix-*-s*.json")),
    }
    expected_counts = {
        "baseline": 12, "scaling": 18, "profile_separation": 6,
        "profile_lp": 6, "lp_cpu": 3, "prototypes": 24,
    }
    lengths = {}
    for group, files in groups.items():
        checks[f"{group}_sample_count"] = len(files) == expected_counts[group]
        durations = []
        for file in files:
            item = read(file)
            duration = item["batch_wall_seconds"]
            durations.append(duration)
            assert 10 <= duration <= 60, (file, duration)
            if "solves" in item:
                for solve in item["solves"]:
                    assert solve["rounds"] == 23 and solve["rows"] == 5842
                    assert abs(solve["objective"] - 12.217676366606236) < 1e-9
                    assert solve["stopped"] == "converged: every placement covers mass 1"
                    assert len(solve["timings"]) == 23
            elif "replays" in item:
                for replay in item["replays"]:
                    assert len(replay["rounds"]) == 23
                    assert replay["rounds"][-1]["rows_held"] == 5842
            elif "sequences" in item:
                for sequence in item["sequences"]:
                    assert len(sequence["objectives"]) == 22
                    assert abs(sequence["objectives"][-1] - 12.217676366606236) < 1e-9
            elif group == "lp_cpu":
                assert abs(item["last_objective"] - 12.217676366606236) < 1e-9
        lengths[group] = {"files": len(files), "min_seconds": min(durations),
                          "max_seconds": max(durations)}
        checks[f"{group}_durations_10_to_60_seconds"] = True
    for label, file in (
        ("baseline_correctness", "baseline-correctness.json"),
        ("accepted_state_identity", "current-identity.json"),
        ("timed_grid_bitwise", "profile-grid-equivalence.json"),
        ("vectorized_equivalence", "vectorized-equivalence.json"),
        ("prefix_equivalence", "prefix-equivalence.json"),
    ):
        checks[label] = read(RAW / file)["passed"]
    checks["input_commit"] = (
        results["input_main_sha"]
        == "14ba672d999fa34b77d422a4a3e1f43e14df572e"
    )
    passed = all(checks.values())
    output = {"passed": passed, "checks": checks, "timed_sample_groups": lengths}
    (RAW / "final-audit.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))  # noqa: T201
    assert passed


if __name__ == "__main__":
    main()
