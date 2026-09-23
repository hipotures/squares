"""Connect fresh captured row workload to the accepted exact witness record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / "cpu-optimization-integration/raw/m5-full-state.json"


def digest(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def main() -> None:
    saved = np.load(ROOT / "raw/current-states.npz")
    reference = json.loads(OLD.read_text())
    hashes = {
        "directions_sha256": digest(saved["directions"].astype(np.int32)),
        "centres_sha256": digest(saved["centres"].astype(np.float64)),
        "matrix_sha256": digest(load_npz(ROOT / "raw/current-rows-csr.npz").toarray()),
        "weights_sha256": digest(saved["weights"][-1]),
    }
    same = {name: hashes[name] == reference[name] for name in hashes}
    assert all(same.values()), same
    data = {"reference_file": str(OLD.relative_to(ROOT.parent.parent)),
            "hashes": hashes, "matches_accepted_M5": same, "passed": True}
    (ROOT / "raw/current-identity.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
