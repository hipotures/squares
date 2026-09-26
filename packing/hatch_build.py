# pyright: reportMissingImports=false
"""Build the accepted native production core into platform installs and wheels.

Compilation happens during package creation, never while the solver runs.
The combined prefix/top-k/scatter/compact core is required on supported
platforms; the older standalone prefix/top-k libraries are retained only for
compatibility with existing callers. Editable builds place binaries beside
the source modules.
"""

from __future__ import annotations

import os
import platform
import shlex
import subprocess
import warnings
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if self.target_name != "wheel":
            return
        system = platform.system()
        if system not in {"Linux", "Darwin"}:
            return
        suffix = ".dylib" if system == "Darwin" else ".so"
        package = Path(self.root) / "src/sqpack/fractional"
        for stem in ("_top13", "_prefix_rows_native"):
            source = package / f"{stem}.c"
            name = f"{stem}{suffix}"
            target = (
                package / name
                if version == "editable"
                else Path(self.directory) / "sqpack-native-build" / name
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.unlink(missing_ok=True)
            command = [
                *shlex.split(os.environ.get("CC", "cc")),
                "-O3",
                *(["-dynamiclib"] if system == "Darwin" else ["-fPIC", "-shared"]),
                "-o", str(target), str(source),
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
            except (OSError, subprocess.CalledProcessError) as exc:
                warnings.warn(
                    f"CPU {stem} native build unavailable; using NumPy fallback: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                continue
            wheel_path = f"sqpack/fractional/{name}"
            build_data["force_include"][str(target)] = wheel_path
            if version == "editable":
                build_data["force_include_editable"][str(target)] = wheel_path
            build_data["infer_tag"] = True
            build_data["pure_python"] = False

        core_name = f"_native_ab_core{suffix}"
        core_target = (
            package / core_name
            if version == "editable"
            else Path(self.directory) / "sqpack-native-build" / core_name
        )
        core_target.parent.mkdir(parents=True, exist_ok=True)
        core_target.unlink(missing_ok=True)
        core_command = [
            *shlex.split(os.environ.get("CC", "cc")),
            "-std=c11",
            "-O3",
            "-fno-fast-math",
            "-ffp-contract=off",
            *(["-dynamiclib"] if system == "Darwin" else ["-fPIC", "-shared"]),
            "-o",
            str(core_target),
            str(package / "native_ab_core.c"),
            str(package / "_prefix_rows_native.c"),
            str(package / "_top13.c"),
        ]
        try:
            subprocess.run(core_command, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                "required native production core could not be built; install a C compiler"
            ) from exc
        wheel_path = f"sqpack/fractional/{core_name}"
        build_data["force_include"][str(core_target)] = wheel_path
        if version == "editable":
            build_data["force_include_editable"][str(core_target)] = wheel_path
        build_data["infer_tag"] = True
        build_data["pure_python"] = False
