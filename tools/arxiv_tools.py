"""
tools/arxiv_tools.py – Smolagents @tool wrappers around the arxiv Python package.

Each function is decorated with @tool so the Smolagents CodeAgent can call
them autonomously. The docstrings act as the tool descriptions the LLM reads
to decide when and how to call each tool.

Phase 2 update:
  - search_arxiv() now returns a JSON-serialisable list of paper dicts in
    addition to the human-readable string, so downstream tools
    (generate_bibtex, write_to_workspace) can consume structured data.
"""

from __future__ import annotations

import json
import textwrap
from typing import Optional

import arxiv
from smolagents import tool

from config import config


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int = 800) -> str:
    """Truncate long text with an ellipsis."""
    return textwrap.shorten(text, width=max_chars, placeholder=" …")


def _result_to_dict(result: arxiv.Result) -> dict:
    """Convert an arxiv.Result to a plain dict for JSON serialisation."""
    return {
        "title": result.title,
        "arxiv_id": result.get_short_id(),
        "url": result.entry_id,
        "pdf_url": result.pdf_url,
        "authors": [a.name for a in result.authors],
        "year": result.published.year,
        "published": result.published.strftime("%Y-%m-%d"),
        "abstract": result.summary,
        "categories": result.categories,
        "journal_ref": result.journal_ref or "",
        "doi": result.doi or "",
    }


def _format_paper(result: arxiv.Result, include_abstract: bool = True) -> str:
    """Format a single arxiv.Result into a readable string."""
    authors = ", ".join(a.name for a in result.authors[:5])
    if len(result.authors) > 5:
        authors += f" … (+{len(result.authors) - 5} more)"

    lines = [
        f"**Title**    : {result.title}",
        f"**ArXiv ID** : {result.get_short_id()}",
        f"**Authors**  : {authors}",
        f"**Published**: {result.published.strftime('%Y-%m-%d')}",
        f"**URL**      : {result.entry_id}",
        f"**PDF**      : {result.pdf_url}",
        f"**Categories**: {', '.join(result.categories)}",
    ]
    if include_abstract:
        lines.append(f"**Abstract** : {_truncate(result.summary)}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 Tools (retained, search_arxiv_papers kept for backward compat.)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def search_arxiv_papers(query: str, max_results: int = 5, sort_by: str = "relevance") -> str:
    """
    Search arXiv for academic papers matching a query string (human-readable output).

    Use this for quick exploration or when you only need to display results.
    For structured downstream processing (BibTeX, LaTeX), use search_arxiv() instead.

    Args:
        query: A natural-language or keyword search query.
        max_results: Maximum number of papers to return (1-20). Defaults to 5.
        sort_by: One of 'relevance', 'lastUpdatedDate', or 'submittedDate'.

    Returns:
        A formatted multi-line string listing the found papers.
    """
    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
        "submittedDate": arxiv.SortCriterion.SubmittedDate,
    }
    criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
    max_results = max(1, min(int(max_results), 20))

    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results, sort_by=criterion)
        results = list(client.results(search))

        if not results:
            return f"No papers found for query: '{query}'"

        sections = [f"Found {len(results)} paper(s) for query: '{query}'\n"]
        for i, paper in enumerate(results, 1):
            sections.append(f"── Paper {i} ──────────────────────────────────")
            sections.append(_format_paper(paper))
        return "\n".join(sections)

    except Exception as exc:  # noqa: BLE001
        return f"[arXiv search error] {exc}"


@tool
def get_paper_details(arxiv_id: str) -> str:
    """
    Retrieve full details for a single arXiv paper by its ID.

    Args:
        arxiv_id: The arXiv paper ID (short form like '2303.08774' or full URL).

    Returns:
        A formatted string with full paper metadata and abstract.
    """
    clean_id = arxiv_id.strip().split("/abs/")[-1].split("/pdf/")[-1].replace(".pdf", "")

    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[clean_id])
        results = list(client.results(search))

        if not results:
            return f"Paper with ID '{arxiv_id}' not found on arXiv."

        paper = results[0]
        lines = [
            "── Full Paper Details ──────────────────────────────────────",
            _format_paper(paper, include_abstract=False),
            "",
            f"**Full Abstract**:\n{paper.summary}",
            "",
            f"**Comment** : {paper.comment or 'N/A'}",
            f"**Journal**  : {paper.journal_ref or 'Not published in journal yet'}",
            f"**DOI**      : {paper.doi or 'N/A'}",
        ]
        return "\n".join(lines)

    except Exception as exc:  # noqa: BLE001
        return f"[arXiv details error] {exc}"


@tool
def download_paper_pdf(arxiv_id: str, filename: Optional[str] = None) -> str:
    """
    Download the PDF of an arXiv paper to the local downloads directory.

    Args:
        arxiv_id: The arXiv paper ID (e.g. '2303.08774').
        filename: Optional custom filename (without extension).

    Returns:
        The absolute path to the downloaded PDF, or an error message.
    """
    clean_id = arxiv_id.strip().split("/abs/")[-1].split("/pdf/")[-1].replace(".pdf", "")
    save_name = (filename or clean_id).strip() + ".pdf"
    save_path = config.pdf_download_dir / save_name

    config.pdf_download_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[clean_id])
        results = list(client.results(search))

        if not results:
            return f"Paper '{arxiv_id}' not found on arXiv."

        paper = results[0]
        paper.download_pdf(dirpath=str(config.pdf_download_dir), filename=save_name)
        return f"PDF downloaded successfully → {save_path.resolve()}"

    except Exception as exc:  # noqa: BLE001
        return f"[PDF download error] {exc}"


@tool
def search_arxiv_by_author(author_name: str, max_results: int = 5) -> str:
    """
    Search arXiv for papers written by a specific author.

    Args:
        author_name: Full or partial author name (e.g. 'Yann LeCun').
        max_results: Maximum number of papers to return (1-20). Defaults to 5.

    Returns:
        A formatted list of papers by that author, or an error message.
    """
    max_results = max(1, min(int(max_results), 20))
    query = f"au:{author_name}"

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )
        results = list(client.results(search))

        if not results:
            return f"No papers found for author: '{author_name}'"

        sections = [f"Found {len(results)} paper(s) by '{author_name}':\n"]
        for i, paper in enumerate(results, 1):
            sections.append(f"── Paper {i} ──────────────────────────────────")
            sections.append(_format_paper(paper, include_abstract=False))
        return "\n".join(sections)

    except Exception as exc:  # noqa: BLE001
        return f"[arXiv author search error] {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 – Tool 1: search_arxiv (structured JSON output)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def search_arxiv(query: str, max_results: int = 5) -> str:
    """
    Search arXiv for recent academic papers and return structured JSON metadata.

    Use this tool (instead of search_arxiv_papers) when the results will be
    passed to other tools such as generate_bibtex or write_to_workspace.
    The LLM can use the optimised query to target the most relevant papers.

    Args:
        query: A precise keyword or Boolean search query optimised for arXiv
               (e.g. 'large language models survey', 'vision transformer 2024').
        max_results: Number of papers to retrieve (1-20). Defaults to 5.

    Returns:
        A JSON string – a list of paper objects, each containing:
          title, arxiv_id, url, pdf_url, authors (list), year, published,
          abstract, categories (list), journal_ref, doi.
        Returns an error string if the search fails.

    Example output (abbreviated):
        [
          {
            "title": "Attention Is All You Need",
            "arxiv_id": "1706.03762",
            "authors": ["Vaswani, Ashish", ...],
            "year": 2017,
            "abstract": "The dominant sequence ...",
            ...
          }
        ]
    """
    max_results = max(1, min(int(max_results), 20))

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        results = list(client.results(search))

        if not results:
            return json.dumps([], indent=2)

        papers = [_result_to_dict(r) for r in results]
        return json.dumps(papers, indent=2, ensure_ascii=False)

    except Exception as exc:  # noqa: BLE001
        return f"[arXiv search error] {exc}"
