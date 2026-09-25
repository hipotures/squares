"""Structured, restartable access to the existing two-route retention gate.

This module does not change a theorem condition or implement a new verifier.
Rejected search candidates never receive a verified filename. A positive receipt
is bound to both the candidate bytes and the verifier source fingerprint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools import decide_certificate as gate
from devtools.frontier_io import atomic_json, digest, read_json
from sqpack.fractional.certificate import closed_form_conditions, verify


def verifier_fingerprint() -> str:
    package = Path(__file__).resolve().parents[1] / "src/sqpack/fractional"
    paths = sorted(package.glob("*.py")) + [Path(gate.__file__), Path(__file__)]
    result = hashlib.sha256()
    for path in paths:
        result.update(path.name.encode())
        result.update(path.read_bytes())
    return result.hexdigest()


def checked_receipt(path: Path, source: Path, expected_side: Fraction) -> dict[str, Any] | None:
    if not path.exists():
        return None
    report = read_json(path)
    if (report.get("source_sha256") != digest(source)
            or report.get("verifier_sha256") != verifier_fingerprint()
            or Fraction(report.get("side", "0")) != expected_side):
        return None
    if report.get("status") == "VERIFIED":
        verified = Path(report["verified_candidate"])
        if not verified.is_file() or digest(verified) != report.get("verified_sha256"):
            raise ValueError("verified artifact no longer matches its full-gate receipt")
    return report if report.get("finished") else None


def decide(source: Path, directory: Path, expected_side: Fraction) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory / "verification.json"
    cached = checked_receipt(receipt, source, expected_side)
    if cached is not None:
        return cached
    raw = source.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    tool_sha = verifier_fingerprint()
    report: dict[str, Any] = {
        "schema": 1, "source": str(source), "source_sha256": source_sha,
        "side": str(expected_side), "verifier_sha256": tool_sha,
        "status": "RUNNING", "category": None, "finished": False,
    }
    checkpoint = directory / "verification-progress.json"
    progress = read_json(checkpoint) if checkpoint.exists() else {}
    if progress.get("source_sha256") != source_sha or progress.get("verifier_sha256") != tool_sha:
        progress = {"source_sha256": source_sha, "verifier_sha256": tool_sha}
    try:
        record = read_json(source, 8 * 1024 * 1024)
        if record.get("least_cell_mass") is None:
            record.pop("least_cell_mass", None)
        certificate, record = gate.load_frozen_bytes(json.dumps(record).encode())
        if certificate.n != 12 or certificate.outer_side != expected_side:
            raise ValueError("candidate n/side differs from the scheduled problem")
        if record.get("variant", "unconditional") != "unconditional":
            raise ValueError("only unconditional claims can advance this frontier")
        if record.get("claim") != f"s(12) >= {expected_side}":
            raise ValueError("candidate claim does not match the scheduled side")
        if Fraction(record["total_mass"]) != certificate.total_mass:
            raise ValueError("candidate mass declaration differs from atom sum")
        failures = [c.name for c in closed_form_conditions(certificate) if not c.holds]
        if failures:
            report.update(status="REJECTED", category="precondition", failures=failures)
            report["finished"] = True
            atomic_json(receipt, report)
            return report
    except (gate.CertificateFormatError, ValueError, TypeError, KeyError) as error:
        report.update(status="REJECTED", category="invalid_input", detail=str(error), finished=True)
        atomic_json(receipt, report)
        return report

    report["mass"] = str(certificate.total_mass)
    pending = directory / "candidate.pending-verification.json"
    minimum = progress.get("minimum_cell_mass")
    if minimum is None:
        began = time.monotonic()
        verdict = verify(certificate)
        minimum = None if verdict.minimum_cell_mass is None else str(verdict.minimum_cell_mass)
        progress.update(minimum_cell_mass=minimum, sweep_failures=list(verdict.failures),
                        sweep_seconds=time.monotonic() - began)
        atomic_json(checkpoint, progress)
    report.update(minimum_cell_mass=minimum, sweep_failures=progress.get("sweep_failures", []))
    if minimum is None or Fraction(minimum) < 1:
        report.update(status="REJECTED", category="coverage_deficit", finished=True)
        if minimum is not None and Fraction(minimum) > 0:
            report["uniform_repair_possible"] = certificate.total_mass / Fraction(minimum) < 12
        else:
            report["uniform_repair_possible"] = False
        atomic_json(receipt, report)
        return report
    record["least_cell_mass"] = minimum
    if not pending.exists() or progress.get("pending_sha256") != digest(pending):
        atomic_json(pending, record)
        progress["pending_sha256"] = digest(pending)
        atomic_json(checkpoint, progress)
    full_log = directory / "verify-full.log"
    stalls = directory / "interval-stalls.json"
    began = time.monotonic()
    with full_log.open("w", encoding="utf-8") as handle, redirect_stdout(handle):
        accepted = gate.decide(pending, quick=False, dump_stalls=stalls)
    report["gate_seconds"] = time.monotonic() - began
    if accepted:
        accepted_sha = digest(pending)
        text = full_log.read_text()
        printed = re.findall(r"RETAINABLE: both routes accept[^\n]*sha256 ([0-9a-f]{64})", text)
        if (printed != [accepted_sha] or digest(source) != source_sha
                or verifier_fingerprint() != tool_sha):
            raise ValueError("full gate receipt/candidate identity changed during verification")
        verified = directory / "candidate.verified.json"
        pending.replace(verified)
        report.update(status="VERIFIED", category="full-retainable", finished=True,
                      verified_candidate=str(verified), verified_sha256=accepted_sha)
    else:
        stall_count = read_json(stalls).get("stalled", 0) if stalls.exists() else 0
        refusals = [line.split("REFUSED:", 1)[1].strip() for line in full_log.read_text().splitlines()
                    if "REFUSED:" in line]
        report.update(status="REJECTED", category="interval_stall" if stall_count else "gate_refusal",
                      stalled_boxes=stall_count, refusals=refusals, finished=True)
    atomic_json(receipt, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--side", type=Fraction, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = decide(args.input, args.report.parent, args.side)
        if args.report.name != "verification.json":
            atomic_json(args.report, report)
        print(f"verification status={report['status']} category={report['category']}", flush=True)
        return 0  # A mathematical refusal is a completed job, not an OS failure.
    except (OSError, RuntimeError, ValueError) as error:
        print(f"verification infrastructure failure: {error}", file=sys.stderr, flush=True)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
