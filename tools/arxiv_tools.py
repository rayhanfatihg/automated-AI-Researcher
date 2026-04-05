"""
tools/arxiv_tools.py – Smolagents @tool wrappers around the arxiv Python package.

Each function is decorated with @tool so the Smolagents CodeAgent can call
them autonomously. The docstrings act as the tool descriptions the LLM reads
to decide when and how to call each tool.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Optional

import arxiv
from smolagents import tool

from config import config


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int = 800) -> str:
    """Truncate long text with an ellipsis."""
    return textwrap.shorten(text, width=max_chars, placeholder=" …")


def _format_paper(result: arxiv.Result, include_abstract: bool = True) -> str:
    """Format a single arxiv.Result into a readable string."""
    authors = ", ".join(a.name for a in result.authors[:5])
    if len(result.authors) > 5:
        authors += f" … (+{len(result.authors) - 5} more)"

    lines = [
        f"**Title**   : {result.title}",
        f"**ArXiv ID**: {result.get_short_id()}",
        f"**Authors** : {authors}",
        f"**Published**: {result.published.strftime('%Y-%m-%d')}",
        f"**URL**     : {result.entry_id}",
        f"**PDF**     : {result.pdf_url}",
        f"**Categories**: {', '.join(result.categories)}",
    ]
    if include_abstract:
        lines.append(f"**Abstract** : {_truncate(result.summary)}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────────────────────────────────────

@tool
def search_arxiv_papers(query: str, max_results: int = 5, sort_by: str = "relevance") -> str:
    """
    Search arXiv for academic papers matching a query string.

    Use this tool whenever the user asks to find, discover, or look up research
    papers on a topic. Returns titles, IDs, authors, publication dates, and
    truncated abstracts for each result.

    Args:
        query: A natural-language or keyword search query (e.g. 'diffusion models
               for image generation', 'transformer architecture survey 2024').
        max_results: Maximum number of papers to return (1–20). Defaults to 5.
        sort_by: Ranking criterion – one of 'relevance', 'lastUpdatedDate',
                 or 'submittedDate'. Defaults to 'relevance'.

    Returns:
        A formatted multi-line string listing the found papers, or an error
        message if the search fails.
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
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=criterion,
        )
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

    Use this tool when you already know the arXiv ID of a paper (e.g. '2303.08774'
    or 'https://arxiv.org/abs/2303.08774') and want to fetch the complete
    metadata including the full abstract.

    Args:
        arxiv_id: The arXiv paper ID (short form like '2303.08774' or full URL).

    Returns:
        A formatted string with full paper metadata and abstract, or an error
        message if the paper is not found.
    """
    # Strip URL prefix if given full link
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

    Use this tool when the user wants to read, analyse, or extract text from
    the full body of a paper (not just the abstract). After downloading, you
    can use other tools to extract and summarise the text.

    Args:
        arxiv_id: The arXiv paper ID (e.g. '2303.08774').
        filename:  Optional custom filename (without extension). Defaults to
                   the arXiv ID.

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

    Use this tool when the user asks for papers by a particular researcher or
    wants to explore an author's publication history.

    Args:
        author_name: Full or partial author name (e.g. 'Yann LeCun',
                     'Geoffrey Hinton').
        max_results: Maximum number of papers to return (1–20). Defaults to 5.

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
