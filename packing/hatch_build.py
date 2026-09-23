# pyright: reportMissingImports=false
"""Build optional CPU selector and prefix libraries into platform wheels.

Compilation happens during wheel creation, never when the solver runs. A
missing compiler leaves a pure Python wheel whose helpers use NumPy fallback
paths. Editable builds place the libraries beside the source modules.
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
