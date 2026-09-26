"""Keep filesystem hashing out of hot calls and attribute measured profiles."""
from pathlib import Path


def edit(path, old, new):
    p = Path(path)
    s = p.read_text()
    if s.count(old) != 1:
        raise RuntimeError(f"missing or duplicated anchor: {path}: {old[:60]}")
    p.write_text(s.replace(old, new, 1))


root = "packing/src/sqpack/fractional/"
edit(root + "native_ab_runtime.py", "\ndef source_digest() -> str:\n",
     "\n@lru_cache(maxsize=1)\ndef source_digest() -> str:\n")
edit(root + "native_ab_runtime.py", 'def build(*, core_only: bool = False) -> dict:\n',
     'def build(*, core_only: bool = False) -> dict:\n    source_digest.cache_clear()\n')
edit("packing/tests/test_native_ab_sessions.py", "import os\n", "")
# A selected-but-unused kernel is not a speedup result. A recovered job can
# retain an older profile; expose that rather than presenting a mixed hour as A/B.
edit("packing/devtools/native_ab.py", '    report = {"schema": 1, "session": manifest,',
     '''    expected = {
        "prefix": ("prefix/c",), "topk": ("topk/c",),
        "scatter": ("scatter/c",), "compact": ("compact/c",),
        "vertices": ("vertices/c",), "exact-depth": ("exact-at/cpp", "exact-cost/cpp"),
    }
    not_exercised = [name for name in manifest["native"]["kernels"]
                     if not any(rows.get(key, {}).get("calls", 0) for key in expected[name])]
    desired = "+".join(manifest["native"]["kernels"]) or "none"
    observed = sorted(key.split("/", 1)[1] for key in rows if key.startswith("direction/"))
    mixed = bool(observed and observed != [desired])
    report = {"schema": 1, "session": manifest,''')
edit("packing/devtools/native_ab.py", '        "metrics": rows, "campaign_delta": campaign_delta,',
     '        "metrics": rows, "not_exercised": not_exercised, "mixed_direction_profiles": mixed,\n        "observed_direction_profiles": observed, "campaign_delta": campaign_delta,')
edit("packing/devtools/native_ab.py", '    if campaign_delta:\n',
     '    if not_exercised:\n        lines.append("SELECTED BUT NOT EXERCISED: " + ",".join(not_exercised))\n    if mixed:\n        lines.append("MIXED PROFILE: recovered work retained an older profile; use sealed replay for a clean comparison")\n    if campaign_delta:\n')
edit("packing/devtools/native_ab.py",
     '    commands.add_parser("doctor", help="show selected profile, build identity and native readiness")',
     '    doctor = commands.add_parser("doctor", help="show selected profile, build identity and native readiness")\n    doctor.add_argument("--native", default="none")')
edit("packing/devtools/native_ab.py", '    if args.command == "doctor":\n        print',
     '    if args.command == "doctor":\n        os.environ["PACK_NATIVE_KERNELS"] = args.native\n        print')
