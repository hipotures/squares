"""Hybrid imports are exact supports, not automatically accepted certificates."""
import argparse
import json
from fractions import Fraction

import pytest

from devtools.frontier_hybrid import Stop, configuration
from devtools.frontier_hybrid_external import minimum
from sqpack.fractional.hybrid_support import load_measure, mapped_points, rational


def test_external_duplicate_points_and_mass(tmp_path):
    path = tmp_path / "source.txt"
    path.write_text("4 1\n10\n100\n3\n10 20 5\n10 20 7\n20 10 0\n")
    source = load_measure(path)
    assert source.mass == Fraction(3, 25)
    assert len(source.atoms) == 2
    assert source.record()["status"] == "SEED_ONLY"
    assert "square_side" not in source.record()
    assert "claim" not in source.record()


@pytest.mark.parametrize("text", [
    "4 1 10 100 1 10 20 -1", "4 1 10 100 1 41 20 1",
    "4 1 0 100 1 10 20 1", "4 1 10 0 1 10 20 1",
    "4 1 10 100 2 10 20 1", "4 1 10 100 1 10 20 1 region corner",
    "4 3 10 100 1 10 10 1", "4 1 10 100 100001",
])
def test_bad_external_input_is_refused(tmp_path, text):
    path = tmp_path / "bad.txt"
    path.write_text(text)
    with pytest.raises(ValueError):
        load_measure(path)


@pytest.mark.parametrize("value", [True, False, 0.5, None, "1/0"])
def test_inexact_or_invalid_rationals_are_refused(value):
    with pytest.raises((ValueError, ZeroDivisionError)):
        rational(value)


def test_exact_union_and_mapping(tmp_path):
    path = tmp_path / "own.json"
    path.write_text(json.dumps({"outer_side": "4", "atoms": [["1/3", "2/7", "1"]]}))
    source = load_measure(path)
    assert mapped_points([source, source], Fraction(5), "scale") == {(Fraction(5, 12), Fraction(5, 14))}
    assert mapped_points([source], Fraction(5), "centre") == {(Fraction(5, 6), Fraction(11, 14))}
    with pytest.raises(ValueError):
        mapped_points([source], Fraction(1), "centre")
    with pytest.raises(ValueError):
        load_measure(path, pinned_record=True)


def test_json_duplicate_keys_and_float_atoms_are_refused(tmp_path):
    path = tmp_path / "bad.json"
    for text in ('{"outer_side":"4","outer_side":"3","atoms":[["1","1","1"]]}',
                 '{"outer_side":"4","atoms":[[0.5,"1","1"]]}'):
        path.write_text(text)
        with pytest.raises(ValueError):
            load_measure(path)


def test_exact_minimum_parsing():
    assert minimum("min covered weight over ALL placements = 1000001/1000000 = 1.000001") == Fraction(1000001, 1000000)
    assert minimum("minimum covered weight over ALL bins = 1 = 1.000000", python_checker=True) == 1
    with pytest.raises(ValueError):
        minimum("PARTIAL RUN\nmin covered weight over ALL placements = 1/1 = 1")
    with pytest.raises(ValueError):
        minimum("VERIFIED")


def test_invalid_net_is_refused_before_search():
    with pytest.raises(ValueError):
        configuration(argparse.Namespace(direction_steps=3, shrink="99999/100000"))


def test_stop_does_not_signal_processes():
    stop = Stop(0)
    stop.poll()
    assert not stop.requested
    stop.signal(2, None)
    assert stop.requested
