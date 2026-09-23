"""Compare temporary n=12 CPU benchmark outputs with the saved serial trajectory."""

import argparse
import glob
import json
import math
import statistics
from pathlib import Path

SERIAL = Path('/tmp/squares-n12-controlled-2.stdout')
REFERENCE_WALL = 71.190
REFERENCE_SEPARATION = 59.407
REFERENCE_LP = 11.780
EXPECTED_OBJECTIVE = 12.217676366606284
EXPECTED_STOP = 'converged: every placement covers mass 1'
DECISION_FIELDS = ('index', 'rows_held', 'rows_added', 'violated', 'support', 'objective')


def read_run(path):
    source = Path(path).read_text()
    report = json.loads(source[source.index('{'):])
    return report['row_run'], report


def differences(run, reference, report, least_reference):
    errors = []
    for key, expected in [('rounds', 23), ('rows', 5481), ('stopped', EXPECTED_STOP)]:
        if run.get(key) != expected:
            errors.append(f'{key}: {run.get(key)!r} != {expected!r}')
    if not math.isclose(run.get('objective', float('nan')), EXPECTED_OBJECTIVE,
                        rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"objective: {run.get('objective')!r} != {EXPECTED_OBJECTIVE!r}")
    actual_rounds = run.get('timings', [])
    expected_rounds = reference['timings']
    if len(actual_rounds) != len(expected_rounds):
        errors.append(f'timings length: {len(actual_rounds)} != {len(expected_rounds)}')
    for i, (actual, expected) in enumerate(zip(actual_rounds, expected_rounds)):
        for key in DECISION_FIELDS:
            a, b = actual.get(key), expected.get(key)
            if a != b:
                errors.append(f'round {i} {key}: {a!r} != {b!r}')
    if least_reference is not None:
        actual = report.get('least_covered')
        if actual is None:
            errors.append('least_covered: unavailable in run output')
        elif not math.isclose(actual, least_reference, rel_tol=1e-12, abs_tol=1e-12):
            errors.append(f'least_covered: {actual!r} != {least_reference!r}')
    return errors


def slices(run):
    rounds = run['timings']
    def collect(items):
        separation = sum(item['separation_s'] for item in items)
        lp = sum(item['lp_s'] for item in items)
        return {'separation_s': round(separation, 3), 'lp_s': round(lp, 3),
                'share': round(separation / (separation + lp), 4) if separation + lp else None}
    return {'round_0': collect(rounds[:1]), 'rounds_1_final': collect(rounds[1:]),
            'last_5_completed': collect(rounds[-5:]),
            'last_5_with_lp': collect([item for item in rounds if item['lp_s'] > 0][-5:])}


def stats(values):
    return {'min': min(values), 'median': statistics.median(values), 'max': max(values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', default=str(SERIAL))
    parser.add_argument('--least-reference', metavar='THREAD_1_STDOUT',
                        help='Output exposing top-level least_covered, such as thread:1')
    parser.add_argument('--variant', action='append', metavar='MODEL:WORKERS:GLOB',
                        help='Repeat for each group; paths can be shell-style globs')
    args = parser.parse_args()
    reference, _ = read_run(args.reference)
    least_reference = None
    if args.least_reference:
        _, least_report = read_run(args.least_reference)
        least_reference = least_report.get('least_covered')
        if least_reference is None:
            raise SystemExit(f'No top-level least_covered in {args.least_reference}')
    all_results = {}
    for spec in args.variant or []:
        model, count, pattern = spec.split(':', 2)
        workers = int(count)
        paths = sorted(glob.glob(pattern))
        if not paths:
            raise SystemExit(f'No files match {pattern}')
        runs = []
        for path in paths:
            run, report = read_run(path)
            errors = differences(run, reference, report, least_reference)
            entry = {'path': path, 'equivalent': not errors, 'differences': errors,
                     'wall_s': run['seconds'],
                     'separation_s': run['separation_seconds'],
                     'lp_s': run['lp_seconds'],
                     'separation_share': run['separation_share'],
                     'rounds': run['rounds'], 'rows': run['rows'],
                     'objective': run['objective'], 'stopped': run['stopped'],
                     'least_covered': report.get('least_covered'),
                     'peak_support': run.get('peak_support'),
                     'pricing_s': report.get('pricing', {}).get('total_s'),
                     'slices': slices(run)}
            runs.append(entry)
        group = {'model': model, 'workers': workers, 'runs': runs,
                 'all_equivalent': all(run['equivalent'] for run in runs)}
        if group['all_equivalent']:
            wall = statistics.median(run['wall_s'] for run in runs)
            separation = statistics.median(run['separation_s'] for run in runs)
            lp = statistics.median(run['lp_s'] for run in runs)
            total_speedup = REFERENCE_WALL / wall
            separation_speedup = REFERENCE_SEPARATION / separation
            ideal = REFERENCE_WALL / (REFERENCE_WALL - REFERENCE_SEPARATION
                                      + REFERENCE_SEPARATION / workers)
            group.update({'wall_s': stats([run['wall_s'] for run in runs]),
                          'separation_s': stats([run['separation_s'] for run in runs]),
                          'lp_s': stats([run['lp_s'] for run in runs]),
                          'total_speedup': total_speedup,
                          'separation_speedup': separation_speedup,
                          'total_efficiency': total_speedup / workers,
                          'separation_efficiency': separation_speedup / workers,
                          'ideal_amdahl_speedup': ideal,
                          'fraction_of_ideal_speedup': total_speedup / ideal,
                          'fraction_of_ideal_gain': ((total_speedup - 1) / (ideal - 1)
                              if workers > 1 else None)})
        all_results[f'{model}:{workers}'] = group
    print(json.dumps(all_results, indent=2))


if __name__ == '__main__':
    main()
