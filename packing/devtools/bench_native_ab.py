"""Short reproducible lab controls, not a substitute for hour-long user measurements.

Uses real retained n12 atoms and actual generated square geometry. The small
corpus is explicitly not claimed representative of the current live frontier.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools.native_ab import PACKING
from devtools.native_ab_replay import seal_corpus, signature
from sqpack.fractional import native_ab_metrics as metrics
from sqpack.fractional import native_ab_runtime as runtime


def make_corpus(root: Path) -> dict:
    from cases.n12_fractional_certificate.replay import FIRST_RUNG_PATH, load
    from sqpack.fractional.colgen import Square, _arrangement_lines, _vertices
    from sqpack.fractional.exact_slabs import PreparedDepth
    from sqpack.fractional.generate import placement_cells
    from sqpack.fractional.model import rotation_from_half_tangent
    if root.exists() and any(root.iterdir()):
        raise ValueError("benchmark corpus must be a new empty directory")
    root.mkdir(parents=True, exist_ok=True)
    os.environ["PACK_NATIVE_KERNELS"] = "none"
    os.environ["PACK_NATIVE_CAPTURE"] = str(root)
    try:
        certificate = load(FIRST_RUNG_PATH)
        points = np.array([[float(a.x), float(a.y)] for a in certificate.atoms])
        weights = np.array([float(a.weight) for a in certificate.atoms])
        for tangent in (Fraction(0), Fraction(1, 8), Fraction(1, 5), Fraction(1, 3)):
            direction = rotation_from_half_tangent(str(tangent), tangent)
            placement_cells(points, weights, direction, float(certificate.outer_side),
                            float(certificate.square_side), keep=3)
        weighted = tuple((Square(Fraction(1), Fraction(0), Fraction(0), Fraction(1),
                                 Fraction(i, 20), Fraction(j, 20), Fraction(1, 2)),
                          Fraction(1, 7 + i * 3 + j)) for i in range(5) for j in range(3))
        _vertices(_arrangement_lines(weighted, Fraction(4)), Fraction(4))
        depth = PreparedDepth(weighted)
        for x in (Fraction(1, 4), Fraction(1, 2), Fraction(1, 2) + Fraction(1, 2**200)):
            depth.at(x, Fraction(1, 3))
        depth.reduced_cost(((Fraction(1), Fraction(1)), (Fraction(3), Fraction(3))), Fraction(4))
    finally:
        os.environ.pop("PACK_NATIVE_CAPTURE", None)
    return seal_corpus(root)


def overhead(root: Path, repetitions: int) -> dict:
    from cases.n12_fractional_certificate.replay import FIRST_RUNG_PATH, load
    from sqpack.fractional.generate import placement_cells
    from sqpack.fractional.model import rotation_from_half_tangent
    certificate = load(FIRST_RUNG_PATH)
    points = np.array([[float(a.x), float(a.y)] for a in certificate.atoms])
    weights = np.array([float(a.weight) for a in certificate.atoms])
    direction = rotation_from_half_tangent("overhead", Fraction(1, 5))
    def run():
        return placement_cells(points, weights, direction, float(certificate.outer_side),
                               float(certificate.square_side), keep=3)
    os.environ["PACK_NATIVE_KERNELS"] = "none"
    os.environ.pop("PACK_NATIVE_CAPTURE", None)
    os.environ.pop("PACK_NATIVE_STATS", None)
    expected = signature(run())
    samples = []
    for sample in range(3):
        for measured in ((False, True) if sample % 2 == 0 else (True, False)):
            if measured:
                os.environ["PACK_NATIVE_STATS"] = str(root / f"sample-{sample}")
                os.environ["PACK_NATIVE_SESSION"] = f"overhead-{sample}"
            else:
                os.environ.pop("PACK_NATIVE_STATS", None)
            start = time.perf_counter()
            for _ in range(repetitions):
                value = run()
            elapsed = time.perf_counter() - start
            assert signature(value) == expected
            metrics.flush(force=True)
            samples.append({"sample": sample, "counters": measured, "directions": repetitions,
                            "seconds": elapsed, "directions_per_second": repetitions / elapsed})
    os.environ.pop("PACK_NATIVE_STATS", None)
    return {"scope": "small retained-atom single-process instrumentation control", "samples": samples}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=12)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--profiles", default="none,compact,scatter,vertices,exact-depth,prefix,topk")
    parser.add_argument("--overhead-repetitions", type=int, default=100)
    args = parser.parse_args(argv)
    if args.seconds <= 0 or args.overhead_repetitions < 1:
        parser.error("positive time and repetition budgets required")
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    corpus = make_corpus(root / "corpus")
    profiles = args.profiles.split(",")
    for name in profiles:
        runtime.parse_selection(name)
    reports = []
    for profile in profiles:
        directory = root / profile
        with (root / f"{profile}.log").open("w", encoding="utf-8") as log:
            process = subprocess.run([sys.executable, "-m", "devtools.native_ab", "replay",
                "--corpus", str(root / "corpus"), "--output", str(directory), "--native", profile,
                "--workers", str(args.workers), "--minutes", str(args.seconds / 60), "--label", profile],
                cwd=PACKING, stdout=log, stderr=subprocess.STDOUT, timeout=args.seconds + 120)
        if process.returncode:
            raise RuntimeError(f"profile {profile} failed; see {root / (profile + '.log')}")
        report_path = next(directory.glob("*/performance.json"))
        report = json.loads(report_path.read_text())
        summary = {"profile": profile, "report": str(report_path),
                   "completed_replays": report["session"]["completed_replays"],
                   "wall_seconds": report["wall_seconds"],
                   "coordinator_cpu_seconds": report["session"]["coordinator_cpu_seconds"],
                   "peak_in_flight": report["session"]["peak_in_flight"],
                   "matched_checks": report["session"]["matched_output_checks"]}
        reports.append(summary)
        print(json.dumps(summary), flush=True)
    result = {"scope": "short small-corpus service/correctness control including startup; not a live speedup claim",
              "corpus_id": corpus["id"], "workers": args.workers, "profiles": reports,
              "overhead": overhead(root / "overhead", args.overhead_repetitions)}
    runtime.atomic_json(root / "results.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
