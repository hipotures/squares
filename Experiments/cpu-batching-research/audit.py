"""Audit retained primary batches and pinned-workload correctness receipts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    files = sorted((ROOT / "raw").glob("[ABCD]-w*-s*.json"))
    files += sorted((ROOT / "raw/full-solver").glob("*.json"))
    assert len(files) == 72, len(files)
    durations = []
    for path in files:
        sample = json.loads(path.read_text())
        duration = sample["batch_wall_seconds"]
        assert 10 <= duration <= 60, (path, duration)
        if path.parent.name != "full-solver":
            assert sample["correctness"].startswith("warmup matrix")
            assert all(sample["thread_limits"][name] == "1" for name in
                       ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"))
        else:
            assert sample["full_state_identical"]
            assert all(run["rounds"] == 23 and run["rows"] == 5842
                       for run in sample["solves"])
        durations.append(duration)
    result = {"cpu_accepted_sha": "2a2efa39edb179128184f19d6a4235a6bbcaebcc",
              "timed_samples": len(files), "min_batch_seconds": min(durations),
              "max_batch_seconds": max(durations), "all_primary_batches_10_to_60_seconds": True,
              "all_fixed_replays_identical_order_centres_matrix_warmup": True,
              "full_solver_trajectory_valid": True}
    (ROOT / "raw/audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
