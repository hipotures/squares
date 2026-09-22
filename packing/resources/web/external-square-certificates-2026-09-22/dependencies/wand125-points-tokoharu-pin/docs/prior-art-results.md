# Verification of Prior Work (Surveyed on 2026-09-13)

A literature survey confirmed that the 5 established bounds have not been previously published.

## Conclusion: All 7 Bounds Are Novel

| n | This work | Best known lower bound | Source | Improvement |
|---|---|---|---|---|
| 26 | **5.45** | 5.3918 = 2√2+(27+2√10)/13 | Green 2000 (private communication to Friedman), DS7 Theorem 9 (k=5) | +0.058 |
| 29 | **5.57** | 5.5117 = 2√2+6/√5 | Green 2000, DS7 Theorem 10 (k=5), monotonicity from n=28 | +0.058 |
| 39 | **6.5** | 6.3506 = 2√2+(113+10√3)/37 | Green 2000, DS7 Theorem 9 (k=6), monotonicity from n=37 | +0.149 |
| 55 | **7.54** | 7.4807 = 1+√(55−2⌊√55⌋+1) | Nagamochi 2005 closed form; no stronger value recorded | +0.059 |
| 56 | **7.62** | 7.5574 = 1+√(56−2⌊√56⌋+1) | Nagamochi 2005 closed form; no stronger value recorded | +0.063 |
| 70 | **8.55** | 8.4162 = 1+√(70−2⌊√70⌋+1) | Nagamochi 2005 closed form; no stronger value recorded | +0.134 |
| 72 | **8.61** | 8.5498 = 1+√(72−2⌊√72⌋+1) | Nagamochi 2005 closed form; no stronger value recorded | +0.060 |

The last four differ in kind from the first three. For n = 26, 29 and 39 the
standing figure was Green's unpublished private communication; for
n = 55, 56, 70 and 72 the survey records no Green value at all, and the
strongest independently verified bound is Nagamochi's closed form. Those four
therefore improve on a published, verified result rather than on an unrecovered
one.

n = 56 and n = 72 also improve on what our own earlier certificates gave by
monotonicity: s(55) ≥ 7.54 put s(56) at 7.54, and s(70) ≥ 8.55 put s(72) at
8.55. Unlike the other bounds here, neither carries further entries with it —
Nagamochi's form already exceeds 7.62 from n = 57 on and 8.61 from n = 73 on.

## Basis

### 1. Friedman's survey DS7: the 2009-08-14 version is the latest
The Electronic Journal of Combinatorics Dynamic Survey DS7 has not been revised since 2009.
Its Table 2 is the authoritative list of lower bounds for n ≤ 100, and the relevant rows are as shown in the table above.
**This is the only literature that systematically provides lower bounds for n ≤ 100.**

### 2. Green's values are from private communication and their proofs are not published
All citations in DS7 are "Green, private communication (2000)", and the geometric proofs have not been recovered.
In jlevy/squares, `packing/frontier/ds7-lower-bound-audit.json` also treats Green's values as
"source-reported; proof not independently verified", keeping the independently verified values
at the Nagamochi-type 1+√(n−1) form (n=26: 5.1231, n=29: 5.4721, n=39: 6.2915).
The same project's `research-2026-09-07-n26-best-known-audit.md` explicitly notes that
"Green's 5.3918 is private communication and the proof has not been recovered."

**Therefore, the 3 bounds in this work are stronger than Green's values in that they are accompanied by fully verifiable certificates.**

### 3. The Kingbird page lists upper bounds only
The record table maintained by David Ellsworth lists the "smallest known square" = upper bounds, and does not include lower bounds.
The relevant upper bounds are n=26: 7/2+3√2/2 ≈ 5.6213 (Friedman 1997),
n=29: 5.93383 (Thomas Schadt, 2025-12), and n=39: 6.81072 (Schadt, 2026-01).

### 4. All prior work based on weighted unavoidable sets is for small n
| Study | Target n | Method |
|---|---|---|
| Stromquist 1984/2003 | 11 | unavoidable points (origination) |
| Nagamochi 2005 | General | generalization of unavoidable points |
| Bentz 2010 (EJC 17 #R126) | 13, 46 | continuously varying families of unavoidable sets |
| Bentz 2016 (arXiv:1606.03746) | 22, 33 | same as above |
| Sam Burns 2026 | 17 | weighted points (268 points, total weight 16.9476) |
| Massaccesi 2026 | 17–19 | 4.5058 |
| jlevy/squares 2026 | 11, 12, 17–21 | fractional certificate (1121 atoms for n=11) |

**None of these address n = 26, 29, or 39.**

## Notes
- Whether Green's private communication can be called "published" is debatable, but in either case, the values in this work improve upon them.
- The known lower bounds for n=29 and n=39 derive from monotonicity (from n=28 and n=37).
  Note that s(29) ≥ 5.57 in this work does **not imply** s(28) ≥ 5.57 (the implication runs in the opposite direction). Exercise care in descriptions.
- Full texts of papers behind walls such as ResearchGate remain unverified. However, because DS7 serves as a dynamic survey tracking lower bounds and no updates for n=26/29/39 have been incorporated since 2009, we judge that there are no published updates.

## References
- Friedman, "Packing Unit Squares in Squares: A Survey and New Results", EJC DS7 (2009-08-14 edition)
  https://www.combinatorics.org/files/Surveys/ds7/ds7v5-2009/ds7-2009.html
- Kingbird / David Ellsworth, "Squares in Squares"
  https://kingbird.myphotos.cc/packing/squares_in_squares.html
- jlevy/squares https://github.com/jlevy/squares
- Bentz, arXiv:1606.03746 / EJC 17(1) #R126
- Sam Burns, "Proposing a Better Lower Bound for n=17 Square Packing"
- Massaccesi, "Another Better Lower Bound for n=17 Square Packing"
