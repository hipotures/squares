"""One bounded CPU queue across repair boosts; screening is NEVER a proof.

Numerical direction search is unchanged. Prepared immutable arrays are installed
once per worker, tasks carry only integer IDs, and cheap directions are batched.
Partial results are checkpointed. Full exact retention still happens afterwards,
outside this pool, so no per-boost nested pools oversubscribe PACK_JOBS.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

from devtools import decide_certificate as gate
from devtools.frontier_dispatch import dispatch
from devtools.frontier_io import atomic_json, canonical_digest, digest, read_json
from devtools.frontier_runtime import code_fingerprint
from sqpack.fractional import interval
from sqpack.fractional.certificate import Certificate, closed_form_conditions

SCHEMA = 1
MAX_BOOSTS = 6
PURPOSE = "repair-interval-screen-only"


@dataclass(frozen=True)
class Prepared:
    atoms: tuple[interval.AtomData | None, ...]
    rotations: tuple[interval.Rotation, ...]
    outer: interval.Interval
    square: interval.Interval


_PREPARED: Prepared | None = None
_CANCELLED: Any = None


class BatchCancelled(Exception):
    """Cooperative cancellation, deliberately not an interval verdict."""


class InterruptibleSearch(interval.DirectionSearch):
    """Poll between the existing bounded box batches; change no arithmetic."""

    group: int

    def tighten(self, boxes):
        if _CANCELLED[self.group]:
            raise BatchCancelled()
        return super().tighten(boxes)


def initialise(prepared: Prepared, cancelled: Any) -> None:
    global _PREPARED, _CANCELLED
    _PREPARED, _CANCELLED = prepared, cancelled
    for atoms in prepared.atoms:
        if atoms is not None:
            for array in (atoms.xlo, atoms.xhi, atoms.ylo, atoms.yhi, atoms.mass):
                array.flags.writeable = False


def evaluate_batch(task: tuple[int, tuple[int, ...]]) -> dict[str, Any]:
    group, indices = task
    prepared = _PREPARED
    if prepared is None or prepared.atoms[group] is None:
        raise RuntimeError("missing prepared boost data")
    atoms = prepared.atoms[group]
    began, cpu_began = time.monotonic(), time.process_time()
    records = []
    cancelled = False
    for index in indices:
        if _CANCELLED[group]:
            cancelled = True
            break
        start = time.monotonic()
        try:
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                search = InterruptibleSearch(atoms, prepared.rotations[index],
                                             prepared.outer, prepared.square)
                search.group = group
                # Match decide_certificate's quick interval mode, including its
                # minimum-enclosing search. No weaker sampled net is accepted.
                outcome = search.search(prune_at=None)
        except BatchCancelled:
            cancelled = True
            break
        records.append({"index": index, "seconds": time.monotonic() - start,
                        "outcome": asdict(outcome)})
    return {"group": group, "records": records, "cancelled": cancelled,
            "wall_seconds": time.monotonic() - began,
            "cpu_seconds": time.process_time() - cpu_began, "worker_pid": os.getpid()}


def _load_family(manifest: Path) -> tuple[dict[str, Any], list[Certificate], Prepared, list[str | None]]:
    request = read_json(manifest)
    entries = request.get("candidates", [])
    if (request.get("schema") != SCHEMA or request.get("purpose") != PURPOSE
            or not 1 <= len(entries) <= MAX_BOOSTS):
        raise ValueError("invalid repair queue manifest")
    side = Fraction(request["side"])
    if not 0 < side < 4:
        raise ValueError("repair side outside the n=12 campaign")
    certificates = []
    for entry in entries:
        source = Path(entry["path"])
        raw = gate.read_bounded(source)
        if not isinstance(entry.get("label"), str) or len(entry["label"]) > 512:
            raise ValueError("invalid boost label")
        if digest(source) != entry["sha256"]:
            raise ValueError("repair source changed after scheduling")
        record = json.loads(raw, object_pairs_hook=gate._object_without_duplicate_keys,
                            parse_float=gate._reject_inexact_json_number,
                            parse_constant=gate._reject_inexact_json_number)
        if not isinstance(record, dict):
            raise ValueError("candidate must be a JSON object")
        if record.get("least_cell_mass") is None:
            record.pop("least_cell_mass", None)
        certificate, record = gate.load_frozen_bytes(json.dumps(record).encode())
        if (certificate.n != 12 or certificate.outer_side != side
                or not 0 < certificate.total_mass < 12
                or record.get("variant", "unconditional") != "unconditional"
                or record.get("claim") != f"s(12) >= {side}"
                or certificate.total_mass != Fraction(record["total_mass"])
                or any(not condition.holds for condition in closed_form_conditions(certificate))):
            raise ValueError("inadmissible repair candidate")
        # Reread bytes, not only the pathname's first digest (no mutable input).
        if raw != gate.read_bounded(source):
            raise ValueError("repair source changed while reading")
        certificates.append(certificate)
    base = certificates[0]
    geometry = tuple((atom.x, atom.y) for atom in base.atoms)
    for certificate in certificates[1:]:
        if (certificate.square_side != base.square_side
                or certificate.half_tangents != base.half_tangents
                or tuple((atom.x, atom.y) for atom in certificate.atoms) != geometry):
            raise ValueError("repair boosts must share exactly the same geometry and net")
        factor = certificate.total_mass / base.total_mass
        if any(a.weight != b.weight * factor for a, b in zip(certificate.atoms, base.atoms, strict=True)):
            raise ValueError("repair family is not a uniform weight scaling")
    if any(a.total_mass >= b.total_mass for a, b in zip(certificates, certificates[1:])):
        raise ValueError("repair boosts must be strictly ordered by exact mass")
    rotations = interval.doubled_net(base.half_tangents)
    prepared_atoms: list[interval.AtomData | None] = []
    errors: list[str | None] = []
    coordinates = None
    for certificate in certificates:
        try:
            if coordinates is None:
                atoms = interval.AtomData.of(certificate)
                coordinates = atoms.xlo, atoms.xhi, atoms.ylo, atoms.yhi
            else:
                scale, masses, total = interval.scaled_atom_masses(certificate)
                atoms = interval.AtomData(*coordinates, np.array(masses, dtype=np.int64), scale, total)
            conditions = (interval._condition_mass_below_n(certificate, atoms),
                          interval._condition_net_reaches_eighth_turn(certificate),
                          interval._condition_containment(certificate))
            errors.append(None if all(c.status == "holds" for c in conditions)
                          else "interval precondition not established")
            prepared_atoms.append(atoms)
        except interval.IntervalInputError as error:
            errors.append(str(error))
            prepared_atoms.append(None)
    return request, certificates, Prepared(tuple(prepared_atoms), rotations,
                                          interval.Interval.of(side),
                                          interval.Interval.of(base.square_side)), errors


def _check_sources(request: dict[str, Any]) -> None:
    if any(digest(Path(entry["path"])) != entry["sha256"] for entry in request["candidates"]):
        raise ValueError("repair candidate bytes changed during screening")


def screen(manifest: Path, report_path: Path, *, workers: int | None = None) -> dict[str, Any]:
    """Run/recover a bounded family screen. Its report is never a proof receipt."""
    began = time.monotonic()
    request, certificates, prepared, errors = _load_family(manifest)
    protected = {manifest.resolve(), *(Path(e["path"]).resolve() for e in request["candidates"])}
    outputs = {report_path.resolve(), (report_path.parent / "queue-checkpoint.json").resolve()}
    if protected & outputs or len(outputs) != 2:
        raise ValueError("queue outputs must not overwrite inputs or each other")
    manifest_sha = digest(manifest)
    source_sha = code_fingerprint(Path(__file__).resolve().parents[1])
    fingerprint = canonical_digest({"manifest": manifest_sha, "source": source_sha, "schema": SCHEMA})
    checkpoint_path = report_path.parent / "queue-checkpoint.json"
    target = float(request.get("target_seconds", 0.5))
    max_batch = request.get("max_batch", 8)
    if (not math.isfinite(target) or not 0.01 <= target <= 5
            or type(max_batch) is not int or not 1 <= max_batch <= 16):
        raise ValueError("invalid repair batching policy")
    saved = read_json(checkpoint_path) if checkpoint_path.exists() else None
    if saved is not None:
        checksum = saved.pop("checksum", None)
        if saved.get("fingerprint") != fingerprint or canonical_digest(saved) != checksum:
            raise ValueError("queue checkpoint identity/integrity mismatch")
    count = interval.interval_worker_count(len(prepared.rotations), workers)
    # Do not fork a process that may already own NumPy/native helper threads.
    # Inputs are prepared once and sent once per spawned worker, not per task.
    context = mp.get_context("spawn") if interval._main_is_importable() else interval._interval_pool_context()
    if context is None:
        count = 1
        cancelled = [0] * len(certificates)
    else:
        cancelled = context.RawArray("b", len(certificates))
    results = [{"state": "PENDING", "reason": None, "records": {},
                "label": entry["label"], "source": entry["path"],
                "source_sha256": entry["sha256"], "mass": str(certificate.total_mass)}
               for entry, certificate in zip(request["candidates"], certificates, strict=True)]

    def reject(group: int, reason: str, evidence: dict[str, Any]) -> None:
        if results[group]["state"] != "PENDING":
            return
        results[group].update(state="QUICK_REJECTED", reason=reason, evidence=evidence)
        cancelled[group] = 1
        print(f"[queue] boost={results[group]['label']} QUICK_REJECTED reason={reason}", flush=True)

    def consume(group: int, record: dict[str, Any]) -> None:
        index = record["index"]
        if type(index) is not int or not 0 <= index < len(prepared.rotations):
            raise ValueError("invalid completed direction index")
        out = record["outcome"]
        outcome = interval.DirectionOutcome(**out)
        if (outcome.label != prepared.rotations[index].label
                or outcome.status not in ("certified", "refuted", "undecided")
                or not math.isfinite(record["seconds"]) or record["seconds"] < 0):
            raise ValueError("invalid completed direction")
        key = str(index)
        if key in results[group]["records"]:
            raise ValueError("duplicate completed direction")
        results[group]["records"][key] = record
        atoms = prepared.atoms[group]
        if atoms is None:
            raise ValueError("unexpected result for refused input")
        if (outcome.status != "certified" or outcome.lower is None or outcome.lower < atoms.scale
                or outcome.stalled or outcome.budget_exhausted):
            reason = "interval-undecided" if outcome.status == "undecided" else "coverage-refuted"
            reject(group, reason, {"direction": index, "outcome": out})
            # A real upper bound below one at an admissible witness transfers to
            # lighter UNIFORMLY scaled weights. A stall is not such a refutation.
            if (outcome.status in ("refuted", "certified") and outcome.upper is not None
                    and outcome.upper < atoms.scale and outcome.witness is not None):
                for lower in range(group):
                    reject(lower, "monotone-coverage-refutation", {
                        "source_group": group, "source_sha256": results[group]["source_sha256"],
                        "direction": index, "outcome": out,
                    })
        elif len(results[group]["records"]) == len(prepared.rotations):
            results[group].update(state="QUICK_ACCEPTED", reason="complete interval screen; full gate still required")
            cancelled[group] = 1
            print(f"[queue] boost={results[group]['label']} QUICK_ACCEPTED (not a proof)", flush=True)

    for group, error in enumerate(errors):
        if error is not None:
            reject(group, "input-not-enclosable", {"detail": error})
    reused = 0
    if saved is not None:
        if len(saved.get("results", [])) != len(results):
            raise ValueError("queue checkpoint group count mismatch")
        # Rebuild decisions from actual saved direction evidence, not status text.
        for group, prior in enumerate(saved["results"]):
            if prior.get("source_sha256") != results[group]["source_sha256"]:
                raise ValueError("queue checkpoint candidate mismatch")
            for key in sorted(prior.get("records", {}), key=int):
                if results[group]["state"] == "PENDING":
                    consume(group, prior["records"][key])
                    reused += 1
    setup_seconds = time.monotonic() - began
    groups = [[index for index in range(len(prepared.rotations))
               if str(index) not in item["records"]] for item in results]
    print(f"[queue] workers={count} boosts={len(results)} directions={len(prepared.rotations)} "
          f"reused={reused} max-in-flight={count} batch=adaptive(1..{max_batch})", flush=True)
    last_print = time.monotonic()

    def checkpoint(stats: dict[str, Any], force: bool) -> None:
        nonlocal last_print
        state = {"schema": SCHEMA, "purpose": PURPOSE, "fingerprint": fingerprint,
                 "manifest_sha256": manifest_sha, "code_sha256": source_sha,
                 "results": results, "metrics": stats, "reused_directions": reused,
                 "updated_at": time.time()}
        atomic_json(checkpoint_path, {**state, "checksum": canonical_digest(state)})
        now = time.monotonic()
        if force or now - last_print >= 60:
            print(f"[queue] completed={stats['completed_items']} reused={reused} "
                  f"in-flight={stats['in_flight']}/{count} batches={stats['submitted_batches']} "
                  f"coordinator-cpu={stats['coordinator_cpu_seconds']:.3f}s", flush=True)
            last_print = now

    if count == 1:
        # The singleton thread only runs one task at a time and starts no nested
        # process pool. It exercises the same completion/checkpoint protocol.
        initialise(prepared, cancelled)
        pool = ThreadPoolExecutor(max_workers=1)
    else:
        pool = ProcessPoolExecutor(max_workers=count, mp_context=context,
                                   initializer=initialise, initargs=(prepared, cancelled))
    try:
        stats = dispatch(pool, evaluate_batch, groups, slots=count,
                         active=lambda group: results[group]["state"] == "PENDING",
                         accept=consume, checkpoint=checkpoint,
                         target_seconds=target, max_batch=max_batch)
    finally:
        for group in range(len(cancelled)):
            cancelled[group] = 1
        pool.shutdown(wait=True, cancel_futures=True)
    _check_sources(request)
    if digest(manifest) != manifest_sha or code_fingerprint(Path(__file__).resolve().parents[1]) != source_sha:
        raise ValueError("queue inputs/executable source changed")
    if any(item["state"] == "PENDING" for item in results):
        raise RuntimeError("incomplete queue screen")
    # Direction records are retained in the checkpoint. The compact final report
    # points to that evidence instead of repeatedly copying it into runner state.
    report = {"schema": SCHEMA, "purpose": PURPOSE, "finished": True,
              "manifest_sha256": manifest_sha, "code_sha256": source_sha,
              "checkpoint_sha256": digest(checkpoint_path),
              "results": [{k: v for k, v in item.items() if k != "records"} for item in results],
              "metrics": {**stats, "setup_seconds": setup_seconds,
                          "total_seconds": time.monotonic() - began},
              "reused_directions": reused}
    atomic_json(report_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if args.report.resolve() == args.input.resolve():
        parser.error("report must not overwrite its input")
    try:
        with (args.report.parent / "queue.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            screen(args.input, args.report)
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"repair queue failed without a proof: {error}", file=sys.stderr, flush=True)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
