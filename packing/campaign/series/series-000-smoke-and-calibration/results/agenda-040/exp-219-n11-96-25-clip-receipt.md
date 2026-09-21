# n=11 96/25 Corner-Clipped Covering Receipt (exp-219)

Status: **RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS on both routes.** H-222 is
confirmed at its registered scope.
`s(11)` does not move.

Session-145 chunk 2,
[exp-219](../../experiments/exp-219-h222-n11-96-25-octagon-class.md): BC-191 auto grids
plus `--seed-windows 5`, `(n, L, B) = (11, 96/25, 9977/10000)`, the 181 half-tangent
folded net (`--direction-steps 180`, the CLI default), and the admitted convex corner
clip at `d = 1/2`: every admissible core meeting a corner triangle `x + y <= 1/2` in its
corner frame is removed from the row domain.

## Commands

From `packing/`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`:

```bash
uv run --frozen --all-extras --group dev python -m devtools.run_fractional_colgen \
  --n 11 --side 96/25 --shrink 9977/10000 --direction-steps 180 --corner-clip 1/2 \
  --grid-counts auto --seed-windows 5 --support-cap 32 --column-rounds 1 \
  --max-rounds 60 --deadline-seconds 2400 --scale 4000000 --verify-serial \
  --freeze .../exp-219-n11-96-25-clip-covering.json \
  --freeze-family .../exp-219-n11-96-25-clip-family.json \
  --json .../exp-219-n11-96-25-clip-run.json \
  --row-log .../exp-219-n11-96-25-clip-rows.jsonl \
  --log .../exp-219-n11-96-25-clip.log
uv run --frozen --all-extras --group dev python -m devtools.decide_certificate \
  --corner-clip 1/2 --dump-stalls .../exp-219-n11-96-25-clip-stalls.json \
  .../exp-219-n11-96-25-clip-covering.json
```

## Covering

| Quantity | Value |
| --- | --- |
| Rows / orbits / sites at round 0 | 6133 / 506 / 3749 |
| LP rounds in round 0 | 32 |
| Objective | `10.868522955888936` (float LP) |
| Least covered mass at the stop | `0.9999999999860997` (float; the exact sweep below decides) |
| Stop | `converged: every placement covers mass 1` after one column round added one orbit |
| Frozen mass | `10868617/1000000 = 10.868617` over 680 atoms |
| Frozen least cell mass (serial clipped sweep) | `2000013/2000000` |
| Record fields | `variant: class`, `corner_clip: 1/2` |
| Wall | 265.8 s |

## Gate

```
...exp-219-n11-96-25-clip-covering.json: n = 11, L = 96/25 = 3.840000, 680 atoms, mass 10868617/1000000 = 10.868617, corner clip d = 1/2
  ceiling 3.990800, certifies every n >= 11
  interval accepted=True enclosure=(Fraction(2000013, 2000000), Fraction(2000013, 2000000)) boxes=1743736 stalled=0 (30s)
  exact    accepted=True least=2000013/2000000 (11s)
  RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS (no square meets x + y <= 1/2 in any corner frame): both routes accept and agree at 2000013/2000000; sha256 5813d822d3f83eef98326de0c16e245466afbcb8c4988b039e81a4bcf3d7040d
```

The certificate file’s SHA-256 is
`5813d822d3f83eef98326de0c16e245466afbcb8c4988b039e81a4bcf3d7040d`.

## Determination

H-222 is **confirmed** at its registered scope.

- Both routes of `decide_certificate --corner-clip 1/2` accept a covering of mass
  strictly below 11 with least charge at least 1 on the clipped domain, so no packing of
  eleven unit squares in `[0, 96/25]^2` has every square avoiding the four corner
  triangles `x + y <= 1/2` (in each corner’s frame).
  Equivalently, every such packing has a square whose corner penetration exceeds `1/2`
  at some corner.
- This is a conditional exclusion for the all-free (octagon) class of lane-a Theorem B
  at side `3.84`; the other fifteen corner-bin classes are untouched, and nothing here
  bounds `s(11)`.
- The retained 88-family transported to `96/25` keeps mass 7 on this domain, so the
  one-body ceiling does not obstruct this class; the clipped covering found mass
  `10.8686`, about `0.13` below the requirement.
- Registration as a frontier result, with its review artifact and a case directory, is a
  separate W2 step; this receipt and the experiment record are the evidence.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
