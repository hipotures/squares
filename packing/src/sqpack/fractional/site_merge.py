"""Merge near-coincident covering-certificate sites without changing the theorem.

The interval route stalls when two region edges coincide to the resolution
floor. Near-coincident atoms are one inferred cause (G5): they cut almost the
same seams. Merging atoms within a Chebyshev radius, summing their weights
onto one D4 orbit, is a change of the candidate, not of the verifier. A radius
of zero is a no-op, so freeze bytes do not move unless a caller asked.

The merge is D4-equivariant on the container: if A is merged with B, every
image of A is merged with the corresponding image of B. Each connected
component collapses to the D4 orbit of its lexicographically first site and
carries the component's total weight equally. A source that was D4-symmetric
stays so; a source that was not is refused rather than silently repaired.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from sqpack.fractional.certificate import Certificate, closed_form_conditions, d4_images
from sqpack.fractional.model import Atom


@dataclass(frozen=True, slots=True)
class MergeReceipt:
    """What one merge did, so a driver can record the change without re-counting."""

    atoms_before: int
    atoms_after: int
    components: int
    collapsed: int
    radius: Fraction


def site_weights(certificate: Certificate) -> dict[tuple[Fraction, Fraction], Fraction]:
    """Weight at each site; duplicate sites sum."""

    weights: dict[tuple[Fraction, Fraction], Fraction] = {}
    for atom in certificate.atoms:
        key = (atom.x, atom.y)
        weights[key] = weights.get(key, Fraction(0)) + atom.weight
    return weights


def merge_near_atoms(
    certificate: Certificate, *, radius: Fraction
) -> tuple[Certificate, MergeReceipt]:
    """Collapse atoms within Chebyshev ``radius``, preserving total mass and D4.

    ``radius == 0`` returns the same certificate object. A negative radius is
    refused. If the source satisfied Condition 1 and the merge would not, that
    is a bug in the merge and is refused rather than written.
    """

    if radius < 0:
        raise ValueError(f"merge radius must be non-negative, not {radius}")
    empty = MergeReceipt(
        len(certificate.atoms), len(certificate.atoms), 0, 0, radius
    )
    if radius == 0 or not certificate.atoms:
        return certificate, empty

    atoms = certificate.atoms
    side = certificate.outer_side
    parent = list(range(len(atoms)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    # A D4-symmetric orbit has to be one component before collapse. Emitting a
    # full orbit from each singleton re-writes the same eight sites eight times
    # and breaks Condition 1 on a source that already held it.
    index_of: dict[tuple[Fraction, Fraction], list[int]] = defaultdict(list)
    for index, atom in enumerate(atoms):
        index_of[(atom.x, atom.y)].append(index)
    for index, atom in enumerate(atoms):
        for image in d4_images(atom.x, atom.y, side):
            for found in index_of.get(image, ()):
                union(index, found)

    for i, first in enumerate(atoms):
        for j in range(i + 1, len(atoms)):
            second = atoms[j]
            if abs(first.x - second.x) <= radius and abs(first.y - second.y) <= radius:
                union(i, j)
                first_images = d4_images(first.x, first.y, side)
                second_images = d4_images(second.x, second.y, side)
                for image_i, image_j in zip(first_images, second_images, strict=True):
                    for left in index_of.get(image_i, ()):
                        for right in index_of.get(image_j, ()):
                            union(left, right)

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(atoms)):
        groups[find(index)].append(index)

    merged: list[Atom] = []
    collapsed = 0
    for members in groups.values():
        sites = [(atoms[index].x, atoms[index].y) for index in members]
        representative = min(sites)
        orbit = tuple(dict.fromkeys(d4_images(*representative, side)))
        if len(members) > len(orbit):
            collapsed += 1
        total = sum((atoms[index].weight for index in members), start=Fraction(0))
        share = total / len(orbit)
        merged.extend(
            Atom(f"{len(merged) + offset:04d}", x, y, share)
            for offset, (x, y) in enumerate(orbit)
        )

    result = Certificate(
        n=certificate.n,
        outer_side=certificate.outer_side,
        square_side=certificate.square_side,
        atoms=tuple(merged),
        half_tangents=certificate.half_tangents,
        symmetry=certificate.symmetry,
    )
    receipt = MergeReceipt(
        len(certificate.atoms),
        len(result.atoms),
        len(groups),
        collapsed,
        radius,
    )
    if site_weights(result) == site_weights(certificate) and len(result.atoms) == len(
        certificate.atoms
    ):
        return certificate, MergeReceipt(
            len(certificate.atoms), len(certificate.atoms), len(groups), 0, radius
        )

    source_symmetric = closed_form_conditions(certificate)[0].holds
    result_symmetric = closed_form_conditions(result)[0].holds
    if source_symmetric and not result_symmetric:
        raise ValueError("merging near sites broke D4 symmetry of a symmetric certificate")
    return result, receipt
