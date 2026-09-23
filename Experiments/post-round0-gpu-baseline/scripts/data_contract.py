#!/usr/bin/env python3
"""Derive transfer sizes from the current round-18 solver trace."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
trace = json.loads((ROOT / "results/profile-serial.json").read_text())
directions = [x for x in trace["profiles"] if x["round"] == 18]
shapes = [tuple(x["meta"]["grid_shape"]) for x in directions]
point_count = directions[0]["meta"]["points_count"]
grid_bytes = sum(8 * r * c for r, c in shapes)
cell_count = sum((r - 1) * (c - 1) for r, c in shapes)
mass_bytes = 8 * cell_count
reach_bytes = cell_count
axis_bytes = sum(8 * (r + c) for r, c in shapes)
range_bytes = sum(16 * (r - 1) for r, c in shapes)
projection_bytes = len(directions) * point_count * 2 * 8
point_bytes = point_count * 2 * 8
weight_bytes = point_count * 8
indices_bytes = len(directions) * 13 * 8
coordinates_mass_bytes = len(directions) * 3 * 3 * 8
mask_bytes = len(directions) * 3 * point_count
result = {
    "round": 18,
    "support_sites": trace["round_timings_exact"][18]["support"],
    "directions": len(directions),
    "points_shape": [point_count, 2],
    "points_dtype": "float64",
    "weights_shape": [point_count],
    "weights_dtype": "float64",
    "direction_input": "two float64 projection coefficients per direction; outer and square side are two shared float64 scalars",
    "grid_shapes": [{"shape": list(shape), "directions": count} for shape, count in Counter(shapes).most_common()],
    "grid_dtype": "float64",
    "mass_dtype": "float64",
    "reachable_dtype": "bool (1 byte per cell)",
    "points_bytes_once": point_bytes,
    "weights_bytes_once": weight_bytes,
    "points_weights_bytes_repeated_per_direction": len(directions) * (point_bytes + weight_bytes),
    "direction_coefficients_bytes": len(directions) * 2 * 8,
    "shared_outer_side_bytes": 16,
    "grid_input_bytes": grid_bytes,
    "reachable_input_bytes": reach_bytes,
    "event_axis_input_bytes": axis_bytes,
    "domain_range_input_bytes": range_bytes,
    "cumsum_mass_output_bytes": mass_bytes,
    "selector_scored_input_bytes": mass_bytes,
    "top13_indices_output_bytes": indices_bytes,
    "three_candidates_coordinates_mass_bytes": coordinates_mass_bytes,
    "three_candidates_bool_masks_bytes": mask_bytes,
    "event_grid_full_return_bytes": projection_bytes + axis_bytes + range_bytes + mass_bytes + reach_bytes,
    "naive_separate_cumsum_and_selector_transfer_bytes": grid_bytes + mass_bytes + mass_bytes + indices_bytes,
    "resident_grid_reachable_axes_input_bytes": grid_bytes + axis_bytes + range_bytes,
    "resident_grid_reachable_axes_top13_output_bytes": indices_bytes,
    "resident_grid_plus_reachable_mask_input_bytes": grid_bytes + reach_bytes,
}
(ROOT / "results/data-contract.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
