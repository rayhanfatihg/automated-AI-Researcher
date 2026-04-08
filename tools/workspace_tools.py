"""
tools/workspace_tools.py – Tool 3 for Phase 2: writing outputs to local disk.

Saves the agent's final products to the workspace:
  - main.tex   → the LaTeX literature review document
  - Referensi.bib → the BibTeX reference file

Uses only Python builtins (os, open) as specified in the project requirements.
"""

from __future__ import annotations

import os
from pathlib import Path

from smolagents import tool

from config import config


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 – Tool 3
# ─────────────────────────────────────────────────────────────────────────────

@tool
def write_to_workspace(tex_content: str, bib_content: str) -> str:
    """
    Write the LaTeX literature review and BibTeX references to the local workspace.

    Saves two files to the configured reports directory:
      - main.tex      : The full LaTeX literature review document.
      - Referensi.bib : The BibTeX citation database.

    Call this tool as the final step once you have:
      1. Collected paper metadata with search_arxiv().
      2. Generated BibTeX entries with generate_bibtex().
      3. Written the LaTeX document content (main.tex body).

    Args:
        tex_content: Complete LaTeX source for the literature review.
                     Should include \\documentclass, \\begin{document}, all
                     sections, \\bibliography{Referensi}, and \\end{document}.
        bib_content: BibTeX source as returned by generate_bibtex(). Contains
                     one or more @article / @misc entries.

    Returns:
        A success message listing the absolute paths of both saved files,
        or an error message describing what went wrong.

    File locations (configurable via .env):
        <REPORTS_DIR>/main.tex
        <REPORTS_DIR>/Referensi.bib
    """
    # Ensure the output directory exists (uses os.makedirs per requirements)
    output_dir = str(config.reports_dir)
    os.makedirs(output_dir, exist_ok=True)

    tex_path = os.path.join(output_dir, "main.tex")
    bib_path = os.path.join(output_dir, "Referensi.bib")

    errors: list[str] = []

    # ── Write main.tex ────────────────────────────────────────────────────────
    try:
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)
    except OSError as exc:
        errors.append(f"Failed to write main.tex: {exc}")

    # ── Write Referensi.bib ───────────────────────────────────────────────────
    try:
        with open(bib_path, "w", encoding="utf-8") as f:
            f.write(bib_content)
    except OSError as exc:
        errors.append(f"Failed to write Referensi.bib: {exc}")

    if errors:
        return "[write_to_workspace errors]\n" + "\n".join(errors)

    tex_abs = str(Path(tex_path).resolve())
    bib_abs = str(Path(bib_path).resolve())

    return (
        "Files saved successfully!\n"
        f"  LaTeX document : {tex_abs}\n"
        f"  BibTeX refs    : {bib_abs}\n\n"
        "You can now compile the PDF with:\n"
        "  pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex"
    )
