"""Replay Mira's candidate s(17) >= 4613/1000 certificate through *this* repository's verifiers.

The retained bytes are
``mira-17squares/certificates/lower_bound_4p613/best-certificate.json``, published by
github.com/Mira-acc/17squares at commit
``0266c9936a303817ac7da0802364034a34fb2558``. They are in this repository's own
certificate schema -- the file descends from
``cases/n17_fractional_certificate/certificate.json`` -- so the object can be handed
straight to ``sqpack`` without a translation layer.
Its ``claim`` field says "candidate only; exact replay required", and the source's
``result.json`` declares the two numbers this script checks against: total mass
``849899249/50000000`` and minimum core mass ``1000002103/1000000000``.

Nothing here decides anything. The verdicts come from
``sqpack.fractional.certificate.verify`` (exact event-cell sweep, rational arithmetic)
and ``sqpack.fractional.interval.verify_by_intervals`` (branch and bound over boxes of
centres in outward-rounded interval arithmetic over the doubled net); this module loads
the bytes, hashes them, feeds them, prints what came back, and refuses on any
disagreement with what the source declared.

Two stages, one certificate::

    uv run --frozen --all-extras --group dev python \\
      resources/web/n17-weighted-certificates-2026-09-20/replay_mira_4613_first_party.py
    uv run --frozen --all-extras --group dev python \\
      resources/web/n17-weighted-certificates-2026-09-20/replay_mira_4613_first_party.py \\
      --interval

Run both from ``packing/``. Measured on a ten-core Apple Silicon host: the exact sweep
over 2,881 net directions costs about ten minutes of wall with the pool sqpack allows
itself, the interval sweep over the 5,761-direction doubled net about half an hour in
one process. ``--directions K`` cuts either stage to K sampled directions for a smoke
test; a smoke run decides nothing about the certificate and never prints the success
line.

On the containment condition. This repository's Condition 4 is the sufficient test
``B (1 + D) < 1``; Mira's proof note uses the sharper ``B^2 (1 + D)^2 < 1 + D^2``, which
is this repository's own T-022/T-024 sharpened containment lemma
(``cases/n11_fractional_certificate/t-022-dilation-limit-proof.md``, implemented as
``devtools.dilation_corollary.sharp_containment_holds``). At this certificate's numbers
both hold, so the stronger hypothesis is not load-bearing here; the script evaluates
both exactly anyway and prints them under their own heading, so a reader never has to
infer which inequality a verdict rested on.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

from sqpack.fractional.certificate import (
    Certificate,
    closed_form_conditions,
    sweep_direction_minimum,
    verify,
)
from sqpack.fractional.interval import doubled_net, verify_by_intervals
from sqpack.fractional.model import Atom

HERE = Path(__file__).resolve().parent
PACKAGE = HERE / "mira-17squares" / "certificates" / "lower_bound_4p613"
CERTIFICATE_PATH = PACKAGE / "best-certificate.json"
RESULT_PATH = PACKAGE / "result.json"
RECEIPTS = HERE / "receipts"

#: The digest the source's own ``result.json`` and ``MANIFEST.sha256.json`` publish.
CERTIFICATE_SHA256 = "749f13335980a66a27a2304f212b5d8796390c81b962149647a4d9ff43a228ec"

SOURCE_REPOSITORY = "github.com/Mira-acc/17squares"
SOURCE_COMMIT = "0266c9936a303817ac7da0802364034a34fb2558"

#: ``packing/`` and the repository root, so printed paths mean one thing (AGENTS.md).
PACKING = HERE.parents[2]
REPO = PACKING.parent


def say(text: str = "") -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def _decimal(value: Fraction, places: int = 15) -> str:
    """A truncated decimal for reading, never for deciding."""

    scaled = value.numerator * 10**places // value.denominator
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled)).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def load(raw: bytes) -> tuple[Certificate, dict[str, Any]]:
    """Rebuild the certificate from one byte snapshot, exactly as the schema declares it."""

    record: dict[str, Any] = json.loads(raw)
    limit = Fraction(record["angle_limit"])
    steps = int(record["direction_steps"])
    certificate = Certificate(
        n=int(record["n"]),
        outer_side=Fraction(record["outer_side"]),
        square_side=Fraction(record["square_side"]),
        atoms=tuple(
            Atom(f"{index:04d}", Fraction(x), Fraction(y), Fraction(weight))
            for index, (x, y, weight) in enumerate(record["atoms"])
        ),
        half_tangents=tuple(limit * k / steps for k in range(steps + 1)),
        symmetry=str(record["symmetry"]),
    )
    return certificate, record


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def sampled_indices(total: int, wanted: int) -> tuple[int, ...]:
    """``wanted`` indices spread over ``range(total)``, both ends included."""

    if wanted >= total:
        return tuple(range(total))
    if wanted <= 1:
        return (0,)
    step = Fraction(total - 1, wanted - 1)
    return tuple(sorted({int(step * k) for k in range(wanted)}))


def containment_analysis(certificate: Certificate) -> dict[str, Any]:
    """Both containment inequalities, evaluated exactly, reported side by side.

    ``coarse`` is this repository's Condition 4, the one ``verify`` decides.
    ``sharp`` is the T-022 sharpened form Mira's proof note uses; it is strictly
    weaker as a hypothesis, so it is reported but never substituted for Condition 4.
    """

    gap = certificate.largest_half_gap_tangent
    side = certificate.square_side
    coarse = side * (1 + gap)
    sharp_left = coarse * coarse
    sharp_right = 1 + gap * gap
    return {
        "largest_half_gap_tangent": str(gap),
        "square_side": str(side),
        "coarse_product": str(coarse),
        "coarse_slack": str(1 - coarse),
        "coarse_holds": coarse < 1,
        "sharp_left": str(sharp_left),
        "sharp_right": str(sharp_right),
        "sharp_slack": str(sharp_right - sharp_left),
        "sharp_holds": sharp_left < sharp_right,
    }


def print_containment(analysis: dict[str, Any]) -> None:
    say("Containment inequalities, evaluated exactly (Fractions, nothing rounded)")
    say(f"  B = {analysis['square_side']}")
    say(f"  D = {analysis['largest_half_gap_tangent']}  (largest half-gap tangent of the net)")
    coarse = Fraction(analysis["coarse_product"])
    say(
        f"  [this repository, Condition 4]  B(1 + D) = {coarse} = {_decimal(coarse)}"
        f"  -> {'HOLDS' if analysis['coarse_holds'] else 'FAILS'}"
    )
    say(f"      slack 1 - B(1 + D) = {analysis['coarse_slack']}")
    say(
        f"  [Mira's proof note / T-022 sharpened form]  B^2(1 + D)^2 < 1 + D^2"
        f"  -> {'HOLDS' if analysis['sharp_holds'] else 'FAILS'}"
    )
    say(f"      B^2(1 + D)^2 = {analysis['sharp_left']}")
    say(f"      1 + D^2      = {analysis['sharp_right']}")
    say(f"      slack        = {analysis['sharp_slack']}")
    if analysis["coarse_holds"]:
        say("  Condition 4 as this repository states it is satisfied; the sharper")
        say("  inequality is reported for comparison and carries no weight in the verdict.")
    else:
        say("  Condition 4 as this repository states it is NOT satisfied. Any acceptance")
        say("  below would rest on the sharper lemma, which `verify` does not decide.")
    say()


def print_header(certificate: Certificate, record: dict[str, Any], digest: str) -> None:
    atoms = len(certificate.atoms)
    grid_bytes = (2 * atoms + 2) ** 2 * 8  # certificate.py `_estimated_grid_bytes`
    say(f"certificate  {CERTIFICATE_PATH.relative_to(REPO)}")
    say(f"sha256       {digest}")
    say(f"source       {SOURCE_REPOSITORY} @ {SOURCE_COMMIT}")
    say(f"id           {record.get('id')}")
    say(f"claim field  {record.get('claim')!r}")
    say(
        f"shape        n = {certificate.n}, L = {certificate.outer_side}, "
        f"B = {certificate.square_side}, {atoms} atoms, "
        f"{len(certificate.half_tangents)} net directions, symmetry {certificate.symmetry}"
    )
    say(
        f"bound        s({certificate.n}) >= {certificate.bounded_side}"
        " if every condition holds"
    )
    say(f"grid         one direction's dense event grid is {grid_bytes / 2**20:.1f} MiB")
    say(f"interpreter  {sys.version.split()[0]} ({platform.platform()})")
    say(f"worktree     {REPO} at {git_commit()}")
    say()


def compare_declared(
    label: str,
    computed: Fraction,
    declared: str | None,
    failures: list[str],
    *,
    strict: bool = True,
) -> dict[str, Any]:
    """Hold a computed rational against the source's declared one, exactly.

    ``strict`` is false only where the computed value is not the quantity the source
    declared -- a sampled sub-net's least mass is an upper bound on the net's, so a
    disagreement there is arithmetic, not a discrepancy.
    """

    if declared is None:
        say(f"  {label}: {computed}  (the source declares nothing to compare against)")
        return {"computed": str(computed), "declared": None, "agrees": None}
    agrees = computed == Fraction(declared)
    say(f"  {label}: {computed} = {_decimal(computed)}")
    verdict = "AGREES" if agrees else ("DISAGREES" if strict else "differs, sample only")
    say(f"    source declares {declared} -> {verdict}")
    if not agrees and strict:
        failures.append(f"{label} is {computed}, the source declares {declared}")
    return {"computed": str(computed), "declared": declared, "agrees": agrees}


def exact_stage(
    certificate: Certificate,
    declared: dict[str, Any],
    *,
    workers: int,
    sample: int | None,
    failures: list[str],
) -> dict[str, Any]:
    """The event-cell verifier, in exact rational arithmetic."""

    say("Stage 1: the exact verifier, sqpack.fractional.certificate.verify")
    say(f"  requested {workers} workers; sqpack applies its own caps (a four-worker")
    say("  ceiling and a 512 MiB grid budget, certificate.py), so the effective pool")
    say("  may be smaller. Directions are independent and the result is net-ordered.")
    say()
    started = time.perf_counter()
    reports: list[tuple[str, str, bool | None]]
    if sample is None:
        verdict = verify(certificate, workers=workers)
        reports = [(c.name, c.detail, c.holds) for c in verdict.conditions]
        least, worst = verdict.minimum_cell_mass, verdict.worst_direction
        total = verdict.total_mass
        searched = len(certificate.half_tangents)
    else:
        directions = certificate.directions
        indices = sampled_indices(len(directions), sample)
        reports = [(c.name, c.detail, c.holds) for c in closed_form_conditions(certificate)]
        least = None
        worst = None
        for index in indices:
            minimum, _ = sweep_direction_minimum(certificate, directions[index])
            if least is None or minimum < least:
                least, worst = minimum, directions[index].label
        reports.append(
            (
                (
                    f"Condition 5 NOT DECIDED, {len(indices)} of "
                    f"{len(directions)} directions sampled"
                ),
                f"least cell mass over the sample {least} at direction {worst}",
                None,
            )
        )
        total = certificate.total_mass
        searched = len(indices)
    elapsed = time.perf_counter() - started

    for name, detail, holds in reports:
        mark = "SMOKE" if holds is None else ("PASS" if holds else "FAIL")
        say(f"  [{mark}] {name}")
        say(f"         {detail}")
    say()
    say("  Against the source's declared numbers:")
    mass = compare_declared("total mass", total, declared.get("total_mass"), failures)
    cell: dict[str, Any] = {"computed": None, "declared": declared.get("minimum_mass")}
    if least is not None:
        cell = compare_declared(
            "least cell mass",
            least,
            declared.get("minimum_mass"),
            failures,
            strict=sample is None,
        )
        cell["worst_direction"] = worst
        say(f"    attained at net direction {worst} of {len(certificate.half_tangents) - 1}")
    else:
        failures.append("the sweep returned no least cell mass")
    say()
    say(f"  {searched} directions swept in {elapsed:.1f} s")
    say()
    accepted = sample is None and all(holds is True for _, _, holds in reports)
    if sample is None and not accepted:
        failures.append(
            "the exact verifier refused: "
            + ", ".join(n for n, _, h in reports if h is not True)
        )
    return {
        "stage": "exact",
        "sampled_directions": None if sample is None else searched,
        "requested_workers": workers,
        "wall_seconds": round(elapsed, 3),
        "conditions": [{"name": n, "detail": d, "holds": h} for n, d, h in reports],
        "total_mass": mass,
        "least_cell_mass": cell,
        "accepted": accepted,
    }


def interval_stage(
    certificate: Certificate,
    declared: dict[str, Any],
    *,
    sample: int | None,
    failures: list[str],
) -> dict[str, Any]:
    """The interval-certified verifier, over the doubled net."""

    net = doubled_net(certificate.half_tangents)
    labels: tuple[str, ...] | None = None
    if sample is not None:
        labels = tuple(net[i].label for i in sampled_indices(len(net), sample))
    say("Stage 2: the interval verifier, sqpack.fractional.interval.verify_by_intervals")
    say(f"  doubled net of {len(net)} directions (theta_k and pi/2 - theta_k), so the D4")
    say("  reflection argument is never invoked and Condition 1 is not needed.")
    say("  enclose=True: no pruning, so the least covered mass is pinned, not just decided.")
    if labels is not None:
        say(f"  SMOKE: restricted to {len(labels)} of {len(net)} directions, which the module")
        say("  reports as `undecided` by design -- a sub-net decides a weaker statement.")
    say()
    started = time.perf_counter()
    verdict = verify_by_intervals(certificate, enclose=True, directions=labels)
    elapsed = time.perf_counter() - started

    for condition in verdict.conditions:
        mark = {"holds": "PASS", "fails": "FAIL", "undecided": "UNDECIDED"}[condition.status]
        say(f"  [{mark}] {condition.name}")
        say(f"         {condition.detail}")
    say()
    statuses = {"certified": 0, "refuted": 0, "undecided": 0}
    for outcome in verdict.directions:
        statuses[outcome.status] += 1
    say(
        f"  directions searched {len(verdict.directions)}: "
        f"{statuses['certified']} certified, {statuses['refuted']} refuted, "
        f"{statuses['undecided']} undecided"
    )
    say(
        f"  boxes {sum(o.boxes for o in verdict.directions)}, "
        f"stalled {sum(o.stalled for o in verdict.directions)}, "
        f"budget-exhausted {sum(o.budget_exhausted for o in verdict.directions)}"
    )
    enclosure = verdict.enclosure
    record: dict[str, Any] = {
        "stage": "interval",
        "sampled_directions": None if labels is None else len(labels),
        "doubled_net_directions": len(net),
        "wall_seconds": round(elapsed, 3),
        "conditions": [
            {"name": c.name, "detail": c.detail, "status": c.status} for c in verdict.conditions
        ],
        "direction_statuses": statuses,
        "boxes": sum(o.boxes for o in verdict.directions),
        "stalled": sum(o.stalled for o in verdict.directions),
        "budget_exhausted": sum(o.budget_exhausted for o in verdict.directions),
        "total_mass": str(verdict.total_mass),
        "accepted": verdict.accepted,
    }
    if enclosure is None:
        say("  no enclosure: a direction was refuted before both bounds were established")
        record["enclosure"] = None
        failures.append("the interval verifier established no enclosure")
    else:
        low, high = enclosure
        say(f"  least covered mass enclosed in [{low}, {high}]")
        say(f"                              = [{_decimal(low)}, {_decimal(high)}]")
        say(f"  enclosure width {high - low}")
        record["enclosure"] = [str(low), str(high)]
        say()
        say("  Against the source's declared numbers:")
        record["total_mass_check"] = compare_declared(
            "total mass", verdict.total_mass, declared.get("total_mass"), failures
        )
        stated = declared.get("minimum_mass")
        if stated is not None:
            value = Fraction(stated)
            inside = low <= value <= high
            say(f"  least cell mass: source declares {stated} = {_decimal(value)}")
            say(f"    inside the enclosure -> {'YES' if inside else 'NO'}")
            record["declared_minimum_inside_enclosure"] = inside
            if not inside and labels is None:
                failures.append(
                    f"the source's minimum {stated} lies outside the interval enclosure "
                    f"[{low}, {high}]"
                )
    say()
    say(f"  {len(verdict.directions)} directions in {elapsed:.1f} s")
    say()
    if labels is None and not verdict.accepted:
        failures.append("the interval verifier did not accept: " + ", ".join(verdict.failures))
    return record


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--interval",
        action="store_true",
        help="run the interval verifier instead of the exact one",
    )
    parser.add_argument(
        "--directions",
        type=int,
        default=None,
        metavar="K",
        help="smoke test: search only K sampled directions; decides nothing",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="workers requested for the exact sweep, before sqpack's own caps",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=None,
        help="write the machine-readable receipt to this path",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.directions is not None and args.directions < 1:
        say("REFUSED: --directions needs a positive count")
        return 2

    raw = CERTIFICATE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CERTIFICATE_SHA256:
        say(f"REFUSED: the certificate hashes to {digest}, expected {CERTIFICATE_SHA256}")
        return 1
    declared: dict[str, Any] = json.loads(RESULT_PATH.read_bytes())
    stated_digest = declared.get("certificate_sha256")
    if stated_digest != CERTIFICATE_SHA256:
        say(
            f"REFUSED: the source's result.json names {stated_digest}, not {CERTIFICATE_SHA256}"
        )
        return 1

    certificate, record = load(raw)
    started_at = datetime.now(UTC)
    wall = time.perf_counter()
    print_header(certificate, record, digest)
    analysis = containment_analysis(certificate)
    print_containment(analysis)

    failures: list[str] = []
    if args.interval:
        stage = interval_stage(certificate, declared, sample=args.directions, failures=failures)
    else:
        stage = exact_stage(
            certificate,
            declared,
            workers=args.workers,
            sample=args.directions,
            failures=failures,
        )
    elapsed = time.perf_counter() - wall

    after = CERTIFICATE_PATH.read_bytes()
    unchanged = hashlib.sha256(after).hexdigest() == CERTIFICATE_SHA256 and after == raw
    say(
        f"certificate bytes re-read after the replay: {'UNCHANGED' if unchanged else 'CHANGED'}"
    )
    if not unchanged:
        failures.append("the certificate file changed during the replay")
    say()

    receipt = {
        "tool": Path(__file__).resolve().relative_to(REPO).as_posix(),
        "generated_at": started_at.isoformat(),
        "certificate": CERTIFICATE_PATH.relative_to(REPO).as_posix(),
        "certificate_sha256": digest,
        "certificate_unchanged_after_replay": unchanged,
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "certificate_claim_field": record.get("claim"),
        "declared_by_source": {
            "total_mass": declared.get("total_mass"),
            "minimum_mass": declared.get("minimum_mass"),
            "slabs": declared.get("slabs"),
            "strict_decimal_bound": declared.get("strict_decimal_bound"),
        },
        "interpreter": sys.version.split()[0],
        "platform": platform.platform(),
        "worktree_commit": git_commit(),
        "wall_seconds": round(elapsed, 3),
        "containment": analysis,
        "result": stage,
        "smoke": args.directions is not None,
        "refusals": failures,
    }
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        say(f"receipt written to {args.receipt}")

    if failures:
        for failure in failures:
            say(f"REFUSED: {failure}")
        return 1
    if args.directions is not None:
        say("SMOKE RUN COMPLETE: a sampled sub-net decides nothing about this certificate.")
        return 0
    stage_name = "interval" if args.interval else "exact"
    say(
        f"REPLAYED: this repository's {stage_name} verifier accepts Mira's certificate, "
        f"so s(17) >= {certificate.bounded_side} on its own terms."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
