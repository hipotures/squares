"""Check the timed event-grid copy against production on representative rounds."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from profile import ORIGINAL_EVENT_GRID, timed_event_grid
from sqpack.fractional.generate import direction_net

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT.parent / "cpu-post-integration-profile" / "raw"


def main() -> None:
    stored = np.load(PROFILE / "current-states.npz")
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = direction_net(case.half_tangents())
    cells = 0
    calls = 0
    for round_index in (0, 18, 22):
        weights = stored["weights"][round_index][stored["membership"]]
        for direction in directions:
            args = (stored["points"], weights, direction,
                    float(case.outer_side), float(case.square_side))
            reference = ORIGINAL_EVENT_GRID(*args, build_reachable=False)
            measured = timed_event_grid(*args, build_reachable=False)
            for name in ("u", "v", "u_events", "v_events", "mass", "lows", "highs"):
                assert np.array_equal(getattr(reference, name), getattr(measured, name))
            assert reference.domain == measured.domain
            cells += reference.mass.size
            calls += 1
    result = {"passed": True, "direction_calls": calls,
              "mass_cells_compared_bitwise": cells,
              "rounds": [0, 18, 22]}
    (ROOT / "raw/profile-equivalence.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
