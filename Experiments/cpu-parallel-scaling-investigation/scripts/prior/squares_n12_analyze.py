"""Read saved n=12 benchmark stdout files and print comparable timing summaries."""

from __future__ import annotations

import json
import statistics as stats
import sys
from pathlib import Path


PREFIX = Path("/tmp/squares-n12-")
FACTORS = (2, 5, 10, 20, 50, 100, float("inf"))


def read_run(name: str) -> dict:
    path = Path(f"{PREFIX}{name}.stdout")
    text = path.read_text()
    brace = text.find("{")
    if brace < 0:
        raise ValueError(f"{path}: missing JSON body; benchmark may still be running")
    try:
        report, end = json.JSONDecoder().raw_decode(text[brace:])
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: incomplete JSON body; benchmark may still be running") from exc
    if text[brace + end :].strip():
        raise ValueError(f"{path}: unexpected text after JSON body")
    run = report["row_run"]
    timings = run["timings"]
    if len(timings) != run["rounds"] or [r["index"] for r in timings] != list(
        range(run["rounds"])
    ):
        raise ValueError(f"{path}: timing indices disagree with round count")
    return {"name": name, "case": report["case"], "run": run, "pricing": report["pricing"]}


def summary(values: list[float]) -> str:
    mean = stats.mean(values)
    cv = stats.pstdev(values) / mean if mean else 0.0
    return (
        f"min={min(values):.3f} median={stats.median(values):.3f} "
        f"max={max(values):.3f} mean={mean:.3f} CV={cv:.2%}"
    )


def timing_slice(rows: list[dict]) -> tuple[float, float, float]:
    sep = sum(row["separation_s"] for row in rows)
    lp = sum(row["lp_s"] for row in rows)
    return sep, lp, sep / (sep + lp) if sep + lp else 0.0


def print_slice(label: str, rows: list[dict], run: dict) -> None:
    sep, lp, share = timing_slice(rows)
    print(
        f"  {label} indices={rows[0]['index']}..{rows[-1]['index']}: "
        f"sep={sep:.3f}s lp={lp:.3f}s sep_share={share:.2%} "
        f"timed_share_of_run={(sep + lp) / run['seconds']:.2%}"
    )


def amdahl(total: float, sep: float) -> str:
    return " ".join(
        f"{factor if factor != float('inf') else 'inf'}x:"
        f"{total / (total - sep + (sep / factor if factor != float('inf') else 0)):.3f}x"
        for factor in FACTORS
    )


def main() -> None:
    controlled = [read_run(f"controlled-{i}") for i in (1, 2, 3)]
    default_path = Path(f"{PREFIX}default.stdout")
    default = read_run("default") if default_path.exists() else None
    runs = controlled + ([default] if default else [])
    assert all(entry is not None for entry in runs)

    for entry in runs:
        run = entry["run"]
        print(
            f"{entry['name']}: wall={run['seconds']:.3f}s "
            f"sep={run['separation_seconds']:.3f}s lp={run['lp_seconds']:.3f}s "
            f"sep_share={run['separation_share']:.2%} "
            f"rounds={run['rounds']} rows={run['rows']} "
            f"objective={run['objective']:.15f} peak_support={run['peak_support']} "
            f"pricing={entry['pricing']['total_s']:.3f}s "
            f"stopped={run['stopped']!r}"
        )
        times = run["timings"]
        print_slice("round 0", times[:1], run)
        print_slice("rounds 1..final", times[1:], run)
        print_slice("last 5 incl terminal", times[-5:], run)
        if times[-1]["lp_s"] == 0 and len(times) >= 6:
            print_slice("last 5 with LP", times[-6:-1], run)

    print("\nControlled repeatability (population CV):")
    for field in ("seconds", "separation_seconds", "lp_seconds"):
        print(f"  {field}: {summary([entry['run'][field] for entry in controlled])}")
    decisions = [
        (
            entry["run"]["rounds"],
            entry["run"]["rows"],
            entry["run"]["objective"],
            entry["run"]["stopped"],
        )
        for entry in controlled
    ]
    print(f"  identical algorithmic decisions: {len(set(decisions)) == 1}")

    total = stats.mean(entry["run"]["seconds"] for entry in controlled)
    sep = stats.mean(entry["run"]["separation_seconds"] for entry in controlled)
    round0 = [timing_slice(entry["run"]["timings"][:1]) for entry in controlled]
    steady_total = total - stats.mean(s + l for s, l, _ in round0)
    steady_sep = sep - stats.mean(s for s, _, _ in round0)
    print("\nAmdahl, separation-only acceleration, controlled means:")
    print(f"  total: T={total:.3f}s S={sep:.3f}s f={sep / total:.2%}: {amdahl(total, sep)}")
    print(
        f"  excluding round 0: T={steady_total:.3f}s S={steady_sep:.3f}s "
        f"f={steady_sep / steady_total:.2%}: {amdahl(steady_total, steady_sep)}"
    )
    if default:
        run = default["run"]
        print(
            f"\nDefault vs controlled mean: wall {run['seconds'] / total:.3f}x; "
            f"sep {run['separation_seconds'] / sep:.3f}x"
        )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"Cannot analyze completed runs: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
