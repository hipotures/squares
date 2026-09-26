"""Integrate shared boost screening with the existing durable frontier controller.

A queue screen can reject a proposal or nominate it for full verification. It
cannot produce VERIFIED, install certificates, or bypass the two-route gate.
"""
from __future__ import annotations

import hashlib
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools.frontier_boost_queue import PURPOSE, SCHEMA
from devtools.frontier_io import atomic_json, canonical_digest, digest, read_json
from devtools.frontier_runtime import code_fingerprint


def run_boosts(root: Path, state: dict[str, Any], attempt: dict[str, Any],
               slack_fractions: list[Fraction], api: Any) -> bool:
    """Finish one bounded repair family, preserving individual boost history."""
    directory = Path(attempt["directory"])
    source = Path(attempt["candidate"])
    side = Fraction(attempt["side"])
    entries = []
    for fraction in slack_fractions:
        entry = next((item for item in attempt["repairs"]
                      if item.get("slack_fraction") == str(fraction)), None)
        if entry is not None and entry.get("status") in ("REJECTED", "VERIFIED", "ERROR"):
            continue
        label = f"{fraction.numerator}-{fraction.denominator}"
        boost_dir = directory / f"boost-{hashlib.sha256(label.encode()).hexdigest()[:16]}"
        boost_dir.mkdir(exist_ok=True)
        boosted = boost_dir / "candidate.unverified.json"
        if entry is None:
            mass = api.write_boosted_candidate(source, boosted, fraction)
            entry = {"slack_fraction": str(fraction), "total_mass": str(mass),
                     "directory": str(boost_dir), "status": "RUNNING"}
            attempt["repairs"].append(entry)
        elif not boosted.exists():
            api.write_boosted_candidate(source, boosted, fraction)
        identity = digest(boosted)
        if entry.get("candidate_sha256", identity) != identity:
            raise ValueError("boost input changed during repair")
        entry["candidate_sha256"] = identity
        entries.append(entry)
    if not entries:
        attempt.update(status="REJECTED", reason="configured uniform repairs exhausted", finished_at=api.stamp())
        state["mode"] = "FRONTIER"
        api.save_state(root, state)
        api.write_views(root, state)
        return True
    source_sha = code_fingerprint(api.REPO / "packing")
    prior = attempt.get("shared_queue")
    # A crash between screening and promotion reuses the original whole-family
    # report, even when some entries have already been applied to runner state.
    if prior is not None and prior.get("code_sha256") == source_sha:
        manifest = Path(prior["manifest"])
        if digest(manifest) != prior["manifest_sha256"]:
            raise ValueError("saved queue manifest changed")
        request = read_json(manifest)
    else:
        request = {"schema": SCHEMA, "purpose": PURPOSE, "side": str(side),
                   "target_seconds": 0.5, "max_batch": 8,
                   "candidates": [{"label": entry["slack_fraction"],
                                   "path": str(Path(entry["directory"]) / "candidate.unverified.json"),
                                   "sha256": entry["candidate_sha256"]} for entry in entries]}
        key = canonical_digest({"request": request, "source": source_sha})[:24]
        queue_dir = directory / f"shared-queue-{key}"
        queue_dir.mkdir(exist_ok=True)
        manifest = queue_dir / "manifest.json"
        if manifest.exists() and read_json(manifest) != request:
            raise ValueError("existing queue manifest differs from the scheduled family")
        if not manifest.exists():
            atomic_json(manifest, request)
        prior = {"manifest": str(manifest), "manifest_sha256": digest(manifest),
                 "code_sha256": source_sha}
        attempt["shared_queue"] = prior
    api.save_state(root, state)
    queue_dir = manifest.parent
    report_path = queue_dir / "report.json"
    api.emit(root, f"[repair-queue] boosts={len(request['candidates'])} "
             f"cpu-budget={state['config']['workers']} batch=adaptive(1..8); shared pool")
    code = api.run_child([sys.executable, "-m", "devtools.frontier_boost_queue",
                          "--input", str(manifest), "--report", str(report_path)],
                         queue_dir / "stdout.log")
    if code or not report_path.is_file():
        api.repair_job_failure(state, attempt, f"verification-error-{code or 70}")
        api.save_state(root, state)
        return True
    report = read_json(report_path)
    if (report.get("purpose") != PURPOSE or report.get("finished") is not True
            or report.get("manifest_sha256") != digest(manifest)
            or report.get("code_sha256") != source_sha
            or len(report.get("results", [])) != len(request["candidates"])
            or report.get("checkpoint_sha256") != digest(queue_dir / "queue-checkpoint.json")):
        raise ValueError("shared queue report identity mismatch")
    metrics = report["metrics"]
    attempt["queue_metrics"] = metrics
    api.emit(root, f"[repair-queue] done workers={metrics['slots']} "
             f"directions={metrics['completed_items']} reused={report['reused_directions']} "
             f"batches={metrics['submitted_batches']} wall={metrics['total_seconds']:.2f}s "
             f"coordinator-cpu={metrics['coordinator_cpu_seconds']:.3f}s")
    for item, spec in zip(report["results"], request["candidates"], strict=True):
        if (item.get("source_sha256") != spec["sha256"] or item.get("source") != spec["path"]
                or item.get("label") != spec["label"] or digest(Path(spec["path"])) != spec["sha256"]):
            raise ValueError("shared queue result does not bind its source")
        entry = next((entry for entry in attempt["repairs"]
                      if entry["slack_fraction"] == spec["label"]), None)
        if entry is None:
            raise ValueError("queue result has no scheduled boost")
        if entry.get("status") in ("VERIFIED", "REJECTED", "ERROR"):
            continue
        entry["screen"] = item
        if item["state"] == "QUICK_REJECTED":
            status, verified = "quick-rejected", None
        elif item["state"] == "QUICK_ACCEPTED":
            api.emit(root, f"[repair] boost={entry['slack_fraction']} screen passed; full exact gate required")
            # The queue is closed/drained before this call. This gate may use
            # the whole CPU budget without overlapping a second process pool.
            status, verified = api.verify_candidate(Path(entry["directory"]), Path(spec["path"]), side)
        else:
            raise ValueError("unfinished/unknown queue state cannot decide a boost")
        entry.update(status="VERIFIED" if verified else (
            "ERROR" if status.startswith("verification-error") else "REJECTED"),
            verifier=status, verified_candidate=verified)
        api.save_state(root, state)
        api.poll_stop()
        api.emit(root, f"[repair] boost={entry['slack_fraction']} mass={entry['total_mass']} -> {status}")
        if verified is not None:
            api.promote_verified(state, side, Path(verified), "shared-queue-uniform-weight-repair")
            attempt.update(status="VERIFIED", verified_candidate=verified, finished_at=api.stamp())
            api.save_state(root, state)
            api.write_views(root, state)
            api.publish_findings(root, state)
            return True
        if entry["status"] == "ERROR":
            api.repair_job_failure(state, attempt, status)
            api.save_state(root, state)
            return True
    attempt.update(status="REJECTED", reason="configured uniform repairs exhausted", finished_at=api.stamp())
    state["mode"] = "FRONTIER"
    state["consecutive_job_errors"] = 0
    api.save_state(root, state)
    api.write_views(root, state)
    return True
