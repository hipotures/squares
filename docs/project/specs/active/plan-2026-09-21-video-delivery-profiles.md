# Feature: Video delivery profiles

**Date:** 2026-09-21 (last updated 2026-09-21)

**Author:** Joshua Levy, with Claude Opus 5

**Status:** Draft

## Overview

`workbench_tools.capture_video` turns the built workbench page into an MP4 and writes a
receipt saying what the frames are.
It stops one step short of the thing the owner actually needs: a statement that the file
it produced is one the destination will accept.

This adds that step.
A **delivery profile** is a named, declared set of constraints on the encoded file —
codec, H.264 profile and level, pixel format, frame size, frame rate, and any ceiling
the destination puts on duration or bytes.
One profile drives the encoder arguments and then checks the encoded file against the
same declaration, so what was asked for and what came out are compared rather than
assumed.

## Goals

- Name the encoder’s settings once, as data, and use that one declaration to both encode
  and verify.
- Fail a capture whose output does not conform, in the same way
  `capture_video.price_steps` already fails a capture whose frame clock is not the
  page’s.
- Record the conformance measurement in the receipt, so a file and its receipt together
  answer “will this upload” without re-running anything.
- Measure fidelity against the page’s own PNG frames, not against another encode, so a
  quality claim is distance from the page.
- Leave one command that validates a delivered file on its own.

## Non-Goals

- Choosing where the videos are hosted, or uploading anything.
  This produces files and evidence about them.
- A per-destination catalogue.
  Two profiles are enough for what exists: an unconstrained archive master and one
  social profile carrying the tightest ceiling we actually face.
- Audio. The animation is silent, and the destinations under consideration accept silent
  MP4.
- Replacing `--height`. The stage’s own coordinates and the 1080p/4K device scales are
  settled in the video plan and are not revisited here.

## Background

Three facts from the end-to-end run on 2026-09-21, which cut n = 1..100 and the whole n
= 1..324 ascent:

- **x264 tags the output level 5.0.** At `-preset slow` it keeps five reference frames,
  whose decoded-picture-buffer size at 1920x1080 exceeds what level 4.0 allows, so it
  raises the level rather than dropping a reference.
  1080p30 needs level 4.0, and the higher tag buys nothing: cutting n = 1..100 both ways
  gives 11,659,220 bytes at level 4.0 against 11,659,739 at 5.0 over the same 3,342
  frames, the constrained file coming out 519 bytes smaller.

- **Nothing checks the file.** The receipt names the encoder’s arguments but not the
  encoded stream, so the two could disagree — an ffmpeg that ignored a flag, a filter
  that changed the frame size — and the receipt would still read as if they had not.

- **The duration ceiling is real and it binds.** n = 1..100 runs 111.4 s and n = 1..324
  runs 382.7 s. A standard X post takes 140 s. Which excerpt fits is a fact about the
  range, decided long before anyone opens an upload dialog, and the tool already knows
  the range’s duration before it captures a frame.

The first cut also found [`D-492`](../../../../defects.md): `rangeDuration` priced a
range without the `fastSimple` speed-up, so the page quoted a range it played faster
than it said, and `price_steps` refused every capture.
Fixed at `e00c4529`. It is the reason this plan exists — the check that caught it is the
model for the check proposed here.

## Design

### Approach

A profile is a frozen dataclass, and the registry of profiles is a module constant.
`capture_video` takes `--profile`, passes it to the encoder, and then measures the file
it wrote and refuses to write a receipt for a file that does not conform.

The measurement and the check are separate functions over plain data, so both are
testable without ffmpeg and without a browser: `measure` parses `ffprobe`’s JSON into a
`DeliveredVideo`, and `conformance` compares a `DeliveredVideo` against a
`DeliveryProfile` and returns the failures.

### Components

| Path | What it is |
| --- | --- |
| `packages/workbench/tools/workbench_tools/delivery.py` | New. `DeliveryProfile`, `PROFILES`, `encode_arguments`, `measure`, `conformance`, `fidelity`, and a `main` that validates a file on its own |
| `packages/workbench/tools/workbench_tools/capture_video.py` | Takes `--profile`; encodes through `delivery.encode_arguments`; checks the encoded file before the receipt is written; records the profile and the measurement in the receipt |
| `packages/workbench/tests/test_delivery.py` | New. Profile-versus-measurement cases over plain data, and the encoder argument contract |
| `packages/workbench/tests/test_capture_and_export.py` | The existing `encode_arguments` contract moves to the profile-driven form |
| `packages/workbench/pyproject.toml` | `squares-workbench-check-delivery` console script |

### API Changes

`capture_video.encode_arguments` moves to `delivery.encode_arguments` and takes a
`DeliveryProfile` as its first argument.
It has one consumer in the repository and one contract test, both updated here.

`capture_video.capture_receipt` gains `profile` and `delivered`, so an existing receipt
read by a future consumer gains two keys rather than changing any.

### The two profiles

|  | `archive` | `social` |
| --- | --- | --- |
| Purpose | The master. Nothing is traded for a destination’s rules | An upload to X, which is the tightest ceiling we face |
| H.264 profile / level | high / 4.0 | high / 4.0 |
| Pixel format | `yuv420p` | `yuv420p` |
| CRF / preset | 18 / `slow` | 18 / `slow` |
| Duration ceiling | none | 140 s |
| Byte ceiling | none | 512 MB |

Level 4.0 is in both because the measurement says it costs nothing and it is the level
1080p30 requires; a master tagged for hardware that cannot play it is not a better
master. What separates the profiles is only the ceilings, which is the honest split: a
ceiling is a property of a destination, not of an encode.

CRF and preset are declared per profile even though both profiles currently agree,
because that is the axis a future destination would move.

### What conformance checks

Codec, H.264 profile, level, pixel format, width, height, frame rate, and that the
stream’s duration matches the receipt’s to within one frame.
Under a profile carrying ceilings, also duration and bytes.
`faststart` is checked by position of the `moov` atom rather than by trusting the flag.

A failure names the constraint, the declared value and the measured one, in that order,
because the useful question on a red check is always which of the two is wrong.

### Fidelity

`fidelity` runs ffmpeg’s `psnr` and `ssim` filters over a declared window of the
capture’s retained PNG frames against the encoded file, and returns both figures with
the window that produced them.
It is not part of conformance: a profile is a statement about the container and the
stream, and fidelity is a measurement whose acceptable value is a judgement.
It is reported, recorded when frames are available, and never silently turned into a
threshold.

The window is declared rather than defaulted to the start of the run, because the first
frames of the ascent are three squares on white and say nothing about how the encoder
handles n = 300.

## Implementation Plan

### Phase 1: profiles, conformance, and the capture wiring

- [ ] `delivery.py`: `DeliveryProfile`, `PROFILES`, `encode_arguments`,
  `DeliveredVideo`, `measure`, `conformance`, `fidelity`, `main`.
- [ ] `capture_video`: `--profile`, encode through the profile, check before the
  receipt, record `profile` and `delivered` in the receipt.
- [ ] Move the `encode_arguments` contract test to the profile-driven form.
- [ ] `test_delivery.py`: conformance over plain data — a conforming measurement, each
  constraint violated one at a time, the ceilings under `social` and their absence under
  `archive`, and a duration that disagrees with the receipt by more than a frame.
- [ ] Console script `squares-workbench-check-delivery`.
- [ ] Ruff, BasedPyright and `pytest ../packages/workbench/tests` at zero findings.

### Phase 2: re-cut and validate the deliverables

- [ ] Re-capture n = 1..324 under `archive` and n = 1..100 under `social`, at 30 fps.
- [ ] Capture n = 1..100 at 60 fps under `social` for comparison against the 30 fps cut.
- [ ] Record the measured fidelity and the conformance result for each.

## Testing Strategy

`conformance` and `measure` are pure functions over plain data, so the table of cases
runs with no ffmpeg, no browser and no fixture video: a conforming `DeliveredVideo`,
then one field wrong at a time, then the ceilings present and absent.

What the unit tests cannot establish is that `measure` parses what `ffprobe` actually
emits. That is covered by the capture itself: every capture now measures its own output
and fails on a mismatch, so a parse that stopped working stops the next cut rather than
passing quietly.

The `fidelity` window’s arithmetic — which frames it names — is tested over plain data;
the filter invocation is not mocked, because a mocked ffmpeg proves nothing about
ffmpeg.

## Rollout Plan

Nothing is published by this change.
It alters a developer tool and adds a checker.

The captures live outside the repository: `packing/site/` is gitignored and built by CI,
and a multi-megabyte MP4 is not committed.
Where the finished files are hosted is a separate decision, tracked on the video epic
`think-hsdj`, Phase 4.

## Open Questions

- Does a silent AAC track widen what accepts the file enough to be worth carrying?
  Not measured. X accepts silent MP4, which is the destination that prompted this.
- Should the 4K device scale get its own profile?
  Level 4.0 does not admit 3840x2160, so a 4K capture would need level 5.1 and the
  profile table would grow a row.
  Deferred until a 4K cut is actually wanted.

## References

- [Known-best atlas video plan](plan-2026-09-07-known-best-atlas-video.md), whose D9
  defines the receipt this extends
- [Workbench from spike to product](plan-2026-09-11-workbench-from-spike-to-product.md)
- [`D-492`](../../../../defects.md), the timing defect the first end-to-end cut found

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
