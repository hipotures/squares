"""Time the old and new small-k surveys on retained real NumPy inputs."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np

from sqpack.fractional.generate import _least_finite_indices


def _samples(call, *, repeats: int) -> list[float]:
    for _ in range(2):
        call()
    times = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        call()
        times.append((time.perf_counter_ns() - started) / 1e6)
    return times


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    fixture_dir = Path(__file__).resolve().parents[2] / "tests/fixtures"
    result: dict[str, object] = {
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "repeats": args.repeats,
        "workloads": {},
    }
    workloads = result["workloads"]
    assert isinstance(workloads, dict)
    for name, filename, zero_weight_grid in (
        ("round0", "round0_selector_flat.npz", True),
        ("round18", "late_selector_flat.npz", False),
    ):
        with np.load(fixture_dir / filename) as archive:
            flat = archive["flat"]

        def old(values: np.ndarray = flat) -> np.ndarray:
            order = np.argpartition(values, 12)[:13]
            order = order[np.isfinite(values[order])]
            return order[np.argsort(values[order])]

        def new(
            values: np.ndarray = flat, *, zero_weights: bool = zero_weight_grid
        ) -> np.ndarray:
            return _least_finite_indices(values, 13, zero_weight_grid=zero_weights)

        old_selected, new_selected = old(), new()
        assert np.array_equal(np.sort(flat[old_selected]), np.sort(flat[new_selected]))
        old_ms = _samples(old, repeats=args.repeats)
        new_ms = _samples(new, repeats=args.repeats)
        workloads[name] = {
            "size": flat.size,
            "finite": int(np.count_nonzero(np.isfinite(flat))),
            "old_ms": old_ms,
            "new_ms": new_ms,
            "old_median_ms": statistics.median(old_ms),
            "new_median_ms": statistics.median(new_ms),
        }
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                name: (data["old_median_ms"], data["new_median_ms"])
                for name, data in workloads.items()
            }
        )
    )


if __name__ == "__main__":
    main()
