"""Exact source measures for hybrid searches, never imported proof certificates."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

UPSTREAM = "6aa82ba457e9eaeaaa3af0833600f27f91a2fce3"
RECORD_BLOB = "4c3f0bb3b2607ad037086e1183324eb4fb7a8d68"
MAX_BYTES = 8 * 1024 * 1024
MAX_POINTS = 100_000


def rational(value: Any) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("an exact integer or rational string is required")
    if len(str(value)) > 512:
        raise ValueError("rational exceeds the input limit")
    return Fraction(value)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True)
class SourceMeasure:
    side: Fraction
    atoms: tuple[tuple[Fraction, Fraction, Fraction], ...]
    sha256: str
    source: str

    @property
    def mass(self) -> Fraction:
        return sum((w for _, _, w in self.atoms), Fraction())

    def record(self) -> dict[str, Any]:
        return {
            "schema": "hybrid-support/v1", "status": "SEED_ONLY",
            "outer_side": str(self.side), "source": self.source,
            "source_sha256": self.sha256,
            "atoms": [[str(x), str(y), str(w)] for x, y, w in self.atoms],
        }


def load_measure(path: Path, *, pinned_record: bool = False) -> SourceMeasure:
    """Read exact support data. Import never transfers a proof claim."""
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("source measure is too large")
    return parse_measure(path.read_bytes(), str(path.resolve()), pinned_record=pinned_record)


def parse_measure(raw: bytes, source: str = "<memory>", *, pinned_record: bool = False) -> SourceMeasure:
    """Parse bounded exact source data independently of filesystem access."""
    if len(raw) > MAX_BYTES:
        raise ValueError("source measure is too large")
    if pinned_record:
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != RECORD_BLOB:
            raise ValueError("published source bytes differ from the pinned record")
    text = raw.decode("utf-8")
    if text.lstrip().startswith("{"):
        data = json.loads(text, object_pairs_hook=_object)
        if not isinstance(data, dict) or not isinstance(data.get("atoms"), list):
            raise ValueError("expected an own certificate or a hybrid source measure")
        side = rational(data["outer_side"])
        entries = data["atoms"]
        if len(entries) > MAX_POINTS:
            raise ValueError("too many source points")
        atoms = []
        for row in entries:
            if not isinstance(row, list) or len(row) != 3:
                raise ValueError("each atom must have exactly x, y, and weight")
            atoms.append((rational(row[0]), rational(row[1]), rational(row[2])))
    else:
        tokens = text.split()
        if len(tokens) < 5 or any(len(token) > 512 for token in tokens):
            raise ValueError("invalid external integer header")
        try:
            sn, sd, denominator, weight_denominator, count = map(int, tokens[:5])
        except ValueError as exc:
            raise ValueError("the external header must contain integers") from exc
        if min(sn, sd, denominator, weight_denominator, count) <= 0 or count > MAX_POINTS:
            raise ValueError("invalid positive header or point count")
        if len(tokens) != 5 + 3 * count:
            raise ValueError("point count mismatch or unsupported conditional trailer")
        side = Fraction(sn, sd)
        if (side * denominator).denominator != 1:
            raise ValueError("the container is not on the coordinate lattice")
        atoms = [
            (Fraction(int(tokens[i]), denominator), Fraction(int(tokens[i + 1]), denominator),
             Fraction(int(tokens[i + 2]), weight_denominator))
            for i in range(5, len(tokens), 3)
        ]
    if side <= 0 or not atoms:
        raise ValueError("empty measure or nonpositive container")
    combined: dict[tuple[Fraction, Fraction], Fraction] = defaultdict(Fraction)
    for x, y, weight in atoms:
        if not (0 <= x <= side and 0 <= y <= side) or weight < 0:
            raise ValueError("negative weight or point outside the container")
        combined[x, y] += weight
    merged = tuple((x, y, weight) for (x, y), weight in sorted(combined.items()))
    return SourceMeasure(side, merged, hashlib.sha256(raw).hexdigest(), source)


def mapped_points(measures: list[SourceMeasure], side: Fraction, mapping: str) -> set[tuple[Fraction, Fraction]]:
    if side <= 0 or mapping not in ("scale", "centre"):
        raise ValueError("invalid target or source mapping")
    result: set[tuple[Fraction, Fraction]] = set()
    for measure in measures:
        for x, y, _ in measure.atoms:
            if mapping == "scale":
                mx, my = x * side / measure.side, y * side / measure.side
            else:
                shift = (side - measure.side) / 2
                mx, my = x + shift, y + shift
            if not (0 <= mx <= side and 0 <= my <= side):
                raise ValueError("the requested mapping moves a source point outside the target")
            result.add((mx, my))
    return result
