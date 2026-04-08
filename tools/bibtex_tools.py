"""
tools/bibtex_tools.py – Tool 2 for Phase 2: BibTeX generation.

Takes structured paper metadata (as produced by search_arxiv) and formats
every entry into valid BibTeX syntax ready to be written to a .bib file.
"""

from __future__ import annotations

import json
import re
from typing import Union

from smolagents import tool


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_cite_key(paper: dict) -> str:
    """
    Derive a BibTeX citation key from author surname + year + first title word.

    Example: Vaswani2017Attention
    """
    authors = paper.get("authors", [])
    first_author = authors[0] if authors else "Unknown"

    # Extract surname (last part before any comma, or last word)
    if "," in first_author:
        surname = first_author.split(",")[0].strip()
    else:
        surname = first_author.strip().split()[-1]

    year = str(paper.get("year", "0000"))

    title = paper.get("title", "Untitled")
    # Take the first meaningful word from the title (skip articles)
    skip = {"a", "an", "the", "of", "in", "on", "for", "with", "and", "or"}
    first_word = next(
        (w for w in re.split(r"\W+", title) if w.lower() not in skip and w),
        "Paper",
    )

    # Sanitise: keep only alphanumeric characters
    raw_key = f"{surname}{year}{first_word}"
    return re.sub(r"[^A-Za-z0-9_]", "", raw_key)


def _escape_bibtex(text: str) -> str:
    """Escape characters that have special meaning in BibTeX."""
    # Protect ampersands and percent signs
    text = text.replace("&", r"\&").replace("%", r"\%")
    return text


def _format_author_list(authors: list[str]) -> str:
    """
    Format an author list into BibTeX 'author' field convention.

    Each name is kept as-is; multiple authors are joined with ' and '.
    """
    return " and ".join(authors)


def _paper_to_bibtex(paper: dict) -> str:
    """Convert a single paper dict to a @article{...} BibTeX entry."""
    cite_key = _make_cite_key(paper)
    authors = _format_author_list(paper.get("authors", ["Unknown"]))
    title = _escape_bibtex(paper.get("title", "Untitled"))
    year = str(paper.get("year", ""))
    abstract = _escape_bibtex(paper.get("abstract", ""))
    url = paper.get("url", "")
    arxiv_id = paper.get("arxiv_id", "")
    journal_ref = paper.get("journal_ref", "")
    doi = paper.get("doi", "")
    categories = ", ".join(paper.get("categories", []))

    # Choose entry type: @article if there's a journal ref, else @misc
    entry_type = "article" if journal_ref else "misc"

    lines = [f"@{entry_type}{{{cite_key},"]
    lines.append(f"  author       = {{{authors}}},")
    lines.append(f"  title        = {{{{{title}}}}},")   # double-braced to preserve case
    lines.append(f"  year         = {{{year}}},")

    if journal_ref:
        lines.append(f"  journal      = {{{_escape_bibtex(journal_ref)}}},")

    lines.append(f"  eprint       = {{{arxiv_id}}},")
    lines.append(f"  archivePrefix = {{arXiv}},")
    lines.append(f"  primaryClass = {{{categories.split(',')[0].strip() if categories else ''}}},")
    lines.append(f"  url          = {{{url}}},")

    if doi:
        lines.append(f"  doi          = {{{doi}}},")

    if abstract:
        # Truncate abstract to 400 chars to keep .bib files manageable
        short_abs = abstract[:400].rstrip() + ("…" if len(abstract) > 400 else "")
        lines.append(f"  abstract     = {{{short_abs}}},")

    lines.append("}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 – Tool 2
# ─────────────────────────────────────────────────────────────────────────────

@tool
def generate_bibtex(paper_metadata: str) -> str:
    """
    Convert a list of paper metadata dictionaries into standard BibTeX entries.

    Use this tool after search_arxiv() to transform structured paper metadata
    into citation-ready BibTeX format for inclusion in a .bib file.

    Args:
        paper_metadata: A JSON string containing a list of paper dicts as
                        returned by the search_arxiv tool. Each dict must have
                        at least: title, authors, year, arxiv_id, url, abstract.
                        You may also pass a single paper dict (not a list).

    Returns:
        A string containing one BibTeX entry per paper, separated by blank
        lines. Returns an error string if parsing fails.

    Example output:
        @misc{Vaswani2017Attention,
          author       = {Vaswani, Ashish and ...},
          title        = {{Attention Is All You Need}},
          year         = {2017},
          eprint       = {1706.03762},
          archivePrefix = {arXiv},
          url          = {https://arxiv.org/abs/1706.03762},
          abstract     = {The dominant sequence...},
        }
    """
    try:
        data = json.loads(paper_metadata)
    except (json.JSONDecodeError, TypeError) as exc:
        return f"[BibTeX error] Could not parse paper_metadata as JSON: {exc}"

    # Accept either a single dict or a list of dicts
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list) or not data:
        return "[BibTeX error] paper_metadata must be a non-empty JSON array of paper objects."

    entries = []
    for paper in data:
        try:
            entries.append(_paper_to_bibtex(paper))
        except Exception as exc:  # noqa: BLE001
            entries.append(f"% [Error generating entry for '{paper.get('title', '?')}': {exc}]")

    return "\n\n".join(entries)
