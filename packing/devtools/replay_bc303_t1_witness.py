"""Replay the known literal bottom-left BC303 T1 witness from bound source bytes.

The reader verifies one disclosed role-C counterexample with exact arithmetic. It does
not search, minimize surplus, replay the full BC303 certificate, or make a routing or
packing-bound claim.

``validate_record(record, repository)`` authenticates retained records against the
reviewed source bytes and the executing reader at the checkout's HEAD. The source
revision names the frozen input proposal; the implementation revision names this reader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from pathlib import Path
from typing import cast

from strif import atomic_write_text

SCHEMA = "bc303-literal-t1-witness/v1"
SOURCE_REVISION = "9a19d39319861c93d85d7213101cf3a8a443c415"
READER_PATH = "packing/devtools/replay_bc303_t1_witness.py"
MEASURE_PATH = (
    "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/"
    "bc-293-measure-free-96-25.json"
)
OUTER_SIDE = Fraction(96, 25)
CORE_SIDE = Fraction(9977, 10000)
HALF_CORE_SIDE = CORE_SIDE / 2
ANGLE_LIMIT = Fraction(207107, 500000)
TOTAL_MASS = Fraction(22524199, 2000000)
ALLOWANCE = TOTAL_MASS - 11
WEIGHT_SCALE = 4_000_000
CORE_LOWER = Fraction(23, 20000)
CORE_UPPER = Fraction(19977, 20000)
MARKS = (
    (Fraction(3152, 3175), Fraction(2336, 3175)),
    (Fraction(2336, 3175), Fraction(3152, 3175)),
)
MARK_WEIGHT = Fraction(106251, 800000)
CAPTURED_INDICES = (
    0,
    2,
    8,
    10,
    16,
    18,
    24,
    26,
    44,
    46,
    52,
    54,
    60,
    62,
    100,
    102,
    140,
    361,
    373,
)
CAPTURED_MASS = Fraction(800003, 800000)
SURPLUS = Fraction(3, 800000)
DETERMINATION = {
    "outcome": "rejected",
    "claim": (
        "for every X in the bottom-left one-corner role-C domain with labels 0 and 15 "
        "absent, S(X) > epsilon"
    ),
    "scope": "the named one-corner BC303 T1 local surplus inequality only",
    "global_routing": "not-claimed",
    "n11_lower_bound": "not-claimed",
    "minimum_surplus": "not-claimed",
}

type Point = tuple[Fraction, Fraction]


class T1ReplayError(ValueError):
    """The source binding, witness, record, or determination violated its contract."""


@dataclass(frozen=True, slots=True)
class SourceSpec:
    path: str
    git_blob: str
    byte_count: int


@dataclass(frozen=True, slots=True)
class Atom:
    index: int
    point: Point
    weight: Fraction


@dataclass(frozen=True, slots=True)
class Measure:
    atoms: tuple[Atom, ...]
    total_mass: Fraction
    weight_scale: int


# 2026-09-20 (Session 145, PR 206): re-bound twice. First from 39714308 to 8f4eca7d,
# where the corner-clip instrument had changed three pinned blobs -- certificate.py,
# sweep.py and generate.py -- and then to 9a19d393, which carries this review's own
# change to generate.py (the clipped branch of ``_CentreDomain.at`` now refuses a clip
# whose sides disagree with its affine bounds).
#
# Read these entries as what they are: *review bindings*, the source bytes the retained
# determination was reviewed against. They are not inputs to it. This reader imports no
# ``sqpack`` module -- the standard library plus ``strif`` -- and ``_literal_witness``
# computes the witness from the measure document alone, so the determination never
# depended on certificate.py, sweep.py or generate.py and re-running the replay
# re-validates the bindings rather than the behaviour of the re-pinned modules. What was
# re-run at each re-binding: this replay and its test module, which reproduce the
# retained witness unchanged; that is a statement about this reader, not about them.
#
# The evidence that the clip-free code paths of those modules are themselves unchanged
# is separate, and does exercise them: an unclipped re-decision of
# packing/campaign/series/series-000-smoke-and-calibration/results/agenda-037/
# n18-467-100-t019-seed-certificate.json, reproducing the pre-PR log
# n18-467-100-t019-seed-decide.log in every field -- interval accepted, enclosure
# 2000007/2000000 both ends, boxes 2543909, stalled 0; exact accepted, least
# 2000007/2000000; sha256 3a11b6303e0663b502b6c1e3fc9d8da285104e199b17022937369bc781479059.
SOURCES = (
    SourceSpec(
        "docs/project/research/research-2026-09-12-n11-selection-routing-first-principles.md",
        "52b042cbb77405dd6c4cf4d394481b00e3ccd78f",
        28_821,
    ),
    SourceSpec(
        "docs/project/reviews/review-2026-09-12-n11-selection-routing-first-principles.md",
        "409d38f79bf1fd5cbf6ade4b1c70d7db44d0a3f2",
        21_658,
    ),
    SourceSpec(
        "docs/project/research/research-2026-09-10-x027-structural-helpers.md",
        "f4f192ca995b7664e235e0bdfdc2a18ccb282ecf",
        38_623,
    ),
    SourceSpec(
        "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/"
        "bc-303-first-wave-selection.md",
        "ef7f2f5d6342904082a291f860f5ba732dc52a41",
        69_368,
    ),
    SourceSpec(MEASURE_PATH, "db8abed8f716a4173b47bcfb19f8e045b44513d1", 17_616),
    SourceSpec(
        "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-031/"
        "proofs/corner-owner-sector-footprints.md",
        "631fe7f861510a51107d458e27a09d32a0b6cad6",
        6_275,
    ),
    SourceSpec(
        "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-032/"
        "proofs/fixed-cover-transfer-review.md",
        "6d07ae56760217277b2ac2cb1cf2887916061d4e",
        10_740,
    ),
    SourceSpec(
        "packing/cases/n11_five_dot_cover/wall-containment-contract.md",
        "24e00f7cbbbb07c26347e22a4b2b3467cea701fa",
        18_245,
    ),
    SourceSpec(
        "packing/src/sqpack/fractional/certificate.py",
        "5c48d1709b19fc65d39e3abe89cfad43e2123cbe",
        22_423,
    ),
    SourceSpec(
        "packing/src/sqpack/fractional/sweep.py",
        "81aaa87307d88f7397051eacaa6518b525e0dffc",
        19_453,
    ),
    SourceSpec(
        "packing/src/sqpack/fractional/adaptive.py",
        "d80f6e060904bc5e01c21f5f23eba87ede456422",
        8_246,
    ),
    SourceSpec(
        "packing/src/sqpack/fractional/classcert.py",
        "523e9f34593d04bfa7a327dbdde3a15cd5582f63",
        30_409,
    ),
    SourceSpec(
        "packing/devtools/owner_footprints.py",
        "65501ad186a463eb5e7e16978daf03e603149fbd",
        23_223,
    ),
    SourceSpec(
        "packing/devtools/wall_owner_footprints.py",
        "da831e51cfbb81e4329ffbfc52005ec61fac2811",
        24_481,
    ),
    SourceSpec(
        "packing/cases/n11_five_dot_cover/unit-parent-centre-contract.md",
        "714229c1250e1403b44ea60fa873b2bd2e5bf4dc",
        10_810,
    ),
    SourceSpec(
        "packing/devtools/wall_owner_parent_compatibility.py",
        "6360f3af422a40fea40c1722da9fcb779fa5b1be",
        27_401,
    ),
    SourceSpec(
        "packing/src/sqpack/fractional/model.py",
        "a5df6094eadfe441dba66fee8fe37a4e5530b6f6",
        2_801,
    ),
    SourceSpec(
        "packing/src/sqpack/fractional/generate.py",
        "f95792ca57139d0991b6a92e1e971d9a0a7b35d3",
        24_267,
    ),
)

_BIN_EDGES = tuple(
    (Fraction(x), Fraction(y))
    for x, y in (
        (1, 0),
        (1, 1),
        (0, 1),
        (-1, 1),
        (-1, 0),
        (-1, -1),
        (0, -1),
        (1, -1),
    )
)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise T1ReplayError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise T1ReplayError(f"non-finite JSON constant {value!r}")


def strict_json_bytes(data: bytes, label: str) -> dict[str, object]:
    """Read one duplicate-key-free, finite JSON object."""

    try:
        value = json.loads(
            data,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise T1ReplayError(f"{label} is not strict JSON: {error}") from error
    if not isinstance(value, dict):
        raise T1ReplayError(f"{label} must be a JSON object")
    return cast(dict[str, object], value)


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise T1ReplayError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise T1ReplayError(f"{label} must be an array")
    return cast(list[object], value)


def _fraction(value: object, label: str) -> Fraction:
    if not isinstance(value, str):
        raise T1ReplayError(f"{label} must be an exact rational string")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise T1ReplayError(f"{label} is not an exact rational") from error


def _git_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def _git(repository: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        error = result.stderr.decode(errors="replace").strip()
        raise T1ReplayError(error or f"git {' '.join(arguments)} failed")
    return result.stdout


def validate_source_bytes(source_bytes: Mapping[str, bytes]) -> None:
    """Require the complete reviewed source manifest and every exact Git blob."""

    expected_paths = {source.path for source in SOURCES}
    if set(source_bytes) != expected_paths:
        raise T1ReplayError("source path set differs from the reviewed proposal")
    for source in SOURCES:
        data = source_bytes[source.path]
        if len(data) != source.byte_count or _git_blob(data) != source.git_blob:
            raise T1ReplayError(f"source bytes changed: {source.path}")


def bind_sources(repository: Path) -> tuple[str, dict[str, bytes], list[dict[str, object]]]:
    """Bind proposal-revision, input-checkout HEAD, and working bytes for all 18 sources."""

    repository = repository.resolve()
    root = Path(_git(repository, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if root != repository:
        raise T1ReplayError("repository argument must name the Git worktree root")
    head = _git(root, "rev-parse", "HEAD").decode().strip()
    if len(head) != 40 or any(character not in "0123456789abcdef" for character in head):
        raise T1ReplayError("current source checkout revision is malformed")

    source_bytes: dict[str, bytes] = {}
    for source in SOURCES:
        path = root / source.path
        if path.is_symlink() or not path.is_file():
            raise T1ReplayError(f"source is not a regular repository file: {source.path}")
        working = path.read_bytes()
        frozen = _git(root, "cat-file", "blob", f"{SOURCE_REVISION}:{source.path}")
        current = _git(root, "cat-file", "blob", f"{head}:{source.path}")
        if working != frozen or current != frozen:
            raise T1ReplayError(
                "source differs across proposal revision, current HEAD, or worktree: "
                f"{source.path}"
            )
        source_bytes[source.path] = working
    validate_source_bytes(source_bytes)
    bindings = [
        {"path": source.path, "git_blob": source.git_blob, "bytes": source.byte_count}
        for source in SOURCES
    ]
    return head, source_bytes, bindings


def _bind_implementation(repository: Path, head: str) -> None:
    """Require the executing reader to be the regular file committed at input HEAD."""

    reader = repository / READER_PATH
    if reader.is_symlink() or not reader.is_file() or Path(__file__).resolve() != reader:
        raise T1ReplayError("executing T1 reader is not the input checkout's reader path")
    try:
        committed = _git(repository, "cat-file", "blob", f"{head}:{READER_PATH}")
    except T1ReplayError as error:
        raise T1ReplayError(
            "executing T1 reader is absent at implementation revision"
        ) from error
    if reader.read_bytes() != committed:
        raise T1ReplayError("executing T1 reader differs from implementation revision")


def _turn(ray: Point) -> Point:
    return -ray[1], ray[0]


def _dot(left: Point, right: Point) -> Fraction:
    return left[0] * right[0] + left[1] * right[1]


def _cross(left: Point, right: Point) -> Fraction:
    return left[0] * right[1] - left[1] * right[0]


def _signed_rays(ray: Point) -> tuple[Point, ...]:
    return ray, _turn(ray), (-ray[0], -ray[1]), (ray[1], -ray[0])


def _canonical_axis(ray: Point) -> Point:
    choices = [
        candidate for candidate in _signed_rays(ray) if candidate[0] > 0 and candidate[1] >= 0
    ]
    if len(choices) != 1:
        raise T1ReplayError("selected square axis has no unique canonical representative")
    return choices[0]


def complete_labels(
    center: Point, ray: Point, marks: Sequence[Point], half_side: Fraction
) -> list[int]:
    """Enumerate every closed-bin label over all four signed frames."""

    available: set[int] = set()
    for mark_index, mark in enumerate(marks):
        displacement = center[0] - mark[0], center[1] - mark[1]
        for first in _signed_rays(ray):
            if not (
                0 <= _dot(displacement, first) <= half_side
                and 0 <= _dot(displacement, _turn(first)) <= half_side
            ):
                continue
            for sector in range(8):
                if (
                    _cross(_BIN_EDGES[sector], first) >= 0
                    and _cross(first, _BIN_EDGES[(sector + 1) % 8]) >= 0
                ):
                    available.add(8 * mark_index + sector)
    return sorted(available)


def closed_core_membership(point: Point, center: Point, ray: Point) -> tuple[bool, Point]:
    """Decide closed selected-core membership and retain both exact axis slacks."""

    displacement = point[0] - center[0], point[1] - center[1]
    slacks = (
        HALF_CORE_SIDE - abs(_dot(displacement, ray)),
        HALF_CORE_SIDE - abs(_dot(displacement, _turn(ray))),
    )
    return all(slack >= 0 for slack in slacks), slacks


def unique_owner_surplus(owners: Sequence[tuple[str, Fraction]]) -> Fraction:
    """Sum each local owner once, refusing identity aliases that would double-count."""

    identities = [identity for identity, _mass in owners]
    if len(identities) != len(set(identities)):
        raise T1ReplayError("local surplus repeats an owner identity")
    return sum((mass - 1 for _identity, mass in owners), Fraction(0))


def _parse_measure(document: Mapping[str, object]) -> Measure:
    expected_fields = {
        "id",
        "n",
        "outer_side",
        "square_side",
        "angle_limit",
        "direction_steps",
        "total_mass",
        "least_cell_mass",
        "symmetry",
        "note",
        "atoms",
    }
    if set(document) != expected_fields:
        raise T1ReplayError("BC303 measure fields changed")
    if (
        document.get("id") != "bc-293-D-free-final"
        or document.get("n") != 11
        or _fraction(document.get("outer_side"), "outer_side") != OUTER_SIDE
        or _fraction(document.get("square_side"), "square_side") != CORE_SIDE
        or _fraction(document.get("angle_limit"), "angle_limit") != ANGLE_LIMIT
        or document.get("direction_steps") != 180
        or _fraction(document.get("total_mass"), "total_mass") != TOTAL_MASS
        or _fraction(document.get("least_cell_mass"), "least_cell_mass") != CAPTURED_MASS
        or document.get("symmetry") != "D4"
        or not isinstance(document.get("note"), str)
    ):
        raise T1ReplayError("BC303 measure identity or frozen constants changed")

    raw_atoms = _sequence(document.get("atoms"), "BC303 atoms")
    if len(raw_atoms) != 377:
        raise T1ReplayError("BC303 measure must contain exactly 377 atoms")
    atoms: list[Atom] = []
    seen: set[Point] = set()
    for index, raw_atom in enumerate(raw_atoms):
        values = _sequence(raw_atom, f"atom {index}")
        if len(values) != 3:
            raise T1ReplayError(f"atom {index} must contain x, y, and weight")
        point = (
            _fraction(values[0], f"atom {index} x"),
            _fraction(values[1], f"atom {index} y"),
        )
        weight = _fraction(values[2], f"atom {index} weight")
        if point in seen:
            raise T1ReplayError(f"atom {index} duplicates a source coordinate")
        if not (0 <= point[0] <= OUTER_SIDE and 0 <= point[1] <= OUTER_SIDE):
            raise T1ReplayError(f"atom {index} is outside the source container")
        if weight <= 0:
            raise T1ReplayError(f"atom {index} has nonpositive weight")
        seen.add(point)
        atoms.append(Atom(index, point, weight))

    weights = {atom.point: atom.weight for atom in atoms}
    for atom in atoms:
        x, y = atom.point
        orbit = {(x, y), (y, x)}
        orbit |= {(OUTER_SIDE - a, b) for a, b in tuple(orbit)}
        orbit |= {(a, OUTER_SIDE - b) for a, b in tuple(orbit)}
        if any(weights.get(image) != atom.weight for image in orbit):
            raise T1ReplayError(f"atom {atom.index} violates weighted D4 symmetry")
    total = sum((atom.weight for atom in atoms), Fraction(0))
    scale = lcm(*(atom.weight.denominator for atom in atoms))
    if total != TOTAL_MASS or scale != WEIGHT_SCALE:
        raise T1ReplayError("BC303 atom weights do not reconstruct total mass or scale")
    return Measure(tuple(atoms), total, scale)


def _axis_aliases() -> list[dict[str, object]]:
    tangent = ANGLE_LIMIT * 0 / 180
    ray = (
        (1 - tangent * tangent) / (1 + tangent * tangent),
        2 * tangent / (1 + tangent * tangent),
    )
    sources = ((False, ray), (True, (ray[1], ray[0])))
    aliases = [
        {
            "folded_index": 0,
            "reflected": reflected,
            "canonical_axis": [str(value) for value in _canonical_axis(source_ray)],
        }
        for reflected, source_ray in sources
    ]
    if aliases != [
        {"folded_index": 0, "reflected": False, "canonical_axis": ["1", "0"]},
        {"folded_index": 0, "reflected": True, "canonical_axis": ["1", "0"]},
    ]:
        raise T1ReplayError("axis source aliases changed")
    return aliases


def _literal_witness(measure: Measure) -> tuple[dict[str, object], list[dict[str, object]]]:
    center = (Fraction(1, 2), Fraction(1, 2))
    ray = (Fraction(1), Fraction(0))
    parent = (
        (Fraction(0), Fraction(0)),
        (Fraction(1), Fraction(0)),
        (Fraction(1), Fraction(1)),
        (Fraction(0), Fraction(1)),
    )
    core = ((CORE_LOWER, CORE_LOWER), (CORE_UPPER, CORE_UPPER))
    if core != (
        (center[0] - HALF_CORE_SIDE, center[1] - HALF_CORE_SIDE),
        (center[0] + HALF_CORE_SIDE, center[1] + HALF_CORE_SIDE),
    ):
        raise T1ReplayError("literal selected core bounds changed")
    if not (
        0 <= parent[0][0] <= core[0][0] < core[1][0] <= parent[2][0] <= OUTER_SIDE
        and 0 <= parent[0][1] <= core[0][1] < core[1][1] <= parent[2][1] <= OUTER_SIDE
    ):
        raise T1ReplayError("literal parent or selected-core containment failed")
    if not all(CORE_LOWER < coordinate < CORE_UPPER for mark in MARKS for coordinate in mark):
        raise T1ReplayError("literal core does not strictly contain both BL marks")
    weights = {atom.point: atom.weight for atom in measure.atoms}
    if any(weights.get(mark) != MARK_WEIGHT for mark in MARKS):
        raise T1ReplayError("literal BL marks or their source weights changed")

    labels = complete_labels(center, ray, MARKS, HALF_CORE_SIDE)
    alias_labels = complete_labels(center, _turn(ray), MARKS, HALF_CORE_SIDE)
    if labels != [3, 4, 11, 12] or alias_labels != labels:
        raise T1ReplayError("literal complete signed-frame labels changed")

    memberships: list[dict[str, object]] = []
    captured: list[Atom] = []
    for atom in measure.atoms:
        inside, slacks = closed_core_membership(atom.point, center, ray)
        coordinate_inside = all(
            CORE_LOWER <= coordinate <= CORE_UPPER for coordinate in atom.point
        )
        if inside != coordinate_inside:
            raise T1ReplayError(f"atom {atom.index} has inconsistent closed membership")
        if inside:
            captured.append(atom)
        memberships.append(
            {
                "index": atom.index,
                "point": [str(value) for value in atom.point],
                "weight": str(atom.weight),
                "weight_units": int(measure.weight_scale * atom.weight),
                "inside_core": inside,
                "axis_slacks": [str(value) for value in slacks],
            }
        )
    indices = tuple(atom.index for atom in captured)
    captured_mass = sum((atom.weight for atom in captured), Fraction(0))
    surplus = unique_owner_surplus((("literal-bottom-left-role-C", captured_mass),))
    if (
        indices != CAPTURED_INDICES
        or len(captured) != 19
        or captured_mass != CAPTURED_MASS
        or surplus != SURPLUS
        or surplus > ALLOWANCE
    ):
        raise T1ReplayError("literal BC303 atom capture or T1 allowance changed")
    return (
        {
            "corner": "bottom-left",
            "role": "C",
            "owner_count": 1,
            "missing_mark_count": 0,
            "parent": [["0", "0"], ["1", "0"], ["1", "1"], ["0", "1"]],
            "center": ["1/2", "1/2"],
            "parent_axis": ["1", "0"],
            "selected_axis": ["1", "0"],
            "core_bounds": [
                [str(CORE_LOWER), str(CORE_LOWER)],
                [str(CORE_UPPER), str(CORE_UPPER)],
            ],
            "marks": [[str(value) for value in mark] for mark in MARKS],
            "mark_weight": str(MARK_WEIGHT),
            "labels": labels,
            "required_absent_labels": [0, 15],
            "captured_indices_zero_based": list(indices),
            "captured_count": len(captured),
            "captured_mass": str(captured_mass),
            "surplus": str(surplus),
            "allowance": str(ALLOWANCE),
            "allowance_formula": "epsilon - 0*w",
            "allowance_minus_surplus": str(ALLOWANCE - surplus),
            "named_strict_inequality_holds": surplus > ALLOWANCE,
        },
        memberships,
    )


def _measure_summary(measure: Measure) -> dict[str, object]:
    return {
        "id": "bc-293-D-free-final",
        "atom_count": len(measure.atoms),
        "distinct_site_count": len({atom.point for atom in measure.atoms}),
        "outer_side": str(OUTER_SIDE),
        "core_side": str(CORE_SIDE),
        "direction_steps": 180,
        "angle_limit": str(ANGLE_LIMIT),
        "symmetry": "D4",
        "positive_weights": all(atom.weight > 0 for atom in measure.atoms),
        "weight_scale": measure.weight_scale,
        "total_mass": str(measure.total_mass),
        "allowance": str(ALLOWANCE),
        "mark_weight": str(MARK_WEIGHT),
    }


def _equipment() -> dict[str, object]:
    return {
        "selected_source_policy": "closed nearest folded source choices",
        "physical_angle_tangent": "0",
        "deterministic_lower_index_seam_compatible": True,
        "axis_source_aliases": _axis_aliases(),
        "closed_core_membership": True,
        "parent_and_selected_core_are_distinct_regions": True,
    }


def validate_record(record: Mapping[str, object], repository: Path) -> None:
    """Authenticate a retained T1 record against source atoms and executing reader."""

    head, source_bytes, _bindings = bind_sources(repository)
    _bind_implementation(repository.resolve(), head)
    source_measure = _parse_measure(
        strict_json_bytes(source_bytes[MEASURE_PATH], "BC303 measure")
    )

    if set(record) != {
        "schema",
        "status",
        "source_revision",
        "implementation_revision",
        "sources",
        "equipment",
        "measure",
        "witness",
        "memberships",
        "determination",
    }:
        raise T1ReplayError("T1 record fields changed")
    revision = record.get("implementation_revision")
    if (
        record.get("schema") != SCHEMA
        or record.get("status") != "complete"
        or record.get("source_revision") != SOURCE_REVISION
        or not isinstance(revision, str)
        or len(revision) != 40
        or any(character not in "0123456789abcdef" for character in revision)
    ):
        raise T1ReplayError("T1 record identity is malformed")
    if revision != head:
        raise T1ReplayError("T1 record implementation revision differs from executing reader")
    expected_sources = [
        {"path": source.path, "git_blob": source.git_blob, "bytes": source.byte_count}
        for source in SOURCES
    ]
    if record.get("sources") != expected_sources:
        raise T1ReplayError("T1 record source bindings changed")
    if record.get("equipment") != _equipment():
        raise T1ReplayError("T1 record equipment changed")
    measure = _mapping(record.get("measure"), "T1 measure summary")
    if measure != {
        "id": "bc-293-D-free-final",
        "atom_count": 377,
        "distinct_site_count": 377,
        "outer_side": "96/25",
        "core_side": "9977/10000",
        "direction_steps": 180,
        "angle_limit": "207107/500000",
        "symmetry": "D4",
        "positive_weights": True,
        "weight_scale": 4_000_000,
        "total_mass": "22524199/2000000",
        "allowance": "524199/2000000",
        "mark_weight": "106251/800000",
    }:
        raise T1ReplayError("T1 record measure summary changed")
    witness = _mapping(record.get("witness"), "T1 witness")
    if witness != {
        "corner": "bottom-left",
        "role": "C",
        "owner_count": 1,
        "missing_mark_count": 0,
        "parent": [["0", "0"], ["1", "0"], ["1", "1"], ["0", "1"]],
        "center": ["1/2", "1/2"],
        "parent_axis": ["1", "0"],
        "selected_axis": ["1", "0"],
        "core_bounds": [["23/20000", "23/20000"], ["19977/20000", "19977/20000"]],
        "marks": [["3152/3175", "2336/3175"], ["2336/3175", "3152/3175"]],
        "mark_weight": "106251/800000",
        "labels": [3, 4, 11, 12],
        "required_absent_labels": [0, 15],
        "captured_indices_zero_based": list(CAPTURED_INDICES),
        "captured_count": 19,
        "captured_mass": "800003/800000",
        "surplus": "3/800000",
        "allowance": "524199/2000000",
        "allowance_formula": "epsilon - 0*w",
        "allowance_minus_surplus": "1048383/4000000",
        "named_strict_inequality_holds": False,
    }:
        raise T1ReplayError("T1 witness summary changed")

    memberships = _sequence(record.get("memberships"), "T1 memberships")
    if len(memberships) != len(source_measure.atoms):
        raise T1ReplayError("T1 record does not retain all 377 memberships")
    captured_indices: list[int] = []
    captured_mass = Fraction(0)
    for atom, value in zip(source_measure.atoms, memberships, strict=True):
        row = _mapping(value, f"membership {atom.index}")
        inside, slacks = closed_core_membership(
            atom.point, (Fraction(1, 2), Fraction(1, 2)), (Fraction(1), Fraction(0))
        )
        expected_row = {
            "index": atom.index,
            "point": [str(value) for value in atom.point],
            "weight": str(atom.weight),
            "weight_units": int(source_measure.weight_scale * atom.weight),
            "inside_core": inside,
            "axis_slacks": [str(value) for value in slacks],
        }
        if (
            row != expected_row
            or type(row.get("index")) is not int
            or type(row.get("weight_units")) is not int
            or type(row.get("inside_core")) is not bool
        ):
            raise T1ReplayError(f"membership {atom.index} differs from bound source atom")
        if inside:
            captured_indices.append(atom.index)
            captured_mass += atom.weight
    if tuple(captured_indices) != CAPTURED_INDICES or captured_mass != CAPTURED_MASS:
        raise T1ReplayError("T1 record capture does not reconstruct")
    if record.get("determination") != DETERMINATION:
        raise T1ReplayError("T1 record overstates or changes its determination")


def replay(repository: Path) -> dict[str, object]:
    """Bind the reviewed sources and replay the literal witness exactly once."""

    head, source_bytes, source_bindings = bind_sources(repository)
    _bind_implementation(repository.resolve(), head)
    measure_document = strict_json_bytes(source_bytes[MEASURE_PATH], "BC303 measure")
    measure = _parse_measure(measure_document)
    witness, memberships = _literal_witness(measure)
    record: dict[str, object] = {
        "schema": SCHEMA,
        "status": "complete",
        "source_revision": SOURCE_REVISION,
        "implementation_revision": head,
        "sources": source_bindings,
        "equipment": _equipment(),
        "measure": _measure_summary(measure),
        "witness": witness,
        "memberships": memberships,
        "determination": dict(DETERMINATION),
    }
    validate_record(record, repository)
    return record


def encode_record(record: Mapping[str, object], repository: Path) -> str:
    """Authenticate and serialize a record with deterministic strict JSON bytes."""

    validate_record(record, repository)
    return json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _publish_record(
    path: Path, record: dict[str, object], encoded: str, repository: Path
) -> None:
    atomic_write_text(path, encoded)
    retained = strict_json_bytes(path.read_bytes(), "retained T1 record")
    validate_record(retained, repository)
    if retained != record:
        raise T1ReplayError("retained T1 record differs after atomic publication")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    try:
        record = replay(arguments.repository)
        encoded = encode_record(record, arguments.repository)
        if arguments.output is not None:
            _publish_record(arguments.output, record, encoded, arguments.repository)
        sys.stdout.write(encoded)
    except (OSError, T1ReplayError) as error:
        sys.stderr.write(
            json.dumps(
                {"schema": SCHEMA, "status": "refused", "error": str(error)},
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
