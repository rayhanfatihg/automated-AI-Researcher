"""
tools/__init__.py – Export all agent tools from this package.

Phase 1 tools: search_arxiv_papers, search_arxiv_by_author,
               get_paper_details, download_paper_pdf
Phase 2 tools: search_arxiv (JSON), generate_bibtex, write_to_workspace
"""

from .arxiv_tools import (
    # Phase 1 (kept for backward compat.)
    download_paper_pdf,
    get_paper_details,
    search_arxiv_by_author,
    search_arxiv_papers,
    # Phase 2 – structured output
    search_arxiv,
)
from .bibtex_tools import generate_bibtex
from .workspace_tools import write_to_workspace

__all__ = [
    # Phase 1
    "search_arxiv_papers",
    "get_paper_details",
    "download_paper_pdf",
    "search_arxiv_by_author",
    # Phase 2
    "search_arxiv",
    "generate_bibtex",
    "write_to_workspace",
]
