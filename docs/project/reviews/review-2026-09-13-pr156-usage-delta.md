# PR156 Native Usage Delta Audit

Snapshot: 2026-09-13 19:30:30 UTC. Historical bead cutoff: 2026-09-12 14:04:44.097 UTC.

A conservative, additive local Codex delta is measurable for 27 completed,
scanner-complete BC329 child task trees.
The selection is disjoint from the 13 roots already listed in think-92jm. The 27 trees
contain 62 recursive sessions in the after snapshot.
Their post-cutoff event delta has 2,191 native response-usage events, 258,809,511 input
tokens (247,444,992 cached), 1,125,247 output tokens (448,041 reasoning), and 41,905.847
seconds of summed agent-active time (11h 38m 25.847s). Input includes cached input;
output includes reasoning output.
Agent-active time sums simultaneous agents and is not elapsed wall time or provider
latency.

## Model and Effort

Model/effort rows are taken from the session event contexts, including recursive
automatic approval reviews.
The stream column is timed model-output items, a lower bound where recorded; it is not
native turn time. First-token wait is available only for the first response of a
completed turn.
Automatic approval review has no timed stream items in these logs, so its
apparent zero is reported as unavailable.

| Model and effort | Responses | Input | Cached input | Output | Reasoning output | Timed stream (s) | Recorded first-token wait (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Automatic approval review, low | 289 | 21,449,076 | 18,315,520 | 32,007 | 14,651 | unavailable | 804.752 |
| GPT-5.6 Sol, high | 64 | 6,840,418 | 6,472,320 | 39,845 | 19,825 | 526.423 | 17.507 |
| GPT-5.6 Sol, max | 666 | 75,713,187 | 73,877,760 | 329,225 | 137,490 | 2,769.575 | 81.985 |
| GPT-5.6 Sol, xhigh | 922 | 122,823,537 | 118,127,744 | 533,867 | 210,038 | 9,285.413 | 172.322 |
| GPT-6 Astra, max | 250 | 31,983,293 | 30,651,648 | 190,303 | 66,037 | 2,831.466 | 85.372 |
| **Additive total** | 2,191 | 258,809,511 | 247,444,992 | 1,125,247 | 448,041 | 15,412.877 | 1,161.938 |

The 15,412.877 seconds of timed model stream and 1,161.938 seconds of recorded
first-token wait measure different client-side intervals.
Do not add either to agent-active time.
A comparable per-model native-turn-time figure is unavailable from this privacy-reduced
delta.

## Included Task Roots

The model and effort below describe each direct child root.
Its recursive subtree can include different model settings and automatic approval
reviews. Every ID is an exact direct child of the shared coordinator in the local
thread-spawn index; the coordinator itself is excluded.

| Task root ID | Agent path | Root model | Root effort | Recursive sessions | Delta agent-active (s) |
| --- | --- | --- | --- | ---: | ---: |
| 01a095df-adce-7dc2-a34f-f3a1860a471c | /root/bc329_calibration_impl | gpt-5.6-sol | xhigh | 3 | 1,908.593 |
| 01a095ef-97d9-7982-818f-a66f2158929b | /root/bc329_bead_gap_audit | gpt-5.6-sol | high | 1 | 481.002 |
| 01a09609-eeed-79e3-aa1b-17d576bf433a | /root/bc329_calibration_review | gpt-6-astra | max | 4 | 4,878.552 |
| 01a09618-d55b-7ce1-8c20-5618dbd4b86e | /root/bc329_preflight_rereview | gpt-5.6-sol | xhigh | 6 | 3,994.799 |
| 01a09944-b190-7d80-9c25-7e4828558eaf | /root/worker_topology_finish | gpt-5.6-sol | xhigh | 3 | 5,685.376 |
| 01a09944-e53c-79f3-843a-3ee09ec41217 | /root/profile_coordinator_finish | gpt-5.6-sol | xhigh | 4 | 7,272.852 |
| 01a09972-5ef0-7531-a67d-8b6a75d74740 | /root/cal5_exact_review | gpt-6-astra | max | 2 | 1,259.299 |
| 01a099b0-19be-7163-9e85-8745b10e9d87 | /root/topology_exact_head_review | gpt-5.6-sol | xhigh | 1 | 372.070 |
| 01a099b0-3b61-7203-8a17-7e57b8d2275a | /root/coordinator_exact_head_review | gpt-5.6-sol | xhigh | 1 | 303.918 |
| 01a099b0-55ff-7ac3-8a0e-2f1270a3109f | /root/runsheet_exact_head_review | gpt-5.6-sol | high | 1 | 271.272 |
| 01a099b5-539a-7080-ad6b-a1d3d2cad8ae | /root/source_distinct_reader_impl | gpt-5.6-sol | xhigh | 3 | 4,169.271 |
| 01a09bee-a2d8-77a2-8f9a-6e8922b4ff4a | /root/coordinator_exact_acceptance | gpt-5.6-sol | max | 1 | 419.501 |
| 01a09bee-e669-7612-961f-c525da1c1013 | /root/reader_admission_repair | gpt-5.6-sol | max | 4 | 3,042.915 |
| 01a09bf5-3a11-7361-a7ef-76310932dfc1 | /root/coordinator_second_repair | gpt-5.6-sol | max | 2 | 223.092 |
| 01a09bfb-34a6-7192-89ab-2b733acb6a10 | /root/run_sheet_operational_review | gpt-5.6-sol | high | 2 | 230.541 |
| 01a09c02-9415-7ce2-937b-5accbbc46a0f | /root/runset_verifier_design | gpt-5.6-sol | xhigh | 2 | 354.151 |
| 01a09c08-5942-73b1-a86d-9b961cac9611 | /root/reader_exact_head_rereview | gpt-6-astra | max | 2 | 730.339 |
| 01a09c08-b240-72c2-bd08-ec5aa0e110f9 | /root/runset_verifier_impl | gpt-5.6-sol | max | 2 | 991.084 |
| 01a09c17-58b4-74e1-8cb7-128aca23aeaf | /root/runset_verifier_exact_review | gpt-5.6-sol | max | 2 | 418.694 |
| 01a09c1d-ce63-7280-8148-008590bf53bb | /root/runset_verifier_refusal_repair | gpt-5.6-sol | max | 2 | 532.994 |
| 01a09c21-9eec-7081-ad42-b25ece55038e | /root/reader_f6f7_exact_review | gpt-6-astra | max | 2 | 667.180 |
| 01a09c22-f698-78d0-a908-6d436a8f4fa2 | /root/coordinator_exact_refusal_repair | gpt-5.6-sol | max | 2 | 956.618 |
| 01a09c2b-b3dd-7771-8d61-dcbe96b7841a | /root/runset_verifier_repair_exact_review | gpt-5.6-sol | max | 2 | 602.141 |
| 01a09c30-3547-7fb2-993a-2747d9208f8b | /root/reader_f6_final_exact_review | gpt-5.6-sol | max | 2 | 708.645 |
| 01a09c31-b091-7190-bf99-d7c337b3d186 | /root/coordinator_final_exact_review | gpt-5.6-sol | max | 2 | 501.119 |
| 01a09c36-05bb-7180-90e2-0eec97be14b9 | /root/coordinator_phase_overflow_repair | gpt-5.6-sol | max | 2 | 502.680 |
| 01a09c39-52b4-76a1-b73f-dc884c7b3c26 | /root/verifier_r3_final_exact_review | gpt-5.6-sol | max | 2 | 427.149 |

## Boundary and Exclusions

The interval is (2026-09-12T14:04:44.097Z, 2026-09-13T19:30:30Z]. The before snapshot
uses the exact think-92jm timestamp.
The end was chosen after the 19:30:17 UTC completion of the verifier R3 review and
before the 19:30:41 UTC start of this accounting task.
The scanner clips task and timed-event intervals at both cutoffs.
A native token event is charged wholly at its completion timestamp, so one response that
crossed a cutoff is assigned to the interval containing its completion.
The calibration implementation root began before the old cutoff but was not part of the
old 13-root subtotal; only its post-cutoff event delta is counted here.

Two BC329 roots are excluded even though the current thread-turn index shows terminal
work. The Codex scanner still marks one session in each recursive tree incomplete, so a
stable tree total would be misleading:

- 01a095eb-45e5-7cb1-ada4-dea2d196f84f — /root/bc329_preflight_repair
- 01a0967a-141e-7983-865b-7332e38f74e3 — /root/bc329_run_sheet_review

The n11_inference_wording_fixes root (01a09605-feb2-76c3-8837-ff494ae84955) is also
excluded because its path does not by itself prove PR156-only ownership.
This deliberately lowers the subtotal.
The in-flight coordinator_arithmetic_final_review root
(01a09c3d-a338-7572-9bc1-ea025368ee40) began before the end cutoff and had no completed
turn at that cutoff; this accounting task itself began afterward.
Explicit BC303/T1/T2 roots, n11 strategy/surplus work, PR149 work, the PR157 task root
and descendants, and the shared coordinator root (01a082b3-057c-7c62-905c-1a543979e33a)
are absent from the whitelist.
The coordinator log crosses branch work and has no branch telemetry.
No allocation from it is inferred.

The local thread index supplies parent links and agent paths, but Codex does not record
a reliable Git-branch field for this purpose.
Branch attribution is therefore an operator decision grounded in the direct-child path
and the PR156 work described in the current draft.
The native event counters are exact for the selected log trees and declared interval;
they are not a full PR156 bill.
Subsequent work and the excluded trees need a later independent checkpoint.

## Reproduction

No raw prompts, reasoning, message bodies, or command histories were printed, retained
in this note, or inspected manually.
The repository-maintained devtools.codex_log_rollup scanner processed local Codex JSONL
event records in memory and emitted only numeric rollup fields through the temporary
/private/tmp/pr156_usage_audit_compute.py script.
That script uses devtools.codex_task_tree_delta metric and subtraction helpers.
This audit also queried only metadata columns in state_5.sqlite and status/timestamps in
thread_history_1.sqlite.
The numeric intermediate /private/tmp/pr156-usage-computed.json has no transcript text.
The measurement pass edited neither repository files, PRs, nor beads; this report was
copied into PR 156 afterward.

Commands used:

~~~shell
tbd show think-92jm --max-lines 300
sqlite3 /Users/levy/.codex/state_5.sqlite '.schema threads' '.schema thread_spawn_edges'
sqlite3 /Users/levy/.codex/thread_history_1.sqlite '.schema thread_turns'
cd packing
PYTHONPATH=. ./.venv/bin/python3 /private/tmp/pr156_usage_audit_compute.py > /private/tmp/pr156-usage-computed.json
~~~

The script fixes its whitelist and both UTC cutoffs, asserts every path resolves to one
direct child, builds retrospective before and after recursive rollups, rejects any
selected tree with an incomplete session, and subtracts the maintained additive metrics.
The 62-session figure counts after-snapshot sessions once per disjoint included tree;
the 2,191 response events and token counts are post-cutoff deltas.
Timed model-stream and agent-active seconds are scanner measurements, not inferred token
costs or provider timings.

The repository’s maintained `devtools.codex_task_tree_delta` CLI can independently
remeasure any listed root at the two cutoffs.
For example, from `packing/`:

```bash
./.venv/bin/python3 -m devtools.codex_task_tree_delta \
  --sessions-root /Users/levy/.codex/sessions \
  --root-id 01a09c39-52b4-76a1-b73f-dc884c7b3c26 \
  --start 2026-09-12T14:04:44.097Z \
  --end 2026-09-13T19:30:30Z \
  --out /private/tmp/pr156-verifier-r3-delta.yaml
```

Run that command for each of the 27 included roots and add disjoint model rows.
The local JSONL archive is required; the public PR alone cannot regenerate native usage.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
