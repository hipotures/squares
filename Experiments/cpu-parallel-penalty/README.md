# Causal CPU parallel-scaling campaign

This research runs the accepted n=12, side=99/25 separation workload on the
current production main. The starting commit is
`897b722f2997fbf09b99b1700787a0052270de30`, which contains production
chunk integration commit `011aa1b5f39457de1e2d9f5589b3df3f04e36575`.
Production source is not edited. Existing user deletions and unrelated
untracked files are excluded from research commits.

The four required checkpoints are Phase A (Tests 1–3), Phase B (Tests 4–6),
Phase C (Test 7), and Phase D (Test 8). All phases are complete. Each
phase's raw evidence, scripts, processed values, and interpretation is
committed and pushed before the next phase begins. Controlled runs use one
thread each for OpenMP, OpenBLAS, and MKL, with three 20–40-second samples
for final comparisons.

Test 8 includes the physical PVE control received after the original
host-access-blocked checkpoint. The first PVE 8-worker batch was under the
10-second minimum, so 8/16-worker endpoints were repeated on both machines
with a revised identical fixed plan. The final comparison is in
`test08-host-vm/processed/summary-complete.json`.

The retained replay inputs are referenced from
`Experiments/cpu-post-integration-profile/raw/current-states.npz`; no copy is
needed here. The existing complete-replay driver is
`Experiments/cpu-chunk-integration/replay.py`.
