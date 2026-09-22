#!/usr/bin/env python3
"""Derive the stage's citation lines from the frontier register and the bibliography.

Under its PROVEN values the stage names where each bound it shows comes from. It shows the
same two numbers `devtools.build_composite_figure_data` draws, so those are the two cited
here: the lower bound is the case's `verified_lower_bound`, what the register itself
certifies, and the upper bound is its `reported_upper_bound`, the best construction on
record. An upper bound the register has not certified is marked `reported`; only a
certified one is `verified`, and that is decided by the register's own rule,
`sqpack.assurance.bounds_agree_at_declared_precision`, so this record, the case checks and
the stage cannot disagree about which ceilings are proven.

**Every rule reads a typed field, never `n`.** Deciding from `n` what the record already
states is how `D-385` happened, and the same four questions recur for each bound:

1. *Is it derived?* A bound the register certifies with `common-knowledge` evidence alone
   -- the grid, the area bound, center counting, which the evidence schema describes as
   "nobody claims it and no citation is owed" -- has no line. For the upper bound that
   also needs the reported construction to be the certified one at the printed precision:
   a grid ceiling under a better reported packing is not what the stage shows.
2. *Is it this project's?* A first-party entry whose novelty the register scores as new is
   the same test that puts the star on the stage, and it cites this project with the one
   result in `frontier/results.yaml` that carries that evidence for this `n`. The year is
   the year the register dated the result's significance. For an upper bound only the
   construction's own evidence, `reported_upper_bound.evidence`, is asked: a new
   certificate of someone else's packing confirms it and does not make it ours, which is
   exactly `n = 29`, whose interval certificate `T-009` is scored new.
3. *Otherwise, whose is it?* A lower bound's previously-published entries must share one
   source key, and that key's authors, year and short venue come from
   `resources/bibliography.yaml`. An upper bound credits the case's own `found_by` and
   `improved_by`, with the venue of its `source_key`; where the register credits nobody,
   the line cites the source itself.
4. *What has this project recorded about it?* Every result for this `n` that carries one
   of the bound's own evidence entries is listed in `results`. Those that carry one this
   project performed -- a replay, an audit, an interval certificate -- confirm the
   external bound and are listed in `confirmed_by`. A result that only cites the source's
   own proof is relevant and listed, and confirms nothing. The shared checker behind
   several first-party certificates is not the bound's own evidence, so a project line
   lists only the results that carry its novel entries, not every earlier rung that used
   the same checker.

The reference says where the bound comes from and nothing else. **Everything this project
has to say about it is one parenthesis at the end of the line, `note`**: `(reported)`
where the register has not certified the bound, `(confirmed T-009)` where a result of ours
checks it, `(reported; confirmed T-009)` where both are true. `note` is composed here
rather than at the stage, so one place spells these words and the width below counts them.

**Nothing is read from prose.** Where the structured record lacks a year or an author it is
left out, not recovered from a body sentence or a credit line: an improved construction's
line carries no year, because `found_year` dates the find and the schema has no field for
the improvement's date. `--review` lists every such case, and every omitted line with the
reason, so a gap is reported rather than filled.

A line must fit in `TEXT_LIMIT` characters, the width the stage sets it in, the reference
and its note together. Where the note leaves too little room, the source's `short_venue`
is used if the bibliography gives one; a line that still does not fit fails the build
rather than being cut, and `--review` names every line that was shortened.

Usage, from `packing/`:

    uv run --frozen --all-extras --group dev python -m devtools.build_bound_citations --update
    uv run --frozen --all-extras --group dev python -m devtools.build_bound_citations --check
    uv run --frozen --all-extras --group dev python -m devtools.build_bound_citations --review
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strif import atomic_output_file

from sqpack.assurance import bounds_agree_at_declared_precision
from sqpack.known_best import KNOWN_BEST_CORPUS
from sqpack.yamlio import safe_load

ROOT = Path(__file__).resolve().parent.parent
FRONTIER = ROOT / "frontier"
EVIDENCE = FRONTIER / "evidence.yaml"
RESULTS = FRONTIER / "results.yaml"
BIBLIOGRAPHY = ROOT / "resources" / "bibliography.yaml"
RECORD = ROOT / "atlas" / "known-best" / "bound-citations.json"
GENERATOR = "devtools.build_bound_citations"
CONTRACT = "packing.squares:BoundCitations/v1"
SCHEMA = "bound-citations.schema.yaml"

#: The cases this record carries, one entry each: the composite's corpus, so the two
#: records cover the same `n` by construction.
CORPUS = KNOWN_BEST_CORPUS

#: The widest line the stage sets, in characters: the reference and its note together,
#: which is what a reader sees on one line. The note used to sit outside this count, drawn
#: as a bare word after the reference, so a line could be checked as fitting and drawn as
#: not (`think-qzmf`).
TEXT_LIMIT = 66

#: The register's two words for a bound's standing. `VERIFIED` is one it certifies at the
#: printed precision; `REPORTED` is one it carries from a source without certifying.
VERIFIED = "verified"
REPORTED = "reported"

PROJECT_NAME = "This project"

#: The novelty the evidence schema gives the grid, area and center-counting bounds.
COMMON_KNOWLEDGE = "common-knowledge"

#: The novelty scores that make a first-party bound this project's. The same set
#: `build_composite_figure_data` stars, which the contract test holds it to.
NOVEL = frozenset({"apparently-novel", "confirmed-novel"})

#: Who performed an entry this project did itself: a replay, an audit, a certificate.
FIRST_PARTY = "repository"


@dataclass(frozen=True, slots=True)
class Source:
    """One bibliography entry: what a citation of the source itself prints."""

    key: str
    authors: tuple[str, ...]
    year: int | None
    venue: str
    #: The venue a line falls back to when its confirmation would not otherwise fit.
    short_venue: str | None = None


@dataclass(frozen=True, slots=True)
class Register:
    """The records every citation is derived from, loaded once per build."""

    evidence: Mapping[str, Mapping[str, Any]]
    results: Sequence[Mapping[str, Any]]
    sources: Mapping[str, Source]
    names: Mapping[str, str]


def load_register() -> Register:
    evidence = safe_load(EVIDENCE.read_text(encoding="utf-8"))["evidence"]
    results = safe_load(RESULTS.read_text(encoding="utf-8"))["results"]
    bibliography = safe_load(BIBLIOGRAPHY.read_text(encoding="utf-8"))
    sources = {
        str(entry["key"]): Source(
            key=str(entry["key"]),
            authors=tuple(str(author) for author in entry["authors"]),
            year=entry["year"],
            venue=str(entry["venue"]),
            short_venue=entry.get("short_venue"),
        )
        for entry in bibliography["sources"]
    }
    return Register(
        evidence={str(entry["id"]): entry for entry in evidence},
        results=results,
        sources=sources,
        names={
            str(name): str(surname) for name, surname in bibliography["credited_names"].items()
        },
    )


def record_name(n: int) -> str:
    """The frontier case record a line comes from, as its file stem."""
    return f"n-{n:03d}"


def load_case(n: int) -> dict[str, Any]:
    text = (FRONTIER / f"{record_name(n)}.md").read_text(encoding="utf-8")
    return safe_load(text.split("---", 2)[1])["packing"]


def join_authors(surnames: Sequence[str]) -> str:
    """One name, two joined by an ampersand, three or more as the first and et al."""
    if not surnames:
        raise ValueError("a citation needs at least one author")
    if len(surnames) == 1:
        return surnames[0]
    if len(surnames) == 2:
        return f"{surnames[0]} & {surnames[1]}"
    return f"{surnames[0]} et al."


def cite(authors: str | None, year: int | None, venue: str) -> str:
    """`Authors Year, venue`, leaving out whichever of the first two is missing."""
    head = " ".join(part for part in (authors, None if year is None else str(year)) if part)
    return f"{head}, {venue}" if head else venue


def note(assurance: str, confirmed_by: Sequence[str]) -> str | None:
    """What this project has to say about the bound, or None where it is nothing.

    One parenthesis at the end of the line, in one vocabulary, holding both of the things
    that were said in two shapes before: the register's standing on the bound, and this
    project's own confirming results. The stage drew `reported` as a bare word after the
    reference and baked `(confirmed, T-009)` into the reference itself, so at `n = 29`,
    the one case that is both, the line read "Squares in Squares (confirmed, T-009)
    reported" -- two annotations of one bound, formatted two ways, saying what looks like
    two contradictory things (the owner, 2026-09-22).

    They do not contradict. `reported` is the register's: it carries this construction's
    value from the catalogue and has not certified it at the printed precision. The
    confirmation is ours: a result of this project's that checks the same bound. At
    `n = 29` both are true, and the line now says so once: "(reported; confirmed T-009)".
    The semicolon separates the two statements, so the comma is left to separate results.
    """
    said = []
    if assurance == REPORTED:
        said.append(REPORTED)
    if confirmed_by:
        said.append(f"confirmed {', '.join(confirmed_by)}")
    return f"({'; '.join(said)})" if said else None


def compose(authors: str | None, year: int | None, source: Source, room: int) -> str:
    """The reference alone: authors, year and venue, with nothing of this project's in it.

    In the source's full venue where that fits the `room` the note leaves, and its short
    venue where it does not; the caller fails a line that fits neither.
    """
    text = cite(authors, year, source.venue)
    if len(text) > room and source.short_venue is not None:
        text = cite(authors, year, source.short_venue)
    return text


def credit(
    reported: Mapping[str, Any], names: Mapping[str, str]
) -> tuple[str | None, int | None]:
    """Who the reported construction is credited to, and the year that credit is dated.

    Finders first, then any improver not already among them: the printed side is the last
    improvement's, and the lineage is what built it. The year is `found_year` only where
    nothing improved the packing since, because it dates the find and the schema carries
    no date for an improvement; an improved line leaves the year out rather than print one
    that belongs to an earlier side.
    """
    finders = [str(name) for name in reported.get("found_by") or []]
    improvers = [str(name) for name in reported.get("improved_by") or []]
    lineage = finders + [name for name in dict.fromkeys(improvers) if name not in finders]
    if not lineage:
        return None, None
    missing = [name for name in lineage if name not in names]
    if missing:
        raise ValueError(f"credited names missing from {BIBLIOGRAPHY.name}: {missing}")
    year = None if improvers else reported.get("found_year")
    return join_authors([names[name] for name in lineage]), year


def in_scope(scope: Mapping[str, Any], n: int) -> bool:
    if "n_values" in scope:
        return n in scope["n_values"]
    return int(scope["n_min"]) <= n <= int(scope["n_max"])


def result_order(result_id: str) -> int:
    """`T-032` sorts as 32, so `T-100` will follow `T-099` rather than `T-010`."""
    return int(result_id.split("-", 1)[1])


def is_novel_first_party(entry: Mapping[str, Any], claim: str) -> bool:
    """The star's test: this project's bound, scored new by the register."""
    return (
        entry.get("claim") == claim
        and entry.get("performed_by") == FIRST_PARTY
        and entry.get("novelty") in NOVEL
    )


def results_carrying(
    n: int, evidence_ids: Iterable[str], results: Sequence[Mapping[str, Any]]
) -> list[str]:
    """The results for this `n` that carry any of these evidence ids, in id order."""
    wanted = set(evidence_ids)
    return sorted(
        (
            str(result["id"])
            for result in results
            if in_scope(result["scope"], n) and wanted & set(result.get("evidence") or [])
        ),
        key=result_order,
    )


def project_result(
    n: int, novel: Sequence[str], results: Sequence[Mapping[str, Any]]
) -> Mapping[str, Any]:
    """The one result that carries every novel entry behind this bound, for this `n`.

    Exactly one or the build fails: two would make the line's result id a choice, and none
    would mean a first-party bound the results register has not recorded.
    """
    matches = [
        result
        for result in results
        if set(novel) <= set(result.get("evidence") or []) and in_scope(result["scope"], n)
    ]
    if len(matches) != 1:
        found = [str(result["id"]) for result in matches]
        raise ValueError(f"n={n}: novel evidence {list(novel)} is carried by results {found}")
    return matches[0]


def own_evidence(ids: Iterable[str], register: Register) -> list[str]:
    """The entries that are this bound's own, rather than the grid or area bound."""
    return [
        item
        for item in dict.fromkeys(str(item) for item in ids)
        if register.evidence[item].get("novelty") != COMMON_KNOWLEDGE
    ]


def drawn(citation: Mapping[str, Any]) -> str:
    """The line as the stage sets it: the reference, then its note where there is one."""
    return " ".join(part for part in (citation["text"], citation["note"]) if part)


def _checked(n: int, label: str, citation: dict[str, Any]) -> dict[str, Any]:
    line = drawn(citation)
    if len(line) > TEXT_LIMIT:
        raise ValueError(
            f"n={n} {label}: {line!r} is {len(line)} characters, over {TEXT_LIMIT}"
        )
    return citation


def _project(
    n: int, label: str, novel: Sequence[str], *, value: str, assurance: str, register: Register
) -> dict[str, Any]:
    result = project_result(n, novel, register.results)
    year = int(str(result["significance"]["scored"])[:4])
    return _checked(
        n,
        label,
        {
            "text": f"{PROJECT_NAME} {year}, result {result['id']}",
            "note": note(assurance, []),
            "basis": "project",
            "assurance": assurance,
            "source_key": None,
            "result": str(result["id"]),
            "results": results_carrying(n, novel, register.results),
            "confirmed_by": [],
            "value": value,
        },
    )


def _source(key: str | None, register: Register, where: str) -> Source:
    if key is None:
        raise ValueError(f"{where}: no source key to cite")
    if key not in register.sources:
        raise ValueError(f"{where}: {key} is not in {BIBLIOGRAPHY.name}")
    return register.sources[key]


def _external(
    n: int,
    label: str,
    *,
    source: Source,
    credited: tuple[str | None, int | None],
    own: Sequence[str],
    value: str,
    assurance: str,
    register: Register,
) -> dict[str, Any]:
    """An external source's line, and what this project has recorded about the bound."""
    performed = [
        item for item in own if register.evidence[item].get("performed_by") == FIRST_PARTY
    ]
    confirmed_by = results_carrying(n, performed, register.results)
    authors, year = credited
    said = note(assurance, confirmed_by)
    return _checked(
        n,
        label,
        {
            "text": compose(authors, year, source, TEXT_LIMIT - len(said or "") - bool(said)),
            "note": said,
            "basis": "external",
            "assurance": assurance,
            "source_key": source.key,
            "result": None,
            "results": results_carrying(n, own, register.results),
            "confirmed_by": confirmed_by,
            "value": value,
        },
    )


def lower_citation(
    n: int, case: Mapping[str, Any], register: Register
) -> dict[str, Any] | None:
    """The line for the certified lower bound, or None where it is derived."""
    bound = case["verified_lower_bound"]
    own = own_evidence(bound["evidence"], register)
    if not own:
        return None
    value = str(bound["value"])
    novel = [
        item for item in own if is_novel_first_party(register.evidence[item], "lower-bound")
    ]
    if novel:
        return _project(n, "lower", novel, value=value, assurance="verified", register=register)
    # A replay of a published bound is still that source's bound; the entries this project
    # performed but did not originate carry the source's key like the author's own do.
    keys = {register.evidence[item].get("source_key") for item in own}
    if len(keys) != 1:
        raise ValueError(f"n={n} lower: evidence {own} names {len(keys)} sources, not one")
    source = _source(keys.pop(), register, f"n={n} lower")
    return _external(
        n,
        "lower",
        source=source,
        credited=(join_authors(source.authors), source.year),
        own=own,
        value=value,
        assurance="verified",
        register=register,
    )


def upper_citation(
    n: int, case: Mapping[str, Any], register: Register
) -> dict[str, Any] | None:
    """The line for the reported upper bound, or None where it is the certified grid."""
    reported = case["reported_upper_bound"]
    verified = case["verified_upper_bound"]
    certified = bounds_agree_at_declared_precision(reported, verified)
    certificate = own_evidence(verified["evidence"], register)
    if certified and not certificate:
        return None
    value = str(reported["value"])
    assurance = VERIFIED if certified else REPORTED
    construction = own_evidence(reported["evidence"], register)
    novel = [
        item
        for item in construction
        if is_novel_first_party(register.evidence[item], "upper-bound")
    ]
    if novel:
        return _project(n, "upper", novel, value=value, assurance=assurance, register=register)
    source = _source(reported.get("source_key"), register, f"n={n} upper")
    names, year = credit(reported, register.names)
    return _external(
        n,
        "upper",
        source=source,
        credited=(names, year) if names else (join_authors(source.authors), source.year),
        own=own_evidence([*construction, *certificate], register),
        value=value,
        assurance=assurance,
        register=register,
    )


def build_entry(n: int, case: Mapping[str, Any], register: Register) -> dict[str, Any]:
    return {
        "n": n,
        "record": record_name(n),
        "upper": upper_citation(n, case, register),
        "lower": lower_citation(n, case, register),
    }


def build_record() -> dict[str, Any]:
    register = load_register()
    return {
        "softschema": {
            "contract": CONTRACT,
            "schema": SCHEMA,
            "envelope": "citations",
            "status": "enforced",
        },
        "citations": {
            "generated_by": GENERATOR,
            "entries": [build_entry(n, load_case(n), register) for n in CORPUS.numbers],
        },
    }


def load_record() -> dict[str, Any]:
    """The citation data, as committed."""
    return json.loads(RECORD.read_text(encoding="utf-8"))["citations"]


def _text(record: Mapping[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def update() -> None:
    content = _text(build_record())
    if RECORD.is_file() and RECORD.read_text(encoding="utf-8") == content:
        print(f"bound citations already current: {RECORD.name}")
        return
    with atomic_output_file(RECORD, make_parents=True) as temporary:
        temporary.write_text(content, encoding="utf-8")
    print(f"bound citations updated: {RECORD.name}")


def check() -> None:
    if not RECORD.is_file():
        raise ValueError(f"missing {RECORD.relative_to(ROOT)}; run with --update")
    if RECORD.read_text(encoding="utf-8") != _text(build_record()):
        raise ValueError(f"stale {RECORD.relative_to(ROOT)}; re-run with --update")
    print("bound citations check passed: matches the frontier register and bibliography")


def coverage(entries: Sequence[Mapping[str, Any]]) -> dict[str, Counter[str]]:
    """Each bound's lines by basis and assurance, with `none` for an omitted line."""
    tally: dict[str, Counter[str]] = {"upper": Counter(), "lower": Counter()}
    for entry in entries:
        for label, counts in tally.items():
            citation = entry[label]
            counts[
                "none" if citation is None else f"{citation['basis']} {citation['assurance']}"
            ] += 1
    return tally


def omissions(
    entries: Sequence[Mapping[str, Any]], cases: Mapping[int, Mapping[str, Any]]
) -> dict[str, list[int]]:
    """Every `n` where a line, or a part of one, was left out, by the reason for it."""

    def credited(n: int, field: str) -> bool:
        return bool(cases[n]["reported_upper_bound"].get(field))

    external_upper = [
        e["n"] for e in entries if e["upper"] is not None and e["upper"]["basis"] == "external"
    ]
    return {
        "upper omitted: the certified grid": [e["n"] for e in entries if e["upper"] is None],
        "upper credits nobody, so the line cites the source without author or year": [
            n
            for n in external_upper
            if not credited(n, "found_by") and not credited(n, "improved_by")
        ],
        "upper improved since found, so the year is left out": [
            n for n in external_upper if credited(n, "improved_by")
        ],
        "upper reported and not certified": [
            e["n"]
            for e in entries
            if e["upper"] is not None and e["upper"]["assurance"] == REPORTED
        ],
        "lower omitted: common-knowledge evidence alone": [
            e["n"] for e in entries if e["lower"] is None
        ],
    }


def linked_results(entries: Sequence[Mapping[str, Any]]) -> dict[str, dict[int, list[str]]]:
    """Which lines this project's results confirm, and which they are only relevant to."""
    links: dict[str, dict[int, list[str]]] = {}
    for entry in entries:
        for label in ("upper", "lower"):
            line = entry[label]
            if line is None:
                continue
            confirming = line["confirmed_by"]
            other = [item for item in line["results"] if item not in confirming]
            if line["basis"] == "project":
                links.setdefault(f"{label} established by", {})[entry["n"]] = line["results"]
            else:
                if confirming:
                    links.setdefault(f"{label} confirmed by", {})[entry["n"]] = confirming
                if other:
                    links.setdefault(f"{label} relevant, not confirming", {})[entry["n"]] = (
                        other
                    )
    return links


def shortened(entries: Sequence[Mapping[str, Any]], register: Register) -> list[str]:
    """The lines set in their source's short venue so the confirmation would fit."""
    found: list[str] = []
    for entry in entries:
        for label in ("upper", "lower"):
            line = entry[label]
            if line is None or line["source_key"] is None:
                continue
            if register.sources[line["source_key"]].venue not in line["text"]:
                found.append(f"n={entry['n']} {label}: {line['text']!r}")
    return found


def review() -> None:
    """Report what every line cites and every place a line or a year was left out."""
    register = load_register()
    cases = {n: load_case(n) for n in CORPUS.numbers}
    entries = [build_entry(n, cases[n], register) for n in CORPUS.numbers]
    for label, counts in coverage(entries).items():
        tallies = ", ".join(f"{key} {value}" for key, value in sorted(counts.items()))
        print(f"{label}: {tallies}")
    print()
    for reason, numbers in omissions(entries, cases).items():
        print(f"{reason} ({len(numbers)}): n = {numbers}")
    print()
    cited: dict[str, list[int]] = {}
    for entry in entries:
        if entry["lower"] is not None:
            key = entry["lower"]["source_key"] or entry["lower"]["result"]
            cited.setdefault(key, []).append(entry["n"])
    for key, numbers in sorted(cited.items(), key=lambda item: (-len(item[1]), item[0])):
        shown = "" if len(numbers) > 12 else f": n = {numbers}"
        print(f"lower cites {key} ({len(numbers)}){shown}")
    print()
    for kind, by_n in linked_results(entries).items():
        grouped: dict[tuple[str, ...], list[int]] = {}
        for n, ids in by_n.items():
            grouped.setdefault(tuple(ids), []).append(n)
        for ids, numbers in grouped.items():
            span = (
                f"n = {numbers[0]}..{numbers[-1]} ({len(numbers)})"
                if len(numbers) > 12
                else f"n = {numbers}"
            )
            print(f"{kind} {', '.join(ids)}: {span}")
    for line in shortened(entries, register):
        print(f"shortened to the source's short venue: {line}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--update", action="store_true", help="write the record")
    group.add_argument("--check", action="store_true", help="fail if the record is stale")
    group.add_argument("--review", action="store_true", help="report coverage and omissions")
    arguments = parser.parse_args(argv)
    try:
        if arguments.update:
            update()
        elif arguments.check:
            check()
        else:
            review()
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
