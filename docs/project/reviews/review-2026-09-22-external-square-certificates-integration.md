# External Square Certificates: Mathematical and Integration Review

Date: 2026-09-22. Owning record:
[Session 152](../../../packing/campaign/agent-sessions/session-152-external-density-and-n11-review.md),
bead `think-6xoc`. This review starts at PR #219’s head
`697cd74873140c9d594cb966e77ba082627aca9c` on `codex/pr-219-followup`.

The source set is the two repositories supplied by the owner, their proof dependencies,
and wand125’s density fork named indirectly by the supplied post.
Complete source trees, release evidence, licence notices, and social captures are
retained in the
[source packet](../../../packing/resources/web/external-square-certificates-2026-09-22/README.md).
The two detailed proof audits are the
[Tokoharu review](review-2026-09-22-tokoharu-density-mathematics.md) and
[Kleddamag n11 review](review-2026-09-22-kleddamag-n11-mathematics.md).

PR #219 merged during the review.
The branch was fast-forwarded to its merge commit
`b57e4d66ad4f4ef8df71f45ca9afa8ff03d844cc`; this intake can therefore merge directly to
main without depending on an unmerged stack.

| Claim | Mathematical review | Executable evidence |
| --- | --- | --- |
| Tokoharu `s(26) >= 1377/250 = 5.508` | Covering theorem, symmetry, exact mass and interval arithmetic reviewed; no blocker found | Complete 201-direction source replay passed |
| Tokoharu `s(29) >= 571/100 = 5.71` | Same proof contract; no blocker found | Complete 201-direction source replay passed |
| Tokoharu `s(11) >= 381/100 = 3.81` | Valid calibration claim, superseded numerically | Complete 201-direction source replay passed |
| Kleddamag `s(11) > 31/8 = 3.875` | Threshold budget, core containment, centre envelopes, cell coverage and strict endpoint reviewed; no blocker found | Complete Python and JavaScript replays, final controls and receipt reconciliation passed |
| wand125’s ten point certificates | Adapter and native theorem contract reviewed; conservative count labels identified | All ten complete exact replays passed all five conditions on the full 201-direction net |
| Kleddamag `s(17) > 461300/99853 ≈ 4.619791` | Prior complete proof audit found no blocker; withholding for lack of C4 contradicted the admission contract | Prior full replay attested in Session 150; adopted here with its provenance limitation stated below |

Both Astra reviewers also cross-reviewed the other lane’s load-bearing derivations.
That independent mathematical review is distinct from independently recomputing all
coverage cells by a second method.

## Findings and their consequences

### The certificate claims and the research implications are different questions

Tokoharu supplies rectangle-density certificates at n = 11, 26 and 29. A nonnegative
integrable density with total mass below n, integrated to at least one over every
contained unit square, excludes a packing of n squares.
Boundary contact adds no area, so it contributes no density mass.
The implementation certifies shrunken cores on a finite angle net with outward rounding;
its positive-area basis does not eliminate the angle-net or shrink argument.
The complete replay and exact premise audit are recorded in the detailed review.

This is a representation and numerical-conditioning improvement within the one-body
weighted-covering method.
[X-027](../../../packing/campaign/explorations/X-027-stromquist-fractional-and-structural-strategy.md)
is the relevant existing mathematical comparison; the detailed density audit identifies
the exact local file and scope.
A limiting argument connecting point masses and densities does not justify converting a
particular certificate by assigning each cell’s mass to its centre.
That changes boundary coverage, and the source itself reports the failure of that
proposed cross-check.
A converter needs a proved error bound paid from the certificate’s actual slack.

Kleddamag’s n11 certificate is a generalized threshold-charge obstruction.
It uses ordinary sites and 2-of-3, 2-of-5 and 3-of-5 features.
The charge budget of a k-of-m feature is `floor(m/k)` times its weight; in particular, a
2-of-5 feature costs twice its weight.
The repository already implements that general budget in
[`threshold.py`](../../../packing/src/sqpack/fractional/threshold.py).
The external contribution is the certificate’s support, weights and adaptive
parent-angle catalogue.
Merely adding those threshold names to the existing code would not reproduce the result.

### High: the density continuation driver accepts mismatched imported claims

The density reviewer reproduced `TARGET_REACHED` for n = 1 using the genuine n29
certificate, and a claimed final side of 100 after changing only imported metadata.
The driver trusts successful coverage flags without binding the target count, total mass
and claimed side to the certified candidate and input.
The published certificates pass separate checks; this defect concerns the driver as an
admission path.

The retained source remains unchanged.
The project must reject such imports before treating a future driver output as evidence.
`think-c0xc` tracks the guard and its two regression cases.
The detailed density review names the exact source lines and raw control receipts.

### The two exact n11 implementations do not provide a second complete method

The Python and JavaScript scans share the same signed-rectangle expansion and
reachable-cell reduction.
Their agreement is useful implementation checking.
Independent quadratic containment checks cover every angle interval, while dense-cell
and boundary probes exercise selected rows.
Those controls do not independently decide the entire coverage premise.
A full source replay and the source-distinct mathematical review must be recorded at
their actual scopes; neither is a complete method-distinct first-party decision.

The n17 translator introduced on the parent branch also cannot be applied unchanged: it
expects triples and a fixed n17 input structure.
The existing n11 threshold model supports the charge families, but its ordinary
certificate contract quantifies over all contained cores, while this release assigns
cores only at centres admissible for the larger parent.
Discarding that restriction can produce a false rejection; retaining it without proving
the centre envelope can produce a false acceptance.

The retained native preflight also finds 5,284 active sites against the interval route’s
4,096-site limit, and 13,580 feature-member slots against its 8,192-slot limit.
These limit reuse of the current native interval implementation.
An adapter needs measured batching or an equivalent representation; the completed
external exact replay already supports the verified bound.

### The social claim of further density improvements is not recovered

The public wand125 density default branch and `add-push-driver` branch retain the same
three certificate values as Tokoharu.
The extra branch adds a continuation driver and tests.
The fetched source set therefore supports 5.508 and 5.71, but supplies no stronger
numerical certificate.
The social sentence is retained as a claim with missing support, rather than assigned an
invented numerical value.

## Source and replay accounting

| Source | Pinned revision | Scope |
| --- | --- | --- |
| Tokoharu density | `b543990f7794b8c511cb46cf3854b7e8166c3674` | All three certificates, interval checker, proof, generator and tests |
| Kleddamag n11 v1.0.2 | `6a733f339395c3514f2ab63d8c4aa64cf63c0b5a` | Strict 31/8 certificate, both checkers, controls and release evidence |
| wand125 points | `1398e42f17f23fe3744bc54425a589fab1f3542c` | Ten certificates; Tokoharu’s cited predecessor also retained |
| wand125 density | `096294aeb5f8b604df5890beda6cd601d05f4561` | Same three certificate values; feature branch `93c0edde5745718b8490c37ee28543abea477b40` adds the driver |
| Guzhou0806 n17 | `32edfd3da78bf80a309398f552b3b602b9c45d6c` | Complete linked source tree and R038 dependency used by the secondary checker |

The acquisition manifest owns file inventories, hashes at the external-source trust
boundary, and exact omission reasons.
Repository Git history owns the integrity of first-party records.
Raw upstream source is never formatted or patched to satisfy the project’s style checks.

## Frontier integration policy

The verified lane records the largest lower bound the repository can certify on its own
evidence, as required by the case schema and Frontier admission rules.
The complete coverage replays and source-distinct proof audits discharge the assumptions
for the external density, n11 threshold and completed point certificates.
Their bounds replace weaker verified fields, with origin `replayed-here` and the actual
C3 method scope. The atlas and generated reader views follow those fields.
In total, 20 verified case bounds improve: 19 from the newly audited sources and one n17
correction using the prior replay.
No upper construction changes, and no result identifier is registered or re-scored.

An intermediate draft incorrectly held these verified fields at older values until a
second, native method existed.
Review against the
[case schema](../../../packing/frontier/square-packing-case.schema.yaml),
[Frontier admission rules](../../../packing/frontier/README.md) and
[epistemics rules](../../../epistemics.md) corrected that decision before adoption: C3
is complete machine replay, C4 adds a second complete method, and C5 can attach mapped
review to either. C4 is additional confirmation, not an admission prerequisite.
The native follow-ups below therefore concern generalization and stronger confirmation.

The reported lane retains literal recovered source claims and their explicit monotonic
consequences. For point certificates, n appears only in the mass-budget inequality.
Two source labels are conservative: the fully replayed n53 certificate has mass
`1287080441/25000000 < 52`, and the fully replayed n69 certificate has mass
`846701027/12500000 < 68`. The same certificate bytes consequently prove
`s(52) >= 369/50 = 7.38` and `s(68) >= 841/100 = 8.41`. These are local deductions from
the external certificates, without a priority claim; they do not replace the literal
reported Green values with statements the upstream source did not make.
The upstream point README explicitly reports the n41 and n71 monotonic consequences.
Tokoharu’s n26 density certificate also improves verified n28 to 5.508, while its
stronger reported Green value remains unchanged.

The same policy review identified an existing inconsistency at n17. Session 150 had
already recorded a complete approximately 1,001-second Kleddamag v1.0.0 replay, matching
the published result byte for byte, and the
[September 21 proof review](review-2026-09-21-n17-kleddamag-461300-99853.md) found no
blocking defect. The case nevertheless withheld `461300/99853` solely for lack of a
second method. This intake corrects both its literal reported field and its verified
lower bound to that strict `s(17) > 461300/99853 = 4.619791…` theorem, retaining T-032
as history. This is a correction based on the earlier repository execution attestation
and proof review; no fresh n17 full replay is claimed.
That older packet retains manifest-bound source outputs and the dated local attestation,
not a separately named copy of local raw replay output.
The new Guzhou archive also makes the former “not retained” description of R038
obsolete: its published tree is now retained, its external Mira numerical dependency is
still external, and R038 has not been locally replayed in this block.

The n17 cross-check also corrects one diagnostic explanation in the older review:
Python’s 15,706 additional slabs equal two cuts per each of 7,853 intervals, at the two
interior polygon vertices.
They are not exterior end slabs.
The JavaScript scanner handles those vertices through clamping without the extra cuts,
as the new n11 review derives for the same checker lineage.
Minimum charges and complete histograms are the appropriate comparison; this correction
does not change the theorem or replay verdict.

## First-party integration review

The first-party audit instruments were reviewed at their source-execution boundary.
Initial provenance gaps were corrected before integration: the density auditor checks
all 62 retained source files before executing its checker, while the n11 auditor pins
the release manifest and checks its 54 payload files before importing source code.
Altered files, missing density checker code and injected n11 modules are refused; the
n11 audit also bypasses pre-existing bytecode caches.
The n11 receipt reconciler binds bounds, budgets, complete row coverage and sample
counts to the pinned certificate.
Both tools publish their final audit JSON atomically.
Twelve focused tests exercise these boundaries and the mathematical counterexamples;
both tools pass Ruff and BasedPyright.
Source bytes were preserved, including upstream whitespace that a raw Git whitespace
check reports; first-party diffs pass that check.

The design keeps source acquisition, independent premise checks, source execution and
case adoption explicit.
Reusing the native point verifier is appropriate for the point certificates; extending
it silently to density integrals or restricted parent-core domains would change its
theorem contract. No further code-review blocker was found in the new audit instruments.
The complete project gate is recorded separately at session close.
These tools and tests protect the reviewed source identity and audit premises; they do
not supply the missing independent global coverage methods.

The publication review also found stale descriptions of T-026 as the current strongest
bound. The explainer now identifies its T-026 proof as historical and links a dated
update to the verified 3.875 Frontier case and mathematical review.
Its original proof values, certificate bytes, edition number and publication date remain
unchanged; the atlas displays the updated current bounds.

## Next technical work

1. Generalize the native verifier to threshold input only with exact source binding,
   k-of-m budgets, complete D4 expansion and bounded integer accumulation.
   Preserve parent-centre domains and the adaptive catalogue, and decide that same
   geometry with an interval method independent of the event sweep.
   `think-d010` owns this first priority.
2. Guard density imports against the two reproduced metadata substitutions.
   Keep rectangle densities in their native representation for verification; an atomic
   approximation needs a separate transport-error proof.
   `think-c0xc` owns the import defect and `think-ck07` the independent density route.
3. Use the external n11 certificate as the comparison target for future research.
   Any first-party rung below 3.875 remains useful as controlled evidence or a simpler
   certificate, but is not a public lower-bound advance.
   The strict 3.875 bound also exceeds the retained 181-direction fixed-core point
   model’s packing-side cap of about 3.869, recorded by
   [X-014 in the certificate-reach analysis](../../../packing/frontier/CERTIFICATE-REACH.md).
   Search within that unchanged model is therefore foreclosed; an improvement requires a
   changed model, for example finer angles or a different core-domain contract.
4. Treat the older n26 point-basis plateau as evidence about the tested representation,
   not a barrier refuted by a distinct packing method.
   Evaluate rectangle pricing against its measured cost and slack with the retained
   source verifier and an explicitly scoped comparison protocol.

## Subsequent main-branch reconciliation

After Session 152 closed and PR 222 passed its final checks at `7d4a755`, PR 218 merged
into main as `d5b1c2e1b`. Its workbench citation renderer and shared data-version stamp
conflicted with the updated atlas exports on this branch.
`think-ujyr` tracks the follow-up merge and renewed validation; it is outside the
completed Session 152 measurement cutoff.

The reconciliation keeps the new renderer and version contract, adds bibliography
entries for the four external sources now supplying verified case bounds, and rebuilds
the citation and figure records from the combined data.
The external certificate bytes and adopted bounds remain unchanged.
The two subsequent work branches hold publication until this base is again green and
mergeable.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
