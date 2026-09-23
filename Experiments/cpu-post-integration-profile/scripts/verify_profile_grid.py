"""Check the research-only timed event grid against current production code."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np
from profile_separation import ORIGINAL_EVENT_GRID, timed_event_grid

from devtools import bench_colgen
from sqpack.fractional.generate import direction_net

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    stored = np.load(ROOT / "raw/current-states.npz")
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = direction_net(case.half_tangents())
    fields = ("u", "v", "u_events", "v_events", "mass", "lows", "highs")
    cases = 0
    cells = 0
    for round_index in (0, 1, 8, 18, 22):
        weights = stored["weights"][round_index][stored["membership"]]
        for direction in directions:
            args = (stored["points"], weights, direction,
                    float(case.outer_side), float(case.square_side))
            expected = ORIGINAL_EVENT_GRID(*args, build_reachable=False)
            actual = timed_event_grid(*args, build_reachable=False)
            for field in fields:
                left, right = getattr(expected, field), getattr(actual, field)
                assert np.array_equal(left.view(np.uint64), right.view(np.uint64)), (
                    round_index, direction.label, field
                )
            assert expected.domain == actual.domain
            assert expected.reachable is actual.reachable is None
            cases += 1
            cells += expected.mass.size
    result = {"rounds": [0, 1, 8, 18, 22], "directions_per_round": len(directions),
              "cases": cases, "mass_cells_compared_bitwise": cells, "passed": True}
    (ROOT / "raw/profile-grid-equivalence.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
