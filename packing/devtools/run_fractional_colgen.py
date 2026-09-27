"""Run the dual-driven column generator at one setting and record what it cost.

The generator is a library call with a dozen parameters, and every run of it
in the record so far was made from a one-off script that was not kept. The
covering-values register carries the consequence in plain words: for the
`n = 12` rung at `99/25`, "the record names no site set and retains no site,
row or round count". This module is the driver, so the next run is a command
with its parameters on the line and a per-round table on its stdout.

It only drives. `generate_adaptive` makes every search decision, the
rationaliser makes the candidate, and nothing here decides a bound: freezing
is the last thing it does, and `devtools.decide_certificate` is what turns a
frozen candidate into a retained one.
"""

from __future__ import annotations

import argparse
import os
import json
import math
import sys
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from concurrent.futures import Executor

from devtools.frontier_phase import PhaseJournal

from sqpack.fractional.ceiling import CeilingCertificate
from sqpack.fractional.certificate import Certificate, verify
from sqpack.fractional.colgen import (
    AdaptiveLog,
    RoundTiming,
    generate_adaptive,
    site_counts_for_side,
)
from sqpack.fractional.corner_clip import (
    CornerClip,
    class_certificate_id,
    class_claim,
    clip_from_optional,
)
from sqpack.fractional.cutting import SupportEntry, family_record, symmetric_placements
from sqpack.fractional.generate import net_half_tangents
from sqpack.fractional.site_merge import MergeReceipt, merge_near_atoms

# The net every retained fractional certificate carries, and the shrink they
# are all built at. Defaults rather than constants: a run that changes them is
# a different instrument and has to say so on the command line.
ANGLE_LIMIT = Fraction(207107, 500000)
DIRECTION_STEPS = 180
SHRINK = Fraction(9977, 10000)
SCALE = 200_000


@dataclass(frozen=True, slots=True)
class RunSettings:
    """Everything the run is, in the units the record quotes."""

    n: int
    outer_side: Fraction
    square_side: Fraction
    grid_counts: tuple[int, ...]
    inset: Fraction
    angle_limit: Fraction
    direction_steps: int
    scale: int
    column_rounds: int
    max_rounds: int
    rows_per_direction: int
    # A second site-set construction: a retained certificate whose atoms are
    # carried to this side and unioned with the grids. ``None`` is the grids
    # alone, which is what every run before BC-197 was.
    seed_certificate: Path | None = None
    seed_map: str = "scale"
    # Sites per ceiling window, see ``window_lattice``; 0 adds none.
    seed_windows: int = 0
    # Heaviest dual rows kept for pricing; ``None`` keeps every positive row.
    support_cap: int | None = 32
    # Lane-a Theorem B's free-corner threshold ``d``. ``None`` is the unconditional
    # program every run before BC-363 was; a value restricts the row domain to cores
    # avoiding all four corner triangles and makes the run a statement about that
    # class of packings, which the frozen candidate then declares.
    corner_clip: Fraction | None = None

    def as_dict(self) -> dict[str, object]:
        settings: dict[str, object] = {
            "n": self.n,
            "outer_side": str(self.outer_side),
            "square_side": str(self.square_side),
            "grid_counts": list(self.grid_counts),
            "inset": str(self.inset),
            "angle_limit": str(self.angle_limit),
            "direction_steps": self.direction_steps,
            "scale": self.scale,
            "column_rounds": self.column_rounds,
            "max_rounds": self.max_rounds,
            "rows_per_direction": self.rows_per_direction,
            "seed_certificate": (
                None if self.seed_certificate is None else str(self.seed_certificate)
            ),
            "seed_map": self.seed_map,
            "seed_windows": self.seed_windows,
            "support_cap": self.support_cap,
        }
        # Only a clipped run names its clip: an unclipped run's settings block and
        # provenance stay byte-for-byte what they were before the clip existed.
        if self.corner_clip is not None:
            settings["corner_clip"] = str(self.corner_clip)
        return settings


def summary(
    settings: RunSettings,
    log: AdaptiveLog,
    candidate: Certificate | None,
    seconds: float,
    frozen: Path | None,
) -> dict[str, object]:
    return {
        "settings": settings.as_dict(),
        "seconds": seconds,
        "stopped": log.stopped,
        "converged": log.stopped.startswith("converged"),
        "objective": log.objective,
        "least_covered": log.least_covered,
        "rounds": [
            {
                "index": entry.index,
                "rows": entry.rows,
                "orbits": entry.orbits,
                "sites": entry.sites,
                "lp_rounds": entry.lp_rounds,
                "objective": entry.objective,
                "least_covered": entry.least_covered,
                "averaged_depth": entry.averaged_depth,
                "reduced_cost": entry.cost,
                "added": entry.added,
                "seconds": entry.seconds,
                "note": entry.note,
            }
            for entry in log.rounds
        ],
        "total_mass": str(log.total_mass) if log.total_mass is not None else None,
        "total_mass_float": float(log.total_mass) if log.total_mass is not None else None,
        "atoms": len(candidate.atoms) if candidate is not None else 0,
        "ceiling_proved": None if log.ceiling is None else log.ceiling.proved,
        "ceiling_detail": None if log.ceiling is None else log.ceiling.detail,
        "frozen": str(frozen) if frozen is not None else None,
    }


def _finite_json_number(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def run_summary_json(result: dict[str, object]) -> str:
    """Encode strict JSON, using null for unavailable solver values."""

    record = dict(result)
    record["objective"] = _finite_json_number(record["objective"])
    record["least_covered"] = _finite_json_number(record["least_covered"])
    rounds = record["rounds"]
    assert isinstance(rounds, list)
    record["rounds"] = [
        {
            **entry,
            "objective": _finite_json_number(entry["objective"]),
            "least_covered": _finite_json_number(entry["least_covered"]),
            "averaged_depth": _finite_json_number(entry["averaged_depth"]),
            "reduced_cost": _finite_json_number(entry["reduced_cost"]),
        }
        for entry in rounds
    ]
    return json.dumps(record, indent=1, allow_nan=False) + "\n"


SEED_MAPS = ("scale", "centre")


def seed_points_from(
    path: Path, outer_side: Fraction, mapping: str
) -> set[tuple[Fraction, Fraction]]:
    """A retained certificate's atom sites, carried to ``outer_side``.

    Two maps, both D4-equivariant about the container centre so the seed
    stays a union of orbits: ``scale`` multiplies every coordinate by the
    ratio of the sides, which keeps each atom's distance to its nearest wall
    in proportion; ``centre`` translates by half the difference of the sides,
    which keeps the atoms' mutual distances and moves them off the walls.
    The weights are not read: a seed is a site set, and the LP sets the mass.
    """

    if mapping not in SEED_MAPS:
        raise ValueError(f"seed map must be one of {SEED_MAPS}, not {mapping!r}")
    record = json.loads(path.read_text())
    source_side = Fraction(record["outer_side"])
    ratio = outer_side / source_side
    shift = (outer_side - source_side) / 2
    points: set[tuple[Fraction, Fraction]] = set()
    for x, y, _weight in record["atoms"]:
        fx, fy = Fraction(x), Fraction(y)
        if mapping == "scale":
            points.add((fx * ratio, fy * ratio))
        else:
            points.add((fx + shift, fy + shift))
    return points


def window_lattice(
    n: int, outer_side: Fraction, square_side: Fraction, per_window: int
) -> set[tuple[Fraction, Fraction]]:
    """Sites inside the ceiling windows, where a sub-``m^2`` solution has to sit.

    Write ``m = ceil(sqrt(n))`` and ``delta = m B - L > 0``. Along one axis, ``m``
    axis-parallel ``B``-squares in a row overlap by ``delta`` in total, and the
    restricted dual only has to keep its depth at most 1 *at the sites*: if no
    site lies in any overlap strip, ``m`` unit weights per row are dual-feasible
    and the restricted optimum is ``m^2`` however small the covering value is.
    That is the exactly round value this pipeline has met at ``n = 13``,
    ``n = 17``, ``n = 18`` and BC-191's coarsest density, read mechanically.

    The remedy is the ``m - 1`` coordinates a hitting set needs: ``x_k`` in
    ``[L - (m - k) B, k B]`` for ``k = 1 .. m - 1``, windows of width ``delta``
    spaced ``B`` apart. Their products form a D4-symmetric lattice, and this
    returns it with ``per_window`` equally spaced sites inside each window (the
    ends excluded), so the LP can choose within the window and a placement
    tilted by the net's first step still finds mass. Direction 0 is what the
    lattice serves; the tilted directions are left to the grids and to column
    generation. Empty when ``per_window`` is 0 or the side is at or above the
    ceiling, where no window exists.
    """

    if per_window <= 0:
        return set()
    m = math.isqrt(n - 1) + 1
    delta = m * square_side - outer_side
    if delta <= 0:
        return set()
    coordinates: list[Fraction] = []
    for k in range(1, m):
        low = outer_side - (m - k) * square_side
        coordinates.extend(low + delta * j / (per_window + 1) for j in range(1, per_window + 1))
    return {(x, y) for x in coordinates for y in coordinates}


class RowLog(list[RoundTiming]):
    """A timings list that writes each LP round to a file as it lands.

    `generate_adaptive` logs a column round at a time, so a run stopped inside
    its first column round used to leave nothing (BC-211's runs B and D). The
    loop appends one `RoundTiming` per LP round to whatever list it is given;
    this one echoes the round to disk on append, so the table exists while
    the run is still going and survives a kill. Index ``-1`` is the warm
    solve a carried row set opens with and does no separation.
    """

    HEADER = (
        f"{'lp':>5} {'rows':>7} {'added':>6} {'violated':>8} {'support':>8} "
        f"{'objective':>13} {'sep_s':>8} {'lp_s':>8}"
    )

    def __init__(self, path: Path) -> None:
        super().__init__()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.handle = path.open("a")
        self.handle.write(self.HEADER + "\n")
        self.handle.flush()

    def append(self, timing: RoundTiming) -> None:
        super().append(timing)
        self.handle.write(
            f"{timing.index:>5} {timing.rows_held:>7} {timing.rows_added:>6} "
            f"{timing.violated:>8} {timing.support:>8} {timing.objective:>13.6f} "
            f"{timing.separation_seconds:>8.2f} {timing.lp_seconds:>8.2f}\n"
        )
        self.handle.flush()

    def close(self) -> None:
        self.handle.close()


def run(
    settings: RunSettings,
    *,
    log_path: Path | None,
    freeze: Path | None,
    verify_serial: bool = False,
    row_log: Path | None = None,
    deadline_seconds: float | None = None,
    freeze_family: Path | None = None,
    merge_radius: Fraction | None = None,
    raw_weights: Path | None = None,
    direction_executor: Executor | None = None,
    phase_log: Path | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    phases = PhaseJournal(phase_log)
    deadline = None if deadline_seconds is None else started + deadline_seconds
    seed: set[tuple[Fraction, Fraction]] = set()
    if settings.seed_certificate is not None:
        seed = seed_points_from(
            settings.seed_certificate, settings.outer_side, settings.seed_map
        )
    seed |= window_lattice(
        settings.n, settings.outer_side, settings.square_side, settings.seed_windows
    )
    timings: RowLog | list[RoundTiming] = RowLog(row_log) if row_log is not None else []
    clip = clip_from_optional(settings.corner_clip, settings.outer_side, settings.square_side)
    snapshot_options = {}
    if raw_weights is not None:
        if clip is not None:
            raise ValueError("raw LP snapshots currently support unconditional searches only")
        from devtools.frontier_snapshot import save as save_raw_snapshot

        def capture(sites, weights):
            save_raw_snapshot(
                raw_weights, sites, weights, n=settings.n,
                square_side=settings.square_side, angle_limit=settings.angle_limit,
                direction_steps=settings.direction_steps,
            )

        snapshot_options["capture_solution"] = capture
    candidate, log = generate_adaptive(
        settings.n,
        settings.outer_side,
        settings.square_side,
        grid_counts=settings.grid_counts,
        inset=settings.inset,
        angle_limit=settings.angle_limit,
        direction_steps=settings.direction_steps,
        scale=settings.scale,
        max_rounds=settings.max_rounds,
        column_rounds=settings.column_rounds,
        rows_per_direction=settings.rows_per_direction,
        support_cap=settings.support_cap,
        log_path=log_path,
        # Never here. The retention boundary is freeze-then-decide, and an
        # in-memory verdict is not evidence about any file (D-433, D-441).
        decide=False,
        seed_points=seed,
        timings=timings,
        deadline=deadline,
        clip=clip,
        direction_executor=direction_executor,
        phase_callback=phases,
        **snapshot_options,
    )
    seconds = time.perf_counter() - started
    if isinstance(timings, RowLog):
        timings.close()
    merge_receipt: MergeReceipt | None = None
    if candidate is not None and merge_radius is not None:
        candidate, merge_receipt = merge_near_atoms(candidate, radius=merge_radius)
        if log.total_mass is not None:
            log.total_mass = candidate.total_mass
    frozen: Path | None = None
    least_cell_mass: str | None = None
    if candidate is not None and freeze is not None:
        if verify_serial:
            # One worker, never the pool: a lane holding one core must not
            # start a parallel sweep, and this only fills the declaration.
            verdict = (
                verify(candidate, workers=1)
                if clip is None
                else verify(candidate, workers=1, clip=clip)
            )
            least_cell_mass = str(verdict.minimum_cell_mass)
        freeze.parent.mkdir(parents=True, exist_ok=True)
        freeze.write_text(certificate_json(candidate, least_cell_mass, clip=clip))
        frozen = freeze
    family_frozen = freeze_priced_family(settings, log, freeze_family)
    result = summary(settings, log, candidate, seconds, frozen)
    result["work_kind"] = "generation"
    if os.environ.get("PACK_NATIVE_SESSION"):
        from sqpack.fractional import native_ab_runtime, native_ab_metrics
        result["native_runtime"] = native_ab_runtime.preflight()
        result["native_session"] = os.environ["PACK_NATIVE_SESSION"]
        native_ab_metrics.flush(force=True)
    result["phase_timings"] = phases.summary()
    result["column_rounds_executed"] = len(log.rounds)
    result["raw_weights"] = str(raw_weights) if raw_weights is not None and raw_weights.exists() else None
    if result["raw_weights"] is not None:
        from devtools.frontier_io import digest
        result["raw_weights_sha256"] = digest(raw_weights)
    result["least_cell_mass"] = least_cell_mass
    result["family_frozen"] = None if family_frozen is None else str(family_frozen)
    result["priced_support_rows"] = (
        None if log.priced_support is None else len(log.priced_support)
    )
    result["merge"] = (
        None
        if merge_receipt is None
        else {
            "radius": str(merge_receipt.radius),
            "atoms_before": merge_receipt.atoms_before,
            "atoms_after": merge_receipt.atoms_after,
            "components": merge_receipt.components,
            "collapsed": merge_receipt.collapsed,
        }
    )
    result["seed_sites"] = len(seed)
    result["lp_log"] = [
        {
            "index": timing.index,
            "rows": timing.rows_held,
            "added": timing.rows_added,
            "violated": timing.violated,
            "support": timing.support,
            "objective": timing.objective,
            "separation_s": round(timing.separation_seconds, 3),
            "lp_s": round(timing.lp_seconds, 3),
        }
        for timing in timings
    ]
    return result


def freeze_priced_family(
    settings: RunSettings, log: AdaptiveLog, path: Path | None
) -> Path | None:
    """Write the priced dual as a ceiling-family record, or skip if there is none."""

    if path is None or not log.priced_support:
        return None
    half_tangents = net_half_tangents(settings.angle_limit, settings.direction_steps)
    entries = tuple(
        SupportEntry(direction, half_tangents[direction], x, y, weight)
        for direction, x, y, weight in log.priced_support
    )
    family = CeilingCertificate(
        settings.n,
        settings.outer_side,
        settings.square_side,
        half_tangents,
        symmetric_placements(entries, settings.outer_side, settings.square_side),
    )
    provenance = {
        "tool": "devtools.run_fractional_colgen",
        "settings": settings.as_dict(),
        "stopped": log.stopped,
        "support_rows": len(log.priced_support),
    }
    record = family_record(family, provenance)
    if settings.corner_clip is not None:
        # The clip belongs at the top level, beside the placements it priced, and not
        # only inside ``provenance.settings`` where a reader has to go looking for it
        # (review defect D4). The covering record declares the hypothesis the same way,
        # so a family and the candidate it priced read alike, and the ceiling readers
        # refuse to print the unconditional sentence over these bytes.
        record["variant"] = "class"
        record["corner_clip"] = str(settings.corner_clip)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=1) + "\n")
    return path


def certificate_json(
    certificate: Certificate,
    least_cell_mass: str | None,
    *,
    clip: CornerClip | None = None,
) -> str:
    """The retained on-disk shape, which `cases/*/replay.py` reads back.

    ``least_cell_mass`` is a declaration and not a decision: it is left null
    when nothing has computed it, so a frozen candidate never carries a number
    no run produced. `devtools.decide_certificate` is what decides the bytes.

    A run under a corner clip writes ``variant`` and ``corner_clip`` into the record,
    so the hypothesis travels with the bytes. The gate refuses ``variant: class``
    unless it is asked for the same clip on its own command line, which is what keeps
    a class candidate from ever being read as the unconditional theorem.

    It also writes the claim and the id of that class rather than the theorem's
    (review defect D1). A clipped record used to carry ``s(n) >= L`` word for word, so
    the only thing standing between those bytes and a reader who takes a claim string
    at face value was ``variant``. The class strings say the class in the claim and
    carry the threshold in the id, and the gate expects exactly them under the flag.
    """

    identifier = (
        f"C-n{certificate.n:03d}-fractional-"
        f"{certificate.outer_side.numerator}-{certificate.outer_side.denominator}"
        if clip is None
        else class_certificate_id(certificate.n, certificate.outer_side, clip.depth)
    )
    claim = (
        f"s({certificate.n}) >= {certificate.bounded_side}"
        if clip is None
        else class_claim(certificate.n, certificate.bounded_side, clip.depth)
    )
    record: dict[str, object] = {
        "id": identifier,
        "n": certificate.n,
        "claim": claim,
        "outer_side": str(certificate.outer_side),
        "square_side": str(certificate.square_side),
        "angle_limit": str(certificate.half_tangents[-1]),
        "direction_steps": len(certificate.half_tangents) - 1,
        "total_mass": str(certificate.total_mass),
        "least_cell_mass": least_cell_mass,
        "symmetry": certificate.symmetry,
        "atoms": [[str(atom.x), str(atom.y), str(atom.weight)] for atom in certificate.atoms],
    }
    if clip is not None:
        record["variant"] = "class"
        record["corner_clip"] = str(clip.depth)
    return json.dumps(record, indent=1) + "\n"


def counts_for(text: str, outer_side: Fraction, square_side: Fraction) -> tuple[int, ...]:
    """``auto`` holds BC-191's site density; anything else is an explicit tuple."""

    if text == "auto":
        return site_counts_for_side(outer_side, square_side)
    return tuple(int(part) for part in text.split(",") if part)


def main(argv: list[str] | None = None, *, direction_executor: Executor | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--side", type=Fraction, required=True, help="container side L")
    parser.add_argument("--shrink", type=Fraction, default=SHRINK, help="square side B")
    parser.add_argument(
        "--grid-counts",
        default="auto",
        help="comma-separated seed grid counts, or 'auto' for BC-191's site density",
    )
    parser.add_argument("--inset", type=Fraction, default=Fraction(1, 2))
    parser.add_argument("--angle-limit", type=Fraction, default=ANGLE_LIMIT)
    parser.add_argument("--direction-steps", type=int, default=DIRECTION_STEPS)
    parser.add_argument("--scale", type=int, default=SCALE)
    parser.add_argument("--column-rounds", type=int, default=8)
    parser.add_argument("--max-rounds", type=int, default=60)
    parser.add_argument("--rows-per-direction", type=int, default=3)
    parser.add_argument(
        "--corner-clip",
        type=Fraction,
        default=None,
        metavar="d",
        help=(
            "lane-a Theorem B free-corner threshold: restrict the row domain to cores "
            "avoiding every corner triangle x + y <= d (0 < d <= 1). The run then "
            "decides that class, and the frozen candidate declares variant: class"
        ),
    )
    parser.add_argument(
        "--support-cap",
        type=int,
        default=32,
        help="heaviest dual rows kept for pricing; 0 keeps every positive row",
    )
    parser.add_argument("--log", type=Path, default=None, help="append the round lines here")
    parser.add_argument("--freeze", type=Path, default=None, help="write the candidate here")
    parser.add_argument(
        "--freeze-family",
        type=Path,
        default=None,
        help="write the priced dual as a ceiling-family record",
    )
    parser.add_argument("--json", type=Path, default=None, help="write the run summary here")
    parser.add_argument("--raw-weights", type=Path, default=None,
                        help="preserve lossless raw LP weights for re-rationalisation")
    parser.add_argument(
        "--verify-serial",
        action="store_true",
        help="fill least_cell_mass with a one-worker sweep before freezing",
    )
    parser.add_argument(
        "--seed-certificate",
        type=Path,
        default=None,
        help="union the grids with a retained certificate's atom sites carried to this side",
    )
    parser.add_argument(
        "--seed-map",
        choices=SEED_MAPS,
        default="scale",
        help="how the seed atoms are carried: scale the coordinates, or centre them",
    )
    parser.add_argument(
        "--seed-windows",
        type=int,
        default=0,
        help="sites per ceiling window to seed (the centred pitch-B lattice); 0 for none",
    )
    parser.add_argument(
        "--deadline-seconds",
        type=float,
        default=None,
        help="wall clock after which no row round starts; the run returns unconverged",
    )
    parser.add_argument(
        "--row-log",
        type=Path,
        default=None,
        help="append one line per LP round here as it lands, so a killed run leaves a table",
    )
    parser.add_argument(
        "--merge-radius",
        type=Fraction,
        default=None,
        help="Chebyshev radius for merging near atoms before freeze; omit to keep every site",
    )
    parser.add_argument("--phase-log", type=Path, help="Unix-timestamped generation phase events")
    args = parser.parse_args(argv)
    if args.support_cap < 0:
        parser.error("--support-cap must be non-negative")
    if args.corner_clip is not None and not 0 < args.corner_clip <= 1:
        parser.error("--corner-clip must satisfy 0 < d <= 1")

    settings = RunSettings(
        n=args.n,
        outer_side=args.side,
        square_side=args.shrink,
        grid_counts=counts_for(args.grid_counts, args.side, args.shrink),
        inset=args.inset,
        angle_limit=args.angle_limit,
        direction_steps=args.direction_steps,
        scale=args.scale,
        column_rounds=args.column_rounds,
        max_rounds=args.max_rounds,
        rows_per_direction=args.rows_per_direction,
        seed_certificate=args.seed_certificate,
        seed_map=args.seed_map,
        seed_windows=args.seed_windows,
        support_cap=None if args.support_cap == 0 else args.support_cap,
        corner_clip=args.corner_clip,
    )
    print(json.dumps(settings.as_dict(), indent=1), flush=True)
    result = run(
        settings,
        log_path=args.log,
        freeze=args.freeze,
        verify_serial=args.verify_serial,
        row_log=args.row_log,
        deadline_seconds=args.deadline_seconds,
        freeze_family=args.freeze_family,
        merge_radius=args.merge_radius,
        raw_weights=args.raw_weights,
        direction_executor=direction_executor,
        phase_log=args.phase_log,
    )
    print(round_table_from(result), flush=True)
    print(
        f"stopped: {result['stopped']}\n"
        f"objective: {result['objective']}\n"
        f"least covered mass: {result['least_covered']}\n"
        f"total mass: {result['total_mass']} = {result['total_mass_float']}\n"
        f"least cell mass: {result.get('least_cell_mass')}\n"
        f"atoms: {result['atoms']}\n"
        f"seed sites: {result['seed_sites']}\n"
        f"frozen: {result['frozen']}\n"
        f"family frozen: {result.get('family_frozen')}\n"
        f"priced support rows: {result.get('priced_support_rows')}\n"
        f"seconds: {result['seconds']:.1f}",
        flush=True,
    )
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(run_summary_json(result))
    return 0


def round_table_from(result: dict[str, object]) -> str:
    """The same table as `round_table`, from the summary a run returns."""

    header = (
        f"{'round':>5} {'rows':>7} {'orbits':>7} {'sites':>7} {'lp_rounds':>9} "
        f"{'objective':>13} {'least_covered':>13} {'depth':>10} {'seconds':>9}  note"
    )
    lines = [header, "-" * len(header)]
    rounds = result["rounds"]
    assert isinstance(rounds, list)
    lines.extend(
        f"{entry['index']:>5} {entry['rows']:>7} {entry['orbits']:>7} "
        f"{entry['sites']:>7} {entry['lp_rounds']:>9} {entry['objective']:>13.6f} "
        f"{entry['least_covered']:>13.6f} {entry['averaged_depth']:>10.6f} "
        f"{entry['seconds']:>9.1f}  {entry['note']}"
        for entry in rounds
    )
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
