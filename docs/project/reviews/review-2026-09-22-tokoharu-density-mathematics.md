# Tokoharu Rectangle Densities: Mathematical and Integration Review

The retained certificates support $s(26)\ge1377/250=5.508$ and $s(29)\ge571/100=5.71$
for freely rotated unit squares.
The accompanying $s(11)\ge381/100$ certificate also passes.
All 201 directions of all three certificates replayed successfully, and an independently
written exact-rational preflight checked the mass, symmetry expansion, angular margin,
input enclosures, and complete axis event sets.
The continuous covering argument and its implementation were reviewed below.
No defect was found in the published certificates’ mathematical argument.

The new search driver has a separate **High** admission defect: `push.py --from` accepts
a certificate for the wrong target count and accepts stale side metadata.
Two retained controls reproduce impossible final bounds with exit status zero.
This finding prevents trusting that driver’s final status as a bound admission decision;
it does not invalidate the three supplied certificate files.

## Scope and Evidence

This is the mathematical lane of session 152, workflow W2, under the coordinator’s
external-source research block.
The reviewed primary source is
[`tokoharu/square-packing-density-bounds` at `b543990f7794b8c511cb46cf3854b7e8166c3674`](https://github.com/tokoharu/square-packing-density-bounds/tree/b543990f7794b8c511cb46cf3854b7e8166c3674).
Its complete tracked tree is retained in the
[source packet](../../../packing/resources/web/external-square-certificates-2026-09-22/tokoharu-density/README.md),
with source identity recorded by the
[acquisition manifest](../../../packing/resources/web/external-square-certificates-2026-09-22/acquisition/sources.json).
Source files were not modified for replay.

The proof-critical files were read in full: `src/certify.py`, `src/verify.cpp`,
`src/run_verify.py`, and `docs/continuous-density-certificate.ja.md`. The review also
inspected the search-to-certificate interfaces in `geometry.py`, `advance.py`,
`push.py`, `global_separation.py`, `net_screen.py`, and `point_export.py`. The LP and
numerical search implementations are not in the trusted proof path: their output is a
candidate until the separate certificate checks succeed.
This review does not assert correctness of every heuristic search operation.

The
[`wand125/square-packing-density-bounds` main tree at `096294aeb5f8b604df5890beda6cd601d05f4561`](https://github.com/wand125/square-packing-density-bounds/tree/096294aeb5f8b604df5890beda6cd601d05f4561)
contains the same three certificate directories and proof implementation.
The difference through Tokoharu’s reviewed head consists only of `src/push.py` and
`tests/test_push.py`. The fetched `add-push-driver` branch adds those search-driver
files without a stronger certificate.
These fetched density trees do not identify the further numerical improvements mentioned
in the supplied X text.

## Mathematical Reduction

Write $K=[0,L]^2$ and let the input contain rectangles $R_j$ with nonnegative rational
masses $w_j$. For positive-area rectangles, define

$$
g(x)=\sum_j\frac{w_j}{8|R_j|}\sum_{S\in D_4}\mathbf1_{S(R_j)}(x).
$$

Every group image is included with multiplicity.
Images that coincide, or overlap other images, contribute separately.
Consequently $g\ge0$, $g$ is invariant under all container symmetries, and
$\int_Kg=\sum_jw_j=M$. Dividing by the area of the rectangle and by eight is necessary:
the stored coefficient is a mass, not the value of the density.
The code implements this in
[`certify.py:35–50`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/certify.py#L35-L50).

If every legal unit square $Q$ satisfies $\int_Qg\ge1$, then $n$ unit squares with
disjoint interiors would satisfy

$$
n\le\sum_{i=1}^n\int_{Q_i}g\le\int_Kg=M<n,
$$

a contradiction.
Square boundaries have area zero, so touching boundaries cause no double
counting for this density.
Rectangle discontinuities do not change that conclusion.
No claim about the optimal packing, or about equality at the reported upper bound,
follows from this obstruction.
Compactness also upgrades exclusion at each displayed rational side to a strict lower
bound: the minimum packing side is attained.
That is a local consequence of the argument; the source’s stated bounds use $\ge$.

### All orientations, including between net angles

The certificate uses

$$
B=\frac{9977}{10000},\qquad D=\frac{83}{40000},\qquad
t_r=rD,\quad\theta_r=2\arctan t_r,\quad 0\le r\le200.
$$

The net reaches past $\pi/4$ because $t_{200}^2+2t_{200}-1=89/40000>0$. For adjacent net
angles,

$$
\tan\frac{\theta_{r+1}-\theta_r}{2}
=\frac{D}{1+t_rt_{r+1}}\le D.
$$

After reflecting the density and square together if necessary, an arbitrary orientation
has a nearest net angle with error at most $\arctan D$. A concentric $B$-square at that
net angle has width at most $B(\cos|\delta|+\sin|\delta|)\le B(1+D)$ across either axis
of the unit square. Here

$$
B(1+D)=\frac{399908091}{400000000}<1.
$$

Thus it lies strictly inside the unit square, and hence inside $K$ whenever the unit
square does. Nonnegative density transfers the net-square coverage bound to the original
unit square. This is an exact containment argument; it does not interpolate sampled
coverage values between angles.
The implementation still pays the finite-net shrink cost.
The rectangle basis has not removed that cost in this certificate format.

At each net angle, the rotation coefficients are the exact rationals

$$
c_r=\frac{40000^2-(83r)^2}{40000^2+(83r)^2},\qquad
s_r=\frac{2\cdot40000\cdot83r}{40000^2+(83r)^2}.
$$

Their integer numerators and denominators fit exactly in binary64 for all admitted
indices. The checker encloses the subsequent divisions by interval arithmetic
([`verify.cpp:113`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/verify.cpp#L113)).
The final net node lies just past 45 degrees; its positive sine and cosine still satisfy
the formulas used by the verifier.

### Continuous centre coverage and symmetry

For a fixed net angle let $a=B(c+s)/2$. The full legal centre domain is $[a,L-a]^2$.
Quarter-turn rotations preserve both the density and the square’s fixed orientation
modulo $\pi/2$, so every centre has an equivalent representative in $[L/2,L-a]^2$. This
reduction uses rotations.
A reflection would reverse the orientation and would not justify keeping that same
fixed-angle centre domain.
The source uses the correct reduction.

At angle zero, the contribution of one rectangle is a product of two piecewise affine
overlap lengths. The sum is bilinear on each cell cut out by the rectangle endpoints
shifted by $\pm B/2$. A bilinear function on a closed rectangle is a convex combination
of its four corner values, so checking all event-grid vertices is sufficient.
Container-domain endpoints are included.
The source collects x-coordinates after the full D4 expansion; the swapped images ensure
it also contains every y-event.
The independent preflight instead collects all four coordinates of every expanded
rectangle and checks that the supplied list contains exactly that union
([`certify.py:52–60`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/certify.py#L52-L60),
[`verify.cpp:107–111`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/verify.cpp#L107-L111)).

For nonzero angles, the centre variables are $x=L/2+uE$, $y=L/2+vE$, where $E=L/2-a$ and
$(u,v)\in[0,1]^2$. The condition $L^2>2B^2$ together with positive $L$ makes $E>0$. The
initial box is the whole unit square.
Every split replaces a closed box by its two closed half-boxes, so there is no coverage
gap along split boundaries.
The dyadic centre and half-width operations are exact at every reachable depth: the
depth refusal occurs before the binary64 mantissa is exhausted.
An unresolved box is a nonzero exit, never a proof of infeasibility.

### Lower bounds on each centre box

For a rectangle $R=[a,d]\times[b,e]$, let $H_R(x,y)=|R\cap(Q_0+(x,y))|$. Translation of
a square changes its symmetric-difference area by at most a constant times the
translation distance.
Each $H_R$, and their finite weighted sum $F$, is therefore Lipschitz and absolutely
continuous on coordinate lines.
Almost everywhere,

$$
\partial_xH_R=\operatorname{length}(Q\cap\{x=a\}\cap R)
-\operatorname{length}(Q\cap\{x=d\}\cap R),
$$

with the analogous bottom-minus-top expression for $\partial_yH_R$. These signs match
the code. `slice()` intersects the two intervals imposed on the other coordinate by the
two rotated-square strip inequalities, then clips against the rectangle edge.
Interval arithmetic encloses this length for the entire centre box.
The weighted sum of signed edge-length intervals encloses the full derivative; any
cancellation retained by the interval sum is legitimate
([`verify.cpp:74–95`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/verify.cpp#L74-L95)).

If $G_x,G_y$ bound the absolute derivatives on a box with half-widths $d_x,d_y$, the
fundamental theorem of calculus along its two coordinate segments gives

$$
F(x,y)\ge F(x_0,y_0)-G_xd_x-G_yd_y.
$$

This remains valid across changes of intersection combinatorics; differentiability at
every boundary point is unnecessary.
The implementation encloses the exact centre and box endpoints, rounds both derivative
penalties upward, and rounds the final lower bound downward.
It accepts a leaf only above an upward-rounded enclosure of the rational threshold
$10001/10000$. The numerical threshold is a sufficient certificate inequality, not a
tolerance that admits violations.

### Inscribed-polygon area and arithmetic

`area_lower()` first handles separation and complete rectangle containment by interval
inequalities. For a partial intersection it constructs an approximate polygon, shrinks
its vertices, and computes an approximate hull.
None of those approximate operations alone supplies proof evidence.
The checker then proves that every proposed vertex lies in both exact shapes, and that
every other vertex lies strictly to the left of each oriented edge.
Those tests establish a convex polygon in counterclockwise order contained in the true
intersection. Its interval triangle-area sum is a lower bound on the true overlap.
Failed containment, degeneracy, or failed convexity returns zero
([`verify.cpp:32–71`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/verify.cpp#L32-L71)).

Consequently the `1e-9` shrink and `1e-14` approximate-hull cutoff can weaken the bound,
but do not certify an incorrectly clipped polygon.
The postchecks establish the needed statement independently of the clipping routine.
The explicit disjointness skips also use outward domain bounds, so they only omit a
contribution proved to be zero.

The interval primitives expand each rounded arithmetic endpoint by `nextafter`.
Multiplication encloses all four endpoint products; division asserts that the divisor
interval excludes zero.
The replay compiled the unchanged source with
`-O2 -std=c++17 -fno-fast-math -ffp-contract=off`. `g++` on this host is Apple Clang
21.0.0, on arm64 macOS 26.5.2. The source checks binary64/IEEE 754 and round-to-nearest
at startup. The trusted base remains the reviewed C++ logic, compiler, standard-library
parsing and `nextafter`, binary64 arithmetic with gradual underflow, and the Python
rational preflight. The program has not been proved correct in Lean or another proof
assistant. It is not a hardened parser for arbitrary hostile interval files.

### Optional smoothing

The source also constructs a continuous function $f=g*k_\varepsilon$, with a normalized
uniform kernel on $[-\varepsilon,\varepsilon]^2$ and $\varepsilon=1/20000$.
Positive-weight rectangles stay strictly more than $\varepsilon$ inside the container,
so smoothing preserves the total mass inside $K$. The kernel’s projection width is at
most $2\sqrt2\varepsilon<3\varepsilon$. The checked margin

$$
B(1+D)+3\varepsilon=\frac{399968091}{400000000}<1
$$

therefore puts the Minkowski sum of a selected net square and the kernel support inside
its containing unit square.
Integrating this containment against the nonnegative normalized kernel proves the same
coverage bound for $f$. This argument in §5 of the Japanese proof is valid.
Smoothing is unnecessary for the packing obstruction itself: $g$ already defines an
absolutely continuous measure with zero mass on square boundaries.

## Exact Preconditions and Replay Results

The independent tool
[`audit_tokoharu_density.py`](../../../packing/devtools/audit_tokoharu_density.py) does
not import `certify.py`. It parses decimal tokens as exact rationals, rejects duplicate
JSON keys, reconstructs all eight images with their multiplicities, integrates their
mass exactly, and checks every supplied binary64 interval against the corresponding
exact rational.
It checks the axis list for completeness, the target side, and the strict
comparison $M<n$. The
[preflight receipt](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/density-exact-preflight/audit.json)
records these checks against the retained source tree.
Before launching an external checker, the tool also binds an archive run to the
acquisition record’s reviewed revision and validates every file against
`acquisition/tokoharu-density.sha256`. Missing, additional, changed, or symlinked files
are refused. The
[archive-binding receipt](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/density-archive-binding/audit.json)
records 62 validated source files and the repeated exact preconditions.
Negative controls alter or remove `src/verify.cpp` in a copied packet and confirm
refusal before any external process starts.

| $n$ | Exact $L$ | Exact total mass $M$ | Positive basis rectangles | Expanded rectangles | Axis vertices |
| --- | --- | --- | ---: | ---: | ---: |
| 11 | $381/100$ | $68302371743812406989/6250000000000000000$ | 24 | 192 | 21,316 |
| 26 | $1377/250$ | $6481789525574810517/250000000000000000$ | 83 | 664 | 360,000 |
| 29 | $571/100$ | $71719849258137554097/2500000000000000000$ | 69 | 552 | 211,600 |

Each mass is strictly below its associated integer.
All 201 angle checks passed for every certificate.
Node counts, leaf counts, and printed minima match the retained upstream summaries.
The replay used four workers, with an explicitly selected 900-second ceiling per
certificate. No ceiling was reached.

| $n$ | Nodes | Leaves | Least printed leaf lower bound | Upstream runner wall time |
| --- | ---: | ---: | ---: | ---: |
| 11 | 5,575,714 | 2,798,615 | 1.0001000043991626 | 73.53 s |
| 26 | 4,533,720 | 2,446,960 | 1.0001000055431877 | 178.65 s |
| 29 | 3,860,166 | 2,035,983 | 1.000100012480408 | 92.74 s |

The durations exclude compilation; the
[full audit receipt](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/density/audit.json)
also records elapsed time including compilation, the interpreter, compiler version,
commands, and the complete upstream summaries.
Each case directory beside it retains standard output, standard error, and all 201
per-angle records. Printed minima are diagnostics; the decisive comparisons occurred
inside the interval checker before printing.

From `packing/`, with the project CPython 3.14 environment and a C++17-capable `g++` on
`PATH`, a complete repeat is:

```bash
density_replay_output="$(mktemp -d "${TMPDIR:-/tmp}/tokoharu-density-review-repeat.XXXXXX")" &&
.venv/bin/python3 -m devtools.audit_tokoharu_density \
  --out "$density_replay_output" \
  --n 26 --n 29 --n 11 --replay --workers 4 --timeout 900 \
  --adversarial --driver-controls
```

The replay creates one child output directory per certificate with `exist_ok=False`. The
`mktemp` command supplies an empty parent, so a prior run cannot make the command fail
or mix old output with new receipts.

The independent geometry controls use exact rational polygon clipping and exact line
sections, calling the unchanged external functions through a small
[C++ probe](../../../packing/devtools/tokoharu_density_probe.cpp).
They cover axis alignment, the first nonzero angle, intermediate angles, the
overshooting last angle, separation, tangency, near tangency, full containment, and
partial overlap. The
[adversarial receipt](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/density-adversarial-final/adversarial/probe.json)
records their counts and output.
These finite controls test the implementation against an independent arithmetic method;
they do not constitute a second global coverage proof.
Focused tests also confirm refusal of an incomplete axis partition and of an input
interval that fails to enclose the declared side.

## Findings

### DENS-1 — High: starting-certificate acceptance bypasses target count and identity

[`push.py:104–114`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/push.py#L104-L114)
checks only a candidate’s `globally_verified` flag and a summary’s `VERIFIED` flag.
The `--from` path at
[`push.py:224–227`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/push.py#L224-L227)
then adopts the side from separate metadata without checking the requested $n$, the
mass, or the agreement between candidate, interval input, and metadata.
The target check can return before any new certificate is built.

Using the genuine n29 certificate with `--n 1 --target 5.71` produces `TARGET_REACHED`,
reports `n=1, best_L=5.71`, and exits zero.
One unit square fits in side 1. In a second control, changing only the copied metadata’s
`L` to `100` makes the driver report `n=29, best_L=100` and exit zero; 29 unit squares
fit in a $6\times6$ grid.
The
[control receipt and logs](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/density-adversarial-final/driver-controls/driver-controls.json)
retain both observations and the mutated metadata.

**Fix:** Validate every starting certificate against the requested count, recomputed
exact mass, side, and linked proof input before setting `best` or testing the target.
`advance.py:21–36` already performs substantially stronger incumbent checks and provides
an available implementation to factor into a shared admission function.
Add regression tests for the wrong-count and stale-metadata paths.
The published rectangle certificates pass these missing checks independently here.
The integration follow-up is tracked as `think-c0xc`.

### DENS-2 — Medium: the raw coverage runner is not a complete bound verifier

[`verify.cpp:100–102`](https://github.com/tokoharu/square-packing-density-bounds/blob/b543990f7794b8c511cb46cf3854b7e8166c3674/src/verify.cpp#L100-L102)
trusts the supplied orbit list, axis-event list, interval validity, and the relation of
that input to the named candidate.
`run_verify.py` reports `VERIFIED` after coverage checks, but has no target $n$ or exact
mass comparison. The Japanese proof correctly documents this limitation; a consumer that
interprets this one status as a complete lower-bound verdict would omit necessary
hypotheses.

**Fix:** Admit a bound only through a wrapper that validates the full exact candidate
and input relation, proves the mass inequality, and then requires all 201 coverage
checks.
The retained independent preflight supplies that missing boundary for these three
fixed source artifacts.
Do not promote `globally_verified` or a saved success string by itself.
Independent density admission is tracked as `think-ck07`.

## Design Assessment and Integration

The method is a useful rectangle-density representation of the one-body fractional
covering problem. Its small proof kernel avoids trusting the numerical LP, pricing,
search seeds, clipping heuristic, or a dense sampling grid.
It should remain a separate certificate type from our rational point-atom certificates:
the integration obligations are an area integral and derivative enclosure, while the
existing point verifier decides discrete event-cell mass in exact arithmetic.
Silently converting a density to cell-centre atoms does not preserve minimum square
coverage. The source’s `point_export.py` labels the result unverified and its README
reports failed conversion checks; that failed diagnostic does not refute the density
certificate.

The comparison to n11 has a precise limit.
[X-027](../../../packing/campaign/explorations/X-027-stromquist-fractional-and-structural-strategy.md#continuous-density-has-the-same-optimum-under-a-precise-convention)
establishes equality of the finite-atom and absolutely continuous covering infima under
the interior-incidence convention.
Rectangle bases can improve conditioning, finite parametrization, and search efficiency.
They cannot evade an independently proved one-body fractional obstruction merely by
spreading point masses into area densities.
This source also retains the $B<1$ net construction, so it provides no demonstration of
full-unit-square certification without shrink.

The three lower-bound statements have interval-certified evidence with completed replays
and discharged exact preconditions.
They meet the
[Frontier admission rule](../../../packing/frontier/README.md#adding-or-reviewing-a-result):
an exact proof, exact replay, or rigorous interval certificate must discharge its
assumptions.
The [case schema](../../../packing/frontier/square-packing-case.schema.yaml)
defines `verified_lower_bound` as the largest lower bound certifiable from the
repository’s evidence.
Each case therefore takes the strongest applicable bound, including valid monotonic
consequences; a weaker certificate remains evidence without displacing a stronger floor.

Under [the evidence rules](../../../epistemics.md#confirmation), these completed replays
support V4/C3; this review, when mapped, and the retained controls support V4/C5. C4 is
not an admission prerequisite.
The finite rational geometry probes do not add another complete C3 method and do not
justify C4 by themselves.
An independent global density implementation remains an assurance and integration
follow-up, not a reason to hold a fully checked bound out of `verified_lower_bound`.
External authorship, replay here, and independent global implementation remain separate
provenance facts. The coordinator owns the shared record updates and result identifiers.

The source-reported improvement over the earlier point certificates is $0.058$ at n26
and $0.14$ at n29. The further-improvement assertion from X remains unlocated in the
fetched density refs; no larger bound is inferred from it.
Our pre-existing verified n26/n29 lower bounds and their source-reported historical
alternatives should remain in the record as separate evidence when the new source is
integrated.

## Supplemental Review: Predecessor Point Adapter

The related
[`wand125/square-packing-bounds` tree at `1398e42f17f23fe3744bc54425a589fab1f3542c`](https://github.com/wand125/square-packing-bounds/tree/1398e42f17f23fe3744bc54425a589fab1f3542c)
contains ten rational point certificates.
This supplemental review checked every certificate header and the complete
[`check_with_sqpack.py` adapter](https://github.com/wand125/square-packing-bounds/blob/1398e42f17f23fe3744bc54425a589fab1f3542c/src/check_with_sqpack.py#L28-L66)
against the native `Certificate` and `verify` contract at repository commit
`b57e4d66ad4f4ef8df71f45ca9afa8ff03d844cc`. Those native files were unchanged in the
working tree during review.
The coordinator runs the independent exact sweeps; admission of each row requires its
complete successful entry in the
[retained replay log](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/wand125-points/sqpack-exact-replay.log).
This adapter review does not substitute for those sweeps.

All ten headers declare $B=9977/10000$ and the same rule $t_r=83r/40000$,
$r=0,\ldots,200$. Every stored coordinate and weight is a rational string, and each
`num_atoms` header agrees with the array length.
The table records the declared masses; the native verifier recomputes them from the
weights before reporting its verdict.

| File target | $L$ | Atoms | Declared mass $M$ | Least integer above $M$ |
| --- | --- | ---: | --- | ---: |
| n26 | $109/20$ | 1376 | $646393601/25000000$ | 26 |
| n29 | $557/100$ | 748 | $453011/15625$ | 29 |
| n39 | $13/2$ | 2724 | $481487971/12500000$ | 39 |
| n40 | $13/2$ | 1892 | $975019903/25000000$ | 40 |
| n53 | $369/50$ | 3196 | $1287080441/25000000$ | **52** |
| n55 | $377/50$ | 3196 | $1362984297/25000000$ | 55 |
| n56 | $381/50$ | 3856 | $1379852479/25000000$ | 56 |
| n69 | $841/100$ | 5684 | $846701027/12500000$ | **68** |
| n70 | $171/20$ | 8060 | $108946291/1562500$ | 70 |
| n72 | $861/100$ | 6384 | $1789465839/25000000$ | 72 |

The adapter passes the actual side, shrink, and atom triples into the native
certificate, then calls `verify(cert, workers=1)` with no corner clip or domain
restriction. The constructor refuses negative weights; verification checks exact D4
symmetry, $M<n$, net reach, strict containment, and minimum mass at least one over every
reachable event cell at all 201 directions.
The exact margins are again $t_{200}^2+2t_{200}-1=89/40000>0$ and
$B(1+D)=399908091/400000000<1$. Thus every unit square contains a checked closed inner
square strictly inside its interior.
Distinct packing squares have disjoint inner squares, so point masses cannot be counted
twice. The contradiction proves the bound at $L$, not $L/B$. No adapter-to-theorem gap
was found for these fixed inputs.

There are three provenance limits for a reusable importer.
First, the adapter hardcodes the net and ignores the textual `net` field; the
declarations agree here, but an importer should require that agreement or parse an
explicit rational net.
A changed declaration would not invalidate a successful proof for the hardcoded net, but
it would make a claim of reproducing the declared procedure inaccurate.
Second, saved `total_mass`, `num_atoms`, and success metadata are not trusted by the
native checker.
This is sound for the recomputed certificate, but the surrounding archive
still needs identity checks to detect stale descriptive fields.
Third, `sys.path.insert(0, "packing/src")` depends on the invocation directory, and an
empty argument list exits zero without checking anything.
Retain the native engine revision, invocation directory, immutable source manifest,
explicit ten-file argument list, and ten completed verdicts; process exit zero alone
does not establish that all ten intended files were checked.

The count $n$ occurs only in the mass condition, as
[`least_size_certified`](../../../packing/src/sqpack/fractional/certificate.py#L171)
also records. The retained log records complete successful exact sweeps for the n53 and
n69 files. The n53 file therefore proves $s(52)\ge369/50$ because
$52-M=12919559/25000000>0$, and the n69 file proves $s(68)\ge841/100$ because
$68-M=3298973/12500000>0$. Neither deduction requires a new geometry run.
These are local arithmetic consequences, not additional numerical claims made by the
source. They belong in the verified lane with the derivation and source certificate
credited; the reported lane preserves the strongest literal external claims for n52 and
n68.

Monotonicity gives $s(39),s(40),s(41)\ge13/2$ from the n39 file; the separate n40 file
is a redundant cross-check at that side and does not prove n39 because its mass exceeds
39\. The $13/2$ transfer remains valid above n41 but ceases to improve the register: at
n42, Nagamochi gives $1+\sqrt{31}>13/2$, whereas the n41 value is $1+\sqrt{30}<13/2$.
Similarly, the n70 file gives the stronger current lower value at n70 and n71; at n72
its inherited $171/20$ is superseded by the separate $861/100$ certificate.
The n52/n53 value is superseded at n54 by $1+\sqrt{41}>369/50$, and the n68/n69 value by
the n70 certificate.
These comparisons use the
[retained Nagamochi bounds](../../../packing/frontier/n-042.md) and preserve their
separate source provenance.
The point source itself explicitly states the n40–44 and n71 monotonic consequences in
[its README](https://github.com/wand125/square-packing-bounds/blob/1398e42f17f23fe3744bc54425a589fab1f3542c/README.md#L44-L45),
so the n41 and n71 values also qualify as source-reported claims.
The larger Nagamochi values remain the strongest reports at n42–44. The density bound
also supplies the verified floor $s(28)\ge5.508$ by monotonicity, while the stronger
reported Green bound at n28 remains in its separate reported field.

The local auditor and focused tests passed Ruff, BasedPyright, and all six focused
tests. Archived sources remain unchanged.
Repository-wide checks and final Frontier record validation belong to the coordinator’s
integration checkpoint.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
