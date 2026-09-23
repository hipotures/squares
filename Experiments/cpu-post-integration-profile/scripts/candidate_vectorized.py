"""Research-only vectorized interval construction; production is untouched."""

from __future__ import annotations

import numpy as np

from sqpack.fractional import colgen, generate


def reachable_values_vectorized(cells: generate.EventGrid):
    ve = cells.v_events
    band_first = np.searchsorted(ve[1:], cells.domain.v_low, side="right")
    band_last = np.searchsorted(ve[:-1], cells.domain.v_high, side="left")
    slabs = (
        (cells.u_events[1:] > cells.domain.u_low)
        & (cells.u_events[:-1] < cells.domain.u_high)
    )
    first_all = np.maximum(
        band_first,
        np.searchsorted(ve[1:], cells.lows - generate._REACH_SLACK, side="right"),
    )
    last_all = np.minimum(
        band_last,
        np.searchsorted(ve[:-1], cells.highs + generate._REACH_SLACK, side="left"),
    )
    valid = slabs & (first_all < last_all)
    row_ids = np.flatnonzero(valid)
    firsts = first_all[valid]
    widths = last_all[valid] - firsts
    offsets = np.empty(row_ids.size, dtype=np.intp)
    if offsets.size:
        offsets[0] = 0
        np.cumsum(widths[:-1], out=offsets[1:])
    values = np.empty(int(widths.sum()), dtype=np.float64)
    for row, first, width, offset in zip(row_ids, firsts, widths, offsets, strict=True):
        values[offset:offset + width] = cells.mass[row, first:first + width]
    return values, row_ids, firsts, offsets


def install() -> None:
    generate._reachable_values = reachable_values_vectorized


class CandidatePool(colgen.ProcessPoolExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, initializer=install, **kwargs)


def install_pool() -> None:
    install()
    colgen.ProcessPoolExecutor = CandidatePool
