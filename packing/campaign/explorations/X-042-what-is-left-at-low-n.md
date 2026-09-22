---
title: X-042 — what is left at low n, after the n = 17 ladder merged
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-042
  title: What Is Left at Low n, After the n = 17 Ladder Merged
  date: '2026-09-22'
  author: Claude session-151 coordinator, with four Fable review lanes and an adversarial Fable validation lane
  campaign: packing.squares
  brief: >-
    Ask again what significant improvement is available at n = 11, n = 17 or another
    low n, now that T-031, T-032 and the Kleddamag retention have merged and the n = 17
    ladder carries five values. Four lanes with disjoint deliverables: the n = 11
    one-body ceiling and what provably escapes it; the n = 17 measure and where the
    remaining gap lives; the cross-n integer plateaus; and the upper-bound and search
    side, which no lower-bound lane covers. Each lane recomputes the arithmetic it
    relies on, because a review that only reads the record inherits the record's errors.
  sources:
  - AGENTS.md
  - operating-rules.md
  - epistemics.md
  - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
  - packing/campaign/explorations/X-041-after-the-n17-certified-bound.md
  - packing/campaign/explorations/X-037-n11-overnight-review-and-route-slate.md
  - packing/frontier/n-011.md
  - packing/frontier/n-017.md
  - packing/frontier/RESULTS.md
  - packing/frontier/CERTIFICATE-REACH.md
  - packing/frontier/covering-values.yaml
  - packing/resources/web/n17-kleddamag-certified-bound-2026-09-21/kleddamag-17-squares-certified-bound/global-certificate.json
  - docs/project/reviews/review-2026-09-20-n17-r012-and-mira-4613-proof-review.md
  - docs/project/reviews/review-2026-09-21-n17-kleddamag-461300-99853.md
  proposes: []
---
# X-042: What Is Left at Low n, After the `n = 17` Ladder Merged

**Status: a review and a ranked slate.** Two measurements were taken while it ran and
are reported here with their rungs; no bound moved and no hypothesis was decided by this
document. `X-041` is its predecessor and this report contradicts it in nine places, each
named below with the recomputation that settles it.

## The Three Claims a Reader Should Carry Away

Stated first, with their evidence, because each one redirects work that `X-041` ranked
differently.

> **1. The `n = 17` ladder is not converging on `4.613`; it is climbing away from it,
> and the only invariant of a certificate in that language is `sigma = L/A`.** `A` moved
> *away* from 1 across the five values — `0.99999379`, `0.99999`, `0.99975`, `0.99951`,
> `0.99853` — and `L/A` rises as `A` falls.
> Under the scale invariance of the parent language, `L = 4613/1000` is a normalisation
> inherited from Mira’s atom coordinates, not a constraint, so “a larger `L`” is not a
> mechanism at all. The cap on the ladder is `s(17)`, not `4.613` and not `4.6755`.

> **2. The external `n = 17` measure has not been re-priced against its own final
> catalogue, and that — not the restriction, and not the atoms — is where its remaining
> headroom is.** Two-thirds of its 7,853 rows sit on a plateau at the identical minimum
> `1.00207034`; 2,631 rows lie below it, 26 within `1e-4` of the global minimum.
> The surplus the measure was priced to carry is `0.0368`; what survived is `1.13e-4`.
> Row generation is not converged.

> **3. At `n = 19` and `n = 26` the target itself is the least defended number in the
> low range.** No computer search on record, first-party or external, has ever reached
> Wainwright’s 1979 `n = 19` packing; the repository’s best is `0.073` short.
> `n = 26` has the largest gap below `n = 27` at `0.4982` and has been improved twice
> historically. Every lower-bound lane aims at a number that at these two sizes nobody
> has defended.

All three are `V0/C0`: each is a reading taken once, in one-off code, on retained bytes.
`OR-1` is explicit that a measurement left in one-off code is a missing tool, and the
three tools these readings show are worth building are named in the slate.

## Evidence Boundary

Read in full by the lanes: `AGENTS.md`, `operating-rules.md`, `epistemics.md`, `X-040`,
`X-041`, `X-037`, `n-011.md`, `n-017.md`, the `T-025`, `T-026`, `T-030`, `T-031` and
`T-032` register entries, `CERTIFICATE-REACH.md`, `covering-values.yaml`, the `T-025`
and `T-026` proof packets, the lane-a2 finer-net record, the two `n = 17` proof reviews,
the Kleddamag artifact’s `PROOF.md`, `global-certificate.json` and release replay, and
the `ceiling`, `threshold`, `relational`, `certificate` and `sweep` modules.

Not done here: no gate was run by any review lane, no instrument was built or retained
by one, and the artifact’s own checkers were not re-run except as noted.
The two measurements this document reports as its own are the `A1` sweep row and the
environment repair, both below.

## Nine Corrections to `X-041`

Each was found by recomputation, not by reading.
Where a correction changes what should be run, the slate row says so.

| # | `X-041` says | Recomputed | Consequence |
| --- | --- | --- | --- |
| 1 | The covering-LP experiment tests “what the selector and the restriction are worth” | `A2` as specified also swaps the adaptive per-row selector (`t` within `0.006°`, `B_row` in `[0.998367, 0.998526]`) for fixed net directions and `B_min` | A plain fail confounds the restriction with the catalogue change and cannot be reported as the restriction’s worth |
| 2 | `A1`’s kill: a lock at `B = 0.9995` means the restriction carries at least `4.6142 − 4.6130` | The rigorous floor is `4.61415 − 4.61398 = 0.0002`, and it is a floor on restriction *plus* selector *plus* support difference | The kill rule as written overstates by 6× |
| 3 | The universal one-body ceiling is “`>= 4.6137` (Mira’s unrestricted point certificate)” | The certificate proves `4.61303`, its dilation endpoint; `4.6137 = L/B` is the `D -> 0` idealisation the lane-a2 record says does not hold for frozen atoms | Over by `6.6e-4` |
| 4 | “Exactly one row is tight … no other within `1e-6`” | Literally true and misleading as a headroom signal: 13 rows are within `1e-5`, 26 within `1e-4`, and two-thirds sit on a `1.00207` plateau | The tight-row count is not the quantity that carries information; the slack distribution is |
| 5 | “The restriction is worth at least `+0.0011` when priced for” | R038’s `+0.0011` over R012 is confounded with the selector *and* a doubling of the support (3,280 against 1,616 atoms) | “At least” is not established |
| 6 | `L*` “is exactly T-025’s own `L/B` on the 181 net” | True by construction — the family and T-025 share `(L, B)` — not by theorem; and `L/B` is not the theorem-bounded quantity | A point certificate’s `L/B` may exceed `L*` by `(1+D)/sqrt(1+D^2)`, up to `3.837607` on the 181 net |
| 7 | The `n = 17` atoms are virtual sites, the `n = 11` atoms encode relations | T-025 itself carries a D4 orbit of eight 2-of-3 atoms of diameter `0.0006`, 7.1% of its threshold budget, straddling `x = B` | Right in proportion (93% wide), wrong as a dichotomy: `n = 11` already uses the virtual-site trick |
| 8 | `n = 20, 21`: “what binds: integer endpoint” | The endpoint forbids reaching `5`, not improving `4.85`; on retained site sets the covering value binds (`19.81` at `4.85`), extrapolating to crossing `20` near `4.86`. Same conflation for `n = 12` | Two slate rows misdiagnosed; a `+0.005` to `+0.01` prize is mislabelled unreachable |
| 9 | `L/B = 3.833820` for `153/40` | `38250/9977 = 3.833818` | Sixth decimal |

A tenth item is an omission rather than an error.
The parent-centre envelope restriction is priced for `n = 17` throughout `X-041` and
never considered for `n = 11`, where the core-scale 88-family does not obstruct it at
`3.82`: its 40 axis-aligned placements have centres `0.498853` from the wall against the
envelope inset `0.5`. It cannot pass `L*`, but it is the cheapest unused lever inside
the last `0.0024` and a free tightening of every retained certificate.

## What the `n = 11` Ceiling Is, Exactly

The `L*` argument reconstructs without a gap.
Scale the 88-family by `1/B` into unit squares in `[0, L*]^2` with closed depth at most
1 and weights summing to 11; weak duality then forces `mu(K) >= 11` for any measure
charging at least 1 to each member; and T-025’s own selection step puts an admissible
core inside each member, so depth does not rise.
No point certificate exists at any side at or above `L* = 38200/9977`, for any shrink
and any net.

What a stronger method must violate is therefore exactly one of two hypotheses:
**additivity** — a charge that is not `mu(P)` for any measure — or **unconditionality**,
a hypothesis about the packing that removes poses of the family without removing count.
That is a sharper statement than the record had, and it settles four candidate routes
negatively at a stroke.
Angle-dependent measure families do not escape, because disjoint cores consume disjoint
sites and the pointwise maximum is a single one-body measure with the same guarantee.
Nor do per-direction shrinks, the unshrunk `B = 1` language, or the parent-centre
envelope. Only relational two-body atoms, `k`-of-`S` and floor atoms, structural
conditioning, the wall-wedge emptiness lemma and higher-rank compositions violate a
hypothesis.

Near-coincident triples sit precisely on the boundary, and the reason is now a
proposition rather than a histogram.
A 2-of-3 atom of diameter `eps` covers the median site’s capture square minus an
`eps`-collar, at a point atom’s budget — so it is a point atom at a
**direction-dependent** virtual site, which no single site can emulate, and which three
point atoms emulate only at budget `3w/2`. Its genuinely relational content is a
pinwheel cut, and a pinwheel needs three placement classes each containing exactly one
pair of the triple. At `eps = 0.014` that is a measure-zero coincidence against a finite
family; at `eps = 0.53` it is generic.
So the virtual-site mechanism is capped with the point language, and the wide-triple
language is not.

## What the `n = 17` Measure Is, Exactly

The sharpest new fact is the slack distribution, and it points somewhere `X-041` does
not. The measure was priced to carry a surplus of `0.0368` and retains `1.13e-4`.
Two-thirds of its rows share one plateau minimum; the 2,631 rows below it group into 24
contiguous angular clusters.
The binding is not the cap signature `X-014` predicts — that would need three tight rows
at the folded Bidwell classes at once, and the tight row at `38.06°` is `1.44°` and
`1.74°` from the two tilts.
It is an optimizer residual on a catalogue that moved under the measure after the
measure was priced.

The restriction, meanwhile, is load-bearing for this artifact and now has an exact
witness rather than an inference: at row 6512, `40.379°`, the core whose vertex touches
the wall sits outside the envelope by `5.5e-5`, captures 561 points, and charges
`199827543/200000000 = 0.999137715` against `M/17 = 0.999907492`. The restricted domain
is nonetheless a genuine relaxation of the unrestricted one, so a pass on the
unrestricted test would still be decisive; it is the *fail* that is confounded, and that
is why correction 1 matters.

## The Two Measurements This Document Reports

**The `A1` cell on our own support, at the external side.** One run at `n = 17`,
`L = 4613/1000`, `B = 9995/10000`, the 181-direction net, seeded from the retained
`n = 17` certificate with a five-per-window lattice: 7,253 sites, 40 rounds, deadline
reached, objective `17.177501`, least covered mass `0.968232`. Unconverged and above 17.
That is consistent with the register’s `17.195968` at `461/100` and says our own site
set does not reach the external side at this net.
`V1/C1`: one run, one instrument, recorded with its command and its round table, not
reproduced.

**The research loop did not run at all in a fresh clone.** Five preconditions no
document named: the image’s `uv` could not resolve the pinned interpreter, the clone was
shallow, a submodule was absent, node modules were missing, and the Rust engine was
unbuilt. After repair the edit tier passes at `124.4 s` against its `240 s` ceiling.
This is recorded because a review block that cannot run its own instruments is not a
review block, and because the next session should not rediscover it.

## The Gate Cannot Reach These Artifacts, and That Is Structural

Found by running the `A2` cell rather than by reasoning about it, and it bounds the
whole external-intake programme rather than one experiment.

`decide_threshold_certificate` retains a record only when **both** routes accept it.
The interval route refuses any input above `MAX_INTERVAL_ATOMS = 4096`
(`src/sqpack/fractional/interval.py:145`), a deliberate memory guard whose own comment
sizes it against the repository’s experience: “the largest retained certificate has
2,260 atoms”. The external `n = 17` measure expands to **6,744 point atoms and 2,008
threshold atoms**, so the interval route refuses it outright and prints
`REFUSED: the interval verifier supports at most 4096 atoms`.

The consequence is not about this artifact.
**No external measure above 4,096 atoms can be retained by this repository’s gate as it
is built**, whatever its mathematics, because one of the two required routes will not
look at it. The `C4` rung is structurally out of reach for artifacts at the scale they
now arrive at, and the five-value ladder shows that scale is rising — 1,620 atoms, then
1,616, then 3,280, then 8,988 sites.

The guard is conservative rather than fundamental.
It exists to refuse an input-driven allocation in the hundreds of megabytes, and it does
that by capping the atom count because the boxes-by-atoms mask is materialised whole.
Batching over atoms as well as over boxes would keep the same memory ceiling at any atom
count: at `BATCH = 4096` and 6,744 atoms the full mask is about 27 MiB, which is the
size the cap was chosen to avoid and not a size the method requires.
Raising the cap without chunking would not be the fix; chunking is.

Until that is done, an external measure of this size can be replayed, reviewed and
retained as bytes — which is what `T-032` and the Kleddamag retention did — and cannot
be decided by this repository’s own two routes.
That is worth stating plainly next to every claim about what the intake programme can
verify.

## Ranked Slate

Ranked by expected information per hour against instruments that exist.
Rows marked **redesigned** differ from `X-041`’s because of a correction above.

### Tier A: the instrument exists and the design is sound

| Rank | Item | First discriminator | Kill | Why it ranks here |
| --- | --- | --- | --- | --- |
| A1 | **Are the `n = 17` triples necessary at these weights?** Empty `threshold_orbits`, set the budget to the point budget, run the artifact’s own sweep | Least point-only charge against `0.861183` | At or above `0.861183` — the triples are decoration at this `A` and the next rung is purely a sites problem | Four minutes, on retained bytes, independent of every contested theorem. The highest value per CPU-second on the slate |
| A2 | **Re-price the measure on its own final catalogue** (H-233) | The LP value on 1,387 orbit variables against 16.99 | Mass at or above `16.998` — no headroom on this support at this `A` | The `#1` ranked mechanism once the slack distribution is read; it is the ladder’s own next step |
| A3 | **`n = 20, 21` are site-limited, not endpoint-limited** (H-F) — **redesigned** | A point certificate of mass below 20 at `243/50 = 4.86` | Converged at or above 20 on two site sets | Corrects a slate row and is worth `+0.01` on a stock instrument |
| A4 | **The grid escape at `n = 12, 20, 21`** (H-U5) | Arm B at the exp-202 budget returns exactly the grid on 5/5 seeds | Any seed below — a new record | The first grid-capable search ever run at these `n`; converts “nobody looked” into a measured negative |
| A5 | **`n = 19` reproduction at 10×** (H-U2) | Best polished seed against `4.885618` | All five at or above `4.8956` | The one low-`n` record no search has reached; any seed below is a record candidate |
| A6 | **T-026 at the 2880-step net** (H-G) | Least charge at `B*` against `M/11` | Least charge below `M/11` — `B*` rises and the `0.0011` is not all available | A rung, not a mechanism: an idle CPU slot, never a block |

### Tier B: a bounded instrument first

`H-234` (the restriction’s worth, censused over all 7,853 rows rather than inferred) and
`H-C` (the parent-envelope domain at `n = 11`) both need the one small domain parameter
the `T-032` note already asks for, and they share it.
`H-A` (is the universal family immune to near-coincident triples?)
needs a face scan over the transported family.
`H-E` (is the `n = 18` lock an exact unit gap?)
needs the fold and both readers.
`H-U8` (core rigidity at the flexible records) needs `cases/trump11/tangent_cones.py`
generalised off its hard-coded `n = 11` tables.

### Tier C: retired or corrected

`H-228` is **refuted as stated**, not blocked: its claim is at side exactly 4, where the
sixteen open grid squares are disjoint and force `mu >= 16` under the interior
convention the unshrunk language must use.
Its confirm condition can never be met, and the hypothesis needs restating as a limit
family below 4 before it is anything.
Angle-dependent measure families are killed outright by the pointwise-maximum argument.
“A larger `L`” at `n = 17` is not a mechanism, by scale invariance.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
