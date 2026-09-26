"""Paired full-generator control for prepared exact pricing/ceiling predicates.

Both variants run the real generator with identical inputs in fresh processes.
The reference variant substitutes only the previous Fraction depth expressions;
no search, LP, float ranking or retention rule is changed. Timings include startup.
All samples, frozen (unverified) candidates and phase logs stay below --root.
This benchmark never promotes a candidate or claims a new packing bound.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import signal
import statistics
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

from devtools.frontier_io import atomic_json, read_json
from devtools.run_fractional_colgen import main as generate
from sqpack.fractional import colgen


class FractionDepth:
    """The pre-optimization exact expressions, benchmark-only control."""

    def __init__(self, weighted):
        self.weighted = tuple(weighted)

    def at(self, x, y):
        return sum((w for square, w in self.weighted if square.covers(x, y)), start=Fraction(0))

    def reduced_cost(self, orbit, outer_side):
        return colgen.reduced_cost(orbit, self.weighted, outer_side)


def signature(directory: Path) -> dict:
    result = read_json(directory / "result.json")
    candidate = directory / "candidate.unverified.json"
    return {
        key: result.get(key)
        for key in (
            "objective",
            "least_covered",
            "converged",
            "stopped",
            "total_mass",
            "atoms",
            "ceiling_proved",
            "ceiling_detail",
            "least_cell_mass",
        )
    } | {
        "rounds": [
            {k: v for k, v in row.items() if k != "seconds"} for row in result["rounds"]
        ],
        "certificate": read_json(candidate) if candidate.exists() else None,
    }


def child(args) -> int:
    if args.child == "reference":
        colgen.PreparedDepth = FractionDepth
    command = [
        "--n",
        "12",
        "--side",
        args.side,
        "--grid-counts",
        args.grid_counts,
        "--direction-steps",
        str(args.steps),
        "--column-rounds",
        str(args.column_rounds),
        "--max-rounds",
        str(args.row_rounds),
        "--support-cap",
        str(args.support_cap),
        "--scale",
        "1600000",
        "--json",
        str(args.root / "result.json"),
        "--freeze",
        str(args.root / "candidate.unverified.json"),
        "--phase-log",
        str(args.root / "phase.log"),
        "--row-log",
        str(args.root / "rows.log"),
        "--log",
        str(args.root / "column.log"),
    ]
    if args.seed_certificate is not None:
        command += ["--seed-certificate", str(args.seed_certificate)]
    return generate(command)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--side", default="198111/50000")
    parser.add_argument("--grid-counts", default="5,7,9")
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--column-rounds", type=int, default=3)
    parser.add_argument("--row-rounds", type=int, default=30)
    parser.add_argument("--support-cap", type=int, default=32)
    parser.add_argument("--seed-certificate", type=Path)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--child", choices=("reference", "prepared"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    args.root = args.root.resolve()
    if args.child:
        return child(args)
    if (
        args.root.exists()
        or min(
            args.samples,
            args.workers,
            args.steps,
            args.column_rounds,
            args.row_rounds,
            args.support_cap,
        )
        < 1
        or not math.isfinite(args.timeout)
        or args.timeout <= 0
    ):
        parser.error("use a new --root and positive counts/timeouts")
    args.root.mkdir(parents=True)
    base = [
        sys.executable,
        "-m",
        "devtools.bench_exact_pricing",
        "--workers",
        str(args.workers),
        "--side",
        args.side,
        "--grid-counts",
        args.grid_counts,
        "--steps",
        str(args.steps),
        "--column-rounds",
        str(args.column_rounds),
        "--row-rounds",
        str(args.row_rounds),
        "--support-cap",
        str(args.support_cap),
    ]
    if args.seed_certificate is not None:
        base += ["--seed-certificate", str(args.seed_certificate.resolve())]
    env = dict(
        os.environ,
        PACK_JOBS=str(args.workers),
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    pairs = []
    for sample in range(args.samples):
        pair = {}
        order = ("reference", "prepared") if sample % 2 == 0 else ("prepared", "reference")
        for mode in order:
            directory = args.root / f"{sample + 1:02d}-{mode}"
            directory.mkdir()
            began = time.monotonic()
            with (directory / "stdout.log").open("w", encoding="utf-8") as output:
                command = [*base, "--child", mode, "--root", str(directory)]
                with subprocess.Popen(
                    command,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                ) as process:
                    try:
                        code = process.wait(timeout=args.timeout)
                    except BaseException:
                        # The benchmark owns this new session, never the user's campaign.
                        if os.name == "posix":
                            os.killpg(process.pid, signal.SIGKILL)
                        else:
                            process.kill()
                        process.wait()
                        raise
                    if code:
                        raise subprocess.CalledProcessError(code, command)
            wall = time.monotonic() - began
            result = read_json(directory / "result.json")
            pair[mode] = {
                "wall_seconds": wall,
                "phase_timings": result["phase_timings"],
                "signature": signature(directory),
            }
        if pair["reference"]["signature"] != pair["prepared"]["signature"]:
            atomic_json(args.root / "mismatch.json", pair)
            raise RuntimeError(
                "generator trajectory, exact ceiling or frozen candidate changed"
            )
        pair["speedup"] = pair["reference"]["wall_seconds"] / pair["prepared"]["wall_seconds"]
        pairs.append(pair)
        atomic_json(args.root / "samples.json", {"pairs": pairs})
        print(
            f"[{int(time.time())}] sample={sample + 1} "
            f"reference={pair['reference']['wall_seconds']:.3f}s "
            f"prepared={pair['prepared']['wall_seconds']:.3f}s "
            f"speedup={pair['speedup']:.3f} identical=True",
            flush=True,
        )
    report = {
        "scope": "paired full generator, includes startup; not a live campaign",
        "settings": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "python": sys.version,
        "platform": platform.platform(),
        "pairs": pairs,
        "median_speedup": statistics.median(p["speedup"] for p in pairs),
        "correctness": "identical rounds, objectives, ceiling and frozen certificate",
    }
    atomic_json(args.root / "results.json", report)
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("pairs", "settings")}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
