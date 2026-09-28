"""Retention gate for bin-cover bundles; never reinterpret them as fixed-B proofs."""
from __future__ import annotations

import argparse
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools.frontier_hybrid_external import (
    EXTERNAL, check_cover, checked_binary, digest, source_identity,
)
from sqpack.fractional.hybrid_bins import parse_bundle


def fingerprint() -> str:
    from devtools.frontier_runtime import code_fingerprint
    return code_fingerprint(Path(__file__).resolve().parents[1])


def checked_receipt(path: Path, source: Path, side: Fraction) -> dict[str, Any] | None:
    from devtools.frontier_io import read_json
    if not path.is_file():
        return None
    report = read_json(path)
    if (report.get("schema") != "hybrid-bin-retention/v1" or not report.get("finished")
            or report.get("source_sha256") != digest(source)
            or report.get("verifier_sha256") != fingerprint()
            or report.get("side") != str(side)):
        return None
    if report.get("status") == "VERIFIED":
        external = report["external"]
        if (external["checker_sources"] != source_identity(EXTERNAL)
                or external["binary_sha256"] != digest(checked_binary(EXTERNAL))):
            return None
        verified = Path(report["verified_candidate"])
        if not verified.is_file() or digest(verified) != report["verified_sha256"]:
            raise ValueError("verified bin artifact changed after acceptance")
    return report


def decide(source: Path, directory: Path, side: Fraction,
           *, workers: int, seconds: float) -> dict[str, Any]:
    from devtools.frontier_io import atomic_json
    directory.mkdir(parents=True, exist_ok=True)
    cached = checked_receipt(directory / "verification.json", source, side)
    if cached is not None:
        return cached
    raw = source.read_bytes()
    record, measure = parse_bundle(raw)
    if measure.side != side:
        raise ValueError("scheduled side differs from the bin bundle")
    sha, code_sha = digest(source), fingerprint()
    plain = directory / "closed-cover.input.txt"
    plain.write_text(record["certificate_txt"], encoding="utf-8")
    external = check_cover(plain, EXTERNAL, directory / "external", side,
                           net=record["net"], workers=workers, seconds=seconds)
    report: dict[str, Any] = {
        "schema": "hybrid-bin-retention/v1", "status": external["status"],
        "side": str(side), "mass": str(measure.mass), "source_sha256": sha,
        "verifier_sha256": code_sha, "external": external, "finished": True,
    }
    if digest(source) != sha or source.read_bytes() != raw or fingerprint() != code_sha:
        raise ValueError("bin candidate or gate source changed during checking")
    if external["status"] == "VERIFIED":
        verified = directory / "bin-cover.verified.json"
        verified.write_bytes(raw)
        report.update(verified_candidate=str(verified), verified_sha256=digest(verified),
                      claim=f"s(12) >= {side}")
    atomic_json(directory / "verification.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--side", type=Fraction, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=7200)
    args = parser.parse_args(argv)
    report = decide(args.input.resolve(), args.report.resolve().parent, args.side,
                    workers=args.workers, seconds=args.seconds)
    from devtools.frontier_io import atomic_json
    atomic_json(args.report, report)
    print(f"bin gate: {report['status']} side={args.side}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
