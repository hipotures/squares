# Profile data

The lightweight operation profiles are stored as machine-readable samples in
`../raw/profile-separation-w*-s*.json` and `../raw/lp-profile-s*.json`.
Complete round timings are in the baseline sample files. Native selector and
HiGHS calls are timed as operations; a Python-only call profiler would miss
their internal work. The uninstrumented replay files quantify instrumentation
overhead, and `../report.md` explains the wall/CPU distinction.
