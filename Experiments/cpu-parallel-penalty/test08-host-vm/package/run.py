"""Standard-library host/VM runner for the identical fixed-iteration native replay."""

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "replay.c"
DATA = HERE / "data.bin"
MANIFEST = HERE / "manifest.json"
BINARY = HERE / "replay"
FLAGS = ["-O3", "-std=c11", "-fno-fast-math", "-march=x86-64-v3", "-mtune=generic"]
EVENTS = "instructions,cycles,ls_any_fills_from_sys.all_dram_io"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    command = ["cc", *FLAGS, "-o", str(BINARY), str(SOURCE), "-lm"]
    subprocess.run(command, check=True)
    return command


def environment(build_command=None):
    cpuinfo = Path("/proc/cpuinfo").read_text()
    flags_line = next((x for x in cpuinfo.splitlines() if x.startswith("flags")), "")
    flags = flags_line.split(":", 1)[-1].split()
    if "avx2" not in flags:
        raise RuntimeError("x86-64-v3 AVX2 feature is not exposed on this machine")
    pmu_dir = Path("/sys/bus/event_source/devices")
    pmus = sorted(x.name for x in pmu_dir.iterdir()) if pmu_dir.exists() else []
    return {"host": platform.node(), "kernel": platform.release(),
            "cpu_model": next((x.split(":", 1)[1].strip() for x in
                              cpuinfo.splitlines() if x.startswith("model name")), ""),
            "cpu_flags": flags, "avx2_available": True,
            "physical_memory_pmu_devices": [x for x in pmus if "umc" in x or "df" in x],
            "all_pmu_devices": pmus,
            "lscpu_json": subprocess.run(["lscpu", "-J"], capture_output=True,
                                          text=True, check=True).stdout,
            "lscpu_extended": subprocess.run(["lscpu", "-e"], capture_output=True,
                                              text=True, check=True).stdout,
            "compiler": subprocess.run(["cc", "--version"], capture_output=True,
                                        text=True, check=True).stdout.splitlines()[0],
            "build_command": build_command,
            "build_flags": FLAGS,
            "source_sha256": digest(SOURCE), "data_sha256": digest(DATA),
            "binary_sha256": digest(BINARY),
            "manifest_sha256": digest(MANIFEST),
            "perf_version": subprocess.run(["perf", "--version"], capture_output=True,
                                           text=True).stdout.strip(),
            "perf_event_paranoid": Path("/proc/sys/kernel/perf_event_paranoid").read_text().strip()}


def parse_perf(path):
    counters = {}
    for row in csv.reader(path.read_text().splitlines()):
        if len(row) > 4 and row[0] and not row[0].startswith("#"):
            try:
                counters[row[2]] = {"count": float(row[0]),
                                    "running_percent": float(row[4])}
            except ValueError:
                counters[row[2]] = {"raw": row}
    return counters


def once(workers, repeats, outdir, label, with_perf):
    command = [str(BINARY), "--data", str(DATA), "--workers", str(workers),
               "--repeats", str(repeats)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
    line = process.stdout.readline().strip()
    if not line.startswith("READY "):
        error = process.stderr.read()
        raise RuntimeError(f"native warmup failed: {line!r} {error}")
    pids = [int(x) for x in line.removeprefix("READY ").split(",")]
    assert len(pids) == workers
    load = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "loadavg": os.getloadavg(),
            "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip()}
    perf = None
    perf_path = outdir / f"perf-{label}-w{workers}.csv"
    if with_perf:
        perf = subprocess.Popen(["perf", "stat", "-x,", "--no-big-num", "-e", EVENTS,
                                 "-p", ",".join(str(p) for p in pids), "-o", str(perf_path)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(0.3)
        if perf.poll() is not None:
            stderr = perf.stderr.read()
            process.stdin.close()
            process.terminate()
            raise RuntimeError(f"perf attach failed: {stderr}")
    start = time.perf_counter()
    process.stdin.write("\n")
    process.stdin.flush()
    result_line = process.stdout.readline().strip()
    external_wall = time.perf_counter() - start
    stderr = process.stderr.read()
    code = process.wait(timeout=30)
    if perf is not None:
        perf.send_signal(signal.SIGINT)
        _, perf_stderr = perf.communicate(timeout=10)
        if perf.returncode not in (0, -signal.SIGINT):
            raise RuntimeError(f"perf failed: {perf_stderr}")
    if code or not result_line.startswith("RESULT "):
        raise RuntimeError(f"replay failed exit={code} stdout={result_line!r} stderr={stderr}")
    result = json.loads(result_line.removeprefix("RESULT "))
    assert result["workers"] == workers and result["repeats"] == repeats
    assert result["directions"] == 181 and result["calls"] == 181 * repeats
    record = {"label": label, "workers": workers, "repeats": repeats,
              "load_before": load, "native": result, "external_wall": external_wall,
              "command": command, "perf_events_requested": EVENTS if with_perf else None,
              "perf_counters": parse_perf(perf_path) if with_perf else None,
              "perf_stderr": perf_stderr if with_perf else None}
    if with_perf:
        assert all(value.get("running_percent", 0) >= 99.5
                   for value in record["perf_counters"].values())
        assert 10 <= result["wall"] <= 60, result["wall"]
    path = outdir / f"{label}-w{workers}.json"
    path.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"label": label, "workers": workers, "repeats": repeats,
                      "wall": result["wall"], "worker_cpu": result["worker_cpu"],
                      "checksum": result["checksum"]}), flush=True)
    return record


def calibrate(outdir, target):
    plan = {"target_seconds": target, "samples": 3, "repeats": {},
            "expected_checksums": {}, "calibration": {},
            "source_sha256": digest(SOURCE), "data_sha256": digest(DATA)}
    for workers in (1, 2, 4, 8, 16):
        # The short run sets only iteration count; it is never performance evidence.
        trial = once(workers, 4, outdir, "calibration", False)
        wall_per_replay = trial["native"]["wall"] / 4
        repeats = math.ceil(target / wall_per_replay)
        if repeats * wall_per_replay > 55:
            repeats = max(1, int(55 / wall_per_replay))
        plan["repeats"][str(workers)] = repeats
        plan["calibration"][str(workers)] = {"wall_per_replay": wall_per_replay,
                                             "estimated_sample_wall": repeats * wall_per_replay}
        # Fixed iteration counts make cross-machine worker checksums comparable.
        receipt = once(workers, repeats, outdir, "plan-check", False)
        plan["expected_checksums"][str(workers)] = receipt["native"]["checksum"]
    (HERE / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print("plan", HERE / "plan.json", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--calibrate", action="store_true")
    p.add_argument("--target-seconds", type=float, default=25)
    p.add_argument("--only", type=int, choices=(1, 2, 4, 8, 16))
    args = p.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    build_command = build()
    manifest = json.loads(MANIFEST.read_text())
    if digest(DATA) != manifest["data_sha256"]:
        raise RuntimeError("captured input SHA-256 mismatch")
    (args.outdir / "environment.json").write_text(
        json.dumps(environment(build_command), indent=2) + "\n")
    if args.calibrate:
        calibrate(args.outdir, args.target_seconds)
        return
    plan = json.loads((HERE / "plan.json").read_text())
    assert plan["source_sha256"] == digest(SOURCE)
    assert plan["data_sha256"] == digest(DATA)
    workers_list = [args.only] if args.only else (1, 2, 4, 8, 16)
    for workers in workers_list:
        repeats = plan["repeats"][str(workers)]
        for sample in range(1, plan["samples"] + 1):
            result = once(workers, repeats, args.outdir, f"sample{sample}", True)
            expected = plan["expected_checksums"][str(workers)]
            if result["native"]["checksum"] != expected:
                raise RuntimeError(f"cross-machine checksum mismatch at workers={workers}")


if __name__ == "__main__":
    main()
