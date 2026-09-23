#!/usr/bin/env python3
"""Package the preserved captured and synthetic workload bytes with SHA-256s.

Usage: python scripts/archive_workloads.py SOURCE_RESEARCH_DIRECTORY
The source is the completed local investigation under packing/benchmarks/.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIMIT = 50 * 1024 * 1024
CAPTURE = "squares-numpy-capture-20260923"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package(source_base: Path, archive_name: str, files: list[Path], restore_base: Path) -> dict:
    archive = ROOT / "workloads" / archive_name
    rels = [p.relative_to(restore_base).as_posix() for p in files]
    originals = [
        {"restore_path": rel, "original_bytes": path.stat().st_size, "sha256": sha256(path)}
        for path, rel in zip(files, rels)
    ]
    command = [
        "tar", "--sort=name", "--mtime=@0", "--owner=0", "--group=0",
        "--numeric-owner", "-I", "zstd -3", "-cf", str(archive),
        "-C", str(restore_base), *rels,
    ]
    subprocess.run(command, check=True)
    subprocess.run(["zstd", "-q", "-t", str(archive)], check=True)
    compressed_size = archive.stat().st_size
    if compressed_size > LIMIT:
        raise RuntimeError(f"{archive_name}: {compressed_size} bytes exceeds 50 MiB")
    return {
        "archive": f"workloads/{archive_name}",
        "archive_bytes": compressed_size,
        "archive_sha256": sha256(archive),
        "original_bytes_total": sum(item["original_bytes"] for item in originals),
        "restore_into": "raw/" if source_base.name == "raw" else "workloads/",
        "files": originals,
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    source = Path(sys.argv[1]).resolve()
    capture_root = source / "raw" / CAPTURE
    synthetic_root = source / "workloads"
    if not (capture_root / "manifest.json").is_file():
        raise FileNotFoundError(capture_root / "manifest.json")
    entries = []
    round0 = sorted(capture_root.glob("r00_*.npy"))
    entries.append(package(source / "raw", "capture-round00.tar.zst", [capture_root / "manifest.json", *round0], source / "raw"))
    late = sorted(capture_root.glob("r18_*.npy"))
    # Groups of 18 directions (36 arrays) keep each Git blob far below 50 MiB.
    for start in range(0, 181, 18):
        stop = min(start + 18, 181)
        group = [p for p in late if start <= int(p.name[5:8]) < stop]
        if group:
            entries.append(package(source / "raw", f"capture-round18-{start:03d}-{stop-1:03d}.tar.zst", group, source / "raw"))
    synthetic = sorted(p for p in synthetic_root.iterdir() if p.is_file() and p.suffix in {".npy", ".bin"})
    entries.append(package(source / "workloads", "synthetic-workloads.tar.zst", synthetic, source / "workloads"))
    manifest = {
        "format": "lossless tar archives compressed with zstd -3",
        "size_limit_bytes": LIMIT,
        "archives": entries,
        "excluded_over_50_mib": [],
    }
    out = ROOT / "manifests" / "workload-sha256.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(entries)} archives, {sum(len(e['files']) for e in entries)} original files, {sum(e['archive_bytes'] for e in entries)} compressed bytes")


if __name__ == "__main__":
    main()
