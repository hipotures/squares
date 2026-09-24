"""Time the accepted 8-worker solver while VM 207 vCPUs are physically pinned."""

import datetime as dt
import json
import os
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SHARED = Path("/srv/ai/benchmarks/squares-cpu-penalty-test08")
BASELINE = REPO / "Experiments/cpu-post-integration-profile/scripts/baseline.py"
PACKING = REPO / "packing"
OUT = HERE / "full-solver-pinned-w8"


def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    marker = SHARED / "SOLVER8_PINNED"
    if not marker.exists() or (SHARED / "SOLVER8_RESTORE").exists():
        raise RuntimeError("PVE pinning is not active")
    pinned_at = dt.datetime.fromtimestamp(marker.stat().st_mtime, dt.timezone.utc)
    age = (dt.datetime.now(dt.timezone.utc) - pinned_at).total_seconds()
    if not 0 <= age <= 90:
        raise RuntimeError(f"PVE pin marker is stale: {age:.1f} seconds")
    OUT.mkdir(parents=True, exist_ok=True)
    # Restrict the parent and every worker to guest CPUs 0..7, which the
    # temporary PVE control maps onto physical CPUs 0..7 (one L3 domain).
    command = ["taskset", "-c", "0-7", "uv", "run", "--frozen", "python", str(BASELINE),
               "--workers", "8", "--samples", "3", "--target-seconds", "20",
               "--output-dir", str(OUT)]
    environment = dict(os.environ, PYTHONPATH=".", OMP_NUM_THREADS="1",
                       OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    receipt = {"pinned_marker_mtime_utc": pinned_at.isoformat(),
               "started_utc": timestamp(), "command": command}
    try:
        with (OUT / "console.log").open("w") as log:
            result = subprocess.run(command, cwd=PACKING, env=environment,
                                    stdout=log, stderr=subprocess.STDOUT)
        receipt["exit_code"] = result.returncode
        receipt["status"] = "complete" if result.returncode == 0 else "failed"
        if result.returncode:
            raise RuntimeError("pinned full-solver benchmark failed")
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        raise
    finally:
        receipt["finished_utc"] = timestamp()
        (OUT / "run-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        (SHARED / "SOLVER8_RESTORE").write_text(timestamp() + "\n")
        print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()
