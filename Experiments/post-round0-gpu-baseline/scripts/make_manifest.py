#!/usr/bin/env python3
"""Write size and SHA-256 inventory for this experiment, excluding itself."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dest = root / "manifests/artifacts.json"
files = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path != dest and "__pycache__" not in path.parts:
        data = path.read_bytes()
        files.append({"path": str(path.relative_to(root)), "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()})
dest.write_text(json.dumps({"files": files, "total_bytes": sum(x["bytes"] for x in files),
                            "largest_bytes": max(x["bytes"] for x in files)}, indent=2) + "\n")
