"""Research-only C-contiguous axis-0 prefix pass with unchanged event semantics."""

from __future__ import annotations

import ctypes
from pathlib import Path

import numpy as np

from sqpack.fractional import colgen, generate

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ctypes.CDLL(str(ROOT / "raw/libprefix_rows.so"))
AXIS0 = LIBRARY.prefix_axis0_rowmajor
AXIS0.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_size_t]
AXIS0.restype = None


def candidate_event_grid(
    points, weights, direction, outer_side, square_side, *, clip=None,
    build_reachable=True,
):
    cosine, sine = float(direction.ux), float(direction.uy)
    half = square_side / 2
    u = points[:, 0] * cosine + points[:, 1] * sine
    v = -points[:, 0] * sine + points[:, 1] * cosine
    domain = generate._CentreDomain.at(direction, outer_side, square_side, clip)

    live = weights > 0
    if not live.any():
        live = np.zeros(points.shape[0], dtype=bool)
        live[:: max(1, points.shape[0] // 600)] = True
    live_u, live_v, live_w = u[live], v[live], weights[live]
    u_events = np.unique(
        np.concatenate([live_u - half, live_u + half, [domain.u_low, domain.u_high]])
    )
    v_events = np.unique(
        np.concatenate([live_v - half, live_v + half, [domain.v_low, domain.v_high]])
    )
    grid = np.zeros((u_events.size, v_events.size))
    left = np.searchsorted(u_events, live_u - half)
    right = np.searchsorted(u_events, live_u + half)
    bottom = np.searchsorted(v_events, live_v - half)
    top = np.searchsorted(v_events, live_v + half)
    np.add.at(grid, (left, bottom), live_w)
    np.add.at(grid, (right, bottom), -live_w)
    np.add.at(grid, (left, top), -live_w)
    np.add.at(grid, (right, top), live_w)
    np.add.accumulate(grid, axis=1, out=grid)
    AXIS0(
        grid.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        grid.shape[0], grid.shape[1],
    )
    mass = grid[:-1, :-1]

    u0, u1 = u_events[:-1], u_events[1:]
    slabs = (u1 > domain.u_low) & (u0 < domain.u_high)
    bands = (v_events[:-1] < domain.v_high) & (v_events[1:] > domain.v_low)
    lows, highs = domain.v_range(u0, u1)
    reachable = (
        slabs[:, None]
        & bands[None, :]
        & (v_events[None, :-1] < highs[:, None] + generate._REACH_SLACK)
        & (v_events[None, 1:] > lows[:, None] - generate._REACH_SLACK)
    ) if build_reachable else None
    return generate.EventGrid(u, v, u_events, v_events, mass, reachable, lows, highs, domain)


def install() -> None:
    generate.event_grid = candidate_event_grid


class CandidatePool(colgen.ProcessPoolExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, initializer=install, **kwargs)


def install_pool() -> None:
    install()
    colgen.ProcessPoolExecutor = CandidatePool
