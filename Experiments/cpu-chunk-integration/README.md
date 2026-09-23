# Ordered four-direction production integration

The production input was `5f10bffeb207d5bc598a6244f11375cee3418d62`.
The accepted production commit is `011aa1b5f39457de1e2d9f5589b3df3f04e36575`.
All runs used n=12, outer side 99/25, the `bench_colgen.Case` default square
side and 181-direction net, and `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`.
The retained `.npz` fixtures are referenced at
`../cpu-post-integration-profile/raw/current-states.npz` and
`../cpu-post-integration-profile/raw/current-rows-csr.npz`; they are not
duplicated here.

Run from `packing/` with the project virtual environment (or `uv run --frozen`):

```bash
export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers 1 --samples 3 --target-seconds 18 --output-dir ../Experiments/cpu-chunk-integration/raw/control-w1
python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers 16 --samples 3 --target-seconds 18 --output-dir ../Experiments/cpu-chunk-integration/raw/control-w16
# Apply production commit 011aa1b5 after the two controls.
python ../Experiments/cpu-chunk-integration/verify.py
python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers 16 --samples 3 --target-seconds 20 --output-dir ../Experiments/cpu-chunk-integration/raw/candidate-w16
python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers 1 --samples 3 --target-seconds 18 --output-dir ../Experiments/cpu-chunk-integration/raw/candidate-w1
python ../Experiments/cpu-chunk-integration/paired_solver.py --samples 3 --target-seconds 18
python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers 4 --samples 3 --target-seconds 18 --output-dir ../Experiments/cpu-chunk-integration/raw/candidate-w4
python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers 8 --samples 3 --target-seconds 18 --output-dir ../Experiments/cpu-chunk-integration/raw/candidate-w8
python ../Experiments/cpu-chunk-integration/replay.py --workers 1 --samples 3 --target-seconds 20 --tag=-accepted
python ../Experiments/cpu-chunk-integration/replay.py --workers 4 --samples 3 --target-seconds 20 --tag=-accepted
python ../Experiments/cpu-chunk-integration/replay.py --workers 8 --samples 3 --target-seconds 20 --tag=-accepted
python ../Experiments/cpu-chunk-integration/replay.py --workers 16 --samples 3 --target-seconds 20 --tag=-postprofile
python ../Experiments/cpu-chunk-integration/replay.py --workers 16 --samples 3 --target-seconds 20 --mode reference --tag=-postprofile
python ../Experiments/cpu-chunk-integration/profile.py --workers 1 --samples 3 --target-seconds 18
python ../Experiments/cpu-chunk-integration/profile.py --workers 16 --samples 3 --target-seconds 18
python ../Experiments/cpu-chunk-integration/verify_profile.py
python ../Experiments/cpu-chunk-integration/summarize.py
```

The first accepted 16-worker replay and its original-task control also remain
under `raw/*-accepted-*.json`. The later `postprofile` pair is used for the
scaling comparison because it was stable and adjacent to the operation profile.
`paired_solver.py` changes only an in-process research hook to replay the
original one-direction mapping on the accepted production commit; it does not
edit source. Each full-solver pair reverses order in sample 2.

`results.json` is regenerated from `raw/` by `summarize.py`. It includes all
sample values, ranges, CVs, and a >=10-second duration audit. The report
explains which numbers are end-to-end and which are steady-state replay.
