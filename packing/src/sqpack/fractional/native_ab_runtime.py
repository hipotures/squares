"""Experimental native selection, explicit local build, and checked C ABI.

No compilation on import, no native threads, and no silent missing-library
fallback. `none` disables even the two previously accepted C helpers for an
unambiguous Python/NumPy reference. HiGHS and NumPy themselves remain native.
"""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import tempfile
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np

KERNELS = ("prefix", "topk", "scatter", "compact", "vertices", "exact-depth")
SOURCES = ("native_ab_core.c", "_prefix_rows_native.c", "_top13.c", "native_ab_exact.cpp")
FLAGS = ("-O3", "-fno-fast-math", "-ffp-contract=off", "-fPIC", "-shared")


def parse_selection(text: str) -> tuple[str, ...]:
    if text == "none":
        return ()
    if text == "all":
        return KERNELS
    if text == "production":
        return ("prefix", "topk")
    names = text.split(",")
    if not names or any(name not in KERNELS for name in names):
        raise ValueError(f"unknown native selection {text!r}; use none, all, production or {KERNELS}")
    if len(set(names)) != len(names):
        raise ValueError("duplicate native switch")
    return tuple(name for name in KERNELS if name in names)


def selection() -> tuple[str, ...]:
    return parse_selection(os.environ.get("PACK_NATIVE_KERNELS", "none"))


def enabled(name: str) -> bool:
    return name in selection()


def source_digest() -> str:
    h = hashlib.sha256()
    for name in SOURCES:
        h.update(name.encode())
        h.update(Path(__file__).with_name(name).read_bytes())
    h.update(repr(FLAGS).encode())
    return h.hexdigest()


def build_directory() -> Path:
    base = Path(os.environ.get("PACK_NATIVE_BUILD_ROOT", str(Path.home() / ".cache/squares-native-ab")))
    return base / f"{platform.system()}-{platform.machine()}-{source_digest()[:24]}"


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def build(*, core_only: bool = False) -> dict:
    if sys.platform != "linux":
        raise RuntimeError("the native A/B build currently targets Linux only")
    directory = build_directory()
    directory.mkdir(parents=True, exist_ok=True)
    sources = Path(__file__).parent
    metadata = {"schema": 1, "abi": 1, "source_sha256": source_digest(), "libraries": {}}
    targets = [("core", os.environ.get("CC", "cc"), "-std=c11", SOURCES[:3])]
    if not core_only:
        targets.append(("exact", os.environ.get("CXX", "c++"), "-std=c++17", SOURCES[3:]))
    for name, compiler, standard, files in targets:
        with tempfile.TemporaryDirectory(dir=directory) as temp:
            output = Path(temp) / f"{name}.so"
            command = [*shlex.split(compiler), standard, *FLAGS,
                       *(str(sources / f) for f in files), "-o", str(output)]
            version = subprocess.run([*shlex.split(compiler), "--version"], check=True,
                                     capture_output=True, text=True).stdout
            completed = subprocess.run(command, capture_output=True, text=True)
            if completed.returncode:
                raise RuntimeError(
                    f"native {name} build failed; exact-depth requires Boost headers "
                    f"(Ubuntu: libboost-dev). Use build --core-only for other switches.\n{completed.stderr}"
                )
            target = directory / f"{name}.so"
            output.replace(target)
            metadata["libraries"][name] = {"path": str(target), "compiler": version,
                "command": command, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    atomic_json(directory / "build.json", metadata)
    library.cache_clear()
    return metadata


@lru_cache(maxsize=4)
def library(name: str) -> ct.CDLL:
    directory = build_directory()
    try:
        meta = json.loads((directory / "build.json").read_text())
        info = meta["libraries"][name]
        path = directory / f"{name}.so"
        if meta["source_sha256"] != source_digest() or hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
            raise ValueError("native binary/source identity mismatch")
    except (OSError, KeyError, ValueError) as exc:
        raise RuntimeError("selected native kernel is unavailable; run python -m devtools.native_ab build") from exc
    lib = ct.CDLL(str(path))
    p, z, i = ct.c_void_p, ct.c_size_t, ct.c_int
    if name == "core":
        lib.ab_version.restype = i
        if lib.ab_version() != 1:
            raise RuntimeError("native core ABI mismatch")
        lib.prefix_axis0_rowmajor.argtypes = [p, z, z]
        lib.prefix_axis0_rowmajor.restype = None
        lib.topk_finite.argtypes = [p, z, z, p]
        lib.topk_finite.restype = z
        lib.ab_scatter.argtypes = [p, z, z, p, p, p, p, p, z]
        lib.ab_scatter.restype = i
        lib.ab_compact.argtypes = [p, z, z, z, p, p, p, p, z, p, z]
        lib.ab_compact.restype = i
        lib.ab_vertices.argtypes = [p, z, ct.c_double, p, p, z]
        lib.ab_vertices.restype = z
    else:
        lib.ab_exact_version.restype = i
        if lib.ab_exact_version() != 1:
            raise RuntimeError("native exact ABI mismatch")
        lib.ab_exact_create.argtypes = [ct.c_char_p]
        lib.ab_exact_create.restype = p
        lib.ab_exact_query.argtypes = [p, ct.c_char_p, i]
        lib.ab_exact_query.restype = p
        lib.ab_exact_destroy.argtypes = [p]
        lib.ab_exact_destroy.restype = None
        lib.ab_exact_free_string.argtypes = [p]
        lib.ab_exact_free_string.restype = None
        lib.ab_exact_error.restype = ct.c_char_p
    return lib


def preflight() -> dict:
    selected = selection()
    for name in ({"core"} if any(k != "exact-depth" for k in selected) else set()) | ({"exact"} if "exact-depth" in selected else set()):
        library(name)
    result = {"kernels": list(selected), "source_sha256": source_digest(),
              "baseline": "Python/NumPy references; HiGHS and NumPy are still native",
              "threads_per_native_call": 1}
    if selected:
        result["build"] = json.loads((build_directory() / "build.json").read_text())
    return result


def pointer(array: np.ndarray) -> int:
    return int(array.ctypes.data)


def int_array(values: np.ndarray) -> np.ndarray:
    if values.dtype.kind not in "iu" or values.ndim != 1:
        raise ValueError("native indices must be one-dimensional integers")
    if values.dtype.kind == "u" and values.size and int(values.max()) > np.iinfo(np.int64).max:
        raise ValueError("native index exceeds int64")
    return np.ascontiguousarray(values, dtype=np.int64)


def require_float(array: np.ndarray, ndim: int, *, contiguous: bool = True, writable: bool = False) -> None:
    if (array.dtype != np.float64 or array.ndim != ndim
            or (contiguous and not array.flags.c_contiguous)
            or (writable and not array.flags.writeable)):
        raise ValueError("native array dtype/layout/writeability precondition failed")


class ExactDepth:
    def __init__(self, weighted: tuple) -> None:
        self.lib = library("exact")
        rows = [str(len(weighted))]
        for first, second, weight in weighted:
            rows.append(" ".join(str(v) for v in (*first, *second, weight.numerator, weight.denominator)))
        self.handle = self.lib.ab_exact_create("\n".join(rows).encode("ascii"))
        if not self.handle:
            raise RuntimeError(self.lib.ab_exact_error().decode())

    def query(self, points: tuple, mode: int = 0) -> Fraction:
        rows = [str(len(points)), *(" ".join(map(str, p)) for p in points)]
        value = self.lib.ab_exact_query(self.handle, "\n".join(rows).encode("ascii"), mode)
        if not value:
            raise RuntimeError(self.lib.ab_exact_error().decode())
        try:
            return Fraction(ct.string_at(value).decode("ascii"))
        finally:
            self.lib.ab_exact_free_string(value)

    def __del__(self) -> None:
        handle = getattr(self, "handle", None)
        if handle:
            self.lib.ab_exact_destroy(handle)
            self.handle = None
