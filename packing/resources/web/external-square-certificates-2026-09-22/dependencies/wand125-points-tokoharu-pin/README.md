# Lower bounds for packing 26, 29, 39, 55, 56, 70 and 72 unit squares

Let `s(n)` be the least side of a square that holds `n` unit squares with
arbitrary orientations, no two overlapping. This repository contains exact
weighted fractional certificates proving

```
s(26) >= 109/20  = 5.45
s(29) >= 557/100 = 5.57
s(39) >= 13/2    = 6.5
s(55) >= 377/50  = 7.54
s(56) >= 381/50  = 7.62
s(70) >= 171/20  = 8.55
s(72) >= 861/100 = 8.61
```

and, as a cross-check on the generator, an eighth certificate for `s(40) >= 13/2`
that also follows from the `n = 39` bound by monotonicity.

The previous figures for these cases come from a private communication from
Trevor Green to Erich Friedman, reported in Friedman's survey *Packing Unit
Squares in Squares* (Electronic Journal of Combinatorics, DS7), whose last
revision is dated 14 August 2009. The underlying argument has not been
published. The bounds here are the first to improve them, and they arrive with
certificates anyone can re-check.

| `n` | previously reported | this repository | improvement |
|---|---|---|---|
| 26 | 5.3923 | **5.45** | +0.0577 |
| 29 | 5.5119 | **5.57** | +0.0581 |
| 39 | 6.3512 | **6.5** | +0.1488 |
| 55 | 7.4807 | **7.54** | +0.0593 |
| 56 | 7.5574 | **7.62** | +0.0626 |
| 70 | 8.4162 | **8.55** | +0.1338 |
| 72 | 8.5498 | **8.61** | +0.0602 |
| 40 | 6.4061 | 6.5 (follows from `n = 39`) | +0.0939 |

For `n = 55, 56, 70, 72` the standing figure is Nagamochi's closed form, which
is the strongest independently verified bound the survey records for those
cases; for `n = 26, 29, 39` it is Green's. By monotonicity `s(39) >= 6.5` also
covers `n = 40..44` against the DS7 table, `s(70) >= 8.55` covers `n = 71`, and
the `n = 26` and `n = 29` bounds cover `27` and `30`.

The `n = 56` and `n = 72` certificates carry no further entries with them.
Nagamochi's closed form already exceeds 7.62 from `n = 57` on and 8.61 from
`n = 73` on, so monotonicity gives nothing there; these two improve their own
cases only.

`s(56)` and `s(72)` improve on what our own earlier certificates already gave.
Monotonicity from `s(55) >= 7.54` put `s(56)` at 7.54 and from `s(70) >= 8.55`
put `s(72)` at 8.55; the direct certificates raise those by 0.08 and 0.06.

## How the proof works

Scatter finitely many points in the container and give each a nonnegative
rational weight. If every unit square that fits, at every orientation and
position, covers total weight at least 1, then `n` non-overlapping squares
cover at least `n`. Choose the weights so the total is strictly below `n` and
no such packing exists.

The certificate is the list of points and weights. Checking it means checking
five conditions, of which the fifth — that *every* placement covers mass 1 —
is the one that needs a computer. Two devices make it finite: a shrunken square
of side `B < 1` tested against a rational net of 201 directions, with
`B(1 + D) < 1` so the shrink absorbs the net's angular gap; and a sweep over
regions of centre positions rather than individual points.

This is the weighted fractional unavoidable-set method. It is not ours; see
[Attribution](#attribution).

## Verifying the certificates

### With this repository's checker

Requires Python 3.10+, NumPy.

```bash
pip install -r requirements.txt
python3 src/verify.py certificates/cert_n29_L557.json
```

It prints each condition as it decides it and ends with `VERIFIED`. It accepts
only JSON; a certificate is data, and loading one from a pickle would run
whatever the file contained.

Conditions 1 to 4 are decided exactly in `Fraction`. Condition 5 runs a
branch-and-bound recursion over centre boxes in float64 under a stated error
budget: `EPS = 1e-9` on geometric comparisons, mass threshold `1 + 1e-9`, boxes
not subdivided below `1e-7`. Coordinates stay under 100 in magnitude and each
compared quantity takes at most six floating-point operations, so rounding error
stays near `1e-13`; the mass is a sum of at most `10^4` nonnegative terms below
1, so its error stays near `1e-11`. Weights are rounded *up* to multiples of
`1e-8`, so rounding can only add mass.

Box counts, zero failures in each: 4,811,681 (`n=26`), 2,524,711 (`n=29`),
8,409,303 (`n=39`), 7,531,281 (`n=40`). Counts vary slightly between runs
because the split order is not deterministic; the outcome does not.

### With jlevy/squares' checker

[`jlevy/squares`](https://github.com/jlevy/squares) carries an independent
implementation that decides Condition 5 in exact integers on the weights'
common scale and returns the true minimum over event cells, rather than testing
a threshold in floating point. **It is the stronger check**, and all four
certificates pass it unmodified.

```bash
git clone https://github.com/jlevy/squares.git
cp src/check_with_sqpack.py certificates/*.json squares/
cd squares && python3 check_with_sqpack.py cert_n29_L557.json
```

```
n = 29   L = 557/100 = 5.57
atoms = 748   total mass = 453011/15625 = 28.992704   budget = 29
accepted = True   (13.8s)
  [ok  ] Condition 1 atoms carry the declared symmetry: 748 atoms closed under D4 about the centre
  [ok  ] Condition 2 total mass below n: total 453011/15625 against n = 29
  [ok  ] Condition 3 net reaches pi/4: final half-tangent 83/200, t^2 + 2t - 1 = 89/40000
  [ok  ] Condition 4 containment B(1 + D) < 1: B = 9977/10000, D = 83/40000, B(1 + D) = 399908091/400000000
  [ok  ] Condition 5 every reachable cell carries mass 1: least cell mass 1000003/1000000 at direction 0
=> s(29) >= 557/100 = 5.57
```

Results on one core, single worker:

| `n` | atoms | distinct under `D4` | total mass | margin under `n` | `verify` |
|---|---|---|---|---|---|
| 26 | 1376 | 179 | 646393601/25000000 = 25.855744 | 0.144256 | accepted, 28.2s |
| 29 | 748 | 100 | 453011/15625 = 28.992704 | **0.007296** | accepted, 13.8s |
| 39 | 2724 | 362 | 481487971/12500000 = 38.519038 | 0.480962 | accepted, 73.4s |
| 55 | 3196 | 410 | 1362984297/25000000 = 54.519372 | 0.480628 | accepted, 131.4s |
| 70 | 8060 | 1058 | 108946291/1562500 = 69.725626 | 0.274374 | accepted, 548.5s |
| 40 | 1892 | 250 | 975019903/25000000 = 39.000796 | 0.999204 | accepted, 45.1s |

The `n = 29` margin is the interesting one: the weights land `0.0073` under
budget, close to the ceiling the method allows. That is why `n = 29` was the
hardest of the three to find, while `n = 39` had room to spare.

## Certificate format

Each JSON file carries

| field | meaning |
|---|---|
| `n` | number of unit squares |
| `L` | container side, exact rational string |
| `B` | shrink factor `9977/10000` |
| `net` | the direction net as a rule: `theta_r = 2*atan(r*83/40000)`, `r = 0..200` |
| `atoms` | `[x, y, weight]` triples, exact rational strings |
| `total_mass` | sum of weights |
| `claim`, `verification` | the statement proved and the command that checks it |

The net is stored as a rule rather than a list; the half-angle tangents are
exactly `r * 83/40000`. `src/check_with_sqpack.py` shows the one-line
conversion to the form `jlevy/squares` expects.

## Finding the certificates

`src/lp.py` and `src/certify.py` search for them. The program is a covering
linear program over `D4` orbit representatives, solved with HiGHS through SciPy,
with rows generated by using the Condition 5 sweep as a separation oracle and
columns generated from dual reduced costs. A run is abandoned once the LP
optimum reaches `n`, since further rows only raise it.

```bash
python3 src/certify.py --n 29 --L 557/100
```

Runs are long and memory-hungry; the searches behind these four certificates
took hours each on a 128 GB machine, and `certify.py` checkpoints its own
progress so a run can resume. Those checkpoints are pickles it wrote itself
and are not part of the verification path.

## Attribution

The method is not ours.

- **Walter Stromquist** introduced unavoidable point sets with unit weights
  (unpublished memos 1984–85; *Packing 10 or 11 Unit Squares in a Square*,
  Electron. J. Combin. 10 (2003) #R8).
- **Hiroshi Nagamochi** introduced weighted score systems tuned by hand
  (Electron. J. Combin. 12 (2005) #R37).
- **Sam Burns** and **Gustavo Massaccesi** fractionalized the weights and
  introduced the exact rational direction net with the `B(1 + D) < 1` shrink,
  in August 2026. Our `B = 9977/10000` on 201 directions is a parameter choice
  within their framework.
- **[jlevy/squares](https://github.com/jlevy/squares)** added row generation
  via a separation oracle, dual-priced column generation, and branch-and-bound
  as a second Condition 5 decider, and documents the whole pipeline.

What is ours is the observation that nobody had run this machinery above
`n = 21`, the search runs, and the certificates. [`docs/prior-art-method.md`](docs/prior-art-method.md)
breaks the method into six components and attributes each;
[`docs/prior-art-results.md`](docs/prior-art-results.md) records the search for
prior publication of the bounds themselves. Japanese originals are alongside as
`*.ja.md`.

If any attribution here is wrong, please open an issue and we will correct it.

## Layout

```
certificates/   the four certificates as JSON
src/verify.py            our checker
src/check_with_sqpack.py adapter for the jlevy/squares checker
src/lp.py, src/certify.py the search
docs/lower-bounds.md      write-up of the argument and the numbers
docs/prior-art-method.md  which parts of the method are prior art, and whose
docs/prior-art-results.md search for prior publication of these bounds
docs/prior-art-*.ja.md    Japanese originals of the two notes above
```

## Status

Computer-assisted certificates, checked by two independent implementations.
They have not been peer reviewed.

Parts of this work were produced with AI assistance under human direction.

## License

MIT. See `LICENSE`.
