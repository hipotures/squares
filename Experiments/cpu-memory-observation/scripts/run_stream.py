#!/usr/bin/env python3
"""Run independent guest-visible STREAM-like samples and persist JSONL."""
import json, pathlib, subprocess, sys, time

root = pathlib.Path(__file__).resolve().parents[1]
binary = root / "raw/stream_guest"
raw = root / "raw"
raw.mkdir(parents=True, exist_ok=True)
with (raw / "stream-samples.jsonl").open("w") as out:
    for op in ("read", "copy", "write", "triad"):
        for workers in (1, 2, 4, 8, 16):
            for sample in (1, 2, 3):
                start = time.time()
                result = subprocess.run([str(binary), str(workers), "384", "10", op], check=True, text=True, capture_output=True)
                row = json.loads(result.stdout)
                row.update(sample=sample, start_unix_s=start, cpu_affinity=f"{workers} workers on CPUs 0-{workers-1}")
                out.write(json.dumps(row, sort_keys=True) + "\n"); out.flush()
                print(f"{op} w{workers} s{sample}: {row['gb_s_decimal']:.2f} GB/s", flush=True)
