#!/usr/bin/env python3
"""Independent stdlib-only reference for the sqtopology orbit counter.

This script re-implements the explicit event set Omega_n, the group action of
G_n = (D4^n semidirect S_n) x D4_container, the induced event cycle types, and
exact Burnside/Pólya orbit counting. It exists only to differentially validate
the C++ oracle in src/orbit.cpp; the two implementations were written from the
same specification but share no code.

Usage:
    tools/orbit_reference.py --self-check
    tools/orbit_reference.py --check-tool build/sqtopology_orbit [--max-n 2]

The default check compares n = 1 and n = 2 against the tool and additionally
compares conjugacy-class counts for n = 1..3 computed with a different
generating set. Small-depth orbit counts are brute-forced directly from the
action as a third, Burnside-free path.
"""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from collections import Counter

D4_ELEMENTS = [
    (rotation, reflected)
    for reflected in (False, True)
    for rotation in range(4)
]

# (rotation, reflected) acts as x -> (+-)x + offset, with the engine's offsets:
#   ring (mod 8): offset = 2 * rotation, wall (mod 4): offset = rotation.


def transform_ring(ring: int, element):
    rotation, reflected = element
    if reflected:
        ring = (8 - ring) % 8
    return (ring + 2 * rotation) % 8


def transform_wall(wall: int, element):
    rotation, reflected = element
    if reflected:
        wall = (4 - wall) % 4
    return (wall + rotation) % 4


def compose_d4(outer, inner):
    outer_rotation, outer_reflected = outer
    inner_rotation, inner_reflected = inner
    rotation = (
        outer_rotation + ((4 - inner_rotation) % 4 if outer_reflected else inner_rotation)
    ) % 4
    return (rotation, outer_reflected != inner_reflected)


def invert_d4(element):
    rotation, reflected = element
    inner = (4 - rotation) % 4 if reflected else rotation
    return ((4 - inner) % 4, reflected)


class Layout:
    def __init__(self, n: int):
        self.n = n
        self.pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        self.pair_index = {pair: index for index, pair in enumerate(self.pairs)}
        self.square_square_count = 64 * len(self.pairs)
        self.event_count = self.square_square_count + 32 * n

    def square_square_event(self, first, second, first_ring, second_ring):
        return 64 * self.pair_index[(first, second)] + 8 * first_ring + second_ring

    def wall_event(self, square, ring, wall):
        return self.square_square_count + 32 * square + 4 * ring + wall

    def event_permutation(self, element):
        square_map, local, container = element
        permutation = [0] * self.event_count
        for (first, second) in self.pairs:
            target_first = square_map[first]
            target_second = square_map[second]
            if target_first < target_second:
                pair = self.pair_index[(target_first, target_second)]
                swap = False
            else:
                pair = self.pair_index[(target_second, target_first)]
                swap = True
            for first_ring in range(8):
                first_target = transform_ring(first_ring, local[first])
                base = 64 * pair
                for second_ring in range(8):
                    second_target = transform_ring(second_ring, local[second])
                    if swap:
                        index = base + 8 * second_target + first_target
                    else:
                        index = base + 8 * first_target + second_target
                    permutation[self.square_square_event(first, second, first_ring, second_ring)] = index
        for square in range(self.n):
            for ring in range(8):
                target_ring = transform_ring(ring, local[square])
                for wall in range(4):
                    target_wall = transform_wall(wall, container)
                    permutation[self.wall_event(square, ring, wall)] = self.wall_event(
                        square_map[square], target_ring, target_wall
                    )
        return permutation


def group_elements(n: int):
    for square_map in itertools.permutations(range(n)):
        for local in itertools.product(D4_ELEMENTS, repeat=n):
            for container in D4_ELEMENTS:
                yield (square_map, tuple(local), container)


def group_size(n: int) -> int:
    size = 8
    for step in range(n):
        size *= 8
    for value in range(2, n + 1):
        size *= value
    return size


def cycle_lengths(permutation):
    seen = [False] * len(permutation)
    lengths = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        length = 0
        current = start
        while not seen[current]:
            seen[current] = True
            current = permutation[current]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths))


def burnside(n: int):
    layout = Layout(n)
    numerator = [0] * (layout.event_count + 1)
    cycle_type_counts = Counter()
    total_from_cycles = 0
    for element in group_elements(n):
        lengths = cycle_lengths(layout.event_permutation(element))
        cycle_type_counts[lengths] += 1
        polynomial = [0] * (layout.event_count + 1)
        polynomial[0] = 1
        degree = 0
        for length in lengths:
            degree += length
            for index in range(degree, length - 1, -1):
                polynomial[index] += polynomial[index - length]
        for index in range(degree + 1):
            numerator[index] += polynomial[index]
        total_from_cycles += 1 << len(lengths)
    assert degree == layout.event_count
    order = group_size(n)
    coefficients = []
    for value in numerator:
        assert value % order == 0, "Burnside numerator is not divisible by |G|"
        coefficients.append(value // order)
    assert total_from_cycles % order == 0
    total = total_from_cycles // order
    assert sum(coefficients) == total
    assert coefficients[0] == coefficients[-1] == 1
    assert coefficients == coefficients[::-1]
    return {
        "n": n,
        "event_count": layout.event_count,
        "group_size": order,
        "coefficients": coefficients,
        "total": total,
        "cycle_type_counts": cycle_type_counts,
    }


def brute_force_layer_counts(n: int, max_weight: int):
    """Orbit counts of d-event subsets from the action alone (no Burnside)."""
    layout = Layout(n)
    permutations = [
        layout.event_permutation(element) for element in group_elements(n)
    ]

    counts = [0] * (max_weight + 1)
    for weight in range(max_weight + 1):
        representatives = set()
        for subset in itertools.combinations(range(layout.event_count), weight):
            mask = 0
            for event in subset:
                mask |= 1 << event
            best = mask
            for permutation in permutations:
                image = 0
                for event in subset:
                    image |= 1 << permutation[event]
                if image < best:
                    best = image
            representatives.add(best)
        counts[weight] = len(representatives)
    return counts


def conjugacy_class_count(n: int, generators=None):
    """Conjugation-orbit BFS with a deliberately different generating set."""
    elements = list(group_elements(n))
    index = {element: position for position, element in enumerate(elements)}
    if generators is None:
        generators = reference_generators(n)
    assert subgroup_size(n, generators) == len(elements), "generators do not generate G_n"
    inverses = [invert_element(generator, n) for generator in generators]
    seen = [False] * len(elements)
    classes = 0
    for start, element in enumerate(elements):
        if seen[start]:
            continue
        classes += 1
        stack = [element]
        seen[start] = True
        while stack:
            current = stack.pop()
            for generator, inverse in zip(generators, inverses):
                conjugated = compose_element(
                    compose_element(generator, current, n), inverse, n
                )
                position = index[conjugated]
                if not seen[position]:
                    seen[position] = True
                    stack.append(conjugated)
    return classes


def reference_generators(n: int):
    identity = (tuple(range(n)), tuple([(0, False)] * n), (0, False))
    generators = []
    for position in range(max(n - 1, 0)):
        square_map = list(range(n))
        square_map[position], square_map[position + 1] = (
            square_map[position + 1],
            square_map[position],
        )
        generators.append((tuple(square_map), identity[1], identity[2]))
    if n >= 2:
        square_map = tuple(list(range(1, n)) + [0])
        generators.append((square_map, identity[1], identity[2]))
    for square in range(n):
        for element in ((1, False), (0, True)):
            local = list(identity[1])
            local[square] = element
            generators.append((identity[0], tuple(local), identity[2]))
    generators.append((identity[0], identity[1], (1, False)))
    generators.append((identity[0], identity[1], (0, True)))
    return generators


def compose_element(outer, inner, n: int):
    square_map = tuple(outer[0][inner[0][square]] for square in range(n))
    local = tuple(
        compose_d4(outer[1][inner[0][square]], inner[1][square]) for square in range(n)
    )
    return (square_map, local, compose_d4(outer[2], inner[2]))


def invert_element(element, n: int):
    square_map = [0] * n
    local = [None] * n
    for square in range(n):
        square_map[element[0][square]] = square
        local[element[0][square]] = invert_d4(element[1][square])
    return (tuple(square_map), tuple(local), invert_d4(element[2]))


def subgroup_size(n: int, generators):
    identity = (tuple(range(n)), tuple([(0, False)] * n), (0, False))
    seen = {identity}
    stack = [identity]
    while stack:
        current = stack.pop()
        for generator in generators:
            candidate = compose_element(generator, current, n)
            if candidate not in seen:
                seen.add(candidate)
                stack.append(candidate)
    return len(seen)


def run_tool(tool_path: str, arguments):
    completed = subprocess.run(
        [tool_path, *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def check_tool(tool_path: str, max_n: int, deep_brute: bool) -> int:
    failures = []
    burnside_results = {}
    for n in range(1, max_n + 1):
        reference = burnside(n)
        burnside_results[n] = reference
        payload = run_tool(tool_path, ["count", "--n", str(n)])
        if payload["event_count"] != reference["event_count"]:
            failures.append(f"n={n}: event_count mismatch")
        if payload["group_size"] != reference["group_size"]:
            failures.append(f"n={n}: group_size mismatch")
        if payload["coefficients"] != [str(value) for value in reference["coefficients"]]:
            failures.append(f"n={n}: coefficient mismatch")
        if str(reference["total"]) != payload["total_orbit_count"]:
            failures.append(f"n={n}: total mismatch")
        tool_cycle_types = Counter(
            {
                _expand_compact(record["cycle_type"]): record["group_elements"]
                for record in payload["cycle_types"]
            }
        )
        if tool_cycle_types != reference["cycle_type_counts"]:
            failures.append(f"n={n}: cycle-type multiplicity mismatch")
        if not all(payload["checks"].values()):
            failures.append(f"n={n}: tool self-check failed: {payload['checks']}")
        print(f"n={n}: {reference['event_count']} events, |G|={reference['group_size']}, "
              f"{len(reference['cycle_type_counts'])} cycle types, total={reference['total']}")

    for n in range(1, max_n + 1):
        expected = conjugacy_class_count(n)
        payload = run_tool(tool_path, ["count", "--n", str(n)])
        if payload["conjugacy_classes"] != expected:
            failures.append(
                f"n={n}: conjugacy classes {payload['conjugacy_classes']} != {expected}"
            )
        else:
            print(f"n={n}: conjugacy classes {expected} (independent generator set)")

    # Burnside-free small-depth orbit counts.
    layer_one = brute_force_layer_counts(1, 3)
    reference_one = burnside_results[1]["coefficients"]
    if layer_one != reference_one[:4]:
        failures.append(f"n=1: brute-force layers {layer_one} != {reference_one[:4]}")
    else:
        print(f"n=1: brute-force layers 0..3 {layer_one} match")
    if deep_brute:
        layer_two = brute_force_layer_counts(2, 2)
        reference_two = burnside_results.get(2, burnside(2))["coefficients"]
        if layer_two != reference_two[:3]:
            failures.append(f"n=2: brute-force layers {layer_two} != {reference_two[:3]}")
        else:
            print(f"n=2: brute-force layers 0..2 {layer_two} match")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("orbit_reference: all differential checks passed")
    return 0


def _expand_compact(compact: str):
    lengths = []
    for part in compact.split():
        if "^" in part:
            base, exponent = part.split("^")
            lengths.extend([int(base)] * int(exponent))
        else:
            lengths.append(int(part))
    return tuple(sorted(lengths))


def self_check() -> int:
    for n in (1, 2):
        result = burnside(n)
        print(f"n={n}: |Omega|={result['event_count']} |G|={result['group_size']} "
              f"total={result['total']}")
    print("orbit_reference: self-check passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--check-tool", metavar="PATH")
    parser.add_argument("--max-n", type=int, default=2)
    parser.add_argument(
        "--deep-brute",
        action="store_true",
        help="also brute-force the n=2 weight-0..2 orbit layers (slower)",
    )
    arguments = parser.parse_args()
    if arguments.check_tool:
        return check_tool(arguments.check_tool, arguments.max_n, arguments.deep_brute)
    if arguments.self_check:
        return self_check()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
