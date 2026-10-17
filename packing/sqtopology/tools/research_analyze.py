#!/usr/bin/env python3
"""Research analysis for the sqtopology discrete topology-space campaign.

This tool reads the machine-readable JSON emitted by

    sqtopology research FIXTURE --max-depth D [--json FILE]

and turns it into (a) compact tables, (b) dependency-free SVG plots, and
(c) same-n seed-overlap statistics from exact `SQK5HEX` key files emitted with
`--emit-keys`.

It is deliberately stdlib-only: reproduced results should not require a plotting
stack. All plots are plain SVG built from polylines and rects.

Subcommands:
    table    FILES...                      human-readable per-depth table
    json     FILES...                      normalized machine-readable summary
    plots    --out DIR FILES...            SVG plots
    overlap  --a FILE --b FILE [--json F]  exact key-set overlap (same n only)
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_result(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def depth_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return result["depths"]


def scaled(value: float, logy: bool) -> float:
    if not logy:
        return value
    return math.log10(value) if value > 0 else float("-inf")


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #

TABLE_HEADER = (
    "fixture", "d", "parents", "raw", "dup", "same", "cross", "new", "cum",
    "dupfrac", "meanC", "trivial", "multi",
)


def table_row(result: dict[str, Any], record: dict[str, Any]) -> list[str]:
    raw = record["raw_candidates"]
    dupfrac = (record["duplicate_candidates"] / raw) if raw else 0.0
    symmetry = record.get("symmetry", {})
    return [
        result["fixture"],
        str(record["depth"]),
        str(record["parents_expanded"]),
        str(raw),
        str(record["duplicate_candidates"]),
        str(record["duplicate_same_level"]),
        str(record["duplicate_cross_level"]),
        str(record["new_unique"]),
        str(record["cumulative_unique"]),
        f"{dupfrac:.3f}",
        f"{record['state_contacts']['mean']:.3f}",
        str(symmetry.get("trivial_group", "")),
        str(symmetry.get("nontrivial_group", "")),
    ]


def command_table(files: Sequence[Path]) -> None:
    widths = [len(h) for h in TABLE_HEADER]
    rows: list[list[str]] = []
    for path in files:
        result = load_result(path)
        for record in depth_rows(result):
            rows.append(table_row(result, record))
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(TABLE_HEADER)))
    print("  ".join("-" * widths[i] for i in range(len(TABLE_HEADER))))
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def compact_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Normalized, plot-ready summary; drops the bulky exact histograms."""
    depths = []
    for record in depth_rows(result):
        depths.append(
            {
                "depth": record["depth"],
                "parents_expanded": record["parents_expanded"],
                "raw_candidates": record["raw_candidates"],
                "duplicate_candidates": record["duplicate_candidates"],
                "duplicate_same_level": record["duplicate_same_level"],
                "duplicate_cross_level": record["duplicate_cross_level"],
                "new_unique": record["new_unique"],
                "cumulative_unique": record["cumulative_unique"],
                "mean_state_contacts": record["state_contacts"]["mean"],
                "state_contacts_exact": record["state_contacts"]["exact"],
                "candidate_contact_total": record["candidate_contact_total"],
                "state_type_totals": record["state_type_totals"],
                "trivial_group": record["symmetry"].get("trivial_group", 0),
                "nontrivial_group": record["symmetry"].get("nontrivial_group", 0),
                "max_group_size_log10": record["symmetry"].get("max_group_size_log10", 0.0),
                "wall_seconds": record["wall_seconds"],
            }
        )
    convergence = result["convergence"]
    return {
        "schema": "sqtopology.research-summary.v1",
        "fixture": result["fixture"],
        "square_count": result["square_count"],
        "event_space_size": result["event_space_size"],
        "seed_contacts": result["seed_contacts"],
        "max_depth": result["max_depth"],
        "max_additions_per_parent": result["max_additions_per_parent"],
        "additions_uncapped": result["additions_uncapped"],
        "canonical_backend": result["canonical_backend"],
        "counts_scope": result["counts_scope"],
        "total_unique": result["total_unique"],
        "wall_seconds": result["wall_seconds"],
        "peak_rss_kib": result["peak_rss_kib"],
        "depths": depths,
        "convergence": {
            "total_candidates": convergence["total_candidates"],
            "total_new_unique": convergence["total_new_unique"],
            "total_duplicates": convergence["total_duplicates"],
            "total_distinct_parent_edges": convergence["total_distinct_parent_edges"],
            "zero_parent_states": convergence["zero_parent_states"],
            "single_parent_states": convergence["single_parent_states"],
            "multi_parent_states": convergence["multi_parent_states"],
            "max_distinct_parents": convergence["max_distinct_parents"],
            "max_incoming_events": convergence["max_incoming_events"],
        },
    }


def command_json(files: Sequence[Path]) -> None:
    for path in files:
        print(json.dumps(compact_summary(load_result(path)), indent=2))


# --------------------------------------------------------------------------- #
# Seed overlap
# --------------------------------------------------------------------------- #

def load_keys(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text().splitlines() if line.strip()}


def command_overlap(args: argparse.Namespace) -> None:
    a = load_keys(args.a)
    b = load_keys(args.b)
    intersection = len(a & b)
    union = len(a | b)
    jaccard = intersection / union if union else 1.0
    payload = {
        "key_a": str(args.a),
        "key_b": str(args.b),
        "size_a": len(a),
        "size_b": len(b),
        "intersection": intersection,
        "union": union,
        "jaccard": jaccard,
        "containment_a_in_b": intersection / len(a) if a else 1.0,
        "containment_b_in_a": intersection / len(b) if b else 1.0,
    }
    text = json.dumps(payload, indent=2)
    if args.json:
        Path(args.json).write_text(text + "\n")
    print(text)


# --------------------------------------------------------------------------- #
# Dependency-free SVG plotting
# --------------------------------------------------------------------------- #

PALETTE = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#17becf", "#e377c2", "#7f7f7f", "#bcbd22",
]


class Canvas:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.parts: list[str] = []

    def add(self, text: str) -> None:
        self.parts.append(text)

    def render(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">\n'
            '<style>text{font-family:ui-sans-serif,system-ui,sans-serif;'
            'font-size:12px;fill:#222} .t{font-size:14px;font-weight:600}'
            '</style>\n'
            + "\n".join(self.parts)
            + "\n</svg>\n"
        )

    def text(self, x: float, y: float, value: str, anchor: str = "start", cls: str = "") -> None:
        klass = f' class="{cls}"' if cls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{klass}>{value}</text>')

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str = "#999", width: float = 1.0,
             dash: str = "") -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}"{dash_attr}/>'
        )

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str = "none") -> None:
        self.add(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" '
            f'fill="{fill}" stroke="{stroke}"/>'
        )

    def polyline(self, points: Sequence[tuple[float, float]], color: str, width: float = 2.0) -> None:
        if not points:
            return
        coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        self.add(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    def circle(self, x: float, y: float, r: float, color: str) -> None:
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}"/>')


def nice_ticks(lo: float, hi: float, count: int = 6) -> list[float]:
    if not math.isfinite(lo) or not math.isfinite(hi):
        return []
    if hi <= lo:
        return [lo]
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / count))
    for factor in (1, 2, 2.5, 5, 10):
        if span / (step * factor) <= count:
            step *= factor
            break
    start = math.floor(lo / step) * step
    ticks = []
    value = start
    while value <= hi + step * 0.5:
        ticks.append(value)
        value += step
    return ticks


def format_tick(value: float) -> str:
    if value == 0:
        return "0"
    magnitude = abs(value)
    if magnitude >= 1e6 or magnitude < 1e-3:
        return f"{value:.0e}"
    if magnitude >= 1000:
        return f"{value/1000:.0f}k" if value % 1000 == 0 else f"{value/1000:.1f}k"
    if magnitude >= 1:
        return f"{value:.0f}"
    return f"{value:g}"


def plot_lines(
    path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    series: list[tuple[str, list[float], list[float]]],
    logy: bool = False,
    logx: bool = False,
    width: int = 760,
    height: int = 480,
) -> None:
    left, right, top, bottom = 82, 30, 46, 60
    plot_w = width - left - right
    plot_h = height - top - bottom
    canvas = Canvas(width, height)
    canvas.text(width / 2, 26, title, anchor="middle", cls="t")

    all_x = [x for _, xs, _ in series for x in xs]
    all_y = [y for _, _, ys in series for y in ys]
    if not all_x:
        path.write_text(canvas.render())
        return
    x_lo, x_hi = min(all_x), max(all_x)
    y_values = [scaled(y, logy) for y in all_y if not (logy and y <= 0)]
    y_lo, y_hi = min(y_values), max(y_values)
    if x_hi == x_lo:
        x_hi = x_lo + 1
    if y_hi == y_lo:
        y_hi = y_lo + 1

    def px(x: float) -> float:
        return left + (x - x_lo) / (x_hi - x_lo) * plot_w

    def py(y: float) -> float:
        return top + plot_h - (scaled(y, logy) - y_lo) / (y_hi - y_lo) * plot_h

    # grid + ticks
    for tick in nice_ticks(x_lo, x_hi, 8):
        gx = px(tick)
        canvas.line(gx, top, gx, top + plot_h, "#eee")
        canvas.text(gx, top + plot_h + 16, format_tick(tick), anchor="middle")
    for tick in nice_ticks(y_lo, y_hi, 7):
        gy = py(10 ** tick if logy else tick)
        canvas.line(left, gy, left + plot_w, gy, "#eee")
        label = format_tick(10 ** tick) if logy else format_tick(tick)
        canvas.text(left - 8, gy + 4, label, anchor="end")
    canvas.line(left, top, left, top + plot_h, "#333")
    canvas.line(left, top + plot_h, left + plot_w, top + plot_h, "#333")
    canvas.text(left + plot_w / 2, height - 14, xlabel, anchor="middle")
    canvas.text(16, top + plot_h / 2, ylabel, anchor="middle")

    for index, (label, xs, ys) in enumerate(series):
        color = PALETTE[index % len(PALETTE)]
        points = [(px(x), py(y)) for x, y in zip(xs, ys) if not (logy and y <= 0)]
        canvas.polyline(points, color)
        for x, y in points:
            canvas.circle(x, y, 2.5, color)
        canvas.rect(left + plot_w - 140, top + 8 + index * 18, 12, 12, color)
        canvas.text(left + plot_w - 122, top + 18 + index * 18, label)
    path.write_text(canvas.render())


def plot_heatmap(
    path: Path,
    title: str,
    depth_records: list[dict[str, Any]],
    width: int = 820,
    height: int = 520,
) -> None:
    left, right, top, bottom = 90, 30, 46, 70
    plot_w = width - left - right
    plot_h = height - top - bottom
    canvas = Canvas(width, height)
    canvas.text(width / 2, 26, title, anchor="middle", cls="t")

    # Gather the union of contact counts actually observed.
    values: set[int] = set()
    for record in depth_records:
        exact = record["state_contacts_exact"]
        values.update(int(entry[0]) for entry in exact)
    if not values:
        path.write_text(canvas.render())
        return
    rows = sorted(values)
    depths = [record["depth"] for record in depth_records]
    columns = len(depths)
    cell_w = plot_w / max(columns, 1)
    cell_h = plot_h / max(len(rows), 1)

    # Log-scaled shading.
    counts = {}
    maximum = 1
    for record in depth_records:
        for contact, count in record["state_contacts_exact"]:
            counts[(int(contact), record["depth"])] = count
            maximum = max(maximum, count)
    log_max = math.log10(maximum + 1)

    for row_index, contact in enumerate(rows):
        for col_index, depth in enumerate(depths):
            count = counts.get((contact, depth), 0)
            intensity = math.log10(count + 1) / log_max if count else 0.0
            shade = int(255 - 215 * intensity)
            color = f"rgb({shade},{shade + (0 if count else 0)},{shade})"
            if count:
                color = f"rgb({int(240-140*intensity)},{int(240-40*intensity)},{int(255-160*intensity)})"
            x = left + col_index * cell_w
            y = top + row_index * cell_h
            canvas.rect(x, y, cell_w, cell_h, color, "#fff")
    for row_index, contact in enumerate(rows):
        canvas.text(left - 8, top + (row_index + 0.7) * cell_h, str(contact), anchor="end")
    for col_index, depth in enumerate(depths):
        canvas.text(left + (col_index + 0.5) * cell_w, top + plot_h + 18, str(depth), anchor="middle")
    canvas.text(left + plot_w / 2, height - 18, "discovery depth", anchor="middle")
    canvas.text(16, top + plot_h / 2, "contact count", anchor="middle")
    canvas.text(left + plot_w + 6, top + plot_h / 2, f"max {maximum}", anchor="start")
    path.write_text(canvas.render())


def command_plots(args: argparse.Namespace) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = [load_result(path) for path in args.files]

    def series_from(getter) -> list[tuple[str, list[float], list[float]]]:
        series = []
        for result in results:
            xs = [record["depth"] for record in depth_rows(result)]
            ys = [getter(record) for record in depth_rows(result)]
            series.append((result["fixture"], xs, ys))
        return series

    plot_lines(
        out / "unique-per-depth.svg",
        "New canonical classes per depth",
        "discovery depth", "new unique classes",
        series_from(lambda r: r["new_unique"]),
    )
    plot_lines(
        out / "cumulative-unique.svg",
        "Cumulative canonical classes vs depth (log scale)",
        "discovery depth", "cumulative unique classes",
        series_from(lambda r: r["cumulative_unique"]), logy=True,
    )
    plot_lines(
        out / "cumulative-unique-linear.svg",
        "Cumulative canonical classes vs depth",
        "discovery depth", "cumulative unique classes",
        series_from(lambda r: r["cumulative_unique"]),
    )
    plot_lines(
        out / "raw-vs-unique.svg",
        "Raw candidates per depth vs new canonical classes",
        "discovery depth", "count (log scale)",
        series_from(lambda r: r["raw_candidates"]) + series_from(lambda r: r["new_unique"]),
        logy=True,
    )
    plot_lines(
        out / "duplicate-fraction.svg",
        "Duplicate candidate fraction vs depth",
        "discovery depth", "duplicate / raw",
        series_from(lambda r: (r["duplicate_candidates"] / r["raw_candidates"]) if r["raw_candidates"] else 0.0),
    )

    # growth ratio needs neighbor access; rebuild explicitly.
    growth_series = []
    for result in results:
        rows = depth_rows(result)
        xs, ys = [], []
        for index in range(1, len(rows)):
            previous = rows[index - 1]["new_unique"]
            current = rows[index]["new_unique"]
            if previous > 0 and current > 0:
                xs.append(rows[index]["depth"])
                ys.append(current / previous)
        growth_series.append((result["fixture"], xs, ys))
    plot_lines(
        out / "growth-ratio.svg",
        "Per-depth growth ratio new(d) / new(d-1)",
        "discovery depth", "ratio (log scale)",
        growth_series, logy=True,
    )

    for result in results:
        plot_heatmap(
            out / f"contacts-{result['fixture']}.svg",
            f"Contact-count distribution by depth: {result['fixture']}",
            compact_summary(result)["depths"],
        )
        # Fall back to exact histograms from the raw record for the heatmap.
    print(f"wrote plots to {out}")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    table = subparsers.add_parser("table")
    table.add_argument("files", nargs="+", type=Path)

    json_parser = subparsers.add_parser("json")
    json_parser.add_argument("files", nargs="+", type=Path)

    plots = subparsers.add_parser("plots")
    plots.add_argument("--out", required=True)
    plots.add_argument("files", nargs="+", type=Path)

    overlap = subparsers.add_parser("overlap")
    overlap.add_argument("--a", required=True, type=Path)
    overlap.add_argument("--b", required=True, type=Path)
    overlap.add_argument("--json", default="")

    args = parser.parse_args()
    if args.command == "table":
        command_table(args.files)
    elif args.command == "json":
        command_json(args.files)
    elif args.command == "plots":
        command_plots(args)
    elif args.command == "overlap":
        command_overlap(args)


if __name__ == "__main__":
    main()
