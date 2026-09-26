"""Guarded pre-publication fixes for native lab process/session boundaries."""
from pathlib import Path


def edit(path, old, new):
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"unexpected integration anchor in {path}: {old[:60]}")
    p.write_text(text.replace(old, new, 1))


root = "packing/src/sqpack/fractional/"
edit(root + "native_ab_runtime.py", "    library.cache_clear()", "    _library.cache_clear()")
edit(root + "native_ab_runtime.py",
     '@lru_cache(maxsize=4)\ndef library(name: str) -> ct.CDLL:\n    directory = build_directory()',
     'def library(name: str) -> ct.CDLL:\n    return _library(name, str(build_directory()))\n\n\n@lru_cache(maxsize=8)\ndef _library(name: str, location: str) -> ct.CDLL:\n    directory = Path(location)')
edit(root + "native_ab_metrics.py", '_pid = 0\n', '_pid = 0\n_context = None\n')
edit(root + "native_ab_metrics.py",
     '    global _pid, _token, _stats, _last_flush, _seen_capture\n    if _pid == os.getpid():\n        return\n    _pid = os.getpid()',
     '    global _pid, _token, _stats, _last_flush, _seen_capture, _context\n    context = (os.getpid(), os.environ.get("PACK_NATIVE_SESSION"), os.environ.get("PACK_NATIVE_STATS"), os.environ.get("PACK_NATIVE_CAPTURE"))\n    if _context == context:\n        return\n    _context = context\n    _pid = os.getpid()')
edit(root + "native_ab_metrics.py", '    if not directory or _pid != os.getpid() or not _stats:\n',
     '    context = (os.getpid(), os.environ.get("PACK_NATIVE_SESSION"), directory, os.environ.get("PACK_NATIVE_CAPTURE"))\n    if not directory or _context != context or not _stats:\n')
# Signal readiness is private to the measurement wrapper; it is not a new
# state transition, proof condition or public campaign data file.
edit("packing/devtools/run_n12_frontier.py",
     '                previous_handlers[signum] = signal.signal(signum, stop.handle)\n            if args.resume:',
     '                previous_handlers[signum] = signal.signal(signum, stop.handle)\n            ready_file = os.environ.get("PACK_NATIVE_STARTED_FILE")\n            if ready_file:\n                atomic_json(Path(ready_file), {"pid": os.getpid(), "ready": True})\n            if args.resume:')
edit("packing/devtools/native_ab.py",
     '        PACK_NATIVE_STATS=str(directory / "processes"))',
     '        PACK_NATIVE_STATS=str(directory / "processes"),\n        PACK_NATIVE_STARTED_FILE=str(directory / "controller-ready.json"))')
edit("packing/devtools/native_ab.py", '            if stop_pending and requested is None:\n',
     '            if stop_pending and requested is None and (directory / "controller-ready.json").exists():\n')
# Preserve a report on launch/runtime errors as well as on ordinary Ctrl-C.
edit("packing/devtools/native_ab.py", '        code = child.wait()\n    finally:',
     '        code = child.wait()\n    except Exception as exc:\n        code = 70\n        runtime.atomic_json(directory / "error.json", {"type": type(exc).__name__, "message": str(exc)})\n        if child is not None and child.poll() is None:\n            child.send_signal(signal.SIGINT)\n            child.wait()\n    finally:')
print("native lab process/session hardening applied")
