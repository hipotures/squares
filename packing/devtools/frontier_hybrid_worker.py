"""One bounded hybrid generation job, invoked through frontier_runtime."""
from __future__ import annotations

import argparse
import json
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

from sqpack.fractional.hybrid_support import load_measure, mapped_points


def generate(manifest: dict[str, Any], directory: Path) -> dict[str, Any]:
    from devtools.frontier_io import atomic_json, digest
    from devtools.frontier_phase import PhaseJournal
    from devtools.frontier_snapshot import save as save_snapshot
    from devtools.run_fractional_colgen import certificate_json
    from sqpack.fractional import native_ab_runtime
    from sqpack.fractional.colgen import generate_adaptive

    native_ab_runtime.preflight()
    sources = []
    for source in manifest["sources"]:
        path = Path(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("source measure changed after the job was scheduled")
        sources.append(load_measure(path))
    side = Fraction(manifest["side"])
    config = manifest["config"]
    seeds = mapped_points(sources, side, config["seed_map"])
    phases = PhaseJournal(directory / "phase.log")
    started = time.perf_counter()
    deadline = started + config["stage_seconds"] * 0.95

    def capture(sites: Any, weights: Any) -> None:
        save_snapshot(directory / "raw-lp.json", sites, weights, n=12,
                      square_side=Fraction(config["shrink"]),
                      angle_limit=Fraction(config["angle_limit"]),
                      direction_steps=config["direction_steps"])
        atomic_json(directory / "search-support.json", {
            "schema": "hybrid-support/v1", "status": "SEED_ONLY", "outer_side": str(side),
            "atoms": [[str(x), str(y), "0"] for x, y in sites.positions()],
        })

    options: dict[str, Any] = dict(
        grid_counts=tuple(config["grid_counts"]), inset=Fraction(1, 2),
        angle_limit=Fraction(config["angle_limit"]), direction_steps=config["direction_steps"],
        scale=config["scale"], max_rounds=config["row_rounds"],
        column_rounds=config["column_rounds"], columns_per_round=config["columns_per_round"],
        rows_per_direction=config["rows_per_direction"], support_cap=config["support_cap"],
        seed_points=seeds, deadline=deadline, capture_solution=capture,
        log_path=directory / "column.log", phase_callback=phases, decide=False,
    )
    if config["mode"] == "control":
        candidate, log = generate_adaptive(12, side, Fraction(config["shrink"]), **options)
        details = {"objective": log.objective, "converged": log.stopped.startswith("converged"),
                   "stopped": log.stopped, "rounds": len(log.rounds)}
    else:
        from sqpack.fractional.hybrid_engine import generate_hybrid
        candidate, details = generate_hybrid(side, config, seeds, directory, deadline, phases, capture)
    if candidate is not None:
        (directory / "candidate.json").write_text(certificate_json(candidate, None), encoding="utf-8")
    result = {
        "schema": "hybrid-generation/v1", "status": "CANDIDATE" if candidate is not None else "UNRESOLVED",
        "side": str(side), "mass": str(candidate.total_mass) if candidate is not None else None,
        "candidate_sha256": digest(directory / "candidate.json") if candidate is not None else None,
        "seconds": time.perf_counter() - started, "phase_timings": phases.summary(),
        "seed_points": len(seeds), **details,
    }
    import math
    for key, value in tuple(result.items()):
        if isinstance(value, float) and not math.isfinite(value):
            result[key] = None
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    args = parser.parse_args(argv)
    directory = args.json.resolve().parent
    if args.freeze.resolve() != directory / "candidate.json":
        raise ValueError("candidate path must belong to this job directory")
    directory.mkdir(parents=True, exist_ok=True)
    result = generate(json.loads(args.manifest.read_text()), directory)
    from devtools.frontier_io import atomic_json
    atomic_json(args.json, result)
    print(json.dumps(result, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
