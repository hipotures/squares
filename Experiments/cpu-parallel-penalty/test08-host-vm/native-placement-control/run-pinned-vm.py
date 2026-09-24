"""Run the fixed native VM control while PVE pins VM 207 vCPUs 0..15."""

import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "tail-retest" / "package"
SHARED = Path("/srv/ai/benchmarks/squares-cpu-penalty-test08")
OUT = HERE / "vm-results"


def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    marker = SHARED / "NATIVE_PINNED"
    if not marker.exists():
        raise RuntimeError("PVE has not published NATIVE_PINNED")
    if (SHARED / "NATIVE_RESTORE").exists():
        raise RuntimeError("PVE restore marker already exists")
    pinned_at = dt.datetime.fromisoformat(marker.read_text().strip())
    age = (dt.datetime.now(dt.timezone.utc) - pinned_at).total_seconds()
    if not 0 <= age <= 90:
        raise RuntimeError(f"PVE pin marker is stale: {age:.1f} seconds")
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = {"pinned_marker": marker.read_text().strip(),
               "started_utc": timestamp(), "endpoints": []}
    environment = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                       MKL_NUM_THREADS="1")
    try:
        for workers in (8, 16):
            start = time.monotonic()
            command = [sys.executable, str(PACKAGE / "run.py"),
                       "--outdir", str(OUT), "--only", str(workers)]
            with (OUT / f"console-w{workers}.log").open("w") as log:
                process = subprocess.run(command, cwd=PACKAGE, env=environment,
                                         stdout=log, stderr=subprocess.STDOUT)
            receipt["endpoints"].append({"workers": workers, "command": command,
                                         "exit_code": process.returncode,
                                         "elapsed_seconds": time.monotonic() - start,
                                         "ended_utc": timestamp()})
            if process.returncode:
                raise RuntimeError(f"pinned VM endpoint workers={workers} failed")
        receipt["status"] = "complete"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        raise
    finally:
        receipt["finished_utc"] = timestamp()
        (OUT / "run-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        (SHARED / "NATIVE_RESTORE").write_text(timestamp() + "\n")
        print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()
