"""Validate that a generated HTML page needs no external resources."""

from __future__ import annotations

import re
from html.parser import HTMLParser

_CSS_RESOURCE = re.compile(
    r"@import\b|url\(\s*(?![\"']?(?:data:|#))",
    re.IGNORECASE,
)
_FETCH_ATTRIBUTES = {
    "audio": ("src",),
    "embed": ("src",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "object": ("data",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "video": ("poster", "src"),
}


class _ResourceParser(HTMLParser):
    """Collect fetch-bearing markup while leaving script text opaque."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.findings: list[str] = []
        self._style_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.casefold(): value for name, value in attrs}
        folded = tag.casefold()
        if folded == "style":
            self._style_depth += 1
        if folded == "script" and values.get("src") is not None:
            self.findings.append("script src")
        if folded == "link" and values.get("href") is not None:
            relationships = set((values.get("rel") or "").casefold().split())
            if "canonical" not in relationships:
                self.findings.append("link href")
        for attribute in _FETCH_ATTRIBUTES.get(folded, ()):
            value = values.get(attribute)
            if value is not None and not value.lstrip().casefold().startswith("data:"):
                self.findings.append(f"{folded} {attribute}")
        inline_style = values.get("style")
        if inline_style is not None:
            self._check_css(inline_style)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.casefold() == "style":
            self._style_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "style":
            self._style_depth = max(0, self._style_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._style_depth:
            self._check_css(data)

    def _check_css(self, css: str) -> None:
        match = _CSS_RESOURCE.search(css)
        if match is not None:
            self.findings.append(match.group(0))


def external_resources(page: str) -> list[str]:
    """Return resource-bearing HTML/CSS constructs that reach outside the page."""
    parser = _ResourceParser()
    parser.feed(page)
    parser.close()
    return parser.findings


def assert_self_contained_html(page: str) -> None:
    """Raise when displaying ``page`` would fetch a resource outside itself."""
    findings = external_resources(page)
    if findings:
        raise ValueError(
            f"the page references {len(findings)} resource(s) outside itself: "
            + ", ".join(findings)
        )
