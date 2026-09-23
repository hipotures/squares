"""Long in-memory replay of the accepted incremental LP row sequence."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import highspy
import numpy as np
from scipy.sparse import csr_matrix, load_npz

from sqpack.fractional.colgen import Rows, _PersistentLp

ROOT = Path(__file__).resolve().parents[1]


def load() -> dict[str, object]:
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "loadavg": os.getloadavg(),
        "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip(),
    }


def one_sequence(
    costs: np.ndarray, blocks: list[np.ndarray], expected: np.ndarray,
    *, profile: bool,
) -> dict[str, object]:
    phases = dict.fromkeys(("model_creation", "row_matrix_stacking", "csr_conversion", "highs_add_rows", "highs_run", "solution_extraction", "other"), 0.0)
    t0 = time.perf_counter()
    model = _PersistentLp(costs)
    phases["model_creation"] += time.perf_counter() - t0
    rows = Rows(matrix=np.zeros((0, len(costs))))
    objectives = []
    first = time.perf_counter()
    for block in blocks:
        rows.pending.extend(block)
        rows.directions.extend([0] * len(block))
        if profile:
            t = time.perf_counter()
            matrix = rows.stacked()
            phases["row_matrix_stacking"] += time.perf_counter() - t
            count = len(rows) - model.held
            t = time.perf_counter()
            new = csr_matrix(-matrix[model.held:])
            starts = new.indptr.astype(np.int32)
            indexes = new.indices.astype(np.int32)
            lower = np.full(count, -highspy.kHighsInf)
            upper = -np.ones(count)
            phases["csr_conversion"] += time.perf_counter() - t
            t = time.perf_counter()
            status = model.highs.addRows(
                count, lower, upper, new.nnz, starts, indexes, new.data
            )
            assert status == highspy.HighsStatus.kOk
            model.held += count
            phases["highs_add_rows"] += time.perf_counter() - t
            t = time.perf_counter()
            assert model.highs.run() == highspy.HighsStatus.kOk
            assert model.highs.getModelStatus() == highspy.HighsModelStatus.kOptimal
            phases["highs_run"] += time.perf_counter() - t
            t = time.perf_counter()
            solution = model.highs.getSolution()
            weights = np.asarray(solution.col_value, dtype=float)
            duals = np.maximum(-np.asarray(solution.row_dual, dtype=float), 0.0)
            objective = float(model.highs.getObjectiveValue())
            phases["solution_extraction"] += time.perf_counter() - t
            assert len(duals) == len(rows)
        else:
            solved = model.solve(rows)
            assert solved is not None
            weights, _duals, objective = solved
        objectives.append(objective)
    sequence_wall = time.perf_counter() - first
    # Different equivalent bases are allowed, but these captured rows must
    # reproduce the accepted objective and a feasible final solution.
    assert len(objectives) == len(blocks) == 22
    assert abs(objectives[-1] - 12.217676366606236) < 1e-9
    assert np.min(expected @ weights) >= 1 - 1e-7
    phases["other"] = sequence_wall - sum(
        val for name, val in phases.items() if name != "model_creation"
    )
    return {"wall_seconds": sequence_wall, "phases": phases,
            "objectives": objectives}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("profile", "reference"), required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=20)
    args = parser.parse_args()
    stored = np.load(ROOT / "raw/current-states.npz")
    counts = stored["row_counts"]
    costs = stored["costs"]
    matrix = load_npz(ROOT / "raw/current-rows-csr.npz").toarray()
    blocks = [matrix[first:last] for first, last in zip(
        np.concatenate(([0], counts[:-1])), counts, strict=True
    )]
    params = (costs, blocks, matrix)
    warm = one_sequence(*params, profile=args.mode == "profile")
    repeats = max(1, math.ceil(args.target_seconds / warm["wall_seconds"]))
    if repeats * warm["wall_seconds"] > 60:
        repeats = max(1, int(60 / warm["wall_seconds"]))
    for sample in range(1, args.samples + 1):
        load_before = load()
        start = time.perf_counter()
        sequences = [one_sequence(*params, profile=args.mode == "profile")
                     for _ in range(repeats)]
        batch_wall = time.perf_counter() - start
        assert batch_wall >= 10, (args.mode, sample, batch_wall)
        result = {
            "mode": args.mode, "sample": sample, "repeats": repeats,
            "load_before": load_before, "warmup_wall_seconds": warm["wall_seconds"],
            "batch_wall_seconds": batch_wall,
            "normalized_wall_seconds": batch_wall / repeats,
            "sequences": sequences,
        }
        path = ROOT / "raw" / f"lp-{args.mode}-s{sample}.json"
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"mode": args.mode, "sample": sample,
                          "batch_wall": round(batch_wall, 3),
                          "per_sequence": round(batch_wall / repeats, 3)}), flush=True)


if __name__ == "__main__":
    main()
