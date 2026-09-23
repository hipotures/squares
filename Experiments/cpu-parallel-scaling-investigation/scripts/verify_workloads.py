#!/usr/bin/env python3
"""Check archived workload bytes and optionally extracted files."""

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifests/workload-sha256.json").read_text())


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--archives-only", action="store_true", help="verify every file by streaming the archives without extraction")
args = parser.parse_args()

files_checked = 0
for entry in manifest["archives"]:
    archive = ROOT / entry["archive"]
    assert archive.stat().st_size == entry["archive_bytes"], archive
    assert sha256(archive) == entry["archive_sha256"], archive
    if args.archives_only:
        expected = {item["restore_path"]: item for item in entry["files"]}
        process = subprocess.Popen(["zstd", "-q", "-dc", str(archive)], stdout=subprocess.PIPE)
        assert process.stdout is not None
        with tarfile.open(fileobj=process.stdout, mode="r|") as members:
            for member in members:
                assert member.isfile(), member.name
                item = expected.pop(member.name)
                assert member.size == item["original_bytes"], member.name
                stream = members.extractfile(member)
                assert stream is not None
                digest = hashlib.sha256()
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
                assert digest.hexdigest() == item["sha256"], member.name
                files_checked += 1
        assert process.wait() == 0, archive
        assert not expected, sorted(expected)
    else:
        base = ROOT / entry["restore_into"]
        for item in entry["files"]:
            path = base / item["restore_path"]
            assert path.is_file(), f"extract archives first: {path}"
            assert path.stat().st_size == item["original_bytes"], path
            assert sha256(path) == item["sha256"], path
            files_checked += 1
print(f"Verified {len(manifest['archives'])} archives and {files_checked} original files")
