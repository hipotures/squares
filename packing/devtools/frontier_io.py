"""Durable, bounded records shared by the unattended frontier tools."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

MAX_RECORD_BYTES = 64 * 1024 * 1024


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, record: dict[str, Any]) -> None:
    atomic_text(path, json.dumps(record, indent=2, allow_nan=False) + "\n")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise ValueError(f"duplicate record key: {key}")
        record[key] = value
    return record


def _nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def read_json(path: Path, limit: int = MAX_RECORD_BYTES) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"record exceeds {limit} bytes: {path}")
    value = json.loads(data, object_pairs_hook=_unique, parse_constant=_nonfinite)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()
