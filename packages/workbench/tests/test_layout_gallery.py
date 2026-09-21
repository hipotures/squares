"""The design gallery's comparison page, without a browser."""

from __future__ import annotations

from pathlib import Path

from workbench_tools.layout_gallery import VIEWPORTS, VIEWS, compare


def test_the_comparison_page_links_both_sets_relative_to_itself(tmp_path: Path) -> None:
    before, after = tmp_path / "shots" / "before", tmp_path / "shots" / "after"
    view = VIEWS[0].name
    width, height = VIEWPORTS[0]
    for root in (before, after):
        (root / view).mkdir(parents=True)
        (root / view / f"{width}x{height}.jpg").write_bytes(b"\xff\xd8\xff")
    (after / view / f"{width}x{height}-end.jpg").write_bytes(b"\xff\xd8\xff")

    page = compare(before, after, tmp_path / "review" / "compare.html").read_text(
        encoding="utf-8"
    )

    assert f'src="../shots/before/{view}/{width}x{height}.jpg"' in page
    assert f'src="../shots/after/{view}/{width}x{height}.jpg"' in page
    # A scrolled picture only one side has is shown against a placeholder, not dropped.
    assert f'src="../shots/after/{view}/{width}x{height}-end.jpg"' in page
    assert "no before picture" in page
    assert "<script" not in page
    assert all(f'id="{v.name}"' in page for v in VIEWS)
