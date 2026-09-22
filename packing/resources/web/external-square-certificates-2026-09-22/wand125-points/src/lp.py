"""Weighted fractional unavoidable-set search (covering LP with row generation).

Certificate at container side L for n squares: D4-symmetric nonnegative atom weights,
total mass < n, every closed B-square at every net direction covers mass >= 1.
This module only searches (floats); exact verification is separate.
"""
import math, sys, time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, vstack

B = 0.9977
EPS = 1e-9
ROW_SHRINK = 5e-4
ROW_SLACK = 1e-5   # LP rows demand mass >= 1 + ROW_SLACK so solver tolerance cannot leave holes


def net_directions(R=200):
    """theta_r = 2*atan(t_r), t_r = r*83/40000 (same rational net as verify.py); (cos, sin, theta)."""
    out = []
    for r in range(R + 1):
        t = r * 83 / 40000
        c = (1 - t * t) / (1 + t * t); s = 2 * t / (1 + t * t)
        out.append((c, s, 2 * math.atan(t)))
    return out


def d4_orbit(x, y, L):
    pts = {(x, y), (y, x), (L - x, y), (y, L - x), (x, L - y), (L - y, x), (L - x, L - y), (L - y, L - x)}
    return sorted(pts)


def make_sites(L, h):
    """D4 orbit representatives on a grid of spacing h in the fundamental domain 0<=x<=y<=L/2."""
    reps = []
    m = int(round(L / h))
    for i in range(0, m // 2 + 1):
        for j in range(i, m // 2 + 1):
            x, y = i * h, j * h
            if x <= L / 2 + 1e-12 and y <= L / 2 + 1e-12:
                reps.append((x, y))
    orbits = [d4_orbit(x, y, L) for (x, y) in reps]
    return orbits


def _pose_images(cx, cy, c, s, L):
    """the 8 D4 images of a pose (centre, direction) as (x, y, cos, sin)."""
    out = []
    for (x, y, cc, ss) in ((cx, cy, c, s), (cy, cx, s, c), (L - cx, cy, -c, s), (cy, L - cx, s, -c),
                           (cx, L - cy, c, -s), (L - cy, cx, -s, c), (L - cx, L - cy, -c, -s), (L - cy, L - cx, -s, -c)):
        out.append((x, y, cc, ss))
    return out


class Cover:
    def __init__(self, L, h_site, dirs, n):
        self.L, self.n = L, n
        self.orbits = make_sites(L, h_site)
        self.osize = np.array([len(o) for o in self.orbits], dtype=float)
        pts = []; owner = []
        for k, o in enumerate(self.orbits):
            for p in o:
                pts.append(p); owner.append(k)
        self.pts = np.array(pts); self.owner = np.array(owner)
        self.dirs = dirs
        self.rows = []      # list of (dir index, cx, cy)
        self.A_blocks = []

    def pose_row(self, di, cx, cy):
        c, s, _ = self.dirs[di]
        dx = self.pts[:, 0] - cx; dy = self.pts[:, 1] - cy
        u = dx * c + dy * s; v = -dx * s + dy * c
        # stricter than the verifier's box test (EPS=1e-9, MINBOX=1e-7): a row satisfied here
        # implies every leaf box around this centre is covered
        inside = (np.abs(u) <= B / 2 - ROW_SHRINK) & (np.abs(v) <= B / 2 - ROW_SHRINK)
        row = np.zeros(len(self.orbits))
        np.add.at(row, self.owner[inside], 1.0)
        return row

    def add_poses(self, poses):
        blk = np.array([self.pose_row(*p) for p in poses])
        self.A_blocks.append(csr_matrix(blk)); self.rows += list(poses)

    def solve(self, interior=False, spread=0.0):
        """Solve the covering LP.

        The covering polytope is massively degenerate: many optimal vertices share the
        same objective, and each one leaves its residual holes in a different place, so
        row generation chases holes forever.  Two remedies, both of which keep the
        objective's optimal value as the reported bound:

        interior=True  -- use HiGHS's interior-point (IPM) without crossover, which
                          returns an analytic-centre-like point of the optimal face
                          rather than a vertex.  Such a point tends to spread weight
                          over all tight constraints, so far fewer poses sit exactly
                          at mass 1 and the next separation finds fewer holes.
        spread > 0     -- re-solve with the objective fixed to its optimum (as a
                          constraint) and maximise the total slack of the rows, i.e.
                          push covered masses above 1 wherever it is free of charge.
        """
        A = vstack(self.A_blocks).tocsr()
        b = -np.full(A.shape[0], 1.0 + ROW_SLACK)
        meth = "highs-ipm" if interior else "highs"
        res = linprog(self.osize, A_ub=-A, b_ub=b, bounds=(0, None), method=meth)
        if not res.success:
            res = linprog(self.osize, A_ub=-A, b_ub=b, bounds=(0, None), method="highs")
        self.w = res.x; self.obj = res.fun
        self.y = -res.ineqlin.marginals if res.ineqlin.marginals is not None else np.zeros(A.shape[0])
        if spread > 0 and res.success:
            # Keep the bound: cap total weight at obj*(1+spread), then maximise the total
            # covered mass so that masses sit strictly above 1 wherever that is free.
            # Rows: coverage_i(w) >= 1 + ROW_SLACK  ->  -A w <= -(1+ROW_SLACK)
            #       total weight   <= cap           ->   osize . w <= cap
            cap = float(self.obj) * (1.0 + spread)
            colsum = np.asarray(A.sum(axis=0)).ravel()
            A2 = vstack([-A, csr_matrix(self.osize.reshape(1, -1))]).tocsr()
            b2 = np.concatenate([-np.full(A.shape[0], 1.0 + ROW_SLACK), [cap]])
            res2 = linprog(-colsum, A_ub=A2, b_ub=b2, bounds=(0, None), method="highs")
            if res2.success:
                w2 = res2.x
                # the reported objective must stay the capped total, not the original optimum
                self.w = w2
                self.obj = float(self.osize @ w2)
        return res.fun

    def price(self, h, max_add=60, tol=1e-6):
        """Column generation.  For an orbit O with representative x the reduced cost is
        |O| - sum_r y_r * #{points of O inside pose r} = |O| - sum_r y_r * #{g in D4 : x in g(Q_r)}.
        Candidates on a grid of spacing h in the fundamental domain with negative reduced cost
        are added (most negative first).  New columns are appended to the constraint matrix."""
        from scipy.sparse import hstack
        L = self.L
        m = int(round(L / h))
        cand = np.array([(i * h, j * h) for i in range(0, m // 2 + 1) for j in range(i, m // 2 + 1)])
        existing = {(round(o[0][0], 9), round(o[0][1], 9)) for o in self.orbits}
        depth = np.zeros(len(cand))
        pos = np.where(self.y > 1e-12)[0]
        if len(pos):
            yr = self.y[pos]
            rc_ = np.array([(self.rows[r][1], self.rows[r][2], self.dirs[self.rows[r][0]][0], self.dirs[self.rows[r][0]][1]) for r in pos])
            # the 8 D4 images of every positive pose, vectorised: arrays of (x, y, cos, sin)
            cx, cy, c, s = rc_[:, 0], rc_[:, 1], rc_[:, 2], rc_[:, 3]
            imgs = [(cx, cy, c, s), (cy, cx, s, c), (L - cx, cy, -c, s), (cy, L - cx, s, -c),
                    (cx, L - cy, c, -s), (L - cy, cx, -s, c), (L - cx, L - cy, -c, -s), (L - cy, L - cx, -s, -c)]
            CH = 256
            for (qx, qy, qc, qs) in imgs:
                for k0 in range(0, len(pos), CH):
                    sl = slice(k0, k0 + CH)
                    dx = cand[None, :, 0] - qx[sl, None]; dy = cand[None, :, 1] - qy[sl, None]
                    u = dx * qc[sl, None] + dy * qs[sl, None]; v = -dx * qs[sl, None] + dy * qc[sl, None]
                    inside = (np.abs(u) <= B / 2 - ROW_SHRINK) & (np.abs(v) <= B / 2 - ROW_SHRINK)
                    depth += yr[sl] @ inside
        osz = np.array([len(d4_orbit(x, y, L)) for (x, y) in cand], dtype=float)
        rc = osz - depth                      # reduced cost
        order = np.argsort(rc)
        new_orbits = []
        for k in order:
            if rc[k] >= -tol or len(new_orbits) >= max_add:
                break
            rep = (round(float(cand[k, 0]), 9), round(float(cand[k, 1]), 9))
            if rep in existing:
                continue
            new_orbits.append(d4_orbit(cand[k, 0], cand[k, 1], L)); existing.add(rep)
        if not new_orbits:
            return 0, float(rc.min())
        # append columns: for each new orbit, count its points inside every held pose
        A = vstack(self.A_blocks).tocsr()
        cols = np.zeros((A.shape[0], len(new_orbits)))
        rows_arr = np.array([(self.rows[r][1], self.rows[r][2]) for r in range(A.shape[0])])
        cs = np.array([(self.dirs[self.rows[r][0]][0], self.dirs[self.rows[r][0]][1]) for r in range(A.shape[0])])
        for j, orb in enumerate(new_orbits):
            for (px, py) in orb:
                dx = px - rows_arr[:, 0]; dy = py - rows_arr[:, 1]
                u = dx * cs[:, 0] + dy * cs[:, 1]; v = -dx * cs[:, 1] + dy * cs[:, 0]
                cols[:, j] += (np.abs(u) <= B / 2 - ROW_SHRINK) & (np.abs(v) <= B / 2 - ROW_SHRINK)
        self.A_blocks = [hstack([A, csr_matrix(cols)]).tocsr()]
        for orb in new_orbits:
            self.orbits.append(orb)
            self.pts = np.vstack([self.pts, np.array(orb)])
            self.owner = np.concatenate([self.owner, np.full(len(orb), len(self.orbits) - 1)])
            self.osize = np.append(self.osize, len(orb))
        return len(new_orbits), float(rc.min())

    def add_local_orbits(self, centres, h, radius, max_add=400):
        """Add atom orbits on a fine grid of spacing h within `radius` of any of the given
        centres (fundamental-domain representatives only).  Used to close small residual holes."""
        L = self.L
        existing = {(round(o[0][0], 9), round(o[0][1], 9)) for o in self.orbits}
        cands = set()
        for (cx, cy) in centres:
            i0, i1 = int(np.floor((cx - radius) / h)), int(np.ceil((cx + radius) / h))
            j0, j1 = int(np.floor((cy - radius) / h)), int(np.ceil((cy + radius) / h))
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    x, y = i * h, j * h
                    if not (0 <= x <= L and 0 <= y <= L):
                        continue
                    # reduce into the fundamental domain 0 <= x <= y <= L/2
                    for (px, py) in d4_orbit(x, y, L):
                        if px <= py + 1e-12 and py <= L / 2 + 1e-12:
                            rep = (round(px, 9), round(py, 9))
                            if rep not in existing:
                                cands.add(rep)
                            break
        new_orbits = [d4_orbit(x, y, L) for (x, y) in sorted(cands)[:max_add]]
        if not new_orbits:
            return 0
        from scipy.sparse import hstack
        A = vstack(self.A_blocks).tocsr()
        cols = np.zeros((A.shape[0], len(new_orbits)))
        rows_arr = np.array([(self.rows[r][1], self.rows[r][2]) for r in range(A.shape[0])])
        cs = np.array([(self.dirs[self.rows[r][0]][0], self.dirs[self.rows[r][0]][1]) for r in range(A.shape[0])])
        for j, orb in enumerate(new_orbits):
            for (px, py) in orb:
                dx = px - rows_arr[:, 0]; dy = py - rows_arr[:, 1]
                u = dx * cs[:, 0] + dy * cs[:, 1]; v = -dx * cs[:, 1] + dy * cs[:, 0]
                cols[:, j] += (np.abs(u) <= B / 2 - ROW_SHRINK) & (np.abs(v) <= B / 2 - ROW_SHRINK)
        self.A_blocks = [hstack([A, csr_matrix(cols)]).tocsr()]
        for orb in new_orbits:
            self.orbits.append(orb)
            self.pts = np.vstack([self.pts, np.array(orb)])
            self.owner = np.concatenate([self.owner, np.full(len(orb), len(self.orbits) - 1)])
            self.osize = np.append(self.osize, len(orb))
        return len(new_orbits)

    def prune(self, keep_recent=2000):
        """Drop rows with zero dual value (non-binding), keeping the most recent rows; dropped
        poses can only be re-added by separation if they become violated again."""
        A = vstack(self.A_blocks).tocsr()
        nrow = A.shape[0]
        keep = np.ones(nrow, dtype=bool)
        ny = min(len(self.y), nrow)
        keep[:ny] = self.y[:ny] > 1e-12          # rows added after the last solve have no dual yet: keep them
        keep[max(0, nrow - keep_recent):] = True
        idx = np.where(keep)[0]
        self.A_blocks = [A[idx]]
        self.rows = [self.rows[i] for i in idx]
        return nrow - len(idx)

    def admissible_centres(self, di, h):
        """grid of centres in the fundamental domain (x<=y<=L/2) where the B-square fits."""
        c, s, _ = self.dirs[di]
        half = (B / 2) * (abs(c) + abs(s))
        lo, hi = half, self.L - half
        xs = np.arange(lo, hi + 1e-9, h)
        X, Y = np.meshgrid(xs, xs, indexing="ij")
        m = (X <= Y + 1e-12) & (Y <= self.L / 2 + 1e-12)
        return X[m], Y[m]

    def masses(self, di, X, Y):
        """covered mass at centres (X,Y) for direction di, using current weights."""
        c, s, _ = self.dirs[di]
        wpt = self.w[self.owner]
        au = self.pts[:, 0] * c + self.pts[:, 1] * s
        av = -self.pts[:, 0] * s + self.pts[:, 1] * c
        pu = X * c + Y * s; pv = -X * s + Y * c
        out = np.empty(len(X))
        # chunk to bound memory
        for k0 in range(0, len(X), 2000):
            sl = slice(k0, k0 + 2000)
            M = (np.abs(au[None, :] - pu[sl, None]) <= B / 2 + 1e-12) & (np.abs(av[None, :] - pv[sl, None]) <= B / 2 + 1e-12)
            out[sl] = M @ wpt
        return out

    def find_violated(self, h, max_per_dir=40, thresh=1.0 - 1e-9):
        found = []
        worst = 1e9
        for di in range(len(self.dirs)):
            X, Y = self.admissible_centres(di, h)
            m = self.masses(di, X, Y)
            worst = min(worst, m.min())
            idx = np.where(m < thresh)[0]
            if len(idx):
                idx = idx[np.argsort(m[idx])][:max_per_dir]
                found += [(di, float(X[i]), float(Y[i])) for i in idx]
        return found, worst


def run(n, L, h_site=1/16, R=200, h_pose0=1/8, h_check=1/32, iters=30, log=print, price_h=None):
    dirs = net_directions(R)
    cov = Cover(L, h_site, dirs, n)
    log(f"n={n} L={L} orbits={len(cov.orbits)} atoms={len(cov.pts)} dirs={len(dirs)}")
    # initial poses: coarse grid, a subset of directions
    poses = []
    for di in range(0, len(dirs), max(1, len(dirs) // 12)):
        X, Y = cov.admissible_centres(di, h_pose0)
        poses += [(di, float(x), float(y)) for x, y in zip(X, Y)]
    cov.add_poses(poses)
    for it in range(iters):
        t = time.time(); obj = cov.solve()
        viol, worst = cov.find_violated(h_check)
        log(f"iter {it}: rows={len(cov.rows)} objective={obj:.5f} (need <{n}) min mass on check grid={worst:.4f} violated={len(viol)} [{time.time()-t:.0f}s]")
        if not viol:
            if price_h is None:
                break
            added, dmax = cov.price(price_h)
            log(f"   pricing: added {added} orbits (max depth {dmax:.4f}); orbits={len(cov.orbits)}")
            if added == 0:
                break
            continue
        cov.add_poses(viol)
    return cov


if __name__ == "__main__":
    n = int(sys.argv[1]); L = float(sys.argv[2])
    hs = float(sys.argv[3]) if len(sys.argv) > 3 else 1/16
    ph = float(sys.argv[4]) if len(sys.argv) > 4 else None
    it = int(sys.argv[5]) if len(sys.argv) > 5 else 30
    cov = run(n, L, h_site=hs, log=lambda m: print(m, flush=True), price_h=ph, iters=it)
    np.save(f"cert_n{n}_L{L}.npy", {"L": L, "n": n, "orbits": cov.orbits, "w": cov.w, "obj": cov.obj}, allow_pickle=True)
