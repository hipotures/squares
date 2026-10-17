#!/usr/bin/env python3
"""Exact trivial-stabilizer spectra for the event action (research).

For the G_n action on the E(n) = 32 n^2 contact events, this script counts
exactly how many weight-d event subsets have a trivial stabilizer, i.e. how
many configurations have a full-size orbit |G_n|. Two independent methods:

  * subgroup Mobius inversion,  #{S : Stab(S)=1} = sum_K mu(1,K) |X^K|,
    where |X^K| is the number of weight-d unions of K-orbits on events.
    Exact for any weight; applied to n=1 where the full subgroup lattice of
    D4 x D4 is small.
  * fixing-element bitmasks, exact for small weights d <= 4 by intersecting
    the sets of group elements that fix each selected event; applied to n=2.

The two methods are also overlapped on n=1 for d <= 3 as an internal check.
The script also verifies the Mobius formula itself on a small synthetic
C2-action by brute force.

The general bound: a configuration with support s < n squares is fixed by
every local D4 element at an untouched square, so a trivial stabilizer forces
support = n <= 2d. Hence for n > 2d no weight-d configuration has a full
orbit, and the fraction is exactly zero.

Usage:
    tools/wreath_stabilizer_spectrum.py [--n1-max-weight 6] [--n2-max-weight 3] [--n2-lattice]
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
from collections import defaultdict
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orbit_reference as orbit_ref  # noqa: E402


# ---------------------------------------------------------------------------
# Tiny generic group/subgroup machinery (tuples as elements, Python ints)
# ---------------------------------------------------------------------------

def close_subgroup(seed, compose):
    """Closure of the elements in `seed` under the group law."""
    subgroup = set(seed)
    frontier = list(subgroup)
    while frontier:
        current = frontier.pop()
        for generator in list(subgroup):
            product = compose(current, generator)
            if product not in subgroup:
                subgroup.add(product)
                frontier.append(product)
    return frozenset(subgroup)


def subgroup_lattice(elements, compose):
    """All subgroups via one-element-at-a-time closure extension."""
    identity = next(element for element in elements
                    if all(compose(element, other) == other for other in elements))
    trivial = frozenset([identity])
    seen = {trivial}
    frontier = [trivial]
    while frontier:
        current = frontier.pop()
        for element in elements:
            if element in current:
                continue
            extended = close_subgroup(list(current) + [element], compose)
            if extended not in seen:
                seen.add(extended)
                frontier.append(extended)
    return sorted(seen, key=len)


def mobius_by_inclusion(lattice):
    """mu(1, K) on the subgroup lattice, from small subgroups upward."""
    mu = {}
    for subgroup in lattice:  # lattice is sorted by increasing size
        if len(subgroup) == 1:
            mu[subgroup] = 1
            continue
        total = 0
        for other in lattice:
            if len(other) < len(subgroup) and other <= subgroup:
                total += mu[other]
        mu[subgroup] = -total
    return mu


# ---------------------------------------------------------------------------
# Method 1: subgroup Mobius inversion (n = 1)
# ---------------------------------------------------------------------------

def orbits_of_subgroup(n, layout, subgroup, compose):
    """Orbits of a subgroup on the event set (orbit sizes as a list)."""
    # Map each event through every element, then union-find style closure.
    representatives = {}
    parent = list(range(layout.event_count))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for element in subgroup:
        permutation = layout.event_permutation(element)
        for event in range(layout.event_count):
            union(event, permutation[event])
    sizes = defaultdict(int)
    for event in range(layout.event_count):
        sizes[find(event)] += 1
    return sorted(sizes.values())


def mobius_trivial_stabilizer_counts(n, max_weight, element_iter):
    """{d: #{S of weight d with trivial stabilizer}} by Mobius inversion."""
    layout = orbit_ref.Layout(n)

    def compose(left, right):
        return orbit_ref.compose_element(left, right, n)

    elements = list(element_iter)
    lattice = subgroup_lattice(elements, compose)
    mu = mobius_by_inclusion(lattice)
    identity = (tuple(range(n)), tuple([(0, False)] * n), (0, False))
    assert mu[frozenset([identity])] == 1
    counts = [0] * (max_weight + 1)
    for subgroup in lattice:
        if mu[subgroup] == 0:
            continue
        sizes = orbits_of_subgroup(n, layout, subgroup, compose)
        polynomial = [0] * (max_weight + 1)
        polynomial[0] = 1
        for size in sizes:
            if size > max_weight:
                continue
            for degree in range(max_weight, size - 1, -1):
                polynomial[degree] += polynomial[degree - size]
        for degree in range(max_weight + 1):
            counts[degree] += mu[subgroup] * polynomial[degree]
    assert all(value >= 0 for value in counts), counts
    return counts, len(lattice)


# ---------------------------------------------------------------------------
# Method 2: setwise stabilizer via map masks and subset permutations
#
# For every ordered pair (a, b) of events, masks[(a, b)] has bit g set iff
# g maps event a to event b. A weight-w subset S is fixed (setwise) by g iff
# g permutes S, i.e. iff for some permutation pi of S, g maps each event of S
# to its pi-image; the corresponding mask is the intersection of the pair
# masks. The subset has a trivial stabilizer iff every such intersection,
# with the identity element removed, is zero.
# ---------------------------------------------------------------------------

def map_masks(n):
    """masks[(a, b)] bit g set iff element g maps event a to event b."""
    layout = orbit_ref.Layout(n)
    elements = list(orbit_ref.group_elements(n))
    masks = defaultdict(int)
    for index, element in enumerate(elements):
        permutation = layout.event_permutation(element)
        for event in range(layout.event_count):
            masks[(event, permutation[event])] |= 1 << index
    identity_index = next(
        index for index, element in enumerate(elements)
        if element == (tuple(range(n)), tuple([(0, False)] * n), (0, False))
    )
    keep = ((1 << len(elements)) - 1) ^ (1 << identity_index)
    return {key: value & keep for key, value in masks.items()}, layout


def setwise_trivial_stabilizer_counts(n, max_weight):
    masks, layout = map_masks(n)
    counts = [0] * (max_weight + 1)
    for weight in range(max_weight + 1):
        if weight == 0:
            continue  # the empty configuration is fixed by the whole group
        total = 0
        for subset in itertools.combinations(range(layout.event_count), weight):
            has_nontrivial = False
            for image_order in itertools.permutations(subset):
                intersection = None
                for source, target in zip(subset, image_order):
                    pair_mask = masks.get((source, target), 0)
                    intersection = pair_mask if intersection is None \
                        else intersection & pair_mask
                    if intersection == 0:
                        break
                if intersection:
                    has_nontrivial = True
                    break
            if not has_nontrivial:
                total += 1
        counts[weight] = total
    return counts


# ---------------------------------------------------------------------------
# Mobiüs self-check on a synthetic action
# ---------------------------------------------------------------------------

def mobius_self_check():
    """Validate the Mobius pipeline against brute force on C2 x C2."""
    # Group C2 x C2 acting on a 4-point set by bitwise xor.
    diagonals = [(0, 0), (1, 0), (0, 1), (1, 1)]

    def compose(left, right):
        return (left[0] ^ right[0], left[1] ^ right[1])

    def action(element, point):
        return point ^ (element[0] | (element[1] << 1))

    lattice = subgroup_lattice(diagonals, compose)
    mu = mobius_by_inclusion(lattice)
    assert len(lattice) == 5, len(lattice)  # trivial, 3 order-2, full
    for weight in range(5):
        brute = 0
        for subset in itertools.combinations(range(4), weight):
            stabilizer = [g for g in diagonals if all(action(g, p) in subset for p in subset)]
            if stabilizer == [(0, 0)]:
                brute += 1
        mobius = 0
        for subgroup in lattice:
            if mu[subgroup] == 0:
                continue
            # orbits of subgroup on points
            orbits = []
            remaining = set(range(4))
            while remaining:
                point = min(remaining)
                orbit = {action(g, point) for g in subgroup}
                orbits.append(len(orbit))
                remaining -= orbit
            polynomial = [0] * (weight + 1)
            polynomial[0] = 1
            for size in orbits:
                if size <= weight:
                    for degree in range(weight, size - 1, -1):
                        polynomial[degree] += polynomial[degree - size]
            mobius += mu[subgroup] * polynomial[weight]
        assert mobius == brute, (weight, mobius, brute)
    print("mobius self-check: C2 x C2 action verified for all weights")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n1-max-weight", type=int, default=6)
    parser.add_argument("--n1-full", action="store_true",
                        help="Mobius counts for every weight 0..32 at n=1")
    parser.add_argument("--n2-max-weight", type=int, default=3)
    parser.add_argument("--skip-checks", action="store_true")
    arguments = parser.parse_args()

    if not arguments.skip_checks:
        mobius_self_check()

    n = 1
    max_weight = orbit_ref.Layout(n).event_count if arguments.n1_full else arguments.n1_max_weight
    print(f"n=1: subgroup Mobius, weights 0..{max_weight}")
    mobius_counts, lattice_size = mobius_trivial_stabilizer_counts(
        n, max_weight, orbit_ref.group_elements(n)
    )
    print(f"n=1: subgroup lattice size {lattice_size}")
    print(f"{'d':>3} {'trivial-stab':>14} {'C(32,d)':>14} {'fraction':>12}")
    for degree in range(max_weight + 1):
        total = comb(32, degree)
        print(f"{degree:>3} {mobius_counts[degree]:>14} {total:>14} "
              f"{mobius_counts[degree] / total:>12.6f}")

    # Internal cross-check: bitmask method for the same small weights.
    check_weight = min(3, max_weight)
    bitmask_counts = setwise_trivial_stabilizer_counts(n, check_weight)
    for degree in range(check_weight + 1):
        assert bitmask_counts[degree] == mobius_counts[degree], (
            degree, bitmask_counts[degree], mobius_counts[degree]
        )
    print(f"n=1: setwise map-mask method agrees for weights 0..{check_weight}")

    # n = 2 by bitmask intersection.
    n = 2
    max_weight = arguments.n2_max_weight
    print(f"n=2: setwise map-mask enumeration, weights 0..{max_weight}")
    counts = setwise_trivial_stabilizer_counts(n, max_weight)
    print(f"{'d':>3} {'trivial-stab':>14} {'C(128,d)':>18} {'fraction':>12}")
    for degree in range(max_weight + 1):
        total = comb(128, degree)
        print(f"{degree:>3} {counts[degree]:>14} {total:>18} "
              f"{counts[degree] / total:>12.6f}")

    # The support bound: nontrivial stabilizer whenever 2d < n.
    for (nn, dd) in ((2, 0), (3, 1), (5, 2)):
        assert 2 * dd < nn
        print(f"n={nn}, d={dd}: 2d < n, trivial-stabilizer count is exactly 0 "
              f"(any d events touch at most {2 * dd} squares)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
