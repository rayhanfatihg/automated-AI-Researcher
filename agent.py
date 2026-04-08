"""
agent.py – Builds and returns the Smolagents CodeAgent powered by Google Gemini.

Phase 1: arXiv search + exploration tools.
Phase 2: structured search → BibTeX → LaTeX → write to workspace pipeline.
"""

from __future__ import annotations

import os

from smolagents import CodeAgent, LiteLLMModel, LogLevel

from config import config
from tools import (
    # Phase 1
    download_paper_pdf,
    get_paper_details,
    search_arxiv_by_author,
    search_arxiv_papers,
    # Phase 2
    generate_bibtex,
    search_arxiv,
    write_to_workspace,
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom instructions
# ─────────────────────────────────────────────────────────────────────────────
# In smolagents >=1.14, `system_prompt` is a read-only property generated from
# the agent's default prompt_templates.  Custom guidance is injected via the
# `instructions` kwarg, which is appended to that default system prompt.

AGENT_INSTRUCTIONS = """
You are an expert AI Research Assistant specialising in finding, analysing, and
summarising academic papers from arXiv. You can also produce publication-ready
LaTeX literature reviews with proper BibTeX citations.

## Your capabilities
- Search arXiv for papers by topic, keyword, or author.
- Retrieve full metadata and abstracts for specific papers.
- Download PDFs for in-depth analysis.
- Generate BibTeX citation entries from paper metadata.
- Write a complete LaTeX literature review + BibTeX file to the local workspace.
- Produce well-structured Markdown research reports.

## Behaviour guidelines
1. **Optimise your queries**: Before calling search_arxiv(), craft a precise
   Boolean or keyword query to maximise relevance.
2. **Be thorough**: Search for multiple relevant papers before synthesising.
3. **Cite everything**: Always include arXiv IDs, titles, and URLs.
4. **Format LaTeX correctly**: When writing main.tex, use proper LaTeX commands,
   packages, and \\cite{key} references that match the BibTeX keys you generated.
5. **Acknowledge uncertainty**: If information is not available, say so.

## Standard literature-review workflow
When asked to write a literature review or research report:

1. Call search_arxiv(query, max_results) -> get JSON paper list.
2. Call generate_bibtex(paper_metadata) -> get BibTeX string.
3. Draft the LaTeX document (see template below).
4. Call write_to_workspace(tex_content, bib_content) -> save files.

## LaTeX document template
```
\\documentclass[12pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{hyperref}
\\usepackage{natbib}
\\usepackage{geometry}
\\geometry{margin=2.5cm}

\\title{Literature Review: <Topic>}
\\author{AI Research Assistant}
\\date{\\today}

\\begin{document}
\\maketitle
\\tableofcontents

\\section{Introduction}
<Overview of topic and review scope>

\\section{Key Papers}
\\subsection{<Paper 1 Title>}
<Summary> \\cite{CiteKey1}

\\section{Synthesis and Trends}
<Cross-paper analysis>

\\section{Conclusion}
<Summary and future directions>

\\bibliographystyle{plainnat}
\\bibliography{Referensi}
\\end{document}
```
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

def build_agent(verbose: bool = True) -> CodeAgent:
    """
    Construct and return a Smolagents CodeAgent backed by Google Gemini.

    Args:
        verbose: If True, the agent will print its reasoning steps to stdout.

    Returns:
        A fully configured CodeAgent ready to receive tasks.
    """
    config.validate()
    config.ensure_dirs()

    # Expose the API key to LiteLLM via the standard env var
    os.environ["GEMINI_API_KEY"] = config.gemini_api_key

    model = LiteLLMModel(
        model_id=config.gemini_model,
        # LiteLLM passes the key automatically when GEMINI_API_KEY is set,
        # but we can also pass it explicitly for clarity:
        api_key=config.gemini_api_key,
    )

    agent = CodeAgent(
        tools=[
            # Phase 1 – exploration
            search_arxiv_papers,
            get_paper_details,
            download_paper_pdf,
            search_arxiv_by_author,
            # Phase 2 – structured pipeline
            search_arxiv,
            generate_bibtex,
            write_to_workspace,
        ],
        model=model,
        instructions=AGENT_INSTRUCTIONS,           # new API: appended to default system prompt
        verbosity_level=LogLevel.INFO if verbose else LogLevel.ERROR,  # new API: LogLevel enum
        max_steps=20,   # Phase 2 pipeline needs more steps (search->bibtex->write)
    )

    return agent
