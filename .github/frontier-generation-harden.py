"""Integration refinements, applied before tests and removed after publication."""
from pathlib import Path


def change(path, old, new):
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"replacement count {text.count(old)}: {old[:120]}")
    p.write_text(text.replace(old, new, 1))


change('packing/devtools/frontier_generation_queue.py', 'import sys\n', '')
change('packing/devtools/frontier_generation_queue.py', '    next_notice = began\n', '    next_notice = began\n    dispatch_turn = 0\n')
change('packing/devtools/frontier_generation_queue.py', '''                for key in list(pending):
                    if not pending[key] or len(serial) + len(futures) >= slots:
                        continue
                    index, context, tail = pending[key].popleft()
                    future = pool.submit(_direction_work, context, tail)
                    futures[future] = (key, index, context)''', '''                ready = [key for key in pending if pending[key]]
                key = ready[dispatch_turn % len(ready)]
                dispatch_turn += 1
                index, context, tail = pending[key].popleft()
                future = pool.submit(_direction_work, context, tail)
                futures[future] = (key, index, context)''')
change('packing/devtools/frontier_generation_queue.py', '            now = time.monotonic()\n            for key, driver in drivers.items():', '''            if not live:
                time.sleep(0.005)
            now = time.monotonic()
            for key, driver in drivers.items():''')
change('packing/devtools/frontier_generation_queue.py', '            if now >= next_notice:', '''            if len(results) == len(jobs) and futures:
                # All useful owners ended (possibly a deadline). Do not wait for
                # discarded work before reaching the bounded cleanup in finally.
                break
            if now >= next_notice:''')
change('packing/devtools/run_n12_frontier.py', '''                    elif (work["kind"] == "resume-generation"
                          or (config["generation_trials"] > 1 and config["workers"] > 1)):''', '''                    elif generation_parallelism(state, work):''')
change('packing/devtools/run_n12_frontier.py', 'def choose_work(state: dict[str, Any]) -> dict[str, Any]:', '''def generation_parallelism(state: dict[str, Any], work: dict[str, Any]) -> bool:
    if state.get("active_generation"):
        return True
    if work["kind"] != "search" or state.get("active") is not None:
        return False
    if state["config"].get("generation_trials", 3) <= 1 or state["config"]["workers"] <= 1:
        return False
    from devtools.frontier_generation_campaign import select_plans
    return len(select_plans(state, work)) > 1


def choose_work(state: dict[str, Any]) -> dict[str, Any]:''')
change('packing/tests/test_frontier_hardening.py', '''["--root", str(tmp_path), "--strategies", "baseline,centre", "--max-cycles", "4"]''', '''["--root", str(tmp_path), "--strategies", "baseline,centre", "--generation-trials", "1", "--max-cycles", "4"]''')
print('Fair shared dispatch and explicit sequential-policy control applied.')
