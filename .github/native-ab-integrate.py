"""One-use, guarded integration of experimental boundaries into the fork only."""
from pathlib import Path


def edit(path, old, new):
    target = Path(path)
    text = target.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"integration anchor missing or duplicated: {path}: {old[:80]}")
    target.write_text(text.replace(old, new, 1))


base = "packing/src/sqpack/fractional/"
edit(base + "generate.py",
     "from sqpack.fractional._prefix_rows import accumulate_axis0\nfrom sqpack.fractional._top13_selector import select_lowest_finite\n",
     "from sqpack.fractional.native_ab_hooks import (\n    accumulate_axis0, select_lowest_finite, scatter, compact,\n    observe_direction, observe_event_grid, observe_topk,\n)\n")
for name, decorator in (("event_grid", "observe_event_grid"), ("placement_cells", "observe_direction"),
                        ("_least_finite_indices", "observe_topk")):
    edit(base + "generate.py", f"\ndef {name}(", f"\n@{decorator}\ndef {name}(")
edit(base + "generate.py",
     "    np.add.at(grid, (left, bottom), live_w)\n    np.add.at(grid, (right, bottom), -live_w)\n    np.add.at(grid, (left, top), -live_w)\n    np.add.at(grid, (right, top), live_w)\n",
     "    scatter(grid, left, right, bottom, top, live_w)\n")
edit(base + "generate.py",
     "    for row, first, width, offset in zip(row_ids, firsts, widths, offsets, strict=True):\n        values[offset:offset + width] = cells.mass[row, first:first + width]\n",
     "    compact(cells.mass, row_ids, firsts, widths, offsets, values)\n")
edit(base + "colgen.py", "import highspy\n",
     "from sqpack.fractional.native_ab_hooks import observe_lp, observe_vertices, observe_depths, flush_after\n\nimport highspy\n")
for name, decorator in (("_vertices", "observe_vertices"), ("_depths", "observe_depths"),
                        ("_direction_chunk_task", "flush_after")):
    edit(base + "colgen.py", f"\ndef {name}(", f"\n@{decorator}\ndef {name}(")
edit(base + "colgen.py", "    def solve(self, rows: Rows)", "    @observe_lp\n    def solve(self, rows: Rows)")
edit(base + "exact_slabs.py", "from __future__ import annotations\n",
     "from __future__ import annotations\n\nfrom sqpack.fractional.native_ab_hooks import exact_at, exact_cost\n")
edit(base + "exact_slabs.py", "    def at(self, x: Fraction, y: Fraction)",
     "    @exact_at\n    def at(self, x: Fraction, y: Fraction)")
edit(base + "exact_slabs.py", "    def reduced_cost(self, orbit:",
     "    @exact_cost\n    def reduced_cost(self, orbit:")
# Lazy capture avoids serializing complete exact contexts on every query.
edit(base + "native_ab_metrics.py", "    os.close(fd)\n    value =", 
     "    os.close(fd)\n    if callable(payload):\n        payload, arrays = payload()\n    value =")
edit(base + "native_ab_runtime.py", "\ndef parse_selection(text: str)",
     "\n@lru_cache(maxsize=128)\ndef parse_selection(text: str)")
with Path(base + "native_ab_hooks.py").open("a") as handle:
    handle.write('''\n\ndef flush_after(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        finally:
            metrics.flush(force=True)
    return wrapped
''')
edit(base + "native_ab_hooks.py", '"ux": str(direction.ux), "uy": str(direction.uy),',
     '"ux": str(direction.ux), "uy": str(direction.uy),\n                    "vx": str(direction.vx), "vy": str(direction.vy),')
# Preserve native choice on already-owned jobs, but NOT the telemetry directory:
# recovered executions belong to the current session; reused files earn no work.
edit("packing/devtools/frontier_runtime.py", 'if p.suffix in (".py", ".c"))',
     'if p.suffix in (".py", ".c", ".cpp"))')
edit("packing/devtools/frontier_runtime.py",
     '        "PACK_JOBS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"\n',
     '        "PACK_JOBS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",\n        "PACK_NATIVE_KERNELS", "PACK_NATIVE_BUILD_ROOT"\n')
edit("packing/devtools/run_fractional_colgen.py", "import argparse\n", "import argparse\nimport os\n")
edit("packing/devtools/run_fractional_colgen.py", '    result["work_kind"] = "generation"\n',
     '    result["work_kind"] = "generation"\n    if os.environ.get("PACK_NATIVE_SESSION"):\n        from sqpack.fractional import native_ab_runtime, native_ab_metrics\n        result["native_runtime"] = native_ab_runtime.preflight()\n        result["native_session"] = os.environ["PACK_NATIVE_SESSION"]\n        native_ab_metrics.flush(force=True)\n')
print("native A/B call-site integration applied")
