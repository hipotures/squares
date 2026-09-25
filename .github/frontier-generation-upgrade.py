"""One-shot source integration; removed after the resulting source is tested."""
from pathlib import Path


def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f"expected one replacement ({text.count(old)}): {old[:180]!r}")
    return text.replace(old, new, 1)


def edit(path, function):
    p = Path(path)
    p.write_text(function(p.read_text()))


def library(s):
    s = once(s, 'from concurrent.futures import ProcessPoolExecutor',
             'from concurrent.futures import Executor, ProcessPoolExecutor')
    s = once(s, '    pool: ProcessPoolExecutor,', '    pool: Executor,')
    s = once(s, '    _direction_pool: ProcessPoolExecutor | None = None,',
             '    _direction_pool: Executor | None = None,\n    phase_callback: Callable[[str, str], None] | None = None,')
    s = once(s, 'class _PersistentLp:', '''def _phase(callback, name: str, event: str) -> None:
    if callback is not None:
        callback(name, event)


class _PersistentLp:''')
    s = once(s, '        columns = len(costs)', '''        if os.environ.get("PACK_GENERATION_MANAGED") == "1":
            for name, value in (("threads", 1), ("parallel", "off")):
                if self.highs.setOptionValue(name, value) != highspy.HighsStatus.kOk:
                    raise RuntimeError(f"HiGHS refused managed option {name}")
        columns = len(costs)''')
    s = once(s, '        warm = lp_model.solve(rows)', '''        _phase(phase_callback, "lp", "start")
        warm = lp_model.solve(rows)
        _phase(phase_callback, "lp", "end")''')
    s = once(s, '        separation_started = time.perf_counter()', '''        _phase(phase_callback, "separation", "start")
        separation_started = time.perf_counter()''')
    s = once(s, '        separation_seconds = time.perf_counter() - separation_started', '''        separation_seconds = time.perf_counter() - separation_started
        _phase(phase_callback, "separation", "end")''')
    s = once(s, '        solved = lp_model.solve(rows)', '''        _phase(phase_callback, "lp", "start")
        solved = lp_model.solve(rows)
        _phase(phase_callback, "lp", "end")''')
    prefix, rest = s.split('def solve_rows(', 1)
    block, suffix = rest.split('#: One dual row after snapping', 1)
    block = once(block, '    workers: int | None = None,', '''    workers: int | None = None,
    direction_executor: Executor | None = None,
    phase_callback: Callable[[str, str], None] | None = None,''')
    block = once(block, '        "clip": clip,', '        "clip": clip,\n        "phase_callback": phase_callback,')
    block = once(block, '    if count == 1:', '''    if direction_executor is not None:
        return _solve_rows_serial_or_pool(*args, _direction_pool=direction_executor, **options)
    if count == 1:''')
    s = prefix + 'def solve_rows(' + block + '#: One dual row after snapping' + suffix
    prefix, block = s.split('def generate_adaptive(', 1)
    block = once(block, '    capture_solution: Callable[[SiteSet, np.ndarray], None] | None = None,', '''    capture_solution: Callable[[SiteSet, np.ndarray], None] | None = None,
    direction_executor: Executor | None = None,
    phase_callback: Callable[[str, str], None] | None = None,''')
    block = once(block, '    sites = site_set_from_grids(outer_side, grid_counts, inset)', '''    _phase(phase_callback, "site_setup", "start")
    sites = site_set_from_grids(outer_side, grid_counts, inset)''')
    block = once(block, '    rows = Rows()', '''    _phase(phase_callback, "site_setup", "end")
    rows = Rows()''')
    block = once(block, '    try:\n        for index in range(column_rounds):', '''    owned_pool = None
    if direction_executor is None and os.environ.get("PACK_JOBS"):
        count = worker_count(len(half_tangents) + 1)
        if count > 1:
            owned_pool = ProcessPoolExecutor(max_workers=count)
            direction_executor = owned_pool
    try:
        for index in range(column_rounds):''')
    block = once(block, '                clip=clip,\n            )\n            seconds =', '''                clip=clip,
                direction_executor=direction_executor,
                phase_callback=phase_callback,
            )
            seconds =''')
    block = once(block, '                found = rank_candidates(sites, weighted, wanted=columns_per_round)', '''                _phase(phase_callback, "pricing", "start")
                found = rank_candidates(sites, weighted, wanted=columns_per_round)
                _phase(phase_callback, "pricing", "end")''')
    block = once(block, '            log.ceiling = check_ceiling(n, symmetrise(weighted), outer_side, clip=clip)', '''            _phase(phase_callback, "ceiling", "start")
            log.ceiling = check_ceiling(n, symmetrise(weighted), outer_side, clip=clip)
            _phase(phase_callback, "ceiling", "end")''')
    block = once(block, '        atoms = rationalise_sites(sites, solution.weights, scale=scale)', '''        _phase(phase_callback, "rationalisation", "start")
        atoms = rationalise_sites(sites, solution.weights, scale=scale)
        _phase(phase_callback, "rationalisation", "end")''')
    block = once(block, '    finally:\n        if handle is not None:', '''    finally:
        if owned_pool is not None:
            owned_pool.shutdown(wait=True, cancel_futures=True)
        if handle is not None:''')
    return prefix + 'def generate_adaptive(' + block


def generator(s):
    s = once(s, 'from pathlib import Path', '''from pathlib import Path
from concurrent.futures import Executor

from devtools.frontier_phase import PhaseJournal''')
    s = once(s, '    raw_weights: Path | None = None,', '''    raw_weights: Path | None = None,
    direction_executor: Executor | None = None,
    phase_log: Path | None = None,''')
    s = once(s, '    started = time.perf_counter()', '''    started = time.perf_counter()
    phases = PhaseJournal(phase_log)''')
    s = once(s, '        **snapshot_options,', '''        direction_executor=direction_executor,
        phase_callback=phases,
        **snapshot_options,''')
    s = once(s, '    result["work_kind"] = "generation"', '''    result["work_kind"] = "generation"
    result["phase_timings"] = phases.summary()''')
    s = once(s, 'def main(argv: list[str] | None = None) -> int:', '''def main(argv: list[str] | None = None, *, direction_executor: Executor | None = None) -> int:''')
    s = once(s, '    args = parser.parse_args(argv)', '''    parser.add_argument("--phase-log", type=Path, help="Unix-timestamped generation phase events")
    args = parser.parse_args(argv)''')
    s = once(s, '        raw_weights=args.raw_weights,', '''        raw_weights=args.raw_weights,
        direction_executor=direction_executor,
        phase_log=args.phase_log,''')
    return s


def runner(s):
    s = once(s, 'from devtools import frontier_policy, frontier_runtime', '''from devtools import frontier_policy, frontier_runtime
from devtools.frontier_phase import timestamped''')
    s = once(s, '    state.setdefault("search_revision", 0)', '''    state.setdefault("search_revision", 0)
    active_generation = state.setdefault("active_generation", [])
    if (not isinstance(active_generation, list) or len(set(active_generation)) != len(active_generation)
            or any(type(i) is not int or not 0 <= i < len(state["cycles"]) for i in active_generation)):
        raise ValueError("invalid active generation cohort")''')
    s = once(s, 'def emit(root: Path, message: str, *, significant: bool = False) -> None:\n', '''def emit(root: Path, message: str, *, significant: bool = False) -> None:
    message = timestamped(message)
''')
    s = once(s, '    args.extend(["--raw-weights", str(directory / "raw-lp.json")])', '''    args.extend(["--raw-weights", str(directory / "raw-lp.json"),
                 "--phase-log", str(directory / "phase.log")])''')
    s = once(s, 'def run_cycle(root: Path, state: dict[str, Any]) -> None:', '''def run_cycle(root: Path, state: dict[str, Any], *, defer_generation: bool = False) -> dict | None:''')
    s = once(s, '(stage for stage in reversed(cycle["stages"]) if stage["status"] == "running"), None', '''(stage for stage in reversed(cycle["stages"]) if stage["status"] in ("running", "queued")), None''')
    s = once(s, '        if incomplete is not None:\n            old_dir =', '''        if incomplete is not None:
            if incomplete["status"] == "queued" and defer_generation:
                return incomplete
            old_dir =''')
    s = once(s, '            if (old_dir / "stdout.log.job.json").exists():', '''            if incomplete["status"] == "queued" or (old_dir / "stdout.log.job.json").exists():''')
    s = once(s, '                "work_kind": "rerationalisation" if raw_source is not None else "generation",', '''                "work_kind": "rerationalisation" if raw_source is not None else "generation",
                "started_epoch": int(time.time()),''')
    s = once(s, '            env = controlled_env(state)\n            code = run_child(args, stage_dir / "stdout.log", env)', '''            if defer_generation:
                generated["status"] = "queued"
                save_state(root, state)
                return generated
            env = controlled_env(state)
            code = run_child(args, stage_dir / "stdout.log", env)''')
    s = once(s, '        verified_path = None\n        if mass is not None', '''        verified_path = None
        verification_started = time.monotonic()
        if mass is not None''')
    s = once(s, '        generated["verifier"] = verifier', '''        generated["verification_seconds"] = time.monotonic() - verification_started
        generated["verifier"] = verifier''')
    s = once(s, 'f"time={float(result.get(\'seconds\') or 0):.0f}s -> {decision}",', '''f"time={float(result.get('seconds') or 0):.0f}s "
            f"verify_s={generated['verification_seconds']:.3f} "
            f"stage_wall_s={max(0, time.time() - generated.get('started_epoch', time.time())):.3f} -> {decision}",''')
    s = once(s, '    if not completed or completed[-1].get("name") == "screen":', '    if not completed:')
    s = once(s, 'def choose_work(state: dict[str, Any]) -> dict[str, Any]:\n', '''def choose_work(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("active_generation"):
        return {"kind": "resume-generation", "reason": "finish the durable strategy cohort"}
''')
    s = once(s, '"row-rounds", "max-row-rounds", "scale", "max-scale", "max-cycles"):', '''"row-rounds", "max-row-rounds", "scale", "max-scale", "max-cycles", "generation-trials"):''')
    s = once(s, '        print(summary(root, state, started))', '        print(timestamped(summary(root, state, started)))')
    s = once(s, '"strategy_width": "1/100000", "target_width": None, "max_cycles": None,', '''"strategy_width": "1/100000", "target_width": None, "max_cycles": None,
                "generation_trials": 3,''')
    s = once(s, 'for key in ("workers", "row_rounds", "max_row_rounds", "scale", "max_scale"):', '''for key in ("workers", "row_rounds", "max_row_rounds", "scale", "max_scale", "generation_trials"):''')
    s = once(s, '            if (config["workers"] < 1 or config["row_rounds"] < 1', '''            if (not 1 <= config["generation_trials"] <= 6
                    or config["workers"] < 1 or config["row_rounds"] < 1''')
    s = once(s, 'f"strategies={\',\'.join(config[\'strategies\'])}")', '''f"strategies={','.join(config['strategies'])} generation-trials={config['generation_trials']}")''')
    s = once(s, '            while (not stop.requested or state.get("active") is not None', '''            while (not stop.requested or state.get("active") is not None or state.get("active_generation")''')
    s = once(s, '                if stop.requested and state.get("active") is None and not active_repair:', '''                if stop.requested and state.get("active") is None and not state.get("active_generation") and not active_repair:''')
    s = once(s, '                if state.get("active") is None and not active_repair:', '''                if state.get("active") is None and not state.get("active_generation") and not active_repair:''')
    s = once(s, '                    else:\n                        run_cycle(root, state)', '''                    elif (work["kind"] == "resume-generation"
                          or (config["generation_trials"] > 1 and config["workers"] > 1)):
                        from devtools.frontier_generation_campaign import run_portfolio
                        run_portfolio(root, state, sys.modules[__name__])
                    else:
                        run_cycle(root, state)''')
    s = once(s, '                if stop.requested and state.get("active") is None:\n                    break', '''                if stop.requested and state.get("active") is None and not state.get("active_generation"):
                    break''')
    s = once(s, '        print(f"frontier runner stopped safely: {error}", file=sys.stderr)', '''        print(timestamped(f"frontier runner stopped safely: {error}"), file=sys.stderr)''')
    s = once(s, '    minutes = max(1, round(elapsed / 60))', '''    minutes = max(1, round(elapsed / 60))
    if "devtools.frontier_generation_queue" in args:
        try:
            progress = read_json(output.parent / "generation-progress.json")
            return (f"[running] generation-queue elapsed_s={elapsed:.1f} "
                    f"serial={progress['serial_owners']} directions={progress['direction_tasks']} "
                    f"slots={progress['slots']} jobs={progress['completed_jobs']}/{progress['jobs']} "
                    f"coordinator_cpu={progress['coordinator_cpu_seconds']:.3f}s")
        except (OSError, ValueError, KeyError):
            return f"[running] generation-queue starting elapsed_s={elapsed:.1f}"''')
    return s


def runtime(s):
    s = once(s, '("--source-result", inputs), ("--input", inputs),', '''("--source-result", inputs), ("--input", inputs), ("--manifest", inputs),''')
    s = once(s, '("--report", outputs), ("--log", outputs), ("--row-log", outputs),', '''("--report", outputs), ("--log", outputs), ("--row-log", outputs), ("--phase-log", outputs),''')
    s = once(s, '        kind = "search" if "devtools.run_fractional_colgen" in args else "verification"', '''        kind = "search" if any(module in args for module in (
            "devtools.run_fractional_colgen", "devtools.frontier_generation_queue"
        )) else "verification"''')
    return s


edit('packing/src/sqpack/fractional/colgen.py', library)
edit('packing/devtools/run_fractional_colgen.py', generator)
edit('packing/devtools/run_n12_frontier.py', runner)
edit('packing/devtools/frontier_runtime.py', runtime)
edit('packing/devtools/frontier_generation_campaign.py', lambda s: s.replace('import json\n', '').replace('frontier_policy, frontier_runtime', 'frontier_policy').replace('def run_portfolio(root: Path, state: dict[str, Any]) -> None:\n    from devtools import run_n12_frontier as frontier', 'def run_portfolio(root: Path, state: dict[str, Any], frontier=None) -> None:\n    if frontier is None:\n        from devtools import run_n12_frontier as frontier'))
edit('packing/devtools/frontier_generation_queue.py', lambda s: s.replace('import hashlib\n', '').replace('import json\n', '').replace('slots=args.workers,', 'slots=min(args.workers, int(os.environ.get("PACK_JOBS", args.workers))),'))
print('Generation integration applied; no proof conditions were modified.')
