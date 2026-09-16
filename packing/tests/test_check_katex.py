"""Real-renderer controls prevent an unsupported formula from receiving a pass."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from devtools import check_katex
from devtools.check_katex import check_files, main


def test_katex_accepts_aligned_math_and_rejects_an_unknown_command(tmp_path: Path) -> None:
    valid = tmp_path / "valid.md"
    valid.write_text(
        r"Inline $\nu_\circ(L)=\tau_{\mathrm{ac}}(L)$."
        "\n\n$$\n"
        r"\begin{aligned}a&=\frac12\\b&=\lfloor a\rfloor\end{aligned}\tag{1}"
        "\n$$\n"
        r"Literal `$\notAKaTeXCommand$` stays code."
    )
    invalid = tmp_path / "invalid.md"
    invalid.write_text(r"$\notAKaTeXCommand$")
    report = check_files([valid, invalid])
    assert report["version"]
    assert report["files"][0]["spans"] == 2
    assert report["files"][0]["errors"] == []
    assert len(report["files"][1]["errors"]) == 1
    assert "Undefined control sequence" in report["files"][1]["errors"][0]["error"]
    assert main([str(invalid)]) == 1


def test_empty_or_missing_inputs_cannot_pass(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one"):
        check_files([])
    empty = tmp_path / "empty.md"
    empty.write_text("No formulas here.")
    assert main([str(empty)]) == 2
    assert main([str(tmp_path / "missing.md")]) == 2


def test_missing_or_failed_node_driver_names_the_cause(tmp_path: Path) -> None:
    document = tmp_path / "math.md"
    document.write_text("$x$")
    missing = tmp_path / "missing-driver.mjs"
    with (
        patch.object(check_katex, "PARSE", missing),
        pytest.raises(FileNotFoundError, match=r"missing-driver[.]mjs"),
    ):
        check_files([document])

    failed = tmp_path / "failed-driver.mjs"
    failed.touch()
    failure = subprocess.CalledProcessError(
        7,
        ["node", str(failed)],
        stderr="driver exploded",
    )
    with (
        patch.object(check_katex, "PARSE", failed),
        patch.object(check_katex.subprocess, "run", side_effect=failure),
        pytest.raises(ValueError, match="driver exploded"),
    ):
        check_files([document])


def test_display_only_syntax_is_rejected_in_inline_math(tmp_path: Path) -> None:
    document = tmp_path / "modes.md"
    document.write_text(r"$$x\tag{1}$$ and $x\tag{1}$")
    report = check_files([document])["files"][0]
    assert report["spans"] == 2
    assert len(report["errors"]) == 1
    # The shared extractor returns display spans before inline spans.
    assert report["errors"][0]["span"] == 2
    assert "only in display equations" in report["errors"][0]["error"]
