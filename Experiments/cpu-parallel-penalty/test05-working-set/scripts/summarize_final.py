"""Reduce long footprint and full-grid variant samples without discarding any."""

import json
import statistics as st
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
MIB = 1024 * 1024


def stats(values):
    return {"values": values, "min": min(values), "median": st.median(values),
            "max": max(values), "cv": st.pstdev(values) / st.mean(values)}


def samples(pattern):
    return [json.loads((RAW / pattern.format(i=i)).read_text()) for i in (1, 2, 3)]


result = {"size_repeats": {}, "tile_repeats": {}, "tile_screen": {},
          "padding_screen": {},
          "tile_bitwise": json.loads((RAW / "tile-bitwise.json").read_text())}
for kind, sizes in (("prefix", (2, 8, 16)), ("top13", (4, 16, 32))):
    for size in sizes:
        endpoints = {}
        for workers in (1, 16):
            xs = samples(f"{kind}-{size * MIB}-w{workers}-repeat-s{{i}}.json")
            assert all(10 <= x["wall"] <= 60 for x in xs)
            endpoints[str(workers)] = stats([x["median_cpu_per_call"] for x in xs])
        result["size_repeats"][f"{kind}-{size}MiB"] = {
            "endpoints": endpoints,
            "cpu_inflation_16_vs_1": endpoints["16"]["median"] / endpoints["1"]["median"],
        }
for workers in (1, 16):
    for rows in (0, 64, 32):
        xs = samples(f"tile-b{rows}-w{workers}-repeat-s{{i}}.json")
        assert all(10 <= x["batch_wall"] <= 60 for x in xs)
        result["tile_repeats"][f"w{workers}-rows{rows}"] = {
            "cpu_per_call": stats([x["median_cpu_per_call"] for x in xs]),
            "sha256": xs[0]["sha256"],
        }
    for rows in (0, 32, 64, 128, 256):
        x = json.loads((RAW / f"tile-b{rows}-w{workers}-screen-s1.json").read_text())
        result["tile_screen"][f"w{workers}-rows{rows}"] = x["median_cpu_per_call"]
    for pad in (0, 4, 32, 64, 256):
        x = json.loads((RAW / f"padding-p{pad}-w{workers}-screen-s1.json").read_text())
        result["padding_screen"][f"w{workers}-pad{pad}"] = x["median_cpu_per_call"]
(ROOT / "processed" / "final.json").write_text(json.dumps(result, indent=2) + "\n")
for key, value in result["size_repeats"].items():
    print(key, round(value["cpu_inflation_16_vs_1"], 3))
for key, value in result["tile_repeats"].items():
    print(key, round(value["cpu_per_call"]["median"] * 1000, 3), "ms")
