"""Verification of a weighted fractional unavoidable-set certificate.

Conditions (see jlevy/squares TUTORIAL, Burns/Massaccesi):
 1. atoms D4-symmetric (by construction: orbits)            -- exact
 2. total mass < n                                          -- exact (Fractions)
 3. net of directions theta_r = 2 atan(t_r) reaches pi/4     -- exact
 4. B (1 + D) < 1, D = max tan(half spacing)                -- exact
 5. every admissible closed B-square at every net direction covers mass >= 1
    -- branch & bound over centres, float64 with margin EPS = 1e-9 on every geometric
       comparison and threshold 1 + 1e-9 on the mass.  Rigour: all coordinates have
       magnitude < 100 and each compared quantity is formed by at most 6 floating-point
       operations, so its absolute rounding error is below 1e-13 << EPS; the mass is a sum
       of at most 10^4 nonnegative terms below 1, so its rounding error is below 1e-11 <<
       1e-9.  Hence every box the sweep accepts is truly covered with mass >= 1.
Weights are rounded UP to multiples of 1/WDEN so rounding can only add mass.
"""
import math, sys, time
from fractions import Fraction
import numpy as np

B = Fraction(9977, 10000)
R = 200
T_STEP = Fraction(83, 40000)          # t_r = r * 83/40000, r = 0..200 -> t_200 = 0.415 > tan(pi/8)
WDEN = 10 ** 8
EPS = 1e-9
MINBOX = 1e-7


def net():
    out = []
    for r in range(R + 1):
        t = r * T_STEP
        c = (1 - t * t) / (1 + t * t); s = 2 * t / (1 + t * t)
        out.append((t, c, s))
    return out


def check_net():
    dirs = net()
    tR = dirs[-1][0]
    assert (tR + 1) ** 2 > 2, "net does not reach pi/4"          # t_R > sqrt(2)-1
    D = max((dirs[r + 1][0] - dirs[r][0]) / (1 + dirs[r][0] * dirs[r + 1][0]) for r in range(R))
    assert B * (1 + D) < 1, "shrink condition fails"
    return dirs, D


def rationalise(w, osize, n):
    wq = [Fraction(math.ceil(x * WDEN), WDEN) if x > 0 else Fraction(0) for x in w]
    total = sum(q * int(k) for q, k in zip(wq, osize))
    return wq, total


def bb_direction(pts, wpt, L, c, s, log=None, max_fails=200, thresh=1.0, split=1, per_cell=None):
    """Branch & bound over centres (x, y) in the admissible square [a, L-a]^2 for one direction.
    A box is covered when the atoms lying inside the closed B-square of EVERY centre in the box
    (with margin EPS) weigh at least 1.  Returns failing centres (empty = pass) and box count."""
    a = (float(B) / 2) * (c + s)
    hb = float(B) / 2
    au = pts[:, 0] * c + pts[:, 1] * s; av = -pts[:, 0] * s + pts[:, 1] * c
    from collections import deque
    cells = []
    edges = [a + (L - 2 * a) * i / split for i in range(split + 1)]
    for i in range(split):
        for j in range(split):
            cells.append((edges[i], edges[i + 1], edges[j], edges[j + 1]))
    fails = []; nbox = 0
    for cell in cells:
        stack = [cell]; cell_fails = 0
        while stack:
            if per_cell is not None and cell_fails >= per_cell:
                break
            x0, x1, y0, y1 = stack.pop(); nbox += 1
            # range of p_u = x c + y s and p_v = -x s + y c over the box (c, s >= 0 on the net)
            pu0, pu1 = x0 * c + y0 * s, x1 * c + y1 * s
            pv0, pv1 = -x1 * s + y0 * c, -x0 * s + y1 * c
            m = (au - pu0 <= hb - EPS) & (pu1 - au <= hb - EPS) & (av - pv0 <= hb - EPS) & (pv1 - av <= hb - EPS)
            mass = wpt[m].sum()
            if mass >= thresh:
                continue
            dx, dy = x1 - x0, y1 - y0
            if max(dx, dy) < MINBOX:
                fails.append(((x0 + x1) / 2, (y0 + y1) / 2, mass)); cell_fails += 1
                if len(fails) >= max_fails:
                    return fails, nbox
                continue
            if dx >= dy:
                xm = (x0 + x1) / 2; stack.append((x0, xm, y0, y1)); stack.append((xm, x1, y0, y1))
            else:
                ym = (y0 + y1) / 2; stack.append((x0, x1, y0, ym)); stack.append((x0, x1, ym, y1))
    return fails, nbox


def verify(cert, log=print, max_fail_per_dir=50):
    L = cert["L"]; n = cert["n"]; orbits = cert["orbits"]; w = cert["w"]
    osize = [len(o) for o in orbits]
    wq, total = rationalise(w, osize, n)
    log(f"condition 2: total mass = {float(total):.6f} (need < {n}) -> {'OK' if total < n else 'FAIL'}")
    if total >= n:
        return False, []
    dirs, D = check_net()
    log(f"conditions 3,4: net R={R}, D={float(D):.6f}, B(1+D)={float(B*(1+D)):.7f} -> OK")
    pts = []; wpt = []
    for o, q in zip(orbits, wq):
        if q > 0:
            for p in o:
                pts.append(p); wpt.append(float(q))
    pts = np.array(pts); wpt = np.array(wpt)
    all_fails = []; t = time.time(); tot_box = 0
    for r, (tq, cq, sq) in enumerate(dirs):
        fails, nb = bb_direction(pts, wpt, float(L), float(cq), float(sq), thresh=1.0 + 1e-9)
        tot_box += nb
        if fails:
            fails.sort(key=lambda f: f[2])
            all_fails += [(r, x, y, m) for (x, y, m) in fails[:max_fail_per_dir]]
        if r % 20 == 0:
            log(f"  dir {r}/{R}: boxes so far {tot_box}, failing poses {len(all_fails)} [{time.time()-t:.0f}s]")
    ok = len(all_fails) == 0
    log(f"condition 5: {'OK' if ok else 'FAIL'} ({len(all_fails)} failing poses, {tot_box} boxes)")
    return ok, all_fails


if __name__ == "__main__":
    if sys.argv[1].endswith(".json"):
        import json
        from fractions import Fraction as F
        j = json.load(open(sys.argv[1]))
        # group atoms into singleton "orbits" (weights already per-point); D4 symmetry of the set is
        # re-checked below
        pts = [(float(F(a[0])), float(F(a[1])), float(F(a[2]))) for a in j["atoms"]]
        L = float(F(j["L"]))
        S = {(round(x, 9), round(y, 9)): w for x, y, w in pts}
        for (x, y), w in list(S.items()):
            for (xx, yy) in ((y, x), (L - x, y), (y, L - x), (x, L - y), (L - y, x), (L - x, L - y), (L - y, L - x)):
                assert abs(S.get((round(xx, 9), round(yy, 9)), -1) - w) < 1e-12, "condition 1 (D4 symmetry) fails"
        print("condition 1: D4 symmetry of atoms -> OK")
        cert = {"L": L, "n": j["n"], "orbits": [[(x, y)] for x, y, w in pts], "w": [w for x, y, w in pts]}
    else:
        raise SystemExit(
            f"expected a .json certificate, got {sys.argv[1]!r}.\n"
            "Only JSON is accepted: loading a certificate from a pickle would "
            "execute whatever the file contains."
        )
    ok, fails = verify(cert, log=lambda m: print(m, flush=True))
    print("VERIFIED" if ok else "NOT VERIFIED")
