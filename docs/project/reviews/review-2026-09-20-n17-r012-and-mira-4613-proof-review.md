# Proof Review: R012 `s(17) >= 461300/99999` and Mira’s `4.613` Certificate

Reviewed 2026-09-20 in worktree `n17-4613-intake` at `061e9ffb`. This is an adversarial
correctness review of two published computer-assisted lower bounds on `s(17)`, the least
side of a square containing seventeen unit squares with disjoint interiors.
It is evidence for the coordinator, not a verdict of record.
Every claim names the file and line, the command, or the exact number it rests on.

**In one line:** no error was found in either argument; R012’s finite premise was
verified here by three methods; Mira’s finite premise was spot-checked on 16 of its 2881
directions and is otherwise unverified here.

## 1. What Was Reviewed

Both sources are the archived copies under
`packing/resources/web/n17-weighted-certificates-2026-09-20/`. They are untracked in
this worktree, so the SHA-256 values below identify the bytes.
All 92 entries of the archive’s `retained-files.sha256` check with `shasum -a 256 -c`.

| Source | Commit | Claim |
| --- | --- | --- |
| `github.com/Guzhou0806/n17-square-packing`, `certificates/R012/` | `931a0dfd64302e277057006e99388fe5c00b7f53` (2026-09-20) | `s(17) >= 461300/99999 = 4.61304613046130…` |
| `github.com/Mira-acc/17squares`, `certificates/lower_bound_4p613/` | `0266c9936a303817ac7da0802364034a34fb2558` (2026-09-07) | `s(17) >= L sqrt(1+h^2)/(B(1+h))`, strict `s(17) > 4.613028635886` |

Files read line by line:

| File | SHA-256 |
| --- | --- |
| `R012/PROOF.md` | `4a53362d6624bebe064ac6c7c1fcf29e8f7ad2847263e5d92ae7a0be2ba07194` |
| `R012/verify.py` | `c85c9d8f90c6bf9d3cc294ea4c8b4135725f8698774fb21f1c90b950c25a33e6` |
| `R012/sweep.py` | `96efe91895ab14d80c6b7162aee91d4687e5d11a60093a9935043a88d4713965` |
| `R012/catalogue.json` | `4d2a89e87f838c385b02ba9fa0fb06c2fd36eb5d85668fb119db31c3dcc96ee1` |
| `R012/orbits.json` | `97d2d227a6578a30276e43b10be5e57ae49a1d3e8def699bf01de96fa3785e60` |
| `R012/MANIFEST.json` | `9ad92ab5b80a9de54c1d84661c4753a5800e25ef90b02577ee405e51a1ad294d` |
| `R012/ATTRIBUTION.md` | `5e300ec2ae60838b22fb185604f6ccbc10c7ab3a9982e7668079a47d1fca5900` |
| `lower_bound_4p613/PROOF.md` | `ddece45ae06a7df440d2377018087037f223c0704c5ba1681a59b10aa6a99b18` |
| `lower_bound_4p613/verify.py` | `b48c5b211b4de061e4f2220915de3e145923126fc9f78636ae59784995d78529` |
| `lower_bound_4p613/exact_sweep.cpp` | `1bb626a560e3c67620b2aa7851bc467db72b3530f6cae394c1d9d9f034910f4b` |
| `lower_bound_4p613/best-certificate.json` | `749f13335980a66a27a2304f212b5d8796390c81b962149647a4d9ff43a228ec` |

First-party context read for comparison: `packing/src/sqpack/fractional/certificate.py`
(Condition 4, lines 11–13 and 333–340), `packing/src/sqpack/fractional/sweep.py`,
`packing/cases/n11_fractional_certificate/t-022-dilation-limit-proof.md`, and the
coordinator’s source-replay receipt
`receipts/guzhou-r012-source-replay-2026-09-20.result.json` with its per-entry rows.

All Python ran under the project interpreter, 3.14.7, through
`uv run --frozen --all-extras --group dev` from `packing/`. Scratch scripts and their
logs are in the gitignored `attic/r012-review/`. They are review experiments, not
registered instruments.

Not reviewed: Mira’s C++ kernel was read but not compiled or run, and the coordinator’s
two first-party replay scripts were not audited.

## 2. Verdict

**R012’s argument is sound as I read it, and I could not break it.** Its written proof
is a sketch in two places; findings F1 and F2 give the missing steps.
Its finite premise is that each of the 2925 catalogue cores captures mass at least
`gamma` over its whole parent-centre envelope.
I re-derived all 2925 obligations from `catalogue.json` and `orbits.json` without the
source’s `verify.py` or `sweep.py` and decided each with this repository’s sweep kernel.
The exact minimum agrees with the source’s kernel on every entry.
Those two kernels have a common ancestor (F9), so I also decided the entries with a
third method that shares nothing with either (E3).

The coordinator’s first-party interval instrument also certified all 2925 entries
(`receipts/guzhou-r012-first-party-001.json`, status `FULL_CATALOGUE_CERTIFIED`). I did
not audit that instrument, so it is cited here and not counted among my own checks.

**Mira’s written argument (PROOF.md sections 3 and 6) is correct.** Its containment
condition is sharper than this repository’s Condition 4, and neither is wrong.
Mira’s finite premise, Condition 5 over 2881 directions, was **not** verified in full.
I decided 16 directions with this repository’s kernel, the tight ones among them, and
each equals the source’s own per-direction log (E9). The coordinator’s first-party
replays of the whole net were still running when this was written, and their logs held
no verdict.

R012 does not depend on Mira’s certificate being valid.
It uses its own measure and recomputes every coverage obligation on it.
In the other direction, R012’s value exceeds Mira’s endpoint, so Mira’s inequality for
`s(17)` would follow from R012; that says nothing about Mira’s certificate as an object.

R012’s value is below the best known packing side, `4.67553009…` (Bidwell 1998, as
recorded in `SYNOPSIS.md`), so it contradicts no known packing.
The contradiction needs only a catalogue minimum above `M/17 = 424969/425000`, about
`0.999927`; the verified minimum is `250023/250000 = 1.000092`.

Claims by status:

| Claim | Status | Basis |
| --- | --- | --- |
| R012: closed core strictly inside the open parent for every angle of the interval, from an endpoint-only test | Holds; written argument omits a step, closed in F1 | `verify.py:107–117`, PROOF.md §2 |
| R012: `[r, L-r]^2` with `r = (A/2) min(f(a), f(b))` is exactly the union of legal parent centres over `[a, b]` | Holds; written argument omits a step, closed in F2 | `verify.py:113–118`, PROOF.md §3 |
| R012: coverage need only hold at parent centres | Proved by the argument as written | PROOF.md §3, §6 |
| R012: measure is D4-invariant; folding preserves the legal domain and the captured mass | Proved as written; invariance also decided atom by atom in E2 | `verify.py:78–85`, F3 |
| R012: catalogue covers `[0, T]`, `T > tan(pi/8)`, without gaps | Proved as written, by exact checks | `verify.py:91, 104–122` |
| R012: `sweep.coverage` returns the exact infimum of captured mass over the closed centre domain | Holds; correctness argued in F4 and tested in E2, E3, E4 | `sweep.py:91–130` |
| R012: every catalogue entry has minimum at least `gamma = 250023/250000` | Computationally verified here | E2, E3 |
| R012: counting step and `17 gamma > M` | Proved as written, apart from a notational slip (F6) | PROOF.md §6 |
| R012: scaling step, `s(17) >= L/A` | Proved as written; the strict form also follows (F7) | PROOF.md §6 |
| R012: self-contained given its own data | Confirmed by reading; the Mira endpoint enters only as a comparison | `verify.py:124–128`, F8 |
| R012: arithmetic claims (bracket, `17 gamma - M`, `S^2 - S_M^2`) | Recomputed exactly; all correct | Section 4.1 |
| R012: a failing certificate cannot print the success marker | No such path found | F10 |
| Mira: finite net covers all orientations under `B^2(1+h)^2 < 1+h^2` | Proved by the argument as written | Mira PROOF.md §3, F11 |
| Mira: dilation-limit endpoint and the strict decimal | Proved as written; arithmetic recomputed | Mira PROOF.md §6, Section 4.1 |
| Mira: Conditions 1 to 4 under this repository’s `closed_form_conditions` | Computationally verified here; all four hold | F11 |
| Mira: Condition 5, least net-core mass `1000002103/1000000000` | **Unverified here** beyond a 16-direction sample; source-reported | `result.json`, E9 |

Nothing reviewed was found to be wrong.

## 3. Findings

Severity is blocking, non-blocking, or note.
None is blocking. F1, F2 and F9 are non-blocking: the first two are gaps in the written
proof that a record citing PROOF.md should carry the closing argument for, and the third
limits which evidence counts as independent.

### F1. The endpoint-only containment test suffices, but PROOF.md §2 skips the monotonicity step (non-blocking)

Location: `verify.py:107–117`; PROOF.md §2.

At both endpoints `u` of an interval the code requires `dot > 0 and dot >= cross`, where
`dot = cos d` and `cross = |sin d|` for the relative angle `d = theta - phi`, and then
`A - B max(dot + cross) > 0`. PROOF.md says only that the greatest relative angle occurs
at an endpoint. The missing steps:

1. `t` and `u` lie in `[0, 1)` (`verify.py:105`), so `theta = 2 arctan t` and
   `phi = 2 arctan u` lie in `[0, pi/2)`, and `d` lies in `(-pi/2, pi/2)` as a real
   number with no ambiguity modulo `2 pi`. On that range the two tests say exactly
   `|d| <= pi/4`.
2. `phi` is strictly increasing in `u`, so `d(u)` is continuous and strictly decreasing.
   Its values over `[a, b]` fill `[d(b), d(a)]`, which lies inside `[-pi/4, pi/4]`. This
   holds for every real `u`, not only rational ones.
3. `cos d + |sin d| = sqrt(2) cos(|d| - pi/4)` increases with `|d|` on `[0, pi/4]`, and
   `|d|` over an interval is greatest at an endpoint.
   That covers a sign change of `d` inside the interval, which happens in 2913 of the
   2925 entries, where `t` lies strictly inside `(a, b)`. In six entries `t` lies
   outside `[a, b]`; the same argument applies.
4. A concentric square of side `B` turned by `d` has half-extent
   `(B/2)(|cos d| + |sin d|)` along each parent axis, so `B (cos d + |sin d|) < A` is
   exactly “closed core inside the open parent interior”.

The strict rational inequality at the two endpoints therefore proves strict containment
on the whole closed interval, and the code checks what the proof states.
The least margin is
`9246825470492230950855738842503/4032079239528994151028755999277446450000`, about
`2.29e-9`, at entry 1189 (`k = 1145`, the first interval with `B = 19997/20000`). I
recomputed it independently and it equals the source’s value exactly.
The largest relative angle at any endpoint is about `2.2e-4` radians, far from `pi/4`.

### F2. The centre envelope is exactly the union, because `f` is quasi-concave (non-blocking)

Location: `verify.py:113–118`; PROOF.md §3.

For a parent at half-tangent `u` in `[0, 1)` the legal centres are
`[A f(u)/2, L - A f(u)/2]^2` with `f(u) = c(u) + s(u) = cos phi + sin phi`, both terms
being nonnegative on `[0, pi/2)`. PROOF.md says `f` has a single interior maximum.
The property needed is that `f = sqrt(2) sin(phi + pi/4)` rises on `[0, sqrt(2) - 1]`
and falls afterwards, so its minimum over any `[a, b]` is at an endpoint.
The centre squares are nested, so their union is the one with the least `f`, and
`[r, L-r]^2` is that square exactly.
Only the last entry (2924) straddles `u = sqrt(2) - 1`; there
`f(a) = 1.414213551845… < f(T) = 1.414213562372…`, and the code takes the smaller.
In every entry the smaller value is at the left endpoint.

Restricting coverage to this domain is legitimate.
A core is needed only at the centre of an actual parent, and a parent inside the
container has its centre in the legal square for its own angle.
The restriction carries real weight: swept over the core’s own centre domain instead,
entries 0 and 1 fall to `493737/500000` and `492619/500000`, below `gamma` (E5). The
test `B (c(t) + s(t))/2 <= inset` on `verify.py:118` is implied by F1 and is not needed
for soundness.

### F3. Folding needs one reflection, and `T > tan(pi/8)` is harmless (note)

Location: PROOF.md §6; `verify.py:78–91`.

A square at angle `phi` is the same set at `phi + pi/2`, so every parent has an angle in
`[0, pi/2)`. If it exceeds `pi/4`, the diagonal reflection `sigma` of the container
sends the parent to one at angle `pi/2 - phi`, inside the container, with centre
`sigma(z)`. The catalogue gives a core `C'` for the reflected parent, and `sigma(C')` is
concentric with the original parent, strictly inside it, and has the same mass because
the measure is `sigma`-invariant.
The full D4 invariance that `verify.py:82–85` constructs is more than the fold needs.
Disjointness of orbits is enforced on `verify.py:84`, so each point carries one weight.

The catalogue extends to `T = 207107/500000`, and
`T^2 + 2T - 1 = 309449/250000000000 > 0` proves `T > sqrt(2) - 1`. Parents with `u`
between `sqrt(2) - 1` and `T` are real parents, and entry 2924 treats them soundly.
The fold never needs them.

### F4. `sweep.coverage` is exact; no reachable cell is skipped (note)

Location: `sweep.py:91–130`.

- **Capture sets:** In the core frame `(u, v) = (c x + s y, -s x + c y)` the centres
  that capture an atom form the closed square of side `B` about the atom’s image
  (`:99–101`), matching `direct_mass` (`:85–89`).
- **Active set per strip:** All events at `a`, removals included, are applied before
  strip `(a, b)` is examined (`:114`). Since `us` holds every rectangle edge, the
  rectangles active on the open strip are exactly those with left edge at most `a` and
  right edge at least `b`. The `continue` on `:115` and the `break` on `:116` come after
  the events are applied, so rectangles that start left of the domain are counted.
- **Reachable range:** `lower` and `upper` (`:111–112`) are the true lower and upper
  boundaries of the rotated domain when `c, s > 0`. Their only breakpoints are at the
  vertices `(L-r, r)` and `(r, L-r)`, whose `u` coordinates are events (`:106`). Both
  are therefore affine on each strip, with extremes at the strip ends, and `(lo, hi)` on
  `:118` is the exact projection of the open strip intersected with the open domain.
  It is neither an over-approximation nor an under-approximation.
- **Index arithmetic:** A cell `(vs[k], vs[k+1])` meets `(lo, hi)` exactly when
  `vs[k+1] > lo` and `vs[k] < hi`, that is `k >= bisect_right(vs, lo) - 1` and
  `k < bisect_left(vs, hi)`. Line `:120` computes that half-open range.
  The clamps never bind, because the polygon’s extreme `v` coordinates are in `vs`.
- **Degenerate cases:** Only `t = 0` gives `s = 0`; the domain is then axis-parallel and
  `(r, L-r)` is exact.
  `c = 0` cannot occur because `t < 1`. Coincident events share a dictionary key, and
  strips have positive width because `us` holds distinct values.
- **Segment tree:** `add` and `query` (`:27–45`) form a range-add, range-minimum tree
  with tags that are never pushed down.
  `v[i]` is the node minimum net of ancestors’ tags, and `query` carries those tags
  down. Every visited child meets the target range, so leaves are always fully covered
  and `vals` is never empty.
- **Integer scaling:** Weights are multiples of `1/scale` by construction (`:100–101`),
  so `int(w*scale)` is exact.
- **Open cells suffice:** PROOF.md §4’s limiting argument is correct and needs what it
  lists: a domain with nonempty interior (`r < L/2`, enforced on `:97`), closed capture,
  and nonnegative weights.

The witness recount on `:126–129` confirms only that the reported minimum is attained at
a real centre. It cannot detect a skipped cell, so a run’s soundness rests on the
reduction above. E2, E3 and E4 test that reduction against code that does not share it.

### F5. `direct_recount` in `verify.py` is a constant, not a check (note)

Location: `verify.py:217`; `sweep.py:130`.

`coverage` returns `'direct_recount': True` unconditionally, so the test on
`verify.py:217` reduces to `value >= gamma`. The real recount is the `need` on
`sweep.py:128`, which raises inside the worker and fails the run.
Nothing unsound follows.

### F6. PROOF.md §6 writes `mu(P_i)` where the cores are meant (note)

Location: PROOF.md §6, the display `17 gamma <= sum mu(P_i) <= M`.

`P_i` is not defined.
If it denotes the parents, the right-hand inequality is unjustified, since two touching
closed parents can share an atom on a common boundary.
The sentence before the display gives the correct argument.
The chosen closed cores lie strictly inside their parents, so they are pairwise disjoint
as sets, `sum mu(C_i) = mu(union C_i) <= M`, and each `mu(C_i) >= gamma`. No atom is
counted twice, and touching parents cause no difficulty.
`verify.py:217` checks `value >= gamma` for every entry, and the recorded catalogue
minimum equals `gamma` exactly.

### F7. The bound is in fact strict (note)

Location: PROOF.md §6.

The argument excludes seventeen interior-disjoint `A`-squares in the closed container
`[0, L]^2` itself. A packing of unit squares at side exactly `L/A` would scale to one,
and the infimum defining `s(17)` is attained by compactness, so `s(17) > L/A`. The
source registers only the weak form, which follows without compactness.

### F8. The digest pins R012’s own measure; the lineage from Mira is as described (note)

Location: `verify.py:23, 88–90`; ATTRIBUTION.md.

`ATOM_DIGEST` is the SHA-256 of the expanded 1616-atom table, so it ties the verifier to
the measure its author ran and to nothing external.
E8 confirms the stated lineage: all 1620 of Mira’s atoms round at `1e-5` onto R012
atoms, the largest coordinate shift is `5.0e-6`, four pairs merge (1620 to 1616), and
every weight was raised, which takes the mass from `16.99798498` to `16.99876`. Rounding
coordinates would not be sound on its own.
It is sound here because every coverage obligation is recomputed on the rounded measure,
which is what `verify.py` and E2 do.

### F9. The source kernel and this repository’s kernel share an ancestor (non-blocking)

Location: ATTRIBUTION.md, “Code and rights”; `sweep.py:120`;
`packing/src/sqpack/fractional/sweep.py:239–240`.

R012’s ATTRIBUTION.md says `sweep.py` descends from this repository’s MIT-licensed
sweep. The two now differ in substance: R012 sweeps with a segment tree and closed-form
boundary functions over vertex events, while `sqpack.fractional.sweep` fills a dense
difference array and clips the domain polygon to each slab.
They still select reachable cells with the same `bisect_right - 1`, `bisect_left` idiom.
Agreement between them is therefore not independent evidence for that idiom.
Three things cover it: the argument in F4, the brute-force oracle of E4, and the
separating-axis pass E3, which forms its own cells and its own reachability test.
A first-party record should cite an instrument that does not inherit the idiom.

### F10. No path prints the success marker for a failing certificate (note)

Location: `verify.py:182–243`.

- `need` raises `ValueError`; nothing relies on `assert`, and optimized mode is refused
  anyway (`:192`).
- The marker is assigned on `:230`, after every check.
  Any exception, `KeyboardInterrupt` included, returns 1 and prints `FAIL_OR_INCOMPLETE`
  (`:237–243`).
- `pool.map` preserves order, `:215` requires each row’s index to equal its position,
  and `:224` requires 2925 rows, so a dropped or reordered entry fails the run.
  A worker crash raises in the parent.
- `--records` prints `PASS_RECORDS_ONLY`, never the full marker.

`integrity()` (`:48–65`) compares files with `MANIFEST.json`, and nothing pins
`MANIFEST.json` itself, so it detects accidental change and not substitution.
That does not affect soundness: `load_math` pins the theorem parameters, the range rules
and the measure digest, and any sixty explicit entries that pass contiguity, containment
and coverage prove the same theorem.
Byte identity is this repository’s job, through the archive’s `retained-files.sha256`
and Git.

The verifier must be run with `-B`, as the source’s README says.
Without it, importing `sweep` writes `__pycache__/`, the file-set comparison on `:59`
fails, and the run is refused (E7). That is fail-closed.

### F11. Mira’s containment condition is correct and sharper than Condition 4 (note)

Location: Mira PROOF.md §3 and §6; `exact_sweep.cpp:56`;
`certificate.py:11–13, 333–340`.

Both conditions bound `B (cos d + sin d)` for an angular error `d` with `tan d <= D`.
This repository uses `cos d + sin d <= 1 + tan d <= 1 + D`. Mira uses the exact maximum
`(1 + D)/sqrt(1 + D^2)`, through the identity
`(1+h)^2 (1+z^2) - (1+z)^2 (1+h^2) = 2 (h-z)(1-hz)`, which I expanded and confirmed.
For Mira’s net `t_k = k h` the half-gap tangent is `h/(1 + k(k+1) h^2)`, greatest at
`k = 0`, so `D = h` exactly.
Both conditions are sufficient.
Mira’s is the sharpened lemma that T-022 already records, and Mira credits it.
`exact_sweep.cpp:56` tests the integer form `4 bi^2 (den+num)^2 < G^2 (den^2 + num^2)`,
which is the same inequality.

This repository’s `verify()` Condition 4 **accepts** Mira’s `(B, net)`; Section 4.1 has
the exact values. Under the coarser lemma the same certificate would give the smaller
endpoint `132854400000000/28799821518679 = 4.6130285881748…`, against Mira’s
`4.6130286358861…`.

The dilation step in §6 is correct: scaling `L`, `B` and the atoms by `r < C0` preserves
coverage, mass and symmetry, keeps the containment strict, and the limit gives the weak
inequality at the radical endpoint.
The strict decimal `4.613028635886` is below that endpoint.

Reading `exact_sweep.cpp` found no error.
Only the two extreme domain vertices are events there, so the slab range uses the
boundary V’s vertex clamped to the slab (`:75–76`), which is the right extremum in that
design. Its sentinels at `-edge-1` and `edge+1` enclose the whole domain.
This is a reading, not a run.

## 4. Exact Arithmetic Recomputed, and Experiments

### 4.1 Arithmetic

`attic/r012-review/arith.py`, Fractions and integer square root only.

| Quantity | Value | Matches source |
| --- | --- | --- |
| `S = L/A` | `461300/99999` | yes |
| 20-digit bracket | `4.61304613046130461304 <= S < 4.61304613046130461305` | yes |
| `17 gamma - M` | `701/250000` | yes |
| `T - 2880 h` | `0` | yes |
| `T^2 + 2T - 1` | `309449/250000000000 > 0` | yes |
| `S_M^2`, Mira’s endpoint squared | `17650291964463886688094912400/829429719507765981945905041` | yes; equals `L^2 (1+h^2)/(B^2 (1+h)^2)` |
| `S^2 - S_M^2` | `1338724704271950594905978540377600/8294131309963187985770427210937705041 > 0` | yes |
| `sqrt(S_M^2)` to 40 places | `4.6130286358861107661720565584026192414009` |  |
| `4.613028635886^2 < S_M^2` | true; `4.613028635887` fails | yes |

Mira’s containment, for `L = 4613/1000`, `B = 19997/20000`, `m = 2880`,
`h = D = 207107/1440000000`:

| Condition | Left side | Right side | Slack |
| --- | --- | --- | --- |
| This repository, `B (1 + D) < 1` | `28799821518679/28800000000000` | `1` | `178481321/28800000000000`, about `6.20e-6` |
| Mira, `B^2 (1+h)^2 < 1 + h^2` | `829429719507765981945905041/829440000000000000000000000` | `2073600042893309449/2073600000000000000` | `3432549852599218031653/276480000000000000000000000`, about `1.24e-5` |

### 4.2 Experiments

**E1. Source unit tests.** `python -X utf8 -B -S test_verify.py` on a scratch copy: 20
tests pass in 5.4 s.

**E2. All 2925 entries, re-derived and decided with this repository’s kernel.**
`independent_pass.py` reads only `orbits.json` and `catalogue.json`. It rebuilds the
measure, decides D4 invariance atom by atom, expands the catalogue, checks contiguity,
the relative-angle bound and strict containment, derives each inset, and calls
`sqpack.fractional.sweep.minimum_covered_mass_integer` with its centre domain replaced
by the parent-centre envelope.
Result: 1616 atoms, 2925 entries, 353 s on 4 workers, least minimum `250023/250000`, no
entry below `gamma`. Compared row by row with the coordinator’s source replay
(`receipts/guzhou-r012-source-replay-2026-09-20.coverage.jsonl.xz`), **the exact minimum
agrees on all 2925 entries**. The minima take five values.
Twenty entries, indices 2238 to 2257, equal `gamma` exactly, so `gamma` is tight.
F9 limits what this agreement shows.

**E3. Separating-axis pass, sharing nothing with either kernel.** `sat_pass.py` forms
cells from capture-rectangle edges and far sentinels only, with no domain vertex as an
event. A cell counts as reachable when the open cell meets the open domain, decided by
the separating axis theorem on the four edge normals.
The predicate is screened in `float64` with a `1e-9` guard band, and every cell inside
the band is decided again in exact Fractions.
Masses are exact `int64` sums.
Result so far: the first 25 sampled entries agree with the source minima.

**E4. Brute force on small instances.** `small_bruteforce.py` builds random instances of
up to 11 atoms, some placed so that capture edges pass through domain vertices, with
`t = 0` among the directions.
Its oracle enumerates arrangement vertices and steps into every adjacent cell, forming
no strips. Seeds 1 and 2: 100 instances; the R012 tree backend, the R012 direct backend,
the repository kernel and the oracle agreed on every one, and none was refused.

**E5. Mutation, and the core’s own domain.** On tight entry 2238, lowering one captured
atom’s weight by `3/1000000` moved the source kernel’s minimum from `250023/250000` to
`1000089/1000000`, below `gamma`, so the `gamma` test is live.
Swept over the core’s own centre domain, entries 0 and 1 give `493737/500000` and
`492619/500000`; entries 30, 60, 1188, 1189, 2238 and 2924 are unchanged.

**E6. Random real parents.** 600,000 parents over 15 entries, with a real angle in the
interval, a centre in the legal square for that angle (35% on its boundary), and a cloud
about the sweep’s own minimiser.
No sample’s mass fell below the swept minimum; the least sampled mass equalled it to six
decimals in every entry; `B (cos d + |sin d|) < A` held throughout.

**E7. Running without `-B`.** `--records` prints `PASS_RECORDS_ONLY` with `-B` and
`FAIL_OR_INCOMPLETE: ValueError: certificate file set differs from manifest` without it.

**E8. Lineage.** `catalogue_facts.py`; results in F8.

## 5. What a First-Party Verification Would Still Need

1. A registered first-party decision of R012’s coverage that does not inherit the
   reachable-cell idiom (F9). The coordinator’s interval branch and bound in
   `replay_guzhou_r012_first_party.py` is such a method.
   E2 shows that the exact kernel also decides every entry, in about six minutes on four
   workers, once its centre domain is a parameter.
2. The obligations list for that instrument: the pinned parameters; the rebuilt measure
   with its mass and symmetry; contiguity from 0 to `T` with `T^2 + 2T - 1 > 0`; for
   each entry the relative-angle range and strict containment at both endpoints, and the
   inset from the endpoint minimum of `f`; coverage at least `gamma` over the closed
   envelope; `17 gamma > M`.
3. A first-party verdict on Mira’s Condition 5. Until the running replays finish, Mira’s
   least net-core mass is source-reported.
4. A decision on what to record.
   R012 and Mira’s certificate are separate results with separate premises, and R012’s
   value is the larger.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
