"""Capture 181 real round-18 directions into a portable little-endian file."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "packing"))
from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.generate import direction_net

DATA = ROOT / "Experiments/cpu-post-integration-profile/raw/current-states.npz"
PACKAGE = HERE.parent / "package"
MAGIC = b"SQCPUV1\0"
MASK = (1 << 64) - 1


def fnv(data, state=14695981039346656037):
    for byte in data:
        state = ((state ^ byte) * 1099511628211) & MASK
    return state


def selected_hash(flat, indices):
    state = 14695981039346656037
    for index in indices:
        state = fnv(struct.pack("<Q", int(index)), state)
        state = fnv(struct.pack("<d", float(flat[index])), state)
    return state


def intervals(cells):
    ve = cells.v_events
    band_first = np.searchsorted(ve[1:], cells.domain.v_low, side="right")
    band_last = np.searchsorted(ve[:-1], cells.domain.v_high, side="left")
    slabs = ((cells.u_events[1:] > cells.domain.u_low)
             & (cells.u_events[:-1] < cells.domain.u_high))
    first = np.maximum(band_first, np.searchsorted(
        ve[1:], cells.lows - generate._REACH_SLACK, side="right"))
    last = np.minimum(band_last, np.searchsorted(
        ve[:-1], cells.highs + generate._REACH_SLACK, side="left"))
    valid = slabs & (first < last)
    first = np.where(valid, first, 0).astype("<u4")
    last = np.where(valid, last, 0).astype("<u4")
    return first, last


def main():
    PACKAGE.mkdir(parents=True, exist_ok=True)
    with np.load(DATA) as stored:
        points, membership = (stored[x] for x in ("points", "membership"))
        weights = stored["weights"][18][membership]
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = direction_net(case.half_tangents())
    outer, side = float(case.outer_side), float(case.square_side)
    live = weights > 0
    assert live.any()
    manifest = {"round": 18, "directions": len(directions), "cases": [],
                "source": str(DATA.relative_to(ROOT))}
    path = PACKAGE / "data.bin"
    with path.open("wb") as handle:
        handle.write(struct.pack("<8sII", MAGIC, 1, len(directions)))
        for number, direction in enumerate(directions):
            cells = generate.event_grid(points, weights, direction, outer, side,
                                        build_reachable=False)
            cosine, sine = float(direction.ux), float(direction.uy)
            half = side / 2
            u = points[:, 0] * cosine + points[:, 1] * sine
            v = -points[:, 0] * sine + points[:, 1] * cosine
            lu, lv, lw = u[live], v[live], weights[live]
            ue, ve = cells.u_events, cells.v_events
            left = np.searchsorted(ue, lu - half).astype("<u4")
            right = np.searchsorted(ue, lu + half).astype("<u4")
            bottom = np.searchsorted(ve, lv - half).astype("<u4")
            top = np.searchsorted(ve, lv + half).astype("<u4")
            lw = lw.astype("<f8", copy=False)
            rows, columns = len(ue), len(ve)
            diff = np.zeros((rows, columns), dtype=np.float64)
            np.add.at(diff, (left, bottom), lw)
            np.add.at(diff, (right, bottom), -lw)
            np.add.at(diff, (left, top), -lw)
            np.add.at(diff, (right, top), lw)
            mass = diff.copy()
            np.add.accumulate(mass, axis=1, out=mass)
            generate.accumulate_axis0(mass)
            assert np.array_equal(mass[:-1, :-1], cells.mass)
            first, last = intervals(cells)
            compact = np.concatenate([
                cells.mass[row, first[row]:last[row]]
                for row in range(rows - 1) if last[row] > first[row]])
            production_flat, *_ = generate._reachable_values(cells)
            assert np.array_equal(compact, production_flat)
            selected = generate._least_finite_indices(compact, 13)
            assert selected.size == 13
            difference_hash = fnv(diff.tobytes())
            mass_hash = fnv(cells.mass.tobytes())
            selection_hash = selected_hash(compact, selected)
            n = len(lw)
            flat_length = int((last - first).sum())
            handle.write(struct.pack("<IIIIQQQ", rows, columns, n, flat_length,
                                     difference_hash, mass_hash, selection_hash))
            for array in (left, right, bottom, top, lw, first, last):
                handle.write(array.tobytes())
            manifest["cases"].append({"direction": number, "rows": rows,
                "columns": columns, "live_sites": n, "reachable_values": flat_length,
                "difference_fnv64": f"{difference_hash:016x}",
                "mass_fnv64": f"{mass_hash:016x}",
                "selection_fnv64": f"{selection_hash:016x}"})
    manifest["data_size_bytes"] = path.stat().st_size
    manifest["data_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest["grid_cells_total"] = sum(x["rows"] * x["columns"] for x in manifest["cases"])
    (PACKAGE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in
        ("directions", "grid_cells_total", "data_size_bytes", "data_sha256")}))


if __name__ == "__main__":
    main()
