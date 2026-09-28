"""Pinned external checks for closed-unit-square covers; not the fixed-B gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

from sqpack.fractional.hybrid_support import UPSTREAM, load_measure

REPO = Path(__file__).resolve().parents[2]
EXTERNAL = REPO / "Experiments/hybrid-dependencies/evand-square-packing"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_identity(root: Path) -> dict[str, str]:
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != UPSTREAM:
        raise ValueError("external checkout is not at the pinned revision")
    dirty = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty.strip():
        raise ValueError("external tracked source has local changes")
    sources = sorted((root / "s12/verify/src").rglob("*.rs"))
    sources += [root / "s12/verify/Cargo.toml", root / "s12/verify/Cargo.lock", root / "s12/xcheck.py"]
    return {str(path.relative_to(root)): digest(path) for path in sources}


def checked_binary(root: Path) -> Path:
    identity = source_identity(root)
    binary = root / "s12/verify/target/release/verify"
    stamp = binary.with_name("hybrid-build.json")
    record = json.loads(stamp.read_text())
    if record != {"source": identity, "binary": digest(binary)}:
        raise ValueError("external binary is missing, changed or not bound to its source; run prepare-external")
    return binary


def run_logged(command: list[str], path: Path, seconds: float, *, cwd: Path | None = None) -> tuple[int, str]:
    if seconds <= 0:
        raise TimeoutError("external checker budget exhausted")
    path.parent.mkdir(parents=True, exist_ok=True)
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("VERIFY_", "TIGHT_"))}
    environment.pop("PYTHONOPTIMIZE", None)
    managed = bool(environment.get("SQUARES_FRONTIER_JOB_TOKEN"))
    with path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=log,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   start_new_session=not managed)
        try:
            code = process.wait(timeout=seconds)
        except BaseException:
            if process.poll() is None:
                if managed:
                    from devtools.frontier_runtime import owned_members, process_info
                    members = owned_members(None, environment["SQUARES_FRONTIER_JOB_TOKEN"])
                    descendants = {process.pid}
                    while True:
                        expanded = descendants | {m["pid"] for m in members if m["ppid"] in descendants}
                        if expanded == descendants:
                            break
                        descendants = expanded
                    for member in reversed(members):
                        current = process_info(member["pid"])
                        if member["pid"] in descendants and current and current["ticks"] == member["ticks"]:
                            try:
                                os.kill(member["pid"], signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                    if process.poll() is None:
                        process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    return code, path.read_text(encoding="utf-8")


def prepare(root: Path, log: Path, seconds: float) -> dict[str, Any]:
    deadline = time.monotonic() + seconds
    if not root.exists():
        root.parent.mkdir(parents=True, exist_ok=True)
        commands = [
            ["git", "clone", "--no-checkout", "--filter=blob:none", "--sparse", "https://github.com/evand/square-packing", str(root)],
            ["git", "-C", str(root), "sparse-checkout", "set", "s12"],
            ["git", "-C", str(root), "fetch", "--depth=1", "origin", UPSTREAM],
            ["git", "-C", str(root), "checkout", "--detach", UPSTREAM],
        ]
        for i, command in enumerate(commands):
            code, _ = run_logged(command, log.with_name(f"checkout-{i}.log"), deadline - time.monotonic())
            if code:
                raise RuntimeError("pinned external checkout failed; inspect checkout logs")
    identity = source_identity(root)
    code, _ = run_logged(["cargo", "build", "--release", "--locked"], log, deadline - time.monotonic(), cwd=root / "s12/verify")
    if code or identity != source_identity(root):
        raise RuntimeError("external build failed or source changed during the build")
    binary = root / "s12/verify/target/release/verify"
    record = {"source": identity, "binary": digest(binary)}
    from devtools.frontier_io import atomic_json
    atomic_json(binary.with_name("hybrid-build.json"), record)
    return record


def minimum(text: str, *, python_checker: bool = False) -> Fraction:
    pattern = (r"^minimum covered weight over ALL bins = ([0-9]+(?:/[1-9][0-9]*)?)\s*="
               if python_checker else
               r"^min covered weight over ALL placements = ([0-9]+/[1-9][0-9]*)\s*=")
    found = re.findall(pattern, text, re.MULTILINE)
    if len(found) != 1 or any(word in text for word in ("PARTIAL", "SAMPLED", "ERROR:", "panicked")):
        raise ValueError("checker did not return one complete exact minimum")
    return Fraction(found[0])


def check_cover(source: Path, root: Path, directory: Path, side: Fraction,
                *, net: int = 6000, workers: int = 1, seconds: float = 7200) -> dict[str, Any]:
    """Rust at N and 2N, plus independent exhaustive Python at N, on frozen bytes."""
    from devtools.frontier_io import atomic_json
    measure = load_measure(source)
    if measure.side != side or not 1 < side < 4 or not 3 <= net <= 200_000 or workers < 1:
        raise ValueError("invalid closed-cover verification request")
    directory.mkdir(parents=True, exist_ok=True)
    binary = checked_binary(root)
    identity = source_identity(root)
    executable_hash = digest(binary)
    report: dict[str, Any] = {
        "schema": "hybrid-closed-cover-gate/v1", "status": "REJECTED", "side": str(side),
        "mass": str(measure.mass), "source_sha256": measure.sha256,
        "upstream": UPSTREAM, "checker_sources": identity, "binary_sha256": executable_hash,
        "net": net, "workers": workers, "checks": [], "finished": False,
    }
    deadline = time.monotonic() + seconds
    if measure.mass < 12:
        for name, nnet, python_checker in (("rust-N", net, False), ("rust-2N", 2 * net, False), ("python-N", net, True)):
            command = ([sys.executable, str(root / "s12/xcheck.py"), str(source), str(nnet), "--all", "--n", "12", "-j", str(workers)]
                       if python_checker else [str(binary), str(source), "12", str(nnet), str(workers), "0"])
            started = time.monotonic()
            code, text = run_logged(command, directory / f"{name}.log", deadline - started)
            value = minimum(text, python_checker=python_checker)
            accepted = code == 0 and value >= 1 and "\nVERIFIED:" in "\n" + text and "NOT VERIFIED" not in text
            report["checks"].append({"name": name, "minimum": str(value), "accepted": accepted,
                                     "seconds": time.monotonic() - started})
            if not accepted:
                break
        checks = report["checks"]
        if len(checks) == 3 and all(c["accepted"] for c in checks):
            if Fraction(checks[0]["minimum"]) != Fraction(checks[2]["minimum"]):
                raise ValueError("independent checkers disagree on the exact minimum")
            if (digest(source) != measure.sha256 or identity != source_identity(root)
                    or digest(binary) != executable_hash):
                raise ValueError("source or checker changed during verification")
            verified = directory / "closed-cover.verified.txt"
            verified.write_bytes(source.read_bytes())
            report.update(status="VERIFIED", verified_candidate=str(verified), verified_sha256=digest(verified),
                          claim=f"s(12) >= {side}")
    report["finished"] = True
    atomic_json(directory / "verification.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--side", type=Fraction, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--external-root", type=Path, default=EXTERNAL)
    parser.add_argument("--net", type=int, default=6000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=7200)
    args = parser.parse_args(argv)
    report = check_cover(args.input.resolve(), args.external_root.resolve(), args.report.parent.resolve(), args.side,
                         net=args.net, workers=args.workers, seconds=args.seconds)
    from devtools.frontier_io import atomic_json
    atomic_json(args.report, report)
    print(json.dumps(report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
