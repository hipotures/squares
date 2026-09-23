# Separation of Prior Art from Our Contribution (Investigation of 2026-09-15)

## Conclusion: All 6 elements of the method are pre-existing. Novelty lies solely in the first application to n ≥ 22.

| # | Element | Assessment | First appearance |
|---|---|---|---|
| 1 | Weighted fractional unavoidable set | **Pre-existing** | Göbel → Stromquist (weight 1, 1984 memo / 2003 EJC) → **Nagamochi 2005** (first weighted: point, segment, and area scores, hand-tuned, no LP) → **Sam Burns 2026-08** (first purely fractional version: n=17, 268 atoms, mass 16.9476) |
| 2 | D4 symmetry | **Pre-existing** | Standard in the field. Explicitly stated in Burns–Massaccesi Condition 1. jlevy uses it as D4 orbits in column generation |
| 3 | Shrink B<1 + finite rational direction net, B(1+D)<1 | **Pre-existing (most critical)** | **Burns 2026-08** established the framework of exact rational direction nets. **Massaccesi 2026-08** explicitly stated `cos ε + sin ε ≤ 1+ε ≤ 1+D` with 181 directions and B=0.9973. jlevy's Conditions 3/4 are restatements of Burns–Massaccesi with sources clearly cited. Our B=0.9977 and 201 directions are merely a parameter change. Shrinking itself is even older, coming from Stromquist's box trick, and both Nagamochi and Bentz papers use the same thing |
| 4 | Covering LP + row generation | **Pre-existing** | Massaccesi first determined weights via LP (rows fixed). **jlevy/squares** added row generation and cutting-plane loop via a separation oracle. Documented in TUTORIAL.md |
| 5 | Column generation via dual pricing | **Pre-existing** | **jlevy/squares**. Adds atomic orbits via reduced cost determination using the dual's `depth_y(x) ≤ 1`. Recorded the 24/5 certificate for n=19 as "a single resumed column generation run" |
| 6 | Branch and bound as a separation oracle | **Pre-existing** | **jlevy/squares**. `sqpack.fractional.certificate.py` runs interval branch and bound as the second verifier for Condition 5. Note that their event-cell sweep is stronger than box branch and bound, determining the true minimum of the continuum exactly |
| — | Medium-scale n (26, 29, 39, 40) | **Novel** | Fractional certificates have never once been attempted for n ≥ 22 |

## Errors in Our Previous Understanding
"Pre-existing methods are limited to n ≤ 22 or the specific cases 13/22/33/46" was **inaccurate**.
The actual frontier of fractional certificates is as follows:
- Burns: n=17 (4.4811)
- Massaccesi: n=17, 18, 19 (4.5058)
- jlevy/squares: n = 11, 12, 17, 18, 19, 20, 21 (T-017 to T-021), including s(21) ≥ 24/5 and s(20) ≥ 97/20
- anabologyco-maker: n=17 (4.5705), with a Lean 4 `native_decide` layer

## Why Novelty Still Remains
Upon directly checking jlevy's `packing/frontier/n-0{26,29,39,40}.md`, in all 4 cases,
**the only independently verified lower bounds are Nagamochi 2005's closed forms**:
- n=26: 5.1231, n=29: 5.4721, n=39: 6.2915, n=40: 6.4031

Green 2000's values (5.3918, 5.5117, 6.3506, 6.3852) are private communications via DS7 Theorem 9/10,
and **the proofs have never been recovered**. Our 4 cases step into this gap.

## Warnings Received and Our Verification Results
jlevy proves a **ceiling** for the method. For net parameter D, a certificate cannot
exist beyond `⌈√n⌉/(1+D)`. Furthermore, empirically, around n = 20, the covering value
is bound well below the ceiling, and the phenomenon where the LP gets pinned to a degenerate
vertex (⌈√n⌉² dual solutions of unit weight) has been observed. Since n=26, 39, 40 are larger
domains, there is a risk that this degeneracy acts more strongly.

**Verification Results (2026-09-15): None of the 4 cases are degenerate.**

| n | L | Mass | Stuck at ⌈√n⌉² | Ceiling ⌈√n⌉/(1+D) | L is below ceiling |
|---|---|---|---|---|---|
| 26 | 5.45 | 25.855744 | No (not 36) | 5.987576 | Yes |
| 29 | 5.57 | 28.992704 | No | 5.987576 | Yes |
| 39 | 6.50 | 38.519038 | No (not 49) | 6.985505 | Yes |
| 40 | 6.50 | 39.000796 | No | 6.985505 | Yes |

## Suggested Attribution in the Paper (Recommended Draft)
> We apply the weighted fractional unavoidable-set certificate method of Burns and
> Massaccesi (2026), which fractionalizes Stromquist's unavoidable point sets (1984/2003)
> and descends from Nagamochi's (2005) weighted point/segment/area score systems and
> Bentz's (2010, 2016) refinements. Following Burns and Massaccesi we reduce orientations
> via D4 symmetry and a rational direction net with the shrink condition B(1+D) < 1.
> Following the generator described in jlevy/squares (2026) we search for certificates by
> a covering LP with row and column generation and verify Condition 5 by interval branch
> and bound. Our contribution is the first application of this method to n ≥ 22,
> specifically n = 26, 29, 39, 40, where the only previously verified lower bound is
> Nagamochi's closed form and where Green's (2000) reported bounds rest on an unrecovered
> private communication.

## Additional Citations to Include
- Stromquist, *Packing 10 or 11 Unit Squares in a Square*, EJC 10 (2003) #R8, and unpublished 1984–85 memos I–III
- Nagamochi, EJC 12 (2005) #R37
- Bentz, EJC 17 (2010) #R126
- Bentz, arXiv:1606.03746 (Note that Theorem 8's "continuously varying family" is a continuity / topological argument, **not a relaxation**. It is not an ancestor of our fractionalization)
- Friedman DS7
- Burns and Massaccesi blog posts
- jlevy/squares repository
- Bašić–Slivková, *On optimal piercing of a square*, Discrete Appl. Math. 247 (2018) 242–251 (transversal framework)

## Contrast with Circle Packing (Framework Usable in Paper)
Markót–Csendes solved circles for n=28, 29, 30, and later 31–33 in 20–50 CPU hours each using pure interval branch and bound. This is a method that rigorously eliminates configuration space **directly**. Our method is a **dual certificate**, obviating the need to search configuration space. For unit squares allowing rotation, direct interval branch and bound has only reached n=3. This contrast constitutes a valid argument.

## Next Directions (If Aiming for Methodological Contributions)
jlevy has progressed beyond point atoms to **threshold atoms** (T-025/T-026, s(11) ≥ 191/50), which provably breaks the ceiling of point atoms. If aiming for a lasting methodological contribution, this is the open ground.

## Caveats / Reservations of the Investigation
1. The full text of Burns's proof notes could not be obtained, only the blog summary. The credit allocation between Burns and Massaccesi relies on Massaccesi's own attributions and jlevy's audit.
2. The fractional covering **principle** itself (LP relaxation of covering/hitting problems, Lovász) is textbook. jlevy explicitly stated that it is "a new instance of an established fractional covering principle, not a new principle." Adopting this framing is appropriate.
