"""Exact row generation: covering LP + branch-and-bound verifier as the separation oracle."""
import sys, time, pickle
import numpy as np
import lp, verify


def dedupe(fails, tol=1e-2, cap=80):
    out = []
    for (r, x, y, m) in sorted(fails, key=lambda f: f[3]):
        if all(not (rr == r and abs(xx - x) < tol and abs(yy - y) < tol) for (rr, xx, yy, mm) in out):
            out.append((r, x, y, m))
        if len(out) >= cap * (verify.R + 1):
            break
    return out


def run(n, L, h_site=1/16, price_h=None, iters=600, log=print, price_every=2, price_max=200, resume=False, prune_above=30000, local_h=1/256, local_radius=0.25, local_trigger=3000, orbit_cap=6000, stall_stop=40):
    import os
    state_path = f"state_n{n}_L{L}.pkl"
    dirs = lp.net_directions(verify.R)
    if resume and os.path.exists(state_path):
        with open(state_path, "rb") as fh:
            cov, it0 = pickle.load(fh)
        cov.dirs = dirs
        log(f"resumed from {state_path}: iter {it0}, rows={len(cov.rows)}, orbits={len(cov.orbits)}")
    else:
        cov = lp.Cover(L, h_site, dirs, n); it0 = 0
        log(f"n={n} L={L} orbits={len(cov.orbits)} atoms={len(cov.pts)} dirs={len(dirs)}")
        poses = []
        for di in range(0, len(dirs), 20):
            X, Y = cov.admissible_centres(di, 1/8)
            poses += [(di, float(x), float(y)) for x, y in zip(X, Y)]
        cov.add_poses(poses)
    last_obj = None; stall = 0
    for it in range(it0, iters):
        if prune_above and len(cov.rows) > prune_above and it % 4 == 3 and hasattr(cov, "y"):
            dropped = cov.prune(keep_recent=15000)
            log(f"   pruned {dropped} non-binding rows; rows={len(cov.rows)}")
        if it % 5 == 4:
            with open(state_path, "wb") as fh:
                pickle.dump((cov, it), fh)
        t = time.time(); obj = cov.solve()
        # stage 1: cheap grid separation; stage 2: exact branch-and-bound separation
        viol, worst = cov.find_violated(1/32, max_per_dir=40)
        stage = "grid"
        if not viol:
            wpt = cov.w[cov.owner]; keep = wpt > 0
            fails = []
            for r, (c, s, _) in enumerate(dirs):
                f, _ = verify.bb_direction(cov.pts[keep], wpt[keep], L, c, s, max_fails=2000, split=8, per_cell=4, thresh=1.0 - 1e-6)
                fails += [(r, x, y, m) for (x, y, m) in f]
            new = dedupe(fails); worst = min([f[3] for f in fails], default=1.0)
            viol = [(r, x, y) for (r, x, y, m) in new]; stage = "b&b"
            # residual holes are few and tight: seed dense atoms around them
            if fails and len(fails) < local_trigger and local_h and len(cov.orbits) < orbit_cap:
                centres = sorted({(round(x, 2), round(y, 2)) for (r, x, y, m) in fails})
                nadd = cov.add_local_orbits(centres, local_h, local_radius)
                log(f"   local atoms: {len(centres)} hole clusters -> added {nadd} orbits; orbits={len(cov.orbits)}")
        log(f"iter {it} [{stage}]: rows={len(cov.rows)} orbits={len(cov.orbits)} objective={obj:.5f} (need <{n}) min mass={worst:.4f} new rows={len(viol)} [{time.time()-t:.0f}s]")
        stall = stall + 1 if (last_obj is not None and abs(obj - last_obj) < 1e-7) else 0
        last_obj = obj
        if stall >= stall_stop:
            log(f"STALLED: objective unchanged for {stall} iterations with holes remaining; stopping")
            break
        new = viol
        if not new:
            if price_h is None or obj < n - 0.02:
                break
            added, rcmin = cov.price(price_h, max_add=price_max)
            log(f"   pricing: added {added} orbits (min reduced cost {rcmin:.4f}); orbits={len(cov.orbits)}")
            if added == 0:
                break
            continue
        elif price_h is not None and obj >= n - 0.1 and it % price_every == price_every - 1:
            added, rcmin = cov.price(price_h, max_add=price_max)
            log(f"   pricing (interleaved): added {added} orbits (min reduced cost {rcmin:.4f}); orbits={len(cov.orbits)}")
        cov.add_poses(new)
    cert = {"L": L, "n": n, "orbits": cov.orbits, "w": cov.w, "obj": cov.obj}
    with open(f"cert_n{n}_L{L}.pkl", "wb") as fh:
        pickle.dump(cert, fh)
    ok, fails = verify.verify(cert, log=log)
    log("VERIFIED: s(%d) >= %s" % (n, L) if ok else "NOT VERIFIED")
    return cov, ok


if __name__ == "__main__":
    n = int(sys.argv[1]); L = float(sys.argv[2])
    hs = float(sys.argv[3]) if len(sys.argv) > 3 else 1/16
    ph = float(sys.argv[4]) if len(sys.argv) > 4 else None
    pa = 30000
    for a in sys.argv:
        if a.startswith("--prune="):
            pa = int(a.split("=")[1])
    run(n, L, h_site=hs, price_h=ph, log=lambda m: print(m, flush=True), resume=("--resume" in sys.argv), prune_above=pa)
