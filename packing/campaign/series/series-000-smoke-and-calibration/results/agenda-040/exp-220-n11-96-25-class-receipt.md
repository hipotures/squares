# Exp-220 n=11 96/25 Class Re-Freeze Receipt

Status: **accepted**. The exp-219 covering re-frozen under the class claim strings.

The registration review of [exp-219](exp-219-n11-96-25-clip-receipt.md)
([h222-registration-review.md](h222-registration-review.md), defect D1) found that the
retained bytes declared `"claim": "s(11) >= 96/25"` and the unconditional id, with only
`variant: class` stopping the file from reading as a bound.
Session 146 corrected the driver and the gate, then repeated the registered command of
[exp-220](../../experiments/exp-220-h222-n11-96-25-class-refreeze.md), byte-for-byte in
its parameters, with new output paths.

## What the bytes now say

| Field | exp-219 | exp-220 |
| --- | --- | --- |
| `claim` | `s(11) >= 96/25` | `corner class d = 1/2 excluded at s(11) >= 96/25` |
| `id` | `C-n011-fractional-96-25` | `C-n011-fractional-96-25-clip-1-2` |
| `variant`, `corner_clip` | `class`, `1/2` | `class`, `1/2` (also at top level of the family record) |
| atoms | 680 | 680, equal as exact Fractions in the same order |
| total mass | 10868617/1000000 | 10868617/1000000 |
| sha256 | `5813d822…7040d` | `876820dde8d55c727dec73c85f245db27661556bb3c7aa06ffb15b01ec97a461` |

The run converged at round 0 in 262.9 s (`converged: every placement covers mass 1`).

## The gate, both ways

With the flag, `decide_certificate --corner-clip 1/2` printed:

```
RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS (no square meets x + y <= 1/2 in any corner frame): both routes accept and agree at 2000013/2000000; sha256 876820dde8d55c727dec73c85f245db27661556bb3c7aa06ffb15b01ec97a461
```

**Erratum (2026-09-20, review defect D5).** The headline above says the hypothesis is
“no square meets x + y <= 1/2 in any corner frame”, which is `min(x + y) > 1/2` — a
strictly smaller hypothesis than the set the sweep actually covered.
What was decided is `min(x + y) >= 1/2`: `corner_clip.half_planes` keeps the boundary on
the kept side deliberately, since “taking it closed keeps a measure-zero boundary the
class cannot realise, which is the safe direction”.
Both readings are sound, and the closed one is the stronger of the two, which is why
T-031 concludes that some square meets the *open* triangle `x + y < 1/2`. The retained
`.stdout` is not edited and the gate was not re-run: the string is what the instrument
printed on the day, and the erratum is the correction layer.

Without the flag it exited 1:

```
REFUSED: cannot load certificate: variant 'class' is declared, and this gate implements only the unconditional conditions; a class certificate cannot be decided here. The one exception is the corner class: pass --corner-clip d
```

The corrected gate now refuses exp-219’s bytes on their claim string, which is the
defect being demonstrated; exp-220 supersedes exp-219 as the record of the exclusion.
Outputs beside this receipt: `exp-220-n11-96-25-class-{covering,family,run}.json`,
`-rows.jsonl`, `.log`, `-decide.stdout`, `-decide-noflag.stdout`.

## What remains

- Registration of the reviewed statement (a results-register entry in the T-023 pattern
  at the scope the review wrote) is BC-367’s first item.
- `devtools/colgen_checkpoint.py` has its own `certificate_json` with no clip parameter,
  so a clipped run frozen or resumed through the checkpoint path would write
  unconditional strings (`think-bxu1`).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
