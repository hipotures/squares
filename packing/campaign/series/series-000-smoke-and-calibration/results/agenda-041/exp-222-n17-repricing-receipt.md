# Exp-222 Re-pricing the n=17 Kleddamag Measure on Its Own Catalogue

Status: **RUN IN PROGRESS — numbers below are placeholders until the full sweep lands.**

This is the `A2` cell of
[X-042](../../../../explorations/X-042-what-is-left-at-low-n.md), hypothesis `H-233`:
the external `461300/99853` measure was priced against a catalogue that row generation
then moved under it, and the question is how much mass a linear program can take out of
it at the same `(L, A)`, on the same support.

## The instrument

[`devtools/reprice_kleddamag_measure.py`](../../../../../devtools/reprice_kleddamag_measure.py)
reads the retained
[`global-certificate.json`](../../../../../resources/web/n17-kleddamag-certified-bound-2026-09-21/kleddamag-17-squares-certified-bound/global-certificate.json)
through `devtools.translate_kleddamag_certificate`’s own `read_source` and `expand`, so
the translation and its nine controls are not re-done here and not re-decided here.
What is new is the **argmin**. The artifact’s checker reports each catalogue row’s least
charge and discards the cell it was attained at; this sweep keeps it, reads the capture
set off the rotated site frame at that cell, and folds it onto the orbits that own the
sites. The result is one linear-program row per catalogue row.

| Piece | Value |
| --- | --- |
| Variables | 1,134 point-orbit weights + 253 two-of-three orbit weights = 1,387, all non-negative |
| Constraint | one per catalogue row, at its minimising cell: `sum_o a_o w_o + sum_s b_s w_s >= 1` |
| `a_o` | how many of orbit `o`’s sites the row’s core captures at that centre |
| `b_s` | how many of orbit `s`’s triples have at least two of three captured |
| Objective | `sum_o |orbit_o| w_o + sum_s |triples_s| w_s`, the artifact’s own `budget_units` arithmetic |
| Read against | `budget_units / minimum_units = 16998427356/1000020517 = 16.998078606` |

The baseline is that ratio and not `budget_units` itself because both conditions are
homogeneous in the weights: a measure of budget `B` whose least charge is `G` rescales
to one charging at least 1 everywhere at mass `B / G`. The artifact’s own measure is
therefore an exactly feasible point of this program at mass `16.998078606`, which `K4`
re-derives rather than assumes.

## Controls

CONTROLS_TABLE

## What was extracted

EXTRACTION

## The linear program

LP_RESULTS

## What the value is, and is not

CAVEATS

## One round of separation

SEPARATION

## Row generation on a sub-catalogue

ROWGEN

## H-239: the dual by angle

H239

## Commands and wall times

COMMANDS

## What this did not establish

NOT_ESTABLISHED

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
