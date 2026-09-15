"""Replay the independent exact BC303 T2 geometry control."""

from fractions import Fraction

from cases.n11_five_dot_cover.bc303_t2_geometry_control import (
    labels,
    ray,
    run_controls,
)


def test_exact_geometry_review_controls() -> None:
    report = run_controls()
    assert report == {
        "scope": "Finite exact geometry only; no atom file or charge evaluation",
        "source_charts": 362,
        "selected_orientations": 361,
        "signed_rays": 1444,
        "bin_zero_source_charts": 182,
        "bin_zero_selected_orientations": 181,
        "d4_chart_and_proper_frame_checks": 2896,
        "critical_centre_checks": 4550,
        "split_fixture_corner_transport_checks": 16,
        "rational_minimum_parent_extent_indices": [0],
        "split_parent_separation": "2022521/878547000",
        "axis_parent_centre_interval_width": "2518679/2540000",
    }


def test_axis_upper_edge_is_excluded_and_fixture_is_sensitive() -> None:
    a = Fraction(3152, 3175)
    east = ray(Fraction(0))
    # At this boundary the second mark supplies label 15, so C is not forced 0.
    assert {0, 15} <= labels((a, a), east)
    # Moving the first S core right by 1/100 removes its ownership of mark 1.
    assert 0 not in labels((Fraction(3, 2), Fraction(737, 1000)), east)
