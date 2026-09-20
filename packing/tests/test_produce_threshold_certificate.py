"""CLI controls for the n-parameterised threshold-atom producer.

Missing ``--n`` is a usage error. A tiny n=2 covering run writes a receipt that is not
an H-216 candidate. ``--check`` touches in-tree APIs and writes no files. The command
embeds no JavaScript and does not import agenda-034 scratch.
"""

from __future__ import annotations

import ast
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse
from scipy.optimize import OptimizeResult

import devtools.produce_threshold_certificate as producer
from devtools import check_no_embedded_js as guard
from devtools.produce_threshold_certificate import (
    ProducerSettings,
    check_in_tree_apis,
    main,
    produce,
    refuse_scratch_imports,
    scientific_refuse,
    solve_covering,
)
from sqpack.fractional.colgen import LpSolution, Rows, SiteSet

MODULE = Path(__file__).resolve().parents[1] / "devtools/produce_threshold_certificate.py"
LIBRARY = Path(__file__).resolve().parents[1] / "src/sqpack/fractional/threshold_separation.py"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def test_n_is_required() -> None:
    try:
        main([])
    except SystemExit as error:
        assert error.code not in (0, None)
        return
    raise AssertionError("missing --n must exit nonzero")


def test_n_below_two_is_refused() -> None:
    code = main(["--n", "1", "--check"])
    assert code != 0


def test_check_validates_apis_and_writes_nothing(tmp_path: Path) -> None:
    output = tmp_path / "out"
    code = main(["--n", "2", "--check", "--output-dir", str(output)])
    assert code == 0
    assert not output.exists()
    apis = check_in_tree_apis()
    assert apis["FamilyGeometry.placements"] == "1"
    assert apis["ThresholdAtom.size"] == "3"


def test_tiny_n2_run_writes_a_non_candidate_receipt(tmp_path: Path) -> None:
    output = tmp_path / "out"
    code = main(
        [
            "--n",
            "2",
            "--outer-side",
            "5/2",
            "--square-side",
            "1",
            "--grid-counts",
            "3",
            "--direction-steps",
            "1",
            "--max-atom-rounds",
            "1",
            "--max-row-rounds",
            "0",
            "--output-dir",
            str(output),
        ]
    )
    receipt_path = output / "receipt.json"
    if not receipt_path.exists():
        raise AssertionError("the producer wrote no receipt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["n"] == 2
    assert receipt["candidate_created"] is False
    assert receipt["h216_verdict"] is None
    assert receipt["scientific_target"] is None
    if receipt["status"] == "refused":
        assert receipt["covering_ran"] is False
        assert receipt["reason"]
        assert code != 0
        return
    assert code == 0
    assert receipt["covering_ran"] is True
    assert receipt["status"] == "unresolved"
    assert isinstance(receipt["objective"], float)
    assert (output / "trajectory.json").exists()
    assert (output / "atoms.json").exists()
    atoms = json.loads((output / "atoms.json").read_text(encoding="utf-8"))
    assert atoms["n"] == 2
    assert atoms["candidate_created"] is False


def test_scientific_targets_are_refused(tmp_path: Path) -> None:
    n11 = scientific_refuse(ProducerSettings(n=11, direction_steps=180))
    assert n11 is not None
    n6 = scientific_refuse(ProducerSettings(n=6, outer_side=Fraction(299, 100)))
    assert n6 is not None
    receipt = produce(ProducerSettings(n=11, direction_steps=180), tmp_path / "n11")
    assert receipt["status"] == "refused"
    assert receipt["covering_ran"] is False
    assert receipt["candidate_created"] is False


def test_the_command_embeds_no_javascript() -> None:
    policy = guard.load_policy()
    for path in (MODULE, LIBRARY, Path(__file__)):
        source = path.read_text(encoding="utf-8")
        assert guard.scan_source(path.name, source, policy) == []


def test_producer_does_not_import_scratch() -> None:
    refuse_scratch_imports()
    for path in (MODULE, LIBRARY, Path(__file__)):
        names = " ".join(_imported_modules(path))
        assert "sepcore" not in names
        assert "lp383" not in names
        assert ".py.txt" not in names
        assert ".txt" not in names


def test_covering_timeout_is_unresolved_never_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout_linprog(*_args: object, **_kwargs: object) -> OptimizeResult:
        return OptimizeResult(
            success=False, status=1, x=None, ineqlin=None, message="time limit"
        )

    monkeypatch.setattr(producer, "linprog", timeout_linprog)
    outcome = solve_covering(sparse.csr_matrix([[1.0, 0.0], [0.0, 1.0]]), np.array([1.0, 1.0]))
    assert outcome.status == "unresolved"
    assert outcome.weights is None
    assert outcome.solver_status == 1
    assert outcome.solver_message == "time limit"


@pytest.mark.parametrize("status", [3, 4])
def test_unsuccessful_covering_states_are_unresolved_never_infeasible(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
) -> None:
    def failed_linprog(*_args: object, **_kwargs: object) -> OptimizeResult:
        return OptimizeResult(
            success=False,
            status=status,
            x=None,
            ineqlin=None,
            message="HiGHS could not resolve the model",
        )

    monkeypatch.setattr(producer, "linprog", failed_linprog)
    outcome = solve_covering(sparse.csr_matrix([[1.0]]), np.array([1.0]))
    assert outcome.status == "unresolved"
    assert outcome.solver_status == status
    assert outcome.solver_message == "HiGHS could not resolve the model"


def test_only_highs_status_two_reports_covering_infeasibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def infeasible_linprog(*_args: object, **_kwargs: object) -> OptimizeResult:
        return OptimizeResult(
            success=False,
            status=2,
            x=None,
            ineqlin=None,
            message="the model is infeasible",
        )

    monkeypatch.setattr(producer, "linprog", infeasible_linprog)
    outcome = solve_covering(sparse.csr_matrix([[0.0]]), np.array([1.0]))
    assert outcome.status == "infeasible"
    assert outcome.solver_status == 2
    assert outcome.solver_message == "the model is infeasible"


@pytest.mark.parametrize(
    ("status", "weights", "marginals", "objective"),
    [
        pytest.param(4, [1.0], [-1.0], 1.0, id="nonoptimal-status"),
        pytest.param(0, [float("nan")], [-1.0], 1.0, id="nonfinite-weights"),
        pytest.param(0, [1.0], [float("nan")], 1.0, id="nonfinite-duals"),
        pytest.param(0, [1.0], [-1.0], float("inf"), id="nonfinite-objective"),
        pytest.param(0, [[1.0]], [-1.0], 1.0, id="weights-not-a-vector"),
        pytest.param(0, [1.0], [[-1.0]], 1.0, id="duals-not-a-vector"),
        pytest.param(0, [1.0, 2.0], [-1.0], 1.0, id="wrong-weight-count"),
        pytest.param(0, [1.0], [-1.0, -2.0], 1.0, id="wrong-dual-count"),
    ],
)
def test_malformed_successful_covering_result_is_unresolved(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    weights: object,
    marginals: object,
    objective: float,
) -> None:
    def malformed_linprog(*_args: object, **_kwargs: object) -> OptimizeResult:
        return OptimizeResult(
            success=True,
            status=status,
            x=np.array(weights),
            ineqlin=OptimizeResult(marginals=np.array(marginals)),
            fun=objective,
            message="synthetic malformed success",
        )

    monkeypatch.setattr(producer, "linprog", malformed_linprog)
    outcome = solve_covering(sparse.csr_matrix([[1.0]]), np.array([1.0]))
    assert outcome.status == "unresolved"
    assert outcome.weights is None
    assert outcome.duals is None
    assert outcome.objective is None
    assert outcome.solver_status == status
    assert outcome.solver_message == "synthetic malformed success"


def test_initial_covering_failure_preserves_unresolved_solver_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def seed_one_row(
        sites: SiteSet,
        _square_side: Fraction,
        _half_tangents: tuple[Fraction, ...],
        rows: Rows,
        **_kwargs: object,
    ) -> LpSolution:
        rows.add(0, (1.0, 1.0), np.ones(len(sites.orbits)))
        return LpSolution(
            np.zeros(len(sites.orbits)),
            np.zeros(1),
            stopped="seeded for solver classification",
        )

    monkeypatch.setattr(producer, "solve_rows", seed_one_row)
    monkeypatch.setattr(
        producer,
        "solve_covering",
        lambda *_args: producer.CoveringSolve(
            "unresolved",
            solver_status=4,
            solver_message="numerical difficulties",
        ),
    )

    receipt = produce(ProducerSettings(n=2), tmp_path / "out")

    assert receipt["status"] == "unresolved"
    assert receipt["covering_ran"] is True
    assert receipt["covering_solver_status"] == 4
    assert receipt["covering_solver_message"] == "numerical difficulties"
