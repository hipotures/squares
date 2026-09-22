# Verification evidence

The certificate establishes **s(11) > 31/8 = 3.875**. Both recorded verification
rounds cover every interval in the same fixed rational certificate.

| Check | Evidence |
|---|---|
| First full Python scan | [Per-interval results](evidence/initial/python.json) |
| First full JavaScript scan | [Aggregate and range results](evidence/initial/secondary/RESULT.json) |
| First independent premise and boundary controls | [Results](evidence/initial/controls.json) |
| Second full verification using the portable launcher | [Summary](evidence/portable/RESULT.json), [Python](evidence/portable/python.json), [JavaScript](evidence/portable/secondary/RESULT.json), [controls](evidence/portable/controls.json) |
| Exhaustive threshold identities and disjoint-site budgets | [Results](threshold-algebra.json), [checker](verify_threshold_algebra.py) |
| Theorem and exact numerical summary | [VERIFIED.json](VERIFIED.json) |
| Certificate and implementation file hashes | [Manifest](MANIFEST.json) |

## Exact checks

The Python scan checks 12,028 intervals and 86,299,918 slabs. Its range queries
certify 511,649,694,680 open cells; those cells are not enumerated one by one.
The JavaScript scan uses 86,275,862 slabs. The implementations subdivide the
domain differently and return identical complete histograms of interval minima.

The independent controls check all 48,112 rational quadratic inequalities
for strict core containment and directly evaluate the charge at 5,586 selected
exact boundary/event centres. The minimum strict core margin is
`1/1000000000000`. Complete coverage comes from the sweeps and the universal
boundary argument in [PROOF.md](PROOF.md); the selected samples provide
additional implementation checks.

| Quantity | Exact value |
|---|---:|
| Minimum charge per core | 0.999962528 |
| Total available budget | 10.999479944 |
| Charge required by eleven cores | 10.999587808 |
| Positive counting surplus | 0.000107864 |

All four values have denominator $10^9$. The positive surplus yields the
contradiction. The certificate SHA-256 is
`57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458`.

The second full scans took about 9.5 minutes in Python and 7.6 minutes in
JavaScript on the recorded machine. Follow the [README](README.md) to run them
again and save a fresh set of results.

## Verification status

The two geometric implementations share a mathematical proof strategy and
certificate. The premise controls are independently implemented using Python’s
standard-library rational arithmetic and do not import the project verifiers.
These provide implementation
diversity, not a different proof method, external peer review, or proof-assistant
formalization. No claim of literature priority is made.

The assertion-based command entry points reject optimized Python execution,
which would disable their assertions. The certificate, geometric kernels,
source reconstruction recipe and full scan records are preserved byte for byte.
The assertion guard does not change their normal-mode executable logic.
The [manifest](MANIFEST.json) records the distributed file hashes.

The original aggregate record is preserved as
[evidence/initial/summary.json](evidence/initial/summary.json). Its
`improvement_over_pass1` field compares against the project's earlier 3.828
bound; it is a historical comparison, not a claim about the literature.
