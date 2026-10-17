# Exact cycle-index counting for the wreath-product topology symmetry group

Third topology-space research note on `work/topology-phase1-native`, following
`docs/boolean-quotient-orbit-counting-2026-10-17.md`. Starting HEAD for this
campaign was `5a51f3c6`. The work was committed in focused steps: `ee10bcd0`
(shared big-integer helpers, 128-bit fix), `c7d8887b` (wreath-product module,
CLI, Python differential, CTest entry), `c55bed51` (tests and goldens), and
`0cda79b5` (stabilizer-spectrum experiments); this documentation commit is the
last step. Host: Ryzen 9 7950X3D guest, 16 vCPUs, 161 GiB RAM, nauty 2.9.3,
g++ 15.2, CMake 4.2.3, Python 3.14.4. All runs use the default Release `build/`
tree (no PGO). The branch is not merged to `main`.

This note executes recommendation A of the previous note: replace direct
enumeration of all `|G_n|` elements with a sum over conjugacy classes of the
wreath product `D4 wr S_n`, push exact counts to `n = 5` and `n = 6` (plus
one-off `n = 7, 8` runs), and study the low-weight coefficients `a_d(n)`,
staged symmetry compression, and trivial-stabilizer spectra. It does not modify
the first note or its erratum.

**Erratum carried forward.** Section 5 of the previous note quotes
`|G_5| = 39,321,600` in its scaling-wall paragraph. The correct order is
`5! * 8^5 * 8 = 31,457,280`, which both the formula and direct enumeration give
(section 3.5 below). The previous note's conclusion is unaffected: direct
enumeration is still the wrong tool at `n = 5`, just less so by 25%.

## Summary

- The new module (`include/sqtopology/wreath.hpp`, `src/wreath.cpp`) counts
  `a_d` and `N_n` exactly by summing over the `5 * T(n)` conjugacy classes of
  `G_n = (D4 wr S_n) x D4_container` instead of enumerating `|G_n|` elements.
  `T(n) = 5, 20, 65, 190, 506, 1265, 2990, 6765` for `n = 1..8`.
- Validation is layered: byte-for-byte equality with the committed direct-oracle
  goldens for `n = 1..4` (including the induced cycle-type distributions), a
  direct element-enumeration cross-check (`wreath-cross`) for `n <= 4`, and an
  independent stdlib-only Python differential (`tools/wreath_reference.py`) for
  `n <= 3` that never uses the class-size formula or class representatives.
- Headline cross-check: the direct oracle enumerates 31,457,280 elements in
  93.46 s and 291.7 MiB for `n = 5`; the class-aggregated counter produces the
  same 801 coefficients and both totals in 0.233 s and 5.2 MiB (about 400x
  faster, 56x smaller).
- `n = 6` full polynomial: 1153 coefficients, 338-digit total, 1.17 s. One-off
  `n = 7` / `n = 8` full runs pass every check (5.14 s / 462 digits, 19.73 s /
  604 digits). Low-weight runs reach `n = 11` in 5.70 s / 132.3 MiB.
- Low-weight structure: `a_d(n)` is non-decreasing in `n`, constant for
  `n >= 2d`, and the increment at the stabilization point is exactly
  `C(d+2, 2)` (proved in section 5; verified for `d <= 6`). The widened build
  (128-bit class-size intermediates, section 9) computes the `n = 12` row in
  13.54 s / 269.6 MiB: `a_6(12) = 443,748,944 = 443,748,916 + 28`, confirming
  the increment theorem's last open prediction and completing the committed
  `a_0..a_6` table for `n = 1..12`.
- Symmetry-subgroup compression is computed for `n <= 6` and weight `<= 4`
  under `D4^n`, `S_n x D4_container`, `D4 wr S_n`, and the full `G_n`.
  These are comparison quotients from related subgroups, not one four-step nested
  chain: `D4^n < D4 wr S_n < G_n`, while `S_n x D4_container` is a different
  subgroup of `G_n`. The data therefore do not support attributing "most" of the
  compression to one symmetry source by comparing the partial-quotient counts
  directly. At `n=6`, weight 4, the local-only quotient actually reduces the
  labeled layer slightly more than the square-permutation-plus-container quotient.
- Trivial-stabilizer spectra: an elementary bound (trivial stabilizer implies
  support `= n`, hence `n <= 2d`) is checked; for `n = 1` the full weight
  spectrum `0..32` is symmetric and reaches 0.9925 at `d = 15`; for `n = 2,
  d = 3` there are exactly 15,360 trivial-stabilizer configurations, i.e. 15
  full-size orbits.
- A latent 64-bit overflow in the shared big-integer division corrupted every
  `n >= 7` run. It was caught by the internal divisibility check and by a
  monotonicity violation, root-caused, fixed with 128-bit intermediates, and
  regression-tested (section 8).

## 1. The class-aggregated Burnside formula (theorem)

The event model is the one established in the previous note: for fixed `n`,
`Omega_n` has `E(n) = 32 n^2` events, labeled topologies are subsets, and

```
G_n = (D4 wr S_n) x D4_container,      |G_n| = n! * 8^n * 8
```

acts on events by permuting them. Burnside/Polya gives the orbit counts

```
a_d = (1/|G_n|) * sum_{g in G_n} [x^d] prod_{cycles c of g} (1 + x^{|c|}),
N_n = (1/|G_n|) * sum_{g in G_n} 2^{c(g)},
```

where `c(g)` is the number of cycles of `g` on `Omega_n`, and complementation
`S -> Omega_n \ S` forces `a_d = a_{E-d}` exactly (previous note, section 1).

Direct evaluation of these sums costs `|G_n|` element applications of about
`E(n)` event steps: `4.0 * 10^8` steps at `n = 4`, `2.5 * 10^10` at `n = 5`,
and `1.1 * 10^16` at `n = 8`. The class aggregation replaces that by a sum over
conjugacy classes:

- **Classification.** Conjugacy classes of `D4 wr S_n` are the standard ones
  for a wreath product `B wr S_n` with `B = D4`: a class is a family of
  disjoint cycles of the square permutation `sigma`, each cycle of length `l`
  decorated with the conjugacy class in `D4` of the folded product of its local
  labels; cycles of the same length are distinguishable only through the
  multiset of their decorations. Adding the independent container class
  multiplies the class count by 5. Number of wreath types:

  ```
  T(n) = sum over partitions n = sum_l l * m_l of  prod_l C(m_l + 4, 4),
  ```

  giving `T = 5, 20, 65, 190, 506, 1265, 2990, 6765`, and
  `5 * T` conjugacy classes for `G_n` (25, 100, 325, 950, 2530, 6325, 14950,
  33825).
- **Class size.** For a type with `m_l` cycles of length `l`, of which
  `m[l][c]` carry `D4` class `c` (sizes `|c| = 1,1,2,2,2`), and
  `r = sum_l m_l` square cycles,

  ```
  S(type) = n! / (prod_l l^{m_l} m_l!)                 (square permutations)
          * prod_l m_l! / prod_c m[l][c]!              (class multinomial)
          * 8^{n-r}                                    (free local labels)
          * prod_{l,c} |c|^{m[l][c]}                   (cycle-product classes)
          * |c_container|                              (container class)
  ```

  every factor an integer by construction. This is the standard centralizer
  count; it is not trusted here until it is checked against element
  enumeration (section 3).
- **Class function.** Conjugate group elements induce conjugate event
  permutations, hence identical induced cycle types and identical Polya
  products. One canonical representative per class therefore determines
  `[x^d] prod (1 + x^{|c|})` for the whole class, and the class size supplies
  the Burnside multiplicity. The implementation further groups classes by
  identical induced cycle type, so the polynomial is evaluated once per
  distinct type (493 types at `n = 5`, 4875 at `n = 8`).

The counting formula actually evaluated is

```
a_d = (1/|G_n|) sum over classes tau of S(tau) * [x^d] prod_{cycles of the
      induced event permutation of any g in tau} (1 + x^{cycle length}).
```

## 2. Implementation

- `include/sqtopology/bigint.hpp` now owns the exact base-`10^9` `BigUint`
  previously local to `src/orbit.cpp`, with 128-bit intermediates in
  `mul_small` and `div_small` (section 8). `kMaxOrbitSquares` rises from 8 to
  12; the direct front ends keep their own caps (`count <= 8`,
  `wreath-cross <= 4`, direct element enumeration `<= 11`).
- `src/orbit.cpp` computes induced event cycle types through the existing
  `ElementAction::map_event` instead of materializing a full event permutation
  per element; this makes the per-class cycle-type step cheap.
- `src/wreath.cpp` implements: recursive generation of all wreath types
  (partitions weighted by class-distribution multinomials), the class-size
  formula, canonical representatives, class aggregation into induced types,
  the exact polynomial/total accumulation in `BigUint`, exact division by
  `|G_n|`, and the `staged_quotient_counts` sub-group tables.
- `src/orbit_main.cpp` adds three subcommands:
  `wreath --n N [--low-weight D] [--cycle-types] [--json FILE]`,
  `wreath-cross --n N`, and `staged --n N --weight D` (the `staged` cap is
  `n <= 6`; `wreath` supports `n <= 12`).
- Every full run checks six invariants internally: class sizes sum to `|G_n|`,
  every coefficient numerator is divisible by `|G_n|`, complement symmetry,
  the two totals (coefficient sum and `sum_g 2^{c(g)}`) agree, `a_0 = a_E = 1`,
  and all coefficients are positive. Low-weight runs check three of them
  (class sizes, divisibility, positivity).
- `tests/data/wreath-count-n5.json` is the committed `n = 5` golden;
  `tests/data/wreath-low-weight.json` is a compact single-line golden with
  columns `a_0..a_6` for `n = 1..12`.

## 3. Validation

### 3.1 Direct element cross-check (`wreath-cross`, `n <= 4`)

For `n <= 4` the tool enumerates all `|G_n|` elements, classifies each one by
folding its labels, counts elements per type, and verifies that (a) the counts
equal the class-size formula and (b) every element of a type induces the event
cycle type computed at the class representative:

| n | elements | classes | classes seen | counts match | induced types match |
|---:|---:|---:|---:|---|---|
| 1 | 64 | 25 | 25 | yes | yes |
| 2 | 1,024 | 100 | 100 | yes | yes |
| 3 | 24,576 | 325 | 325 | yes | yes |
| 4 | 786,432 | 950 | 950 | yes | yes |

### 3.2 Committed goldens (`n <= 4`)

`tests/test_orbit.cpp` re-runs the class-aggregated counter with
`--cycle-types` and compares, byte-for-byte, the coefficient arrays, the
totals, the distinct induced-type counts, and the full induced-type
distribution tables against `tests/data/orbit-count-n{1..4}.json` — the
direct-oracle goldens of the previous note. All checks pass, so the two
essentially different implementations agree at every coefficient and every
class of every `n <= 4`.

### 3.3 Independent Python differential (`n <= 3`)

`tools/wreath_reference.py` shares no code with the C++ counter. It:

- enumerates every element of `G_n` (at most 24,576 for `n = 3`);
- computes each element's wreath type by folding labels along the
  square-permutation cycles;
- obtains class sizes by counting elements, never by the size formula;
- evaluates the Polya binomials once per enumerated type, and with
  `--deep-constancy` verifies on every single element that the induced cycle
  type is the same within a type;
- with `--bfs` re-partitions the group by generator-BFS conjugation and
  verifies that this partition equals the wreath-type partition;
- recomputes the `D4^n` and `S_n x D4_container` staged rows by enumerating
  those subgroups element by element;
- compares everything (coefficients, totals, induced-type table, low-weight
  prefix, staged rows) against `sqtopology_orbit` output.

CTest target `sqtopology_wreath_reference` runs this for `n = 1..3` with
`--deep-constancy --bfs` in 2.10 s. It reproduces `N_1 = 67,753,072`,
`N_2 = 332,317,140,421,910,940,456,278,459,867,471,872`, and the 83-digit
`N_3` of the previous note.

### 3.4 Live `n = 6` pins and the `n = 5` golden

The test suite recomputes `n = 6` live and pins the head coefficients
`a_0..a_9`, the 336-digit center coefficient `a_576`, and the 338-digit total;
it also verifies that a low-weight run reproduces the full-run prefix. The
`n = 5` run is compared against the committed 135,899-byte golden, all 801
coefficients and the total.

### 3.5 Direct oracle `n = 5` versus class aggregation (headline)

`./build/sqtopology_orbit count --n 5` enumerates all 31,457,280 group
elements (93.46 s wall, 298,724 KiB peak RSS). The class-aggregated
`wreath --n 5` run takes 0.2329 s wall and 5,324 KiB peak RSS. All 801
coefficients and both totals are identical; corrected `|G_5| = 31,457,280`
(section "Erratum carried forward"). This is the campaign's headline
independent confirmation of the aggregation at a size where the direct oracle
is still feasible.

## 4. Exact counts

### 4.1 Group and class sizes

| n | `E(n)` | `|G_n|` | wreath types | conjugacy classes | induced types | wall | peak RSS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 32 | 64 | 5 | 25 | 6 | 0.00005 s | 4.1 MiB |
| 2 | 128 | 1,024 | 20 | 100 | 26 | 0.0006 s | 4.2 MiB |
| 3 | 288 | 24,576 | 65 | 325 | 78 | 0.005 s | 4.2 MiB |
| 4 | 512 | 786,432 | 190 | 950 | 203 | 0.039 s | 4.5 MiB |
| 5 | 800 | 31,457,280 | 506 | 2,530 | 493 | 0.233 s | 5.2 MiB |
| 6 | 1,152 | 1,509,949,440 | 1,265 | 6,325 | 1,112 | 1.172 s | 6.7 MiB |
| 7 | 1,568 | 84,557,168,640 | 2,990 | 14,950 | 2,384 | 5.140 s | 10.2 MiB |
| 8 | 2,048 | 5,411,658,792,960 | 6,765 | 33,825 | 4,875 | 19.73 s | 18.0 MiB |

The wreath-type counts follow from the generating function above and are
verified by exhaustive generation; the function also gives
`T(9..11) = 14725, 31027, 63505` (73625, 155135, 317525 classes). Element-to-class
compression is `|G_n| / (5 T(n))`: about 12,400x at `n = 5` and 1.6 * 10^8 at
`n = 8`.

### 4.2 Coefficient heads

```
n = 5: a_0..a_9 = 1, 5, 125, 3650, 150193, 7288314, 391975513,
                  22201383232, 1281296279355, 73681412412155
n = 6: a_0..a_9 = 1, 5, 125, 3660, 152092, 7599740, 434321891,
                  27189870037, 1806257816768, 124059363877872
n = 7: a_0..a_9 = 1, 5, 125, 3660, 152268, 7642376, 442602511,
                  28553860161, 2003351963914, 149677257448070
n = 8: a_0..a_9 = 1, 5, 125, 3660, 152283, 7646395, 443646723,
                  28786050904, 2048162517410, 157358767167918
```

### 4.3 Centers and totals

`a_{E/2}` is the center of the complement-symmetric polynomial; `N_n` is the
total class count. The digit strings below are exact.

`n = 5` (`E = 800`, center index 400):

```
a_400 = 597770824014915513258547590087908136303681664869654384837623338443898
        009724106834201694870003473918912582635672156515686607676092130464718
        192217220346612977807442416858379254664498268923185622779513656354280
        3201055274415036611250460                                    (232 digits)

N_5   = 211970470202509031984836820800600352716780936949979225225951419624600
        264088218988297543081844289002361850988742565191425938720108149893031
        826966838170901259817222845944004542377370314162129723472476905414551
        801575194044147739119321088                                 (234 digits)
```

`n = 6` (`E = 1152`, center index 576):

```
a_576 = 952164912434645377125105001907600946725073723227561833080594335224036
        292447818143512884627842473235327015062688107669089708228947242905828
        316299598743872554412851036119974804963453768242863774963360036837508
        800190495867610152767160498187004755288958775352170590156362633863584
        223572122216418001545447666718783637445604016349458165578544  (336 digits)

N_6   = 405128316699448586355061594148435894175408664353151259350042061225291
        941373582124194042484383160553849324869252453296150098582231609504353
        713412225660415244769694085914439944121994597215045539531993820932349
        150852978852663750824190718468030525332533319923001636861654888227686
        44607570789899208605569598935408252535579981746020551560790016  (338 digits)
```

Both are pinned in `tests/test_orbit.cpp` (n = 6 live; n = 5 in the golden).
The `n = 7` (462-digit) and `n = 8` (604-digit) totals exist from the one-off
runs but are not committed as goldens; their leading coefficients are in
section 4.2, and the totals can be regenerated with the command in section 10.
Complement symmetry means the popular `a_d` for small `d` have mirror twins
`a_{E-d}` with the same value.

## 5. Low-weight structure of `a_d(n)`

### 5.1 The table

Exact `a_d(n)` for `d = 0..6` and `n = 1..12`
(`tests/data/wreath-low-weight.json`; all entries recomputed live in the
test suite for `n` in `{1,2,3,4,5,6,7,8,10}` and, under the dedicated
`sqtopology_wreath_n12` CTest target, for `n = 12`):

| d | n=1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 2 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 2 | 22 | 87 | 119 | 125 | 125 | 125 | 125 | 125 | 125 | 125 | 125 | 125 |
| 3 | 116 | 1411 | 2979 | 3560 | 3650 | 3660 | 3660 | 3660 | 3660 | 3660 | 3660 | 3660 |
| 4 | 744 | 26620 | 92770 | 137549 | 150193 | 152092 | 152268 | 152283 | 152283 | 152283 | 152283 | 152283 |
| 5 | 3568 | 481126 | 2985882 | 5938772 | 7288314 | 7599740 | 7642376 | 7646395 | 7646685 | 7646706 | 7646706 | 7646706 |
| 6 | 15454 | 8133610 | 94975858 | 268405879 | 391975513 | 434321891 | 442602511 | 443646723 | 443741543 | 443748484 | 443748916 | 443748944 |

### 5.2 The `a_1` formula (proved)

A single event is either a square-square event or a wall event. Local `D4`
transformations and the container `D4` preserve ring parity (rotations shift
rings by even amounts, reflections negate). Up to square permutation, local
`D4`, and container `D4`:

- square-square events split by the unordered pair of ring parities:
  `{even, even}`, `{even, odd}`, `{odd, odd}` — 3 classes;
- wall events split by ring parity — 2 classes;

so `a_1(n) = 3 + 2 = 5` for `n >= 2`. For `n = 1` there are no square pairs,
so `a_1(1) = 2`. Both values match the table, and the `n >= 2` value is
therefore a theorem, not a fitted pattern.

### 5.3 Support, monotonicity, stabilization (proved)

See also `docs/geometric-realizability-phase2d-2026-10-17.md` section 2, which
sharpens this into the full support decomposition theorem
(`f_d(k) = a_d(k) - a_d(k-1)`, with `f_d(k)` the number of canonical classes
of support exactly `k`, bijected across all `n >= k`).

For a `d`-event configuration, each square-square event touches two squares and
each wall event one, so its support spans at most `2d` squares.

**Proposition.** Let `a_d(n)` count `G_n`-orbits of weight-`d` subsets.

1. `a_d(n) <= a_d(n+1)` (embed `Omega_n` into `Omega_{n+1}`; and if two
   configurations supported in the first `n` squares are equivalent under
   `G_{n+1}`, restricting the witness to the support and completing it to a
   permutation of the first `n` squares shows they are equivalent under
   `G_n`).
2. `a_d(n+1) = a_d(n)` for `n >= 2d` (every weight-`d` class has a
   representative supported in any chosen set of `n >= 2d` squares, and
   relabeling that set to `[n]` transports the action).
3. Consequently `a_d(n) = a_d(2d)` for all `n >= 2d`.
4. The increment at the stabilization point is exactly

   ```
   a_d(2d) - a_d(2d-1) = C(d+2, 2).
   ```

   New classes at `n = 2d` must have support `= 2d`, which forces all `d`
   events to be square-square events on pairwise disjoint square pairs. Such a
   configuration is classified up to `G_{2d}` by the multiset of the `d`
   unordered ring-parity pairs (3 possibilities per event, and local `D4`s are
   transitive on each parity class of rings), giving `C(d+2, 2)` multisets.

Data check (`d = 1..6`): increments `3, 6, 10, 15, 21, 28 = C(3,2), C(4,2),
C(5,2), C(6,2), C(7,2), C(8,2)`, with stabilization visible in the table at
`n = 2, 4, 6, 8, 10, 12`. The `d = 6` increment closes the row: `a_6` rises
from `443,748,916` at `n = 11` to exactly `443,748,944` at `n = 12`, matching
the theorem's prediction. The widened build (section 9) supports `n = 12`;
the prediction recorded in the first revision of this note is now an exact
computation.

### 5.4 What is not claimed

The table is a finite exact computation plus the stabilization theorem, not an
asymptotic expansion; there is no closed form for general `d` and `n` here.
The `a_d(2d)` values themselves (`5, 125, 3660, 152283, 7646706, ...`) are
computed, not derived; only their increments at the stabilization point have
the proof above.

## 6. Symmetry-subgroup compression: related quotients, not one nested chain

Four exact quotient counts were computed for `n <= 6`, weight `<= 4`:

| label | group | order |
|---|---|---|
| `local_only` | `D4^n` | `8^n` |
| `squares_only` | `S_n x D4_container` | `n! * 8` |
| `local_and_squares` | `D4 wr S_n` | `n! * 8^n` |
| `full` | `G_n` | `n! * 8^n * 8` |

The earlier wording called these "four nested quotients". That is not correct.
The containments are

```
D4^n  <  D4 wr S_n  <  G_n,
S_n x D4_container  <  G_n,
```

while `D4^n` and `S_n x D4_container` are not consecutive members of one
subgroup chain. Consequently, ratios involving `local_only` and
`squares_only` are useful comparative measurements, but they cannot be read
as an additive or uniquely attributable decomposition of the total compression.
The symmetry actions overlap and interact.

The `full` row is exactly the low-weight mode of the full counter (asserted for
every `n = 2..6` in the tests). Full rows for `n = 1` and `n = 2`:

| n | quotient | `a_0` | `a_1` | `a_2` | `a_3` | `a_4` |
|---:|---|---:|---:|---:|---:|---:|
| 1 | local | 1 | 8 | 84 | 696 | 4748 |
| 1 | squares+container | 1 | 8 | 100 | 792 | 5244 |
| 1 | wreath | 1 | 8 | 84 | 696 | 4748 |
| 1 | full | 1 | 2 | 22 | 116 | 744 |
| 2 | local | 1 | 20 | 456 | 10224 | 228500 |
| 2 | squares+container | 1 | 44 | 1756 | 53028 | 1303352 |
| 2 | wreath | 1 | 11 | 236 | 5150 | 114490 |
| 2 | full | 1 | 5 | 87 | 1411 | 26620 |

Weight-4 column for all computed rows:

| n | local | squares+container | wreath | full | local/full | squares/full |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4748 | 5244 | 4748 | 744 | 6.4x | 7.0x |
| 2 | 228500 | 1303352 | 114490 | 26620 | 8.6x | 49.0x |
| 3 | 1818864 | 17287512 | 308842 | 92770 | 19.6x | 186.3x |
| 4 | 8109928 | 56410526 | 409190 | 137549 | 59.0x | 410.1x |
| 5 | 26649780 | 87797686 | 432142 | 150193 | 177.4x | 584.6x |
| 6 | 72228348 | 98039030 | 435031 | 152092 | 474.9x | 644.6x |

The last two columns answer a specific conditional question: how much smaller the
full quotient is than each partial quotient. They do **not** say which symmetry
source "caused most" of the total compression.

For a cleaner baseline, at `n=6`, weight 4, the unquotiented labeled layer has

```
C(E(6),4) = C(1152,4) = 73,001,944,800
```

configurations. Relative to that same labeled layer:

- local `D4^6`: `73,001,944,800 / 72,228,348 ~= 1,010.7x` compression;
- `S_6 x D4_container`: `73,001,944,800 / 98,039,030 ~= 744.6x`;
- `D4 wr S_6`: `73,001,944,800 / 435,031 ~= 167,808.6x`;
- full `G_6`: `73,001,944,800 / 152,092 ~= 479,985.4x`.

Thus the previous conclusion that square permutations plus the container
"dominate" while local `D4` is weak is not supported. On this measured layer,
the local-only quotient is itself slightly stronger than the
square-permutation-plus-container quotient. Along the genuinely nested chain

```
labeled -> D4^6 -> D4 wr S_6 -> G_6
```

the successive reductions at weight 4 are approximately `1010.7x`,
`166.0x`, and `2.86x`. Along the alternative comparison
`labeled -> (S_6 x D4_container) -> G_6`, the reductions are approximately
`744.6x` and `644.6x`. These numbers demonstrate strong contribution from
both symmetry families and a substantial interaction; they should not be
interpreted as a unique factorization of compression.

At `n = 1` the wreath quotient equals the local quotient because
`D4 wr S_1 = D4`, while `S_1 x D4_container = D4` acts on a different
coordinate factor (container walls rather than local square features), so the
two partial quotient counts need not agree beyond weight 1.

Like `a_d(n)` itself, every subgroup-orbit count shown here stabilizes once
`n >= 2d` by the same support argument. At `n = 6` the full weight-4 value
(152092) is still below its `n = 8` stabilized value 152283; the other
subgroup rows were not extended to `n=7,8` in this campaign.

## 7. Trivial-stabilizer spectra

`tools/wreath_stabilizer_spectrum.py` counts weight-`d` event subsets with a
trivial stabilizer in `G_n` (equivalently, configurations whose orbit has the
full size `|G_n|`). Two independent exact methods are implemented and
cross-checked against each other and against a brute-forced synthetic
`C2 x C2` action; the full script runs in 8.7 s:

- subgroup Mobius inversion, `#{S : Stab(S) = 1} = sum_K mu(1,K) |X^K|`,
  applied to `n = 1` where the subgroup lattice of `D4 x D4` has 389 elements;
- setwise map-mask enumeration, exact for small weights, applied to `n = 2,
  d <= 3`.

**Bound (proved).** If a configuration does not touch some square, a nontrivial
local `D4` element at that square fixes it, so a trivial stabilizer forces
support `= n`. Since the support is at most `2d`, a trivial stabilizer can
only exist for `n <= 2d`; for `n > 2d` the count is exactly 0. The script
asserts the zero count for `(n, d) = (2, 0), (3, 1), (5, 2)`.

`n = 1` full spectrum, selected weights (`E = 32`; the counts are symmetric
under `d <-> 32 - d`):

| d | trivial-stab | `C(32,d)` | fraction |
|---:|---:|---:|---:|
| 0 | 0 | 1 | 0.000000 |
| 1 | 0 | 32 | 0.000000 |
| 2 | 128 | 496 | 0.258065 |
| 3 | 3,072 | 4,960 | 0.619355 |
| 4 | 27,648 | 35,960 | 0.768854 |
| 5 | 176,896 | 201,376 | 0.878436 |
| 6 | 833,152 | 906,192 | 0.919399 |
| 7 | 3,207,936 | 3,365,856 | 0.953082 |
| 8 | 10,163,456 | 10,518,300 | 0.966264 |
| 12 | 223,300,352 | 225,792,840 | 0.988961 |
| 15 | 561,477,120 | 565,722,720 | 0.992495 |
| 16 | 596,464,768 | 601,080,390 | 0.992321 |

For `n = 2`, `d <= 2` contribute 0, and `d = 3` contributes 15,360 of
341,376 (`4.4994%`) — exactly `15 * |G_2|`, i.e. 15 full-size orbits among the
`a_3(2) = 1411` weight-3 classes.

The spectrum is a statement about the action of the full group `G_n` on
labeled configurations. It is not a measurement on the canonical graph and
makes no claim about its geometry.

## 8. The `n >= 7` big-integer overflow

The first `n = 7` low-weight run produced

```
a_0..a_6 = 1, 5, 125, 3660, 152268, 7642376, 6288372
```

with `all_coefficients_divisible = false`. The `a_6` value is smaller than
`n = 6`'s `434,321,891`, contradicting monotonicity (section 5.3), and the
divisibility self-check flagged the arithmetic rather than the counting. The
same corruption appeared at `n = 8` (`a_5 = 828,986`, `a_6 = 515,176`).

Root cause: `BigUint::div_small` computed `remainder * 10^9 + limb` in 64 bits.
This overflows when the divisor exceeds about `2^64 / 10^9 ~ 1.84 * 10^10`;
`|G_7| = 84,557,168,640 ~ 8.5 * 10^10` is already over the bound, while
`|G_6| = 1,509,949,440` is safely under it, which is why `n <= 6` was clean.
A simulated wraparound reproduces the exact bad quotient `6,288,372`; the
true value is `442,602,511`. A latent second overflow in `mul_small`
(`limb * factor + carry` for large factors) was fixed at the same time.

Fix: both operations accumulate in `unsigned __int128`; the n = 7 regression
pins the exact numerator `|G_7| * 442,602,511 = 37,425,215,163,114,455,040`
and its exact division (`tests/test_orbit.cpp`, `test_bigint_wide_paths`).
After the fix all `n = 7` and `n = 8` runs pass every check, and the goldens
and pinned values for `n <= 6` were re-confirmed byte-for-byte (their
divisors and factors were always within the safe range).

## 9. Performance

Timings from the JSON reports (class generation / event cycle types /
polynomial / total, peak RSS from `getrusage`):

| n | classes | induced types | class gen | event cycles | polynomial | total | peak RSS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 25 | 6 | 0.000004 s | 0.000014 s | 0.000015 s | 0.00005 s | 4.1 MiB |
| 2 | 100 | 26 | 0.000009 s | 0.000112 s | 0.000446 s | 0.0006 s | 4.2 MiB |
| 3 | 325 | 78 | 0.000015 s | 0.000474 s | 0.004474 s | 0.005 s | 4.2 MiB |
| 4 | 950 | 203 | 0.000031 s | 0.002236 s | 0.036552 s | 0.039 s | 4.5 MiB |
| 5 | 2,530 | 493 | 0.000064 s | 0.008864 s | 0.223079 s | 0.233 s | 5.2 MiB |
| 6 | 6,325 | 1,112 | 0.000202 s | 0.031404 s | 1.138982 s | 1.172 s | 6.7 MiB |
| 7 | 14,950 | 2,384 | 0.000434 s | 0.101662 s | 5.034887 s | 5.140 s | 10.2 MiB |
| 8 | 33,825 | 4,875 | 0.001026 s | 0.300516 s | 19.425955 s | 19.733 s | 18.0 MiB |

The polynomial accumulation dominates (96% at `n = 5`, 98.4% at `n = 8`);
class generation is negligible, and event cycle types cost 1.5% at `n = 8`.
Memory stays under 20 MiB at `n = 8` because the state is the class table and
one `BigUint` polynomial, not the 5.4 * 10^12 group elements (the direct
oracle needs 291.7 MiB for `n = 5` alone).

Low-weight prefix runs (`--low-weight 6`) scale to `n = 12` after the
class-size widening (below):

| n | 9 | 10 | 11 | 12 |
|---:|---:|---:|---:|---:|
| total | 0.88 s | 2.32 s | 5.70 s | 13.54 s |
| peak RSS | 31.0 MiB | 64.1 MiB | 132.3 MiB | 269.6 MiB |

At `n = 12` the run visits `5 * 126,730 = 633,650` classes and induces 62,457
distinct event cycle types (up from 34,357 at `n = 11`); the event-cycle step
costs 13.05 s of the 13.54 s total (96.4%), class generation 0.019 s, and the
`BigUint` polynomial accumulation 0.47 s. The largest single induced-type
aggregate is `1.10 * 10^19`, just under the 64-bit ceiling, so induced-type
`class_elements` values stay JSON numbers; only the group order and the
class-size sum (`2.63333914461654220800 * 10^20`) switch to decimal strings.

**Widening to `n = 12` (this revision).** `|G_12| ~ 2.633 * 10^20` exceeds
`std::uint64_t`, so the class-size product and the Burnside weight accumulation
now use `unsigned __int128` intermediates (`BigWide` in `wreath.hpp`) and exact
big-integer multiplication (`BigUint::mul_big`); the division by `|G_n|` is
performed factor by factor (`n!`, then `8^(n+1)`), each an exact 64-bit
division when the full quotient is exact. The direct element-enumeration APIs
(`group_element_count`, `decode_group_element`, the `count` command) remain
capped at `n <= 11` by a separate constant, since their result genuinely
overflows 64 bits; the class-aggregated counter is the only `n = 12` path.
Results for `n <= 11` are byte-for-byte unchanged (all four pre-existing CTest
targets pass without golden updates).

The committed `n = 8` full run (19.7 s) and the direct `n = 5` oracle
(93.5 s) are one-off validations, not part of CTest.

## 10. Reproducibility

~~~bash
# n = 5 golden and the low-weight table (n = 12 row needs the widened build)
./build/sqtopology_orbit wreath --n 5 --json tests/data/wreath-count-n5.json
for n in $(seq 1 12); do
  ./build/sqtopology_orbit wreath --n "$n" --low-weight 6 --json /tmp/lw$n.json
done
# n = 12 regression used by the dedicated CTest target
./build/sqtopology_orbit_tests --wreath-n12

# direct element cross-checks and staged tables
./build/sqtopology_orbit wreath-cross --n 4
./build/sqtopology_orbit staged --n 6 --weight 4

# headline comparison at n = 5 (93.5 s, 291.7 MiB)
./build/sqtopology_orbit count --n 5 --json /tmp/orbit5.json

# independent Python differential (2.1 s) and stabilizer spectra
python3 tools/wreath_reference.py --check-tool build/sqtopology_orbit \
  --max-n 3 --deep-constancy --bfs
python3 tools/wreath_stabilizer_spectrum.py --n1-full --n2-max-weight 3
~~~

`ctest --test-dir build` runs five targets: production `sqtopology_tests`
(1.40 s), `sqtopology_orbit_tests` (6.96 s, includes the wreath suite),
`sqtopology_wreath_n12` (13.58 s, the `--wreath-n12` regression described
below), `sqtopology_orbit_reference` (8.74 s), and
`sqtopology_wreath_reference` (2.21 s); total 32.93 s, all passing at the
documentation commit. The ordinary orbit test suite deliberately avoids
enumerating all `n = 5` elements and keeps the `n = 12` run out: it uses the
committed golden plus the live `n = 6` recomputation (about 1.2 s) instead.
The dedicated `sqtopology_wreath_n12` target live-recomputes the `n = 12`
row and asserts the stabilized `a_d(12) = a_d(2d)` values for `d <= 6`, the
128-bit group order `263333914461654220800`, and every internal check.

## 11. What is theorem, what is exact computation, what is empirical

- **Theorem / proof-level:** the event model and the action (previous note);
  the wreath-product conjugacy classification and class-size formula
  (standard, and validated against enumeration for `n <= 4`); the
  class-function property of the induced event cycle type; the Burnside/Polya
  formulas and complement symmetry; the support bound and the
  monotonicity/stabilization/increment statements of section 5; the
  trivial-stabilizer bound `n <= 2d`; and the `a_1` formula.
- **Exact arithmetic results:** all coefficients and totals for `n = 5`
  (committed golden) and `n = 6` (live-pinned); the one-off `n = 7, 8` full
  polynomials with all internal checks; the `a_0..a_6` table for `n = 1..12`
  (the `n = 12` row live-pinned by the dedicated CTest target); the staged
  tables for `n <= 6`, weight `<= 4`; the `n = 1` full trivial-stabilizer
  spectrum and the `n = 2, d <= 3` counts. The Python differential
  independently confirms the machinery for `n <= 3`; `n >= 4` rests on one
  implementation plus its six internal checks and the shared structural tests.
- **Empirical / implementation:** all timings and memory figures; the exact
  growth of digit counts (a random-subset heuristic `digits(N_n) ~
  E * log10(2) - log10|G_n|` agrees within one digit for `n = 1..8` but is not
  used as a theorem).
- **Verified prediction:** the increment theorem predicted
  `a_6(12) = 443,748,944` before the widened build existed, and the `n = 12`
  run produces exactly that value; for `d >= 7` the same rule remains the
  theorem's prediction until a build supporting `n >= 14` exists.

## 12. Limitations

- The `wreath` counter now supports `n <= 12` (128-bit class sizes, exact
  big-integer multiplication, factor-wise division by `|G_n|`); extending the
  low-weight table beyond `d = 6` needs `n >= 14` rows, each a larger one-off
  run. The direct element-enumeration APIs (`group_element_count`,
  `decode_group_element`, the `count` command) remain capped at `n <= 11`
  because `|G_12|` itself exceeds `std::uint64_t`.
- The `n = 7` and `n = 8` full polynomials are one-off validation runs and are
  not committed as goldens; only the computed values recorded in this note
  (section 4) and in the run outputs represent them.
- The independent implementation boundary is `n = 3` (full element
  enumeration) — the same boundary as the previous note's Python oracle.
  `n = 4` is covered by the cross-check against all 786,432 elements, and
  `n >= 5` by the golden plus internal checks only.
- Staged tables are limited to `n <= 6` and are low-weight only; the
  stabilizer spectra beyond `n = 1` are limited to small `d`.
- The low-weight table's monotonicity/stabilization assertions are corollaries
  of the support argument; they are not a substitute for computing the values
  they pin.
- None of this changes the production canonicalizer or the meaning of the
  search; the counts are orbit counts of the audited symmetry contract, and
  `N_n` remains "canonical contact-topology classes", not square packings.

## 13. Recommended next direction

- **A. Widen to `n = 12` and close the `a_6` row (executed in this revision).**
  The class-size path and Burnside weight accumulation now use 128-bit
  intermediates; the `n = 12` run verified `a_6(12) = 443,748,944` and the
  stabilized `a_d(12) = a_d(2d)` values for `d <= 6`, and the row is pinned by
  the committed golden plus the `sqtopology_wreath_n12` CTest target.
- **B. One-off full `n = 9..11` runs.** Still supported; extrapolating the
  polynomial step (about proportional to `T(n) * E(n)^2`) gives roughly
  10-25 minutes for `n = 11`, so all three are feasible in one session and
  would extend the total-orbit-count record without code changes.
- **C. Geometric realizability (Phase 2).** The strategic question remains
  which canonical contact-topology classes are realizable as square packings;
  class-aggregated counting is now cheap enough that filtering experiments no
  longer compete with counting for compute budget.
- **D. Production canonicalization.** Still orthogonal; no evidence from this
  campaign that the canonicalizer needs changes.

**Recommendation: C, with B as an optional measurement.** A is executed; B is
a pure record-extension; C is the destination identified in the previous note
and the counting wall is no longer in its way.
