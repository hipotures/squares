# Test 7: ordered four-direction task timeline

The control retains the production four-consecutive-direction chunks,
persistent `ProcessPoolExecutor`, and original result/row order. The driver uses
explicit futures so each chunk's submission, worker start/finish, future-ready,
and parent-consume times can be observed. The control submits chunks in
production order. The cost-first experiment submits the same chunks in
descending order of their **previous-round** cell counts; round zero remains
in production order. The balanced experiment packs expensive and cheap
directions into four-direction chunks using the same previous-round cell
counts. It retrieves chunk futures as required by the original direction
order, so rows are still materialized in exactly that order. Prediction is
cheap and uses only data already observed by the previous round; no future
round is inspected.

The driver also times the uninstrumented production `pool.map` replay to
quantify instrumentation/scheduling-wrapper overhead. The timeline version
wraps `event_grid` in workers only to record output grid dimensions; it calls
the production function unchanged. Exact row directions, centres, matrix,
and accepted count are checked against the retained production hashes.

Each important timing sample repeats complete 23-round in-memory replays to
at least 20 seconds. Raw traces are compressed JSON in `raw/`; scripts,
reduced min/median/max/CV, and interpretation are preserved in this directory.
`scripts/run_final.py` rotates the order of production, ordered, and cost-first
endpoints across three long sets. `scripts/run_balanced.py` takes three adjacent
ordered/balanced pairs. `processed/summary.json` retains all 23-round timeline
statistics for each mode.
