#!/usr/bin/env python3
"""Independent stdlib-only reference for the wreath-product class counter.

This script differentially validates the class-aggregated Burnside counter in
src/wreath.cpp for n <= 3. It shares no code with the C++ implementation and
deliberately never uses the C++ class-size formula, canonical class
representatives, or the aggregation by D4 class multiplicities:

  * every group element of G_n = (D4 wr S_n) x D4_container is enumerated
    directly (|G_n| = n! * 8^n * 8, at most 24,576 elements for n = 3);
  * each element's wreath-product conjugacy type is computed by folding its
    local D4 labels along its square-permutation cycles;
  * class sizes are obtained by counting elements per type, not by formula;
  * the Pólya binomials are evaluated once per type at an arbitrary element of
    that type (and, for n <= 2 by default, the induced event cycle type is
    verified to be constant across every element of the type);
  * the Burnside numerator is summed over types and divided by |G_n|;
  * the S_n x D4_container and D4^n sub-group stages are recomputed by
    enumerating those subgroups element by element.

The event geometry and the element action on events are imported from the
already validated orbit_reference.py, itself an independent re-implementation
of the C++ action (not of the class aggregation under test here).

Usage:
    tools/wreath_reference.py --self-check
    tools/wreath_reference.py --check-tool build/sqtopology_orbit [--max-n 3]
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orbit_reference as orbit_ref  # noqa: E402  (path bootstrap above)

D4_CLASS_NAMES = [
    "identity",
    "rotation180",
    "rotation90",
    "reflection_corner_axis",
    "reflection_side_axis",
]


def d4_class(element):
    """Conjugacy class id of a D4 element, in the C++ D4Class order."""
    rotation, reflected = element
    if not reflected:
        if rotation == 0:
            return 0
        return 1 if rotation == 2 else 2
    return 3 if rotation % 2 == 0 else 4


def wreath_type_of_element(n: int, element):
    """(container class, counts[l][c]) of one element, by folding labels.

    counts is a tuple of tuples: for every square-cycle length l in 1..n and
    every D4 class c, the number of l-cycles whose cycle product (fold of the
    local labels in cycle order, using the compose convention of
    orbit_reference) lies in class c. This is an independent computation of
    the standard wreath-product conjugacy invariant; it never calls the C++
    classifier and never uses a formula.
    """
    square_map, local, container = element
    counts = [[0] * 5 for _ in range(n + 1)]
    seen = [False] * n
    for start in range(n):
        if seen[start]:
            continue
        cycle = []
        current = start
        while not seen[current]:
            seen[current] = True
            cycle.append(current)
            current = square_map[current]
        product = (0, False)
        for square in cycle:
            product = orbit_ref.compose_d4(local[square], product)
        counts[len(cycle)][d4_class(product)] += 1
    frozen = tuple(tuple(row) for row in counts)
    return (d4_class(container), frozen)


def enumerate_types(n: int):
    """All elements of G_n grouped by wreath type: {type: [elements...]}."""
    buckets = defaultdict(list)
    for element in orbit_ref.group_elements(n):
        buckets[wreath_type_of_element(n, element)].append(element)
    return buckets


def event_cycle_type(n: int, element):
    """Sorted tuple of cycle lengths of the induced action on the events."""
    return orbit_ref.cycle_lengths(orbit_ref.Layout(n).event_permutation(element))


def polynom_coefficients(lengths, max_degree):
    """[x^d] prod (1 + x^length) for d = 0..max_degree."""
    polynomial = [0] * (max_degree + 1)
    polynomial[0] = 1
    for length in lengths:
        if length > max_degree:
            continue
        for degree in range(max_degree, length - 1, -1):
            polynomial[degree] += polynomial[degree - length]
    return polynomial


def burnside_from_classes(n: int, weight_max: int | None = None, verbose=False):
    """Exact coefficients from per-type enumeration (no class-size formula)."""
    layout = orbit_ref.Layout(n)
    if weight_max is None:
        weight_max = layout.event_count
    order = orbit_ref.group_size(n)

    buckets = enumerate_types(n)
    numerators = [0] * (weight_max + 1)
    induced_by_type = {}
    for type_key, elements in buckets.items():
        representative = elements[0]
        lengths = event_cycle_type(n, representative)
        induced_by_type[type_key] = lengths
        # Constancy of the induced cycle type on the type (checked exhaustively
        # only in the deep-constancy mode of check_tool; here one arbitrary
        # element of the bucket is used).
        polynomial = polynom_coefficients(lengths, weight_max)
        size = len(elements)
        for degree in range(weight_max + 1):
            numerators[degree] += size * polynomial[degree]

    coefficients = []
    for value in numerators:
        assert value % order == 0, "Burnside numerator is not divisible by |G|"
        coefficients.append(value // order)
    if weight_max == layout.event_count:
        assert coefficients[0] == 1
        assert coefficients[-1] == 1
        assert coefficients == coefficients[::-1]
    total = sum(coefficients)
    return {
        "n": n,
        "event_count": layout.event_count,
        "group_size": order,
        "types": len(buckets),
        "class_size_sum": sum(len(elements) for elements in buckets.values()),
        "induced_by_type": induced_by_type,
        "coefficients": coefficients,
        "total": total,
    }


def check_constancy(n: int):
    """Every element of a wreath type induces the same event cycle type."""
    layout = orbit_ref.Layout(n)
    seen = {}
    elements = 0
    for element in orbit_ref.group_elements(n):
        type_key = wreath_type_of_element(n, element)
        lengths = orbit_ref.cycle_lengths(layout.event_permutation(element))
        elements += 1
        if type_key in seen:
            if seen[type_key] != lengths:
                return False, elements
        else:
            seen[type_key] = lengths
    return True, elements


def conjugacy_partition(n: int):
    """Conjugation-orbit labels via generator BFS (independent of types)."""
    elements = list(orbit_ref.group_elements(n))
    index = {element: position for position, element in enumerate(elements)}
    generators = orbit_ref.reference_generators(n)
    inverses = [orbit_ref.invert_element(g, n) for g in generators]
    label = [-1] * len(elements)
    classes = 0
    for start in range(len(elements)):
        if label[start] >= 0:
            continue
        label[start] = classes
        stack = [elements[start]]
        while stack:
            current = stack.pop()
            for generator, inverse in zip(generators, inverses):
                conjugated = orbit_ref.compose_element(
                    orbit_ref.compose_element(generator, current, n), inverse, n
                )
                position = index[conjugated]
                if label[position] < 0:
                    label[position] = classes
                    stack.append(conjugated)
        classes += 1
    return elements, label, classes


def staged_reference(n: int, weight_max: int):
    """D4^n and S_n x D4_container stages by direct element enumeration."""
    layout = orbit_ref.Layout(n)
    identity_square_map = tuple(range(n))
    identity_local = tuple([(0, False)] * n)
    identity_container = (0, False)

    def burnside(elements, order):
        numerators = [0] * (weight_max + 1)
        for element in elements:
            lengths = orbit_ref.cycle_lengths(layout.event_permutation(element))
            polynomial = polynom_coefficients(lengths, weight_max)
            for degree in range(weight_max + 1):
                numerators[degree] += polynomial[degree]
        values = []
        for value in numerators:
            assert value % order == 0
            values.append(value // order)
        return values

    local_elements = [
        (identity_square_map, local, identity_container)
        for local in itertools.product(orbit_ref.D4_ELEMENTS, repeat=n)
    ]
    squares_elements = [
        (square_map, identity_local, container)
        for square_map in itertools.permutations(range(n))
        for container in orbit_ref.D4_ELEMENTS
    ]
    return {
        "local_only": burnside(local_elements, 8**n),
        # S_n x D4_container has order n! * 8; group_size(n) = n! * 8^n * 8.
        "squares_only": burnside(squares_elements, orbit_ref.group_size(n) // 8**n),
    }


def run_tool(tool_path: str, arguments):
    completed = subprocess.run(
        [tool_path, *arguments], check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


def _expand_compact(compact: str):
    lengths = []
    for part in compact.split() if compact else []:
        if "^" in part:
            base, exponent = part.split("^")
            lengths.extend([int(base)] * int(exponent))
        else:
            lengths.append(int(part))
    return tuple(sorted(lengths))


def check_tool(tool_path: str, max_n: int, deep_constancy: bool, bfs: bool) -> int:
    failures = []

    for n in range(1, max_n + 1):
        reference = burnside_from_classes(n)
        order = reference["group_size"]

        payload = run_tool(tool_path, ["wreath", "--n", str(n), "--cycle-types"])
        if payload["schema"] != "sqtopology.wreath-count.v1":
            failures.append(f"n={n}: unexpected schema")
        if payload["event_count"] != reference["event_count"]:
            failures.append(f"n={n}: event_count mismatch")
        if payload["group_size"] != reference["group_size"]:
            failures.append(f"n={n}: group_size mismatch")
        if payload["class_size_sum"] != reference["class_size_sum"]:
            failures.append(f"n={n}: class size sum mismatch")
        if payload["wreath_conjugacy_types"] * 5 != payload["total_conjugacy_classes"]:
            failures.append(f"n={n}: wreath class factor mismatch")
        if payload["total_conjugacy_classes"] != reference["types"]:
            failures.append(
                f"n={n}: class count {payload['total_conjugacy_classes']} != "
                f"{reference['types']} enumerated types"
            )
        if payload["coefficients"] != [str(v) for v in reference["coefficients"]]:
            failures.append(f"n={n}: coefficient mismatch")
        if payload["total_orbit_count"] != str(reference["total"]):
            failures.append(f"n={n}: total mismatch")
        if not all(payload["checks"].values()):
            failures.append(f"n={n}: tool self-check failed: {payload['checks']}")

        # Induced-type aggregation: group sizes summed per induced cycle type.
        expected = defaultdict(lambda: [0, 0])
        for type_key, elements in enumerate_types(n).items():
            lengths = reference["induced_by_type"][type_key]
            expected[lengths][0] += len(elements)
            expected[lengths][1] += 1
        table = {}
        for record in payload["induced_cycle_types"]:
            lengths = _expand_compact(record["cycle_type"])
            table[lengths] = [record["class_elements"], record["classes"]]
        if dict(table) != {key: list(value) for key, value in expected.items()}:
            failures.append(f"n={n}: induced cycle-type table mismatch")
        if payload["distinct_induced_cycle_types"] != len(expected):
            failures.append(f"n={n}: distinct induced type count mismatch")

        # Low-weight mode against the same reference prefix.
        low = run_tool(tool_path, ["wreath", "--n", str(n), "--low-weight", "6"])
        if low["coefficients"] != [str(v) for v in reference["coefficients"][:7]]:
            failures.append(f"n={n}: low-weight coefficient mismatch")

        # Staged sub-groups by direct enumeration (cheap for n <= 3).
        staged = staged_reference(n, 4)
        staged_payload = run_tool(tool_path, ["staged", "--n", str(n), "--weight", "4"])
        for stage, values in staged.items():
            if staged_payload["coefficients"][stage] != [str(v) for v in values]:
                failures.append(f"n={n}: staged {stage} mismatch")

        if deep_constancy or n <= 2:
            constant, elements = check_constancy(n)
            if not constant:
                failures.append(f"n={n}: induced cycle type not constant on a type")
            else:
                print(f"n={n}: induced cycle type constant on all {elements} elements")

        if bfs:
            elements, labels, classes = conjugacy_partition(n)
            if classes != reference["types"]:
                failures.append(
                    f"n={n}: BFS conjugacy classes {classes} != types {reference['types']}"
                )
            else:
                type_by_label = {}
                label_by_type = {}
                consistent = True
                for element, label in zip(elements, labels):
                    type_key = wreath_type_of_element(n, element)
                    if type_by_label.setdefault(label, type_key) != type_key:
                        consistent = False
                    if label_by_type.setdefault(type_key, label) != label:
                        consistent = False
                if not consistent:
                    failures.append(
                        f"n={n}: BFS conjugation partition differs from wreath types"
                    )
                else:
                    print(
                        f"n={n}: BFS conjugacy partition equals the wreath-type "
                        f"partition ({classes} classes)"
                    )

        print(
            f"n={n}: {reference['event_count']} events, |G|={order}, "
            f"{reference['types']} classes, total={reference['total']}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("wreath_reference: all differential checks passed")
    return 0


def self_check() -> int:
    for n in (1, 2):
        result = burnside_from_classes(n)
        print(
            f"n={n}: {result['types']} classes, |G|={result['group_size']}, "
            f"total={result['total']}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--check-tool", metavar="PATH")
    parser.add_argument("--max-n", type=int, default=3)
    parser.add_argument(
        "--deep-constancy",
        action="store_true",
        help="verify induced-type constancy on every element for all n",
    )
    parser.add_argument(
        "--bfs",
        action="store_true",
        help="also verify the partition against generator BFS conjugation",
    )
    arguments = parser.parse_args()
    if arguments.check_tool:
        return check_tool(
            arguments.check_tool, arguments.max_n, arguments.deep_constancy, arguments.bfs
        )
    if arguments.self_check:
        return self_check()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
