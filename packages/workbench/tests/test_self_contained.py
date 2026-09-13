"""The workbench self-containment check reads markup and CSS, not JavaScript text."""

import pytest

from workbench_tools.build_site import dirty_metadata
from workbench_tools.self_contained import assert_self_contained_html


def test_dirty_metadata_is_explicit() -> None:
    assert dirty_metadata(dirty=True) == (
        '<meta name="squares-workbench-dirty" content="true">'
    )
    assert dirty_metadata(dirty=False) == (
        '<meta name="squares-workbench-dirty" content="false">'
    )


@pytest.mark.parametrize(
    "fragment",
    [
        '<script src="https://example.test/app.js"></script>',
        '<link rel="stylesheet" href="https://example.test/app.css">',
        "<style>@import 'https://example.test/app.css';</style>",
        "<style>.mark { background: url(https://example.test/mark.svg); }</style>",
        '<div style="background: url(../mark.svg)"></div>',
        '<img src="https://example.test/mark.svg">',
    ],
)
def test_external_resource_is_refused(fragment: str) -> None:
    with pytest.raises(ValueError, match="outside itself"):
        assert_self_contained_html(f"<html><body>{fragment}</body></html>")


@pytest.mark.parametrize(
    "fragment",
    [
        '<script>URL.createObjectURL(new Blob(["ok"]));</script>',
        '<link rel="canonical" href="https://example.test/workbench/">',
        '<a href="https://example.test/explainer/">explainer</a>',
        "<style>.font { src: url(data:font/woff2;base64,AAAA); }</style>",
        "<style>.mark { fill: url(#gradient); }</style>",
        '<img src="data:image/svg+xml;base64,AAAA">',
    ],
)
def test_local_or_nonfetch_reference_is_allowed(fragment: str) -> None:
    assert_self_contained_html(f"<html><body>{fragment}</body></html>")
