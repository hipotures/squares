# Exact Replay of the Ten wand125 Point Certificates

The live transcript is [`sqpack-exact-replay.log`](sqpack-exact-replay.log).
The source adapter is the unmodified `src/check_with_sqpack.py` from
`wand125/square-packing-bounds` at `1398e42f17f23fe3744bc54425a589fab1f3542c`. The
native checker is this repository’s `sqpack.fractional.certificate.verify`, unchanged
from `b57e4d66ad4f4ef8df71f45ca9afa8ff03d844cc`. The invocation directory is the
repository root, because the external adapter resolves `packing/src` relative to it.
The runtime is the project’s CPython 3.14.7 environment, with one verifier worker.

The original run reads the corresponding clean pinned clone under
`/private/tmp/squares-frontier-20260922/wand125-square-packing-bounds`. Its retained
bytes are under [`../../wand125-points/`](../../wand125-points/); the acquisition
manifest binds every archived file to that source tree.
Reproduce from the repository root, using the retained copy:

```bash
point_source=packing/resources/web/external-square-certificates-2026-09-22/wand125-points
packing/.venv/bin/python3 -u "$point_source/src/check_with_sqpack.py" \
  "$point_source/certificates/cert_n26_L545.json" \
  "$point_source/certificates/cert_n29_L557.json" \
  "$point_source/certificates/cert_n39_L650.json" \
  "$point_source/certificates/cert_n40_L650.json" \
  "$point_source/certificates/cert_n53_L738.json" \
  "$point_source/certificates/cert_n55_L754.json" \
  "$point_source/certificates/cert_n56_L762.json" \
  "$point_source/certificates/cert_n69_L841.json" \
  "$point_source/certificates/cert_n70_L855.json" \
  "$point_source/certificates/cert_n72_L861.json"
```

Acceptance requires ten completed entries, each with `accepted = True`, all five
conditions passing, and the corresponding final bound line.
The adapter exits zero on an empty file list, so exit status alone does not establish
this declared scope.
The native checker recomputes exact total mass and the complete 201-direction event-cell
minimum; saved upstream success strings and floating-point checks are not its premises.

The adapter and each certificate header were independently reviewed in the
[density review’s point-adapter section](../../../../../../docs/project/reviews/review-2026-09-22-tokoharu-density-mathematics.md#supplemental-review-predecessor-point-adapter).
The source n53 mass is below 52, and the source n69 mass is below 68. Both complete
sweeps passed. Reducing only the target count therefore proves the same side at n52 or
n68 without changing a geometric premise.
These are local deductions from the source data, not claims quoted from its README.

The exact sweep supplies one complete coverage method.
No independent interval sweep is claimed by this receipt.
These complete replays and the mathematical premise audit support the verified case
fields, with the local n52/n68 deductions recorded separately from the literal upstream
claims.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
