# H-230 Gap-g Wedge Derivation (Session 148, chunk 5)

Status: **CANNOT REACH** (lane verdict), unreviewed: the adversarial review and the
`devtools.gap_wedge` port were stopped by the owner at 17:02Z and resume under
`think-n1v2`; the lane’s exact-check scripts are retained as text under
`h230-gap-wedge-scratch/` and the port’s partial diff as
`h230-gap-wedge-port-partial.patch`. The lane’s report follows as delivered.

Working notes, written incrementally.
Branch `claude/kind-wright-whxxn6-chunk5`, read-only; all computation with
`packing/.venv/bin/python3`, exact `Fraction` arithmetic wherever a number is a claim.
Assurance labels follow `conventions.md` section 4: *proved* (a complete argument in
this report), *verified* (an exact check on the retained record), *numerical* (a float
or high-precision figure that is a check on a reported number, not a claim).

## 0. The retained family (verified)

`lane-a6-loop-family-1.json` and `lane-a6-saturated-symmetric-153-40.json` (agenda-034)
are byte-identical: the A6 64-family, `n = 11`, `L = 153/40`, `B = 9977/10000`, total
weight exactly 11, 64 placements in 16 D4 half-orbits of four images each.
The two `lane-a6-independent-cut-family-*.json` records are atom-admission records
*about* this family (64 placements declared) and its 56-placement sibling, not families.
Census (tilt = 2 atan(half-tangent); gaps are the core’s distances to the four walls):

| tilt | weight x images | mass | nearest two wall gaps |
| --- | --- | --- | --- |
| 0 / 90 deg | 13/32 x 8 | 13/4 | 0.0012, 0.0012 (corners) |
| 0 / 90 deg | 1/8 x 8 | 1 | 0.0007, 1.143 (mid-wall) |
| 0.264 / 89.736 | 1/16 x 8 | 1/2 | 0.0017, 0.9995 |
| 0.527 / 89.473 | 1/16 x 8 | 1/2 | 0.0011, 1.134 |
| 0.791 / 89.209 | 1/4 x 8 | 2 | 0.0011, 0.9998 |
| 1.318 / 88.682 | 1/8 x 8 | 1 | 1.0015, 1.005 (interior) |
| **7.111 / 82.889** | **3/32 x 8** | **3/4** | **0.0159 (wall), 0.0931 (adjacent wall)** |
| 29.892 / 60.108 | 1/4 x 8 | 2 | 0.6417, 0.7089 (interior) |

The 7.11 degree orbit X-040 names is the eight-image D4 orbit of half-tangent
`621321/10000000`, weight `3/32` per image, mass `3/4`, sitting in each corner with its
nearest wall at gap `0.0159` and the adjacent wall at gap `0.0931`. The largest weight
in the family is `13/32 < 1/2`.

Correction to the paragraph above: the two 64-placement files that are byte-identical
are `lane-a6-loop-family-1.json` and `lane-a6-saturated-symmetric-153-40.json` (md5
`70c8d780…`). `lane-a6-independent-cut-family-1.json` is the threshold-atom admission
record *about* that family (`placements: 64`, `declared_total_weight: 11`,
`distinct_sites: 76`, `admitted: false`), `-2.json` the same for the 56-placement
sibling, and `lane-a3-family-153-40-sites-round1-exact25.json` is the 280-placement
lane-a3 family, not the A6 one.
Everything below is on the 64-family.
All 64 placements have positive weight, so “every pair with positive weight” is all 2016
unordered pairs.

Scripts (all `packing/.venv/bin/python3`, exact `Fraction`): `census.py` (section 0),
`wedge.py` (lemma tools, rigorous rational bounds on the intrusion depths),
`family_test.py` / `family_test.out` (per-wall pocket data and the 1344 ordered
(placement, wall, neighbour) pocket contacts), `robust_check.py` / `robust_check.out`
(admissible unit squares, separations from the 7.11° pockets, the 88 near-overlap
pairs), `extended.py` / `extended.out` (S–S conflicts, extended-depth maximum, exact
7.11° numbers, g_max curve).
Total runtime under a minute.

## 1. The gap-g wall-wedge lemma (proved)

**Frame.** Wall `y = 0`, container above it.
`Q` is a closed unit square whose lowest vertex is `V = (0, g)`, `0 <= g < 1`; its
lower-right edge leaves `V` at angle `θ` and its lower-left edge at angle `π/2 − θ`,
`0 <= θ <= π/2`; `c = cos θ`, `s = sin θ`. The other vertices are `E_R = (c, g + s)`,
`E_L = (−s, g + c)`, `E_T = (c − s, g + s + c)`. The *pockets* are the regions between
`Q` and the wall:

```
T_R = {0 <= x <= c, 0 <= y <= g + x s/c},   area  c g + ½ s c,
T_L = {−s <= x <= 0, 0 <= y <= g − x c/s},  area  s g + ½ s c.
```

(`T_R` is a trapezoid of width `c` with parallel sides `g` and `g + s`; at `g = 0` it is
the wall-vertex triangle of X-040 row D6.)

**Lemma A (unit square in a wedge; tight).** Let `0 < ψ <= π/2` and let a unit square
`P` lie in the wedge `{y >= 0, y <= (x − a) tan ψ}`. Then every point of `P` has
`x >= a + cos ψ cot ψ`, and this is attained.

*Proof.* Write `P`’s orientation as `α ∈ [0, π/2)` and label its vertices lowest `Λ`,
leftmost `W = Λ + (−sin α, cos α)`, topmost `T = W + (cos α, sin α)` (for `α = 0` the
labels are degenerate and the bound follows by closedness).
From `y_Λ >= 0`: `y_W >= cos α`, `y_T >= cos α + sin α`. The upper wedge line applied at
`W` gives `x_W − a >= cos α cot ψ`, and applied at `T` gives
`x_W − a >= (cos α + sin α) cot ψ − cos α`. The first bound decreases in `α`, the second
`f(α) = cos α (cot ψ − 1) + sin α cot ψ` has `f'(ψ) = (1 − sin ψ cos ψ)/sin ψ > 0` and
`f(π/2) = cot ψ >= cos ψ cot ψ`, so on `[ψ, π/2]` it stays above its value at `α = ψ`;
the two bounds cross exactly at `α = ψ`, where both equal `cos ψ cot ψ`. Hence
`x_min >= a + cos ψ cot ψ`. Attained by the square with an edge on the upper wedge line
at distance `cot ψ` from the apex (its lower vertices then touch the wall).
∎

**Lemma B (gap-g pocket protection).** Let `P` be any other unit square in `{y >= 0}`
interior-disjoint from `Q`. Define, with `u = cos ψ`,

```
d_R(θ, g) = max( max_{ψ ∈ [θ, π/2]} cot ψ (g + s − cos ψ),
                 max_{ψ ∈ (0, θ]}  [ c − cot ψ (cos ψ − g) ] ),
d_L(θ, g) = the same with c and s exchanged,
```

i.e. `d_R = max_{u ∈ [0, min(c, g + s)]} u (g + s − u)/√(1 − u²)` when `g <= c` (the
second family is then dominated by `ψ = θ`, where the two agree, because
`cot ψ (cos ψ − g)` is decreasing in `ψ` while `cos ψ > g`). Then

```
P ∩ T_R ⊆ {x >= c − d_R} ∪ {x <= d_L − s},   P ∩ T_L ⊆ {x <= −s + d_L} ∪ {x >= c − d_R},
```

so the *forced-empty regions*

```
S_R = T_R ∩ {max(0, d_L − s) <= x <= c − d_R},   S_L = T_L ∩ {−s + d_L <= x <= −max(0, d_R − c)}
```

contain no point of any other square of the packing, and the packing wastes

```
A(θ, g) = area(S_R) + area(S_L),
area(S_R) = (x_r − x_l) (g + ½ (x_l + x_r) s/c) for x_l = max(0, d_L − s), x_r = c − d_R (0 if x_r <= x_l),
```

per square (`area(S_L)` mirrored).
At `g = 0` and `d_L <= s`, `d_R <= c` this is `½ s c (1 − d_R/c)² + ½ s c (1 − d_L/s)²`,
X-040’s formula, with `d(θ)` the intrusion depth measured from the pocket’s open end.

*Proof.* `P` and `Q` are convex and interior-disjoint, so some supporting line `ℓ` of
`Q` has `P` in the closed half-plane `H` opposite `Q`. Parametrise `ℓ` by the vertex it
passes through and its outward normal angle `φ` (exterior angle ranges: at `V`,
`φ ∈ [−90° − θ, −90° + θ]`; at `E_R`, `[−90° + θ, θ]`; at `E_T`, `[θ, 90° + θ]`; at
`E_L`, `[90° + θ, 180° + θ]`). A direct check of `n · (p − vertex)` at the four corners
of `T_R` shows `H ∩ T_R` is empty or a single boundary point for every line through
`E_T`, for the lines through `E_R` with `φ ∈ (0, θ]`, and for the lines through `E_L`
with `φ` in `[90° + θ, 180°]`; the remaining cases are: (i) `ℓ` through `E_R`, line
angle `ψ = φ + 90° ∈ [θ, 90°]`: `P` lies in `{y >= 0}` below `ℓ`, a wedge of angle `ψ`
with apex on the wall at `x = c − (g + s) cot ψ`; Lemma A gives
`x_min(P) >= c − cot ψ (g + s − cos ψ)`. (ii) `ℓ` through `V`, line angle `ψ ∈ (0, θ]`:
wedge with apex `−g cot ψ`, so `x_min(P) >= cot ψ (cos ψ − g)`; `ψ = 0` is impossible
(`P` would lie in a strip of height `g < 1`). (iii) `ℓ` through `V` with negative line
angle `−β`, `β ∈ (0, 90° − θ]`, or through `E_L` with `φ ∈ (180°, 180° + θ]`: these are
cases (ii) and (i) of the *left* pocket in the mirrored frame (`θ ↔ π/2 − θ`, `x ↔ −x`),
so `P` is a left-opening wedge occupant with `x_max(P) <= −s + d_L`. Taking the maxima
over each family gives the displayed inclusions; `S_R`, `S_L` are the parts of the
pockets outside every reachable zone, and they lie inside the container because `Q` does
(`x_V − s >= 0`, `x_V + c <= L`). ∎

**Lemma C (extended regions at a common wall have disjoint interiors).** For two
interior-disjoint unit squares `Q_a`, `Q_b` in the container and one fixed wall `w`,
with `S_a`, `S_b` their forced-empty regions at that wall: `int S_a ∩ Q_b = ∅` (Lemma B)
and `int S_a ∩ int S_b = ∅`. Hence, per wall, the regions `U ∪ S^{(w)}` of the squares
of a packing are pairwise interior-disjoint.

*Proof of the second claim.* Suppose `p ∈ int S_a ∩ int S_b`. The ray from `p` away from
the wall meets the lower boundary of `Q_a` at `q_a` and of `Q_b` at `q_b`, both beyond
`p` (each pocket is the region between the wall and the square over the pocket’s
along-wall range); say `q_b` is the nearer one.
Then `q_b` is on `Q_b`’s boundary and strictly inside `T_a` at the same along-wall
coordinate as `p`, hence in `S_a`; points of `int Q_b` just beyond `q_b` lie in
`int S_a`, contradicting Lemma B. ∎

Pockets of two squares at *different* walls are not covered by this lemma (a point in a
corner can lie under one square’s bottom pocket and beside another’s side pocket without
contradiction), so the extended-capture inequality below is stated per wall.
The family test in section 3 checked all S pieces against each other, across walls too,
and found no overlap, so nothing there depends on the distinction.

**Validity range and g_max.** Lemmas A–C hold for every `0 <= g < 1`; the argument gives
a nonempty `S` exactly when `c − d_R > max(0, d_L − s)` or its mirror.
Numerically (`extended.out`, sampling plus golden refinement, float):
`g_max(7.11°) ≈ 0.959`, `g_max(20°) ≈ 0.863`, `g_max(30°) ≈ 0.775`,
`g_max(40.18°) ≈ 0.715`, `g_max(45°) ≈ 0.7071`. The waste is *not* maximal at `g = 0`:
at fixed `θ` it rises with the gap (the strip `c g + s g` is added faster than the
intrusions grow) until `g ≈ 0.2`–`0.4`, e.g.
`A(40.18°, g) ≈ 0.3203, 0.3298, 0.3721, 0.4034, 0.3547` at
`g = 0, 0.0146, 0.0918, 0.2, 0.4`.

**Check at g = 0, θ = 40.18° (numerical, matches X-040 / R2).** The stationary point of
`f(u) = u (G − u)/√(1 − u²)` is the root of `G − 2u + u³ = 0`: for `G = s = 0.64519`,
`u* = 0.34272`, `d_R = 0.110346`; for `G = c = 0.76402`, `u* = 0.41872`,
`d_L = 0.159214`;
`A = 0.5 s c [(1 − d_R/c)² + (1 − d_L/s)²] = 0.18042 + 0.13984 = 0.32025`. The rigorous
rational bound from `wedge.d_R_upper` (400-piece envelope, `A >= 0.32014`) brackets it.
This is R2’s `0.3203`; the lemma reduces to lane 2’s wall-vertex lemma at `g = 0`.

**Rigour of the computed bounds.** `wedge.d_R_upper` bounds each `u (G − u)/√(1 − u²)`
piecewise (concave-quadratic maximum over the piece, `1/√(1 − u²)` at the piece’s right
end, rational `isqrt` bounds) and handles the `g > c` V-family separately, so every `d`
used below is a rational **upper** bound and every `S` polygon a rigorous **subset** of
the true forced-empty region; every `A` quoted is a rigorous lower bound.
The untrimmed pockets `T` are exact.

## 2. The two-body conflict condition (proved)

Let placements `p`, `q` stand for unit squares `U_p`, `U_q` (concentric with the
recorded cores, at the recorded tilt; where the concentric unit square leaves the
container by `<= 4.2e-4`, it is translated back inside — 24 placements of mass 7/2 need
this, see finding 6). Define the *extended region*
`E(p) = U_p ∪ ⋃_walls (S_R ∪ S_L)(U_p)`.

**Conflict condition (exact, pairwise).** `p` and `q` cannot coexist in a physical
packing if `int E(p) ∩ int E(q) ≠ ∅`, i.e. if any of

(a) `int U_p ∩ int U_q ≠ ∅` (ordinary overlap), (b) `U_q ∩ int S(U_p) ≠ ∅` or
`U_p ∩ int S(U_q) ≠ ∅` (a square enters the other’s pocket), (c)
`int S(U_p) ∩ int S(U_q) ≠ ∅` (pockets overlap),

each decided exactly by a separating-axis test on rational polygons, (c) taken at a
common wall. As a function of the two tilts, the two gaps and the along-wall separation
`x` of the lowest vertices (`V_p = (0, g_p)`, `V_q = (x, g_q)` in the wall frame,
`x > 0`), (b) for `q` entering `p`’s right pocket is: the polygon `U_q` meets the open
trapezoid `{max(0, d_L(θ_p, g_p) − s_p) < x' < c_p − d_R(θ_p, g_p),
0 < y < g_p + x' s_p/c_p}`, whose left end is `q`’s leftmost point `x − s_q` when `q`’s
lower-left edge is the one facing `p`; and (c) is the overlap of two such trapezoids,
one per square, in the same frame.
Validity: (a) is the packing condition; (b) and (c) are Lemma B and Lemma C. ∎

**But (b) and (c) are consequences of (a) for unit squares.** Lemma B and C are of the
form “disjoint ⇒ pockets respected”; their contrapositives say “a square in a pocket, or
overlapping pockets, ⇒ the squares overlap”.
So for unit squares the wedge conflict edge is *never stronger than the overlap edge*.
The only way it can be new in the certificate language is through the shrunk relaxation:
two **cores** (side `B = 9977/10000`) that are disjoint while the extended regions of
their unit squares meet.
That is the condition tested in section 3, and it is the only place a conflict-edge atom
could gain anything.

Area form.
Since `E(p)`, `E(q)` are interior-disjoint subsets of the container, any strip
`[0, L] × [0, h]` satisfies `area(E(p) ∩ strip) + area(E(q) ∩ strip) <= L h`; this is
implied by (a)–(c) and is weaker, so it is not tested separately.
Globally the family would have to waste more than `L² − 11 = 3.63` for an area argument
to bite; the family’s total forced-empty area is about `0.17 + 0.03 = 0.2` (7.11° orbit
plus the near-axis strips), so area is hopeless at n = 11.

## 3. The exact test on the 64-family (verified)

**Per-orbit forced-empty areas (rigorous lower bounds, unit squares, nearest walls).**

| orbit (tilt, weight) | wall gap g of the unit square | d_R, d_L (upper bounds) | A >= |
| --- | --- | --- | --- |
| 0°/90°, 13/32 (corners) | 0.00002 | 0, 0 | 0.00002 |
| 0°/90°, 1/8 (mid-wall) | −0.00042 → shifted to 0 | 0, 0 | 0.00042 (at the nominal pose) |
| 0.264°, 1/16 | 0.00054 | 0.00001, 0.00458 | 0.00284 |
| 0.527°, 1/16 | −0.00009 → 0 | 0.00002, 0.00912 | 0.00460 |
| 0.791°, 1/4 | −0.00010 → 0 | 0.00005, 0.01361 | 0.00690 |
| **7.111°/82.889°, 3/32, nearest wall** | **0.014635** | **0.004802, 0.110170** | **0.076219** |
| **7.111°/82.889°, 3/32, adjacent wall** | **0.091805** | **0.011689, 0.119797** | **0.150434** |
| 1.318°, 1/8; 29.9°/60.1°, 1/4 | >= 0.64 (interior) | — | 0 (no S survives) |

The 7.11° member (index 40; `half-tangent 621321/10000000`,
`cos = 99613960214959/100386039785041`, `sin = 12426420000000/100386039785041`) has core
gaps `(l, r, b, t) = (2.6184, 0.093088, 2.6956, 0.015918)` and unit-square gaps
`g_top = 1697680742228220374051/116002622172292042976480 = 0.014635`,
`g_right = 1679546273130697871177/18294809650767291626960 = 0.091805`. Its pockets: top
wall `T_R`, `T_L` of areas `0.06323`, `0.07594`; right wall `0.15252`, `0.07278`. **The
gap extension does reach the 7.11° orbit at gap 0.016**: it protects `A >= 0.0762` under
the nearest wall and `A >= 0.1504` under the adjacent one, `0.2266` per member, `0.17`
over the orbit’s mass `3/4`. H-230’s second kill clause ("the wedge shrinks to zero at
7.11° and gap 0.016") is therefore *not* what kills it.

**Pairwise results, all 2016 pairs, exact.**

- Pairs whose cores overlap (interior): 480 unordered (960 ordered in
  `family_pairs.json` counting walls).
  Every one of the 376 ordered (a, wall, b) contacts in which `U_b` enters `S(U_a)` has
  overlapping cores. **Pairs with disjoint cores and `U_b` entering `S(U_a)`: 0.** With
  `core_b` entering `S(U_a)`: 0. (`family_test.out`, `robust_check.out`.)
- **Pairs with disjoint cores and `int S_a ∩ int S_b ≠ ∅`: 0** (`extended.out`, all 120
  S pieces against each other).
- Pairs with disjoint cores whose unit squares overlap: 88, all with core separation
  `0.00007` and unit overlap depth `<= 0.00236` — the ordinary shrink-tax near-overlaps
  (the 1.32°/88.68° mid-wall members against the 0.53°/89.47° ones, and the 60.11° ring
  members against each other).
  These *are* valid conflict edges `x_p + x_q <= 1` independent of any wedge lemma, and
  the family satisfies each with room: the largest pair sum among them is
  `1/4 + 1/4 = 1/2`.
- Hence **no pair of positive-weight placements violates the wedge conflict condition**,
  and no pair of the family violates any pairwise edge at all, since every weight is
  `<= 13/32 < 1/2`.

**The aggregate an atom would price (verified).** The per-wall extended-capture point
inequality `Σ_{p : z ∈ U_p ∪ S_p^{(w)}} x_p <= 1` is valid for every `z` and wall `w`
(Lemma C); the quantity computed below counts `S` pieces at all walls at once, so it
bounds every per-wall version from above.
Over all 1724 vertices and pairwise edge intersections of the 64 cores and 120 S pieces,
the closed extended depth of the family is **exactly 1**, attained only where the core
depth is already 1 (the corner: `13/32 + 13/32 + 3/32 + 3/32` from the two corner
placements and the two 7.11° images at the corner core’s edge `x = 0.9989`; the mid-wall
stacks). Since the closed vertex maximum bounds the depth of every open cell, the
family’s extended depth never exceeds 1: extended-capture point atoms, and threshold or
floor atoms built on them, do not cut.

**Why the extension cannot reach the 7.11° orbit as a two-body cut (exact numbers).**
Every square that enters a 7.11° pocket is one whose *core already overlaps the 7.11°
core* (the corner squares at `13/32`, the 0.79°, 0.26°, 0.53° and mid-wall members along
the two walls, the mirror image), so their conflicts are already priced by the point
atoms, and the family pays for them (depth exactly 1 in the corner).
The nearest core-disjoint positive-weight neighbours of member 40 are

| neighbour | wall | dist(U_b, T) | dist(core_b, T) | dist(U_b, S) |
| --- | --- | --- | --- | --- |
| 57 (0.53°, w = 1/16) | right (g = 0.0918) | **0.002940** | 0.004091 | 0.122732 |
| 24 (0°, w = 1/8) | right | 0.011166 | 0.012316 | 0.130963 |
| 57 | top (g = 0.0146) | 0.112087 | 0.113238 | 0.996221 |
| 24 | top | 0.120318 | 0.121468 | 1.003475 |

(exact rationals for the squared distances are in `extended.out`; the same numbers hold
for the other seven images by D4). The quantity that is too small is the reach of the
pocket at its open end: the 0.53° neighbour sits `0.00294` outside the *untrimmed*
pocket `T` of the adjacent wall and `0.1227` outside the provably empty part `S`,
because the intrusion depth there is `d_L(7.11°, 0.0918) = 0.1198` and Lemma A is tight
(a unit square with an edge on the supporting line through `E_L`, touching the wall,
physically occupies that zone while disjoint from `Q`). No lemma of the form “the region
between the square and the wall is empty” can protect more than `T` minus its intrusion
zones, so to conflict with the nearest core-disjoint neighbour a lemma would need a
protected region extending `>= 0.1227` beyond `S` along the wall (`>= 0.0029` beyond
`T`), i.e. it would have to forbid a configuration that is realisable.
And even that edge would be `x_40 + x_57 <= 1` against a pair sum of
`3/32 + 1/16 = 5/32`.

## 4. What an instrument would need, and its price

A conflict-edge atom in `sqpack.fractional.relational` would be a *clique atom*
`(K, w)`: `K` a D4-closed set of pose cells (centre rectangle × net direction), charge
`w` to a core in any cell of `K`, budget `w`, with the certificate obligation that any
two cores in distinct cells of `K` (or in one cell) cannot coexist.
Point atoms are the case where `K` is “cells whose closed core contains a site”.
Beyond the serializer, Condition 1' symmetry and the charge arithmetic (all reusable),
it needs a **two-body cell predicate**: for each pair of cells prove every pair of poses
conflicts, by interval boxes over centres and directions (the
`minimum_charge_interval_boxes` style, but pairwise) — a new verification route with its
own independent second implementation under the two-route rule.
With `int E(p) ∩ int E(q) ≠ ∅` as the conflict, the predicate needs Lemma B’s `d` bounds
per cell (monotone in `g`, so box bounds are easy) and polygon-intersection certainty
over the box. Estimate: several days of tooling plus the review of a new counting
argument, comparable to the D4 unshrunk verifier.

Priced against section 3: the family violates none of the 2016 pairwise conditions, its
extended depth is `<= 1` everywhere, and the only conflict edges the family’s disjoint
cores do carry are the 88 shrink-tax near-overlaps, whose value is bounded by the
unshrunk correction X-040 already prices at `<= 0.0024` at n = 11. The instrument would
be built to price a relation the retained family already respects.
Do not build it for this purpose; the record for BC-364’s exit is the reason above.

## 5. Verdict

```
VERDICT: CANNOT REACH
```

The gap-g lemma exists, is proved here, reproduces `0.3203` at `g = 0`, and reaches the
7.11° orbit (`A >= 0.0762` at gap `0.0146`, `>= 0.1504` at the adjacent wall’s gap
`0.0918`); but its conflict edge is implied by disjointness for unit squares, is new
only through the core relaxation, and on the 64-family every square that enters a 7.11°
pocket already overlaps the 7.11° core, while the nearest core-disjoint neighbour is
`0.1227` outside the provable region (`0.0029` outside the whole pocket, inside a
realisable intrusion zone).
H-230’s first kill clause holds: the best provable gap extension leaves every weighted
pair of the family compatible.

## Numbered findings

1. (proved) Lemmas A–C: a unit square in a wedge of angle `ψ` keeps `cos ψ cot ψ` from
   the apex, tight; a square at gap `g` and tilt `θ` forces empty the pocket parts
   `S_R`, `S_L` with intrusion depths `d_R = max_u u(g + s − u)/√(1 − u²)` (and mirror),
   valid for all `0 <= g < 1`; extended regions of disjoint squares are
   interior-disjoint.
2. (numerical, matches R2) `g = 0`, `θ = 40.18°`: `d_R = 0.110346`, `d_L = 0.159214`,
   `A = 0.32025`; rigorous rational bound `A >= 0.32014`.
3. (numerical) `A(θ, g)` increases with `g` up to `g ≈ 0.2`–`0.4`; `g_max ≈ 0.959` at
   7.11°, `0.7071` at 45°.
4. (verified) The 7.11° orbit (mass 3/4, unit-square gaps `0.014635` and `0.091805`) is
   reached: `A >= 0.076219` and `>= 0.150434` per member.
5. (verified) On all 2016 pairs of the 64-family: 0 core-disjoint pairs with a square in
   the other’s `S`, 0 with `int S ∩ int S ≠ ∅`; the closed extended depth maximum is
   exactly 1, equal to the core depth there; 88 core-disjoint pairs have overlapping
   unit squares (shrink tax, depth `<= 0.00236`), none with pair sum above `1/2`.
6. (verified, incidental) 24 placements of total mass `7/2` (the mid-wall `1/8` orbit at
   core gap `0.0007`, the 0.79° `1/4` orbit and the 0.527° `1/16` orbit) have concentric
   unit squares that leave the container by `1e-4`–`4.2e-4`; the physical core of a
   contained unit square at net angle `α'` within `δ` of its true angle sits at gap
   `>= ½[(cos α' + sin α')(cos δ − B) − |cos α' − sin α'| sin δ] > 0`, so a one-body
   domain tightening is valid but only moves these sites by `<= 4.2e-4` (the D4 unshrunk
   correction, `<= 0.0024`), not a cut.
7. (proved) For unit squares the wedge conflict edge is implied by the overlap edge; a
   conflict-edge atom class gains only through the shrunk relaxation, and on this family
   that gain is zero beyond the near-overlap edges.
8. (assessment) A clique-atom class with a two-body cell predicate is several days of
   tooling; against finding 5 it would price nothing on this family.
   Recommend recording BC-364’s gap-g exit as “cannot reach” and disposing H-230 as
   killed under its first clause, keeping the lemma (section 1) as the reviewed
   derivation note.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
