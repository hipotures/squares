"""Re-rationalise one preserved LP solution without invoking any LP solver."""
from __future__ import annotations

import argparse
import time
from fractions import Fraction
from pathlib import Path

from devtools.frontier_io import atomic_json, atomic_text, digest, read_json
from devtools.frontier_snapshot import rationalise
from devtools.run_fractional_colgen import certificate_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--source-result", type=Path, required=True)
    parser.add_argument("--scale", type=int, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args(argv)
    began = time.monotonic()
    sources = {args.source_result.resolve(), args.snapshot.resolve()}
    if args.freeze.resolve() in sources or args.json.resolve() in sources or args.freeze.resolve() == args.json.resolve():
        raise ValueError("refinement outputs must not overwrite inputs or each other")
    result_sha = digest(args.source_result)
    snapshot_sha = digest(args.snapshot)
    result = read_json(args.source_result)
    if result.get("raw_weights_sha256") != snapshot_sha:
        raise ValueError("raw LP snapshot does not match the source result digest")
    if result.get("converged") is not True:
        raise ValueError("only a converged raw LP solution may be re-rationalised")
    candidate = rationalise(args.snapshot, args.scale)
    settings = result["settings"]
    if settings["n"] != candidate.n or Fraction(settings["outer_side"]) != candidate.outer_side:
        raise ValueError("raw LP snapshot and source result describe different problems")
    if Fraction(settings["square_side"]) != candidate.square_side:
        raise ValueError("raw LP snapshot and source result use different shrink")
    if int(settings["direction_steps"]) != len(candidate.half_tangents) - 1:
        raise ValueError("raw LP snapshot and source result use different direction net")
    if Fraction(settings["angle_limit"]) != candidate.half_tangents[-1]:
        raise ValueError("raw LP snapshot and source result use different angle limit")
    if digest(args.source_result) != result_sha or digest(args.snapshot) != snapshot_sha:
        raise ValueError("raw refinement inputs changed while reading")
    atomic_text(args.freeze, certificate_json(candidate, None))
    result.update({
        "settings": {**settings, "scale": args.scale},
        "total_mass": str(candidate.total_mass), "total_mass_float": float(candidate.total_mass),
        "atoms": len(candidate.atoms), "frozen": str(args.freeze), "least_cell_mass": None,
        "raw_weights": str(args.snapshot), "raw_weights_sha256": snapshot_sha,
        "work_kind": "rerationalisation", "column_rounds_executed": 0,
        "lp_rounds_executed": 0, "source_result": str(args.source_result),
        "seconds": time.monotonic() - began,
    })
    atomic_json(args.json, result)
    print(f"rerationalised scale={args.scale} mass={candidate.total_mass}; LP solves=0", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
