"""Prepare fixed long-duration 8/16-worker host/VM retest after short host sample.

The selected computation and captured data are unchanged. Expected checksums
are derived from the recorded per-direction selection hashes using the same
FNV-1a combination as replay.c, then checked against the original plan.
"""

import hashlib
import json
import shutil
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "package"
PACKAGE = HERE / "package"
MASK = (1 << 64) - 1
OFFSET = 14695981039346656037
PRIME = 1099511628211
REPEATS = {"8": 350, "16": 620}


def fnv_u64(value: int, state: int) -> int:
    for byte in value.to_bytes(8, "little"):
        state = ((state ^ byte) * PRIME) & MASK
    return state


def checksum(selection_hashes: list[int], workers: int, repeats: int) -> str:
    combined = OFFSET
    for worker in range(workers):
        state = OFFSET
        subset = selection_hashes[worker::workers]
        for _ in range(repeats):
            for selected in subset:
                state = fnv_u64(selected, state)
        combined = fnv_u64(state, combined)
    return f"{combined:016x}"


def main() -> None:
    manifest = json.loads((ORIGINAL / "manifest.json").read_text())
    old = json.loads((ORIGINAL / "plan.json").read_text())
    hashes = [int(item["selection_fnv64"], 16) for item in manifest["cases"]]
    for workers, repeats in old["repeats"].items():
        assert checksum(hashes, int(workers), repeats) == old["expected_checksums"][workers]

    PACKAGE.mkdir(parents=True, exist_ok=True)
    for name in ("replay.c", "data.bin", "manifest.json"):
        link = PACKAGE / name
        if not link.exists():
            link.symlink_to(Path("..") / ".." / "package" / name)
    shutil.copy2(ORIGINAL / "run.py", PACKAGE / "run.py")
    new = dict(old)
    new["repeats"] = dict(old["repeats"])
    new["expected_checksums"] = dict(old["expected_checksums"])
    new["retest_reason"] = ("Original host w8 sample lasted 7.902868434 s; "
                            "fixed repeats increased for w8/w16 on both machines.")
    new["original_plan_repeats"] = old["repeats"]
    for workers, repeats in REPEATS.items():
        new["repeats"][workers] = repeats
        new["expected_checksums"][workers] = checksum(hashes, int(workers), repeats)
    (PACKAGE / "plan.json").write_text(json.dumps(new, indent=2) + "\n")

    archive = HERE / "package.tar.gz"
    with tarfile.open(archive, "w:gz", dereference=True) as output:
        for name in ("replay.c", "data.bin", "manifest.json", "run.py", "plan.json"):
            output.add(PACKAGE / name, arcname=name, recursive=False)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (HERE / "package.sha256").write_text(f"{digest}  package.tar.gz\n")
    print(json.dumps({"repeats": REPEATS,
                      "checksums": {workers: new["expected_checksums"][workers]
                                    for workers in REPEATS},
                      "archive_sha256": digest,
                      "archive_bytes": archive.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
