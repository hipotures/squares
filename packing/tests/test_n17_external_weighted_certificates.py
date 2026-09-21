"""Controls for the two external n = 17 weighted certificates replayed here.

Mira's 4613/1000 certificate and Guzhou0806's R012 catalogue are other authors' bytes,
archived under ``resources/web/n17-weighted-certificates-2026-09-20/`` and decided by the
two replay instruments beside them. The full replays take minutes and leave receipts;
these tests are the fast part that has to stay true: the archived bytes are the pinned
ones, each instrument certifies the placements where the certificate is tight, and each
refuses a forgery one unit away from them. A verifier that passes the tight placement
and also passes the forgery is not measuring the measure.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import lzma
import sys
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

from sqpack.fractional.certificate import closed_form_conditions, sweep_direction_minimum

PACKET = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "web"
    / "n17-weighted-certificates-2026-09-20"
)
RECEIPTS = PACKET / "receipts"

#: Where Mira's certificate is tight: the exact replay's worst direction.
MIRA_TIGHT_DIRECTION = 2194
MIRA_LEAST_CELL_MASS = Fraction(1000002103, 1000000000)

#: R012 entries that attain ``gamma`` exactly, and the two ends of the catalogue.
R012_ENTRIES = (0, 504, 2240, 2924)
R012_TIGHT_ENTRY = 2240


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, PACKET / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered before execution: dataclasses resolve annotations through sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mira() -> ModuleType:
    return _load("replay_mira_4613_first_party")


@pytest.fixture(scope="module")
def r012() -> ModuleType:
    return _load("replay_guzhou_r012_first_party")


def test_mira_bytes_are_pinned_and_closed_form_conditions_hold(mira: ModuleType) -> None:
    raw = mira.CERTIFICATE_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == mira.CERTIFICATE_SHA256
    certificate, _ = mira.load(raw)
    assert certificate.n == 17
    assert certificate.bounded_side == Fraction(4613, 1000)
    assert len(certificate.atoms) == 1620
    assert len(certificate.half_tangents) == 2881
    assert certificate.total_mass == Fraction(849899249, 50000000)
    assert all(condition.holds for condition in closed_form_conditions(certificate))


def test_mira_tight_direction_is_exact_and_a_lightened_measure_is_refused(
    mira: ModuleType,
) -> None:
    certificate, _ = mira.load(mira.CERTIFICATE_PATH.read_bytes())
    direction = certificate.directions[MIRA_TIGHT_DIRECTION]
    minimum, _ = sweep_direction_minimum(certificate, direction)
    assert minimum == MIRA_LEAST_CELL_MASS

    # The slack at this direction is 2103/10^9. Three parts in a million off every
    # weight keeps the measure D4-symmetric and nonnegative and must sink the minimum
    # below one, by exactly the factor.
    factor = Fraction(999997, 1000000)
    lightened = dataclasses.replace(
        certificate,
        atoms=tuple(
            dataclasses.replace(atom, weight=atom.weight * factor) for atom in certificate.atoms
        ),
    )
    forged, _ = sweep_direction_minimum(lightened, direction)
    assert forged == MIRA_LEAST_CELL_MASS * factor
    assert forged < 1


def test_r012_records_and_negative_controls_pass(r012: ModuleType, tmp_path: Path) -> None:
    # Records mode: bytes against the pinned manifest, the closed-form arithmetic, the
    # Mira site provenance, and all ten controls -- the source's five counterexamples,
    # the raised threshold, gamma-is-tight, two lightened measures and the faithful
    # restriction. It decides no coverage, says so, and exits non-zero so that a
    # records run is never mistaken for a certified one.
    status = r012.main(["--no-coverage", "--tag", "control", "--receipts-dir", str(tmp_path)])
    assert status == 1
    receipt = json.loads((tmp_path / "guzhou-r012-first-party-control.json").read_text())
    assert receipt["status"] == "RECORDS_ONLY_NO_COVERAGE"
    assert receipt["controls_run"] == 10
    assert receipt["controls_passed"] is True
    assert receipt["closed_form"]["mass_gap_17gamma_minus_M"] == "701/250000"
    assert receipt["mira_provenance"]["passed"] is True


def test_r012_sampled_entries_certify_and_one_unit_above_gamma_is_refuted(
    r012: ModuleType,
) -> None:
    problem = r012.load_problem(r012.DEFAULT_CERT)
    atom_data = r012.build_atom_data(problem.atoms)
    threshold = 1000092
    assert Fraction(threshold, atom_data.scale) == Fraction(250023, 250000) == problem.gamma
    for index in R012_ENTRIES:
        entry = problem.entries[index]
        outcome = r012.decide_entry(
            atom_data,
            problem.outer,
            label=str(index),
            t=entry.t,
            side=entry.side,
            inset=entry.inset,
            threshold=threshold,
        )
        assert outcome.status == "certified", index
    tight = problem.entries[R012_TIGHT_ENTRY]
    raised = r012.decide_entry(
        atom_data,
        problem.outer,
        label="tight+1",
        t=tight.t,
        side=tight.side,
        inset=tight.inset,
        threshold=threshold + 1,
    )
    assert raised.status == "refuted"


def test_retained_receipts_record_full_acceptance() -> None:
    exact = json.loads((RECEIPTS / "mira-4613-first-party-exact.json").read_text())
    assert exact["smoke"] is False
    assert exact["refusals"] == []
    assert exact["result"]["accepted"] is True
    assert exact["result"]["least_cell_mass"]["computed"] == str(MIRA_LEAST_CELL_MASS)

    interval = json.loads((RECEIPTS / "mira-4613-first-party-interval.json").read_text())
    assert interval["smoke"] is False
    assert interval["refusals"] == []
    assert interval["result"]["accepted"] is True
    low, high = (Fraction(bound) for bound in interval["result"]["enclosure"])
    assert 1 <= low <= MIRA_LEAST_CELL_MASS <= high

    catalogue = json.loads((RECEIPTS / "guzhou-r012-first-party-001.json").read_text())
    assert catalogue["status"] == "FULL_CATALOGUE_CERTIFIED"
    assert catalogue["coverage"]["certified"] == catalogue["coverage"]["of"] == 2925
    assert catalogue["coverage"]["total_stalled"] == 0
    rows = lzma.decompress((RECEIPTS / "guzhou-r012-first-party-001.jsonl.xz").read_bytes())
    assert hashlib.sha256(rows).hexdigest() == catalogue["coverage"]["jsonl_sha256"]

    source = json.loads(
        (RECEIPTS / "guzhou-r012-source-replay-2026-09-20.result.json").read_text()
    )
    assert source["status"] == "PASS_COMPLETE_PARENT_CATALOGUE_GLOBAL_LOWER_BOUND"
    assert source["actual_catalogue_minimum"] == "250023/250000"
