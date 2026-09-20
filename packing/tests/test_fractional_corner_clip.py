"""Controls for the convex corner clip, the domain predicate of lane-a Theorem B.

The predicate is a few lines of rational arithmetic, and that is exactly why it needs a
control it cannot pass by accident. The one used here is R1's own measurement in X-040:
the retained 88-core ceiling family, transported to ``96/25`` by centre homothety, keeps
**exactly 7** of its total weight 11 once the four corner triangles at ``d = 1/2`` are
cut. That number is what says the predicate folds the angle correctly; the same code
written with ``cos`` in place of ``max(|cos|, |sin|)`` reads the family's four mirrored
flush corner cores as deep in the container and reports 9.

The rest is the two gate routes: that they take the clip, that they agree on the number
it produces, that a clip which empties the domain is a refusal and not a vacuous pass,
and that a certificate refused without the clip is accepted with it -- which is what
makes the clip load-bearing rather than decorative.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from devtools.decide_certificate import main as gate_main
from devtools.declare_least_cell_mass import declare
from devtools.independent_ceiling_reader import decide as read_ceiling
from devtools.independent_ceiling_reader import main as ceiling_reader_main
from devtools.independent_ceiling_reader import parse_record
from devtools.polish_ceiling_family import load_family as load_polishable_family
from devtools.replay_ceiling_family import main as replay_family_main
from devtools.run_fractional_colgen import RunSettings, certificate_json, freeze_priced_family
from sqpack.fractional.ceiling import CeilingCertificate, verify_ceiling
from sqpack.fractional.certificate import Certificate, verify
from sqpack.fractional.colgen import AdaptiveLog, square_at, square_excluded
from sqpack.fractional.corner_clip import CornerClip, EmptyClippedDomainError
from sqpack.fractional.interval import verify_by_intervals
from sqpack.fractional.model import Atom, rotation_from_half_tangent
from sqpack.fractional.sweep import centre_domain, minimum_covered_mass

PACKING = Path(__file__).resolve().parents[1]
RETAINED_FAMILY = (
    PACKING
    / "campaign/series/series-000-smoke-and-calibration/results/agenda-034"
    / "ceiling-family-191-50.json"
)

#: R1's transport: the family's side ``191/50`` carried to ``96/25``. Because the side
#: scales by the same factor, the homothety about the container centre is the homothety
#: about the corner, so every centre is simply multiplied.
TRANSPORT = Fraction(96, 25) / Fraction(191, 50)

CONDITION5_EXACT = "Condition 5 every reachable cell carries mass 1"
CONDITION5_INTERVAL = "Condition 5 every admissible centre covers mass 1"


# --- the predicate on hand-computed poses ------------------------------------


def test_the_flush_corner_core_penetrates_by_exactly_one_minus_b() -> None:
    """A concentric ``B``-core of a flush unit square reaches ``x + y = 1 - B``.

    The unit square ``[0, 1]^2`` has ``min(x + y) = 0``; its concentric ``B``-core is
    ``[(1 - B)/2, (1 + B)/2]^2``, whose own minimum is ``1 - B``. Both the centre form
    and the slab form have to say so.
    """
    side, shrink = Fraction(4), Fraction(7, 10)
    clip = CornerClip(side, shrink, Fraction(1, 2))
    centre = Fraction(1, 2)
    assert clip.penetration(centre, centre, Fraction(1), Fraction(0)) == 1 - shrink
    assert clip.excludes(centre, centre, Fraction(1), Fraction(0))
    axes = (Fraction(1), Fraction(0), Fraction(0), Fraction(1))
    assert clip.square_penetration(axes, (centre, centre), shrink / 2) == 1 - shrink


def test_the_threshold_is_closed_and_the_predicate_is_d4_invariant() -> None:
    side, shrink = Fraction(4), Fraction(7, 10)
    depth = Fraction(1, 2)
    clip = CornerClip(side, shrink, depth)
    axis = (Fraction(1), Fraction(0))
    # A centre placed so that the penetration is exactly d: the triangle is closed, so
    # this core meets it and is removed.
    on_the_line = (depth + shrink) / 2
    assert clip.penetration(on_the_line, on_the_line, *axis) == depth
    assert clip.excludes(on_the_line, on_the_line, *axis)
    # One ulp of rational further in and it is kept.
    inside = on_the_line + Fraction(1, 10**6)
    assert not clip.excludes(inside, inside, *axis)
    # The eight D4 images of a centre all have the same penetration.
    x, y = Fraction(3, 5), Fraction(9, 10)
    images = (
        (x, y),
        (side - x, y),
        (x, side - y),
        (side - x, side - y),
        (y, x),
        (side - y, x),
        (y, side - x),
        (side - y, side - x),
    )
    values = {clip.penetration(a, b, *axis) for a, b in images}
    assert len(values) == 1


def test_the_reach_is_folded_so_a_quarter_turn_matches_the_upright_square() -> None:
    """``t = 1`` is a quarter turn: the same square, so the same reach.

    This is the property the retained family's mirrored placements depend on, and the
    one a ``cos``-only predicate gets wrong.
    """
    clip = CornerClip(Fraction(4), Fraction(7, 10), Fraction(1, 2))
    upright = rotation_from_half_tangent("0", Fraction(0))
    quarter = rotation_from_half_tangent("1", Fraction(1))
    assert clip.reach(upright.ux, upright.uy) == Fraction(7, 10)
    assert clip.reach(quarter.ux, quarter.uy) == Fraction(7, 10)
    tilted = rotation_from_half_tangent("t", Fraction(2, 5))
    assert clip.reach(tilted.ux, tilted.uy) == Fraction(7, 10) * Fraction(21, 29)


def test_the_slab_form_agrees_with_the_centre_form_on_every_d4_image() -> None:
    """`colgen.Square` images permute and sign the axes; the predicate must not care."""
    side, shrink = Fraction(4), Fraction(7, 10)
    clip = CornerClip(side, shrink, Fraction(1, 2))
    direction = rotation_from_half_tangent("t", Fraction(2, 5))
    centre = (Fraction(3, 4), Fraction(6, 5))
    square = square_at(direction, centre, side, shrink)
    expected = clip.excludes(centre[0], centre[1], direction.ux, direction.uy)
    assert square_excluded(square, clip, side) == expected
    assert all(square_excluded(image, clip, side) == expected for image in square.images())


def test_the_clipped_centre_domain_is_an_octagon_with_the_derived_cut() -> None:
    side, shrink, depth = Fraction(96, 25), Fraction(9977, 10000), Fraction(1, 2)
    direction = rotation_from_half_tangent("0", Fraction(0))
    plain = centre_domain(side, shrink, direction)
    clipped = centre_domain(side, shrink, direction, clip=CornerClip(side, shrink, depth))
    assert len(plain) == 4
    assert len(clipped) == 8
    cut = depth + shrink
    assert min(u + v for u, v in clipped) == cut
    # Nothing was invented: every vertex is still an admissible centre.
    half = shrink / 2
    assert all(half <= u <= side - half and half <= v <= side - half for u, v in clipped)


def test_an_absent_clip_leaves_the_centre_domain_byte_for_byte() -> None:
    side, shrink = Fraction(96, 25), Fraction(9977, 10000)
    for tangent in (Fraction(0), Fraction(2, 5), Fraction(207107, 500000)):
        direction = rotation_from_half_tangent(str(tangent), tangent)
        assert centre_domain(side, shrink, direction, clip=None) == centre_domain(
            side, shrink, direction
        )


# --- R1's control: the retained family restricted to the clipped domain -------


def _retained_family(factor: Fraction) -> CeilingCertificate:
    """The retained 88-core family, every centre carried by a homothety of ``factor``."""
    record = json.loads(RETAINED_FAMILY.read_text())
    family = CeilingCertificate.from_record(record)
    moved = tuple(
        type(p)(p.half_tangent, p.centre_x * factor, p.centre_y * factor, p.weight, p.side)
        for p in family.placements
    )
    return CeilingCertificate(
        family.n,
        family.outer_side * factor,
        family.square_side,
        family.half_tangents,
        moved,
    )


def _residual(family: CeilingCertificate, depth: Fraction) -> tuple[Fraction, Fraction]:
    """``(kept, removed)`` weight of the family against the clip at ``depth``."""
    clip = CornerClip(family.outer_side, family.square_side, depth)
    kept = removed = Fraction(0)
    for placement in family.placements:
        ax, ay, _, bx, by, _ = placement.slabs()
        if clip.excludes_square(
            (ax, ay, bx, by), (placement.centre_x, placement.centre_y), placement.side / 2
        ):
            removed += placement.weight
        else:
            kept += placement.weight
    return kept, removed


def test_the_transported_family_keeps_exactly_seven_on_the_clipped_domain() -> None:
    """R1's number, reproduced: residual 7 against a requirement of 11 at 96/25.

    The acceptance test of the predicate itself. Four corners, mass 1 each, exactly the
    equality lane-a Lemma 4 records ("mass 1 meeting each corner triangle x + y <= d for
    d <= 0.9"), and the reason the all-free class is the one branch of Theorem B with
    headroom.
    """
    family = _retained_family(TRANSPORT)
    assert family.outer_side == Fraction(96, 25)
    assert family.total_weight == 11
    kept, removed = _residual(family, Fraction(1, 2))
    assert kept == 7
    assert removed == 4


def test_the_residual_is_the_same_at_the_family_s_own_side_and_moves_only_at_one() -> None:
    """The ``191/50`` squeeze artefact R1 diagnosed, read from the other side.

    At the family's own side the clip removes a fifth unit once ``d`` reaches 1; at
    ``96/25`` it does not, because the mid-wall core's edge sits at ``1.005`` there
    rather than ``0.997``. A predicate that could not see that difference would not be
    measuring the geometry.
    """
    home = _retained_family(Fraction(1))
    moved = _retained_family(TRANSPORT)
    for depth in (Fraction(1, 4), Fraction(1, 2), Fraction(9, 10)):
        assert _residual(home, depth) == (Fraction(7), Fraction(4))
        assert _residual(moved, depth) == (Fraction(7), Fraction(4))
    assert _residual(home, Fraction(1)) == (Fraction(6), Fraction(5))
    assert _residual(moved, Fraction(1)) == (Fraction(7), Fraction(4))


def test_a_ceiling_family_that_enters_a_corner_triangle_fails_k4() -> None:
    """The family is a ceiling for the unconditional program and not for the clipped one.

    Both readers have to say so: the first-party ``verify_ceiling`` and the independent
    reader written from the statement, which shares no code with it.
    """
    family = _retained_family(TRANSPORT)
    clip = CornerClip(family.outer_side, family.square_side, Fraction(1, 2))
    plain = verify_ceiling(family)
    assert plain.proved
    clipped = verify_ceiling(family, clip=clip)
    assert not clipped.proved
    assert clipped.failures == ("K4 every placement avoids the corner triangles",)
    record = parse_record(family.to_record())
    independent = read_ceiling(record, Fraction(1, 2))
    assert not independent["K4"]["holds"]
    assert independent["K4"]["count_meeting_a_triangle"] == 32
    assert independent["corner_clip_residual"] == {
        "depth": "1/2",
        "kept": "7",
        "removed": "4",
    }


def test_a_clipped_verdict_names_the_class_it_is_about() -> None:
    """A clipped statement must never be quotable as the unconditional one."""
    family = _retained_family(TRANSPORT)
    clip = CornerClip(family.outer_side, family.square_side, Fraction(1, 2))
    kept = tuple(
        placement
        for placement in family.placements
        if not clip.excludes_square(
            placement.slabs()[0:2] + placement.slabs()[3:5],
            (placement.centre_x, placement.centre_y),
            placement.side / 2,
        )
    )
    survivors = CeilingCertificate(
        7, family.outer_side, family.square_side, family.half_tangents, kept
    )
    verdict = verify_ceiling(survivors, clip=clip)
    assert verdict.proved
    assert "corner triangles x + y <= 1/2" in verdict.statement
    assert "that class of packings" in verdict.statement
    assert "corner triangles" not in verify_ceiling(family).statement


# --- the two gate routes ------------------------------------------------------

# A container, a shrink and a two-direction net small enough to decide in milliseconds
# by both routes. The single central atom is the whole certificate: Condition 5 then
# says every admissible core contains the centre, which is false on the full domain
# (a core in a container corner contains nothing) and true once the corner triangles at
# d = 1 are cut. So the clip is what decides it, which is the point of the fixture.
# ``n = 5`` only to clear ``ceiling_side``: three B-squares fit across 19/10, so the
# gate would refuse any smaller n before either route ran.
TINY_SIDE = Fraction(19, 10)
TINY_SHRINK = Fraction(7, 10)
TINY_NET = (Fraction(0), Fraction(5, 12))


def _tiny_certificate(side: Fraction = TINY_SIDE) -> Certificate:
    centre = side / 2
    return Certificate(
        n=5,
        outer_side=side,
        square_side=TINY_SHRINK,
        atoms=(Atom("centre", centre, centre, Fraction(1)),),
        half_tangents=TINY_NET,
    )


def test_the_clip_is_what_decides_the_tiny_certificate() -> None:
    certificate = _tiny_certificate()
    clip = CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1))
    plain = verify(certificate, workers=1)
    assert not plain.accepted
    assert plain.failures == (CONDITION5_EXACT,)
    clipped = verify(certificate, workers=1, clip=clip)
    assert clipped.accepted
    assert clipped.minimum_cell_mass == 1


def test_both_routes_agree_on_the_number_under_the_clip() -> None:
    """The gate's own test, on a clipped domain: same value, enclosure of width zero."""
    certificate = _tiny_certificate()
    clip = CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1))
    exact = verify(certificate, workers=1, clip=clip)
    interval = verify_by_intervals(certificate, enclose=True, clip=clip)
    assert interval.accepted
    enclosure = interval.enclosure
    assert enclosure is not None
    assert enclosure[0] == enclosure[1]
    assert enclosure[0] == exact.minimum_cell_mass
    # The interval route refuses the same certificate on the full domain, so the two
    # routes are agreeing about the clip and not about a certificate that never needed
    # one.
    assert not verify_by_intervals(certificate, enclose=True).accepted


def test_clipping_can_only_raise_the_least_covered_mass() -> None:
    """Cutting rows out of a covering program cannot lower its worst placement."""
    certificate = _tiny_certificate()
    clip = CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1))
    for direction in certificate.directions:
        plain, _ = minimum_covered_mass(certificate.atoms, direction, TINY_SIDE, TINY_SHRINK)
        clipped, _ = minimum_covered_mass(
            certificate.atoms, direction, TINY_SIDE, TINY_SHRINK, clip=clip
        )
        assert clipped >= plain


def test_a_clip_that_removes_everything_is_a_refusal_and_not_a_vacuous_pass() -> None:
    """An empty class has nothing to quantify over, so Condition 5 must fail, not pass."""
    small = Fraction(3, 2)
    certificate = _tiny_certificate(small)
    clip = CornerClip(small, TINY_SHRINK, Fraction(1))
    direction = certificate.directions[0]
    try:
        centre_domain(small, TINY_SHRINK, direction, clip=clip)
    except EmptyClippedDomainError:
        pass
    else:  # pragma: no cover - the fixture is chosen so the domain is empty
        raise AssertionError("the clip was expected to empty the domain")
    exact = verify(certificate, workers=1, clip=clip)
    assert not exact.accepted
    assert exact.failures == (CONDITION5_EXACT,)
    assert exact.minimum_cell_mass is None
    interval = verify_by_intervals(certificate, enclose=True, clip=clip)
    assert not interval.accepted
    assert interval.failures == (CONDITION5_INTERVAL,)


# --- the record and the gate's variant policy ---------------------------------


def _frozen(tmp_path: Path, clip: CornerClip | None) -> Path:
    certificate = _tiny_certificate()
    least = verify(certificate, workers=1, clip=clip).minimum_cell_mass
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "candidate.json"
    path.write_text(certificate_json(certificate, str(least), clip=clip))
    return path


def test_a_clipped_run_declares_its_hypothesis_in_the_frozen_bytes(tmp_path: Path) -> None:
    plain = json.loads(_frozen(tmp_path / "a", None).read_text())
    assert "variant" not in plain
    assert "corner_clip" not in plain
    clipped = json.loads(
        _frozen(tmp_path / "b", CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1))).read_text()
    )
    assert clipped["variant"] == "class"
    assert clipped["corner_clip"] == "1"


def test_the_gate_decides_a_clipped_record_only_when_asked_for_that_clip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _frozen(tmp_path, CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1)))
    # Without the flag the record is refused by name, exactly as before this branch.
    assert gate_main([str(path)]) == 1
    assert "REFUSED" in capsys.readouterr().out
    # With a different threshold it is refused for disagreeing with its own bytes.
    assert gate_main([str(path), "--corner-clip", "1/2"]) == 1
    assert "declared corner_clip" in capsys.readouterr().out
    # With the threshold it declares, both routes decide it and say what it is.
    assert gate_main([str(path), "--corner-clip", "1"]) == 0
    printed = capsys.readouterr().out
    assert "RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS" in printed
    assert "corner clip d = 1" in printed


def test_an_unclipped_record_is_refused_under_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _frozen(tmp_path, None)
    assert gate_main([str(path), "--corner-clip", "1"]) == 1
    assert "declares variant 'unconditional'" in capsys.readouterr().out


def test_a_record_carrying_a_clip_without_the_class_variant_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _frozen(tmp_path, CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1)))
    record = json.loads(path.read_text())
    record["variant"] = "unconditional"
    path.write_text(json.dumps(record, indent=1) + "\n")
    assert gate_main([str(path), "--corner-clip", "1"]) == 1
    assert gate_main([str(path)]) == 1
    assert "without variant: class" in capsys.readouterr().out


def test_the_declaration_tool_reads_the_clip_out_of_the_record(tmp_path: Path) -> None:
    """``least_cell_mass`` has to be the number the gate will then recompute."""
    clip = CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1))
    path = _frozen(tmp_path, clip)
    record = json.loads(path.read_text())
    record["least_cell_mass"] = None
    path.write_text(json.dumps(record, indent=1) + "\n")
    accepted, detail = declare(path)
    assert accepted
    assert "under the corner clip d = 1" in detail
    assert json.loads(path.read_text())["least_cell_mass"] == "1"


# --- the strings the bytes carry (review defects D1 and D4) -------------------


def test_an_unclipped_freeze_keeps_the_theorem_s_claim_and_id_byte_for_byte() -> None:
    """The unconditional strings are the ones every retained candidate already has."""
    record = json.loads(certificate_json(_tiny_certificate(), "1"))
    assert record["claim"] == "s(5) >= 19/10"
    assert record["id"] == "C-n005-fractional-19-10"
    assert "variant" not in record
    assert "corner_clip" not in record


def test_a_clipped_freeze_claims_the_class_and_cannot_be_read_as_a_bound() -> None:
    """D1: ``variant`` was the only field between these bytes and ``s(n) >= L``."""
    clip = CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1))
    record = json.loads(certificate_json(_tiny_certificate(), "1", clip=clip))
    assert record["claim"] == "corner class d = 1 excluded at s(5) >= 19/10"
    # The one property a reader scanning for bounds depends on.
    assert not str(record["claim"]).startswith("s(")
    assert record["id"] == "C-n005-fractional-19-10-clip-1-1"
    assert record["variant"] == "class"
    assert record["corner_clip"] == "1"


def test_the_gate_refuses_the_unconditional_claim_on_a_class_record(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shape of the exp-219 bytes: variant: class, theorem claim. Refused, by name."""
    path = _frozen(tmp_path, CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1)))
    record = json.loads(path.read_text())
    record["claim"] = "s(5) >= 19/10"
    path.write_text(json.dumps(record, indent=1) + "\n")
    assert gate_main([str(path), "--corner-clip", "1"]) == 1
    printed = capsys.readouterr().out
    assert "is the unconditional theorem conclusion on a variant: class record" in printed
    assert "corner class d = 1 excluded at s(5) >= 19/10" in printed


def test_the_gate_refuses_a_class_record_carrying_the_unconditional_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _frozen(tmp_path, CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1)))
    record = json.loads(path.read_text())
    record["id"] = "C-n005-fractional-19-10"
    path.write_text(json.dumps(record, indent=1) + "\n")
    assert gate_main([str(path), "--corner-clip", "1"]) == 1
    printed = capsys.readouterr().out
    assert "!= class id 'C-n005-fractional-19-10-clip-1-1'" in printed


def test_the_gate_accepts_the_class_claim_and_id_under_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """What the driver writes is what the gate expects, on the same bytes."""
    path = _frozen(tmp_path, CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1)))
    assert gate_main([str(path), "--corner-clip", "1"]) == 0
    assert "RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS" in capsys.readouterr().out


def test_the_unconditional_claim_check_is_unchanged_without_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _frozen(tmp_path, None)
    record = json.loads(path.read_text())
    record["claim"] = "s(5) >= 2"
    path.write_text(json.dumps(record, indent=1) + "\n")
    assert gate_main([str(path)]) == 1
    assert "!= theorem conclusion 's(5) >= 19/10'" in capsys.readouterr().out


# --- the family record and the readers that print sentences about it ----------


def _priced_family(tmp_path: Path, depth: Fraction | None) -> Path:
    """One priced support row frozen as a ceiling family, clipped or not."""
    centre = TINY_SIDE / 2
    settings = RunSettings(
        n=5,
        outer_side=TINY_SIDE,
        square_side=TINY_SHRINK,
        grid_counts=(2,),
        inset=Fraction(1, 2),
        angle_limit=TINY_NET[-1],
        direction_steps=1,
        scale=1000,
        column_rounds=1,
        max_rounds=1,
        rows_per_direction=1,
        corner_clip=depth,
    )
    log = AdaptiveLog(stopped="test", priced_support=((0, centre, centre, Fraction(1)),))
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = freeze_priced_family(settings, log, tmp_path / "family.json")
    assert path is not None
    return path


def test_a_clipped_family_declares_the_class_at_its_top_level(tmp_path: Path) -> None:
    """D4: the clip was reachable only through ``provenance.settings``."""
    record = json.loads(_priced_family(tmp_path / "clipped", Fraction(1)).read_text())
    assert record["variant"] == "class"
    assert record["corner_clip"] == "1"
    assert record["provenance"]["settings"]["corner_clip"] == "1"
    plain = json.loads(_priced_family(tmp_path / "plain", None).read_text())
    assert "variant" not in plain
    assert "corner_clip" not in plain
    assert "corner_clip" not in plain["provenance"]["settings"]


def test_the_replay_refuses_a_class_family_until_it_is_asked_for_that_clip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _priced_family(tmp_path, Fraction(1))
    assert replay_family_main([str(path)]) == 1
    printed = capsys.readouterr().out
    assert "declares variant: class at corner clip d = 1" in printed
    assert replay_family_main([str(path), "--corner-clip", "1/2"]) == 1
    assert "declared corner_clip 1 != the requested 1/2" in capsys.readouterr().out
    assert replay_family_main([str(path), "--corner-clip", "1"]) == 0
    assert '"corner_clip": "1"' in capsys.readouterr().out


def test_the_independent_reader_refuses_a_class_family_without_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _priced_family(tmp_path, Fraction(1))
    assert ceiling_reader_main([str(path)]) == 2
    printed = capsys.readouterr().out
    assert "variant: class at corner clip d = 1" in printed
    # Whatever it printed, it is not this reader's unconditional theorem sentence.
    assert "no D4-symmetric measure" not in printed


def test_the_polisher_refuses_a_class_family_rather_than_dropping_the_clip(
    tmp_path: Path,
) -> None:
    path = _priced_family(tmp_path, Fraction(1))
    with pytest.raises(ValueError, match="decides the unconditional program only"):
        load_polishable_family(path, None)
    # An unclipped family is polishable exactly as before.
    assert load_polishable_family(_priced_family(tmp_path / "plain", None), None) is not None


def test_the_declaration_tool_refuses_a_class_record_with_no_threshold(
    tmp_path: Path,
) -> None:
    path = _frozen(tmp_path, CornerClip(TINY_SIDE, TINY_SHRINK, Fraction(1)))
    record = json.loads(path.read_text())
    del record["corner_clip"]
    record["least_cell_mass"] = None
    path.write_text(json.dumps(record, indent=1) + "\n")
    with pytest.raises(ValueError, match="must declare corner_clip"):
        declare(path)
