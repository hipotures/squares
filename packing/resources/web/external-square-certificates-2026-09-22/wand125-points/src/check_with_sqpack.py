"""Verify our certificates with jlevy/squares' own verifier, unmodified.

Usage, from a checkout of jlevy/squares:

    python3 check_with_sqpack.py cert_n26_L545.json cert_n29_L557.json \
                                 cert_n39_L650.json cert_n40_L650.json

Our JSON stores the direction net as a rule rather than a list:
``theta_r = 2*atan(r * 83/40000)`` for ``r = 0..200``. sqpack wants the
half-angle tangents themselves, which is exactly ``r * 83/40000``.
"""

import json
import os
import sys
import time
from fractions import Fraction

sys.path.insert(0, "packing/src")

# Python 3.13 added os.process_cpu_count; older runtimes need the fallback.
if not hasattr(os, "process_cpu_count"):
    os.process_cpu_count = lambda: os.cpu_count() or 1

from sqpack.fractional.certificate import Certificate, verify  # noqa: E402
from sqpack.fractional.model import Atom  # noqa: E402

F = Fraction
R = 200
T_STEP = F(83, 40000)


def load(path: str) -> Certificate:
    d = json.load(open(path))
    return Certificate(
        n=d["n"],
        outer_side=F(d["L"]),
        square_side=F(d["B"]),
        atoms=tuple(
            Atom(str(i), F(a[0]), F(a[1]), F(a[2]))
            for i, a in enumerate(d["atoms"])
        ),
        half_tangents=tuple(T_STEP * r for r in range(R + 1)),
    )


def main(paths: list[str]) -> int:
    failed = 0
    for path in paths:
        cert = load(path)
        print(f"=== {path}")
        print(f"    n = {cert.n}   L = {cert.outer_side} = {float(cert.outer_side)}")
        print(f"    atoms = {len(cert.atoms)}   total mass = {cert.total_mass} "
              f"= {float(cert.total_mass):.6f}   budget = {cert.n}")
        t0 = time.time()
        v = verify(cert, workers=1)
        print(f"    accepted = {v.accepted}   ({time.time() - t0:.1f}s)")
        for r in v.conditions:
            print(f"      [{'ok  ' if r.holds else 'FAIL'}] {r.name}: {r.detail}")
        if v.accepted:
            print(f"    => s({cert.n}) >= {cert.bounded_side} = {float(cert.bounded_side)}")
        else:
            failed += 1
            print(f"    failures: {v.failures}")
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
