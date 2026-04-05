"""
agent.py – Builds and returns the Smolagents CodeAgent powered by Google Gemini.

The agent is given all arXiv tools and a system prompt that instructs it to
act as an autonomous AI research assistant.
"""

from __future__ import annotations

import os

from smolagents import CodeAgent, LiteLLMModel

from config import config
from tools import (
    download_paper_pdf,
    get_paper_details,
    search_arxiv_by_author,
    search_arxiv_papers,
)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert AI Research Assistant specialising in finding, analysing, and
summarising academic papers from arXiv.

## Your capabilities
- Search arXiv for papers by topic, keyword, or author.
- Retrieve full metadata and abstracts for specific papers.
- Download PDFs for in-depth analysis.
- Produce well-structured Markdown research reports.

## Behaviour guidelines
1. **Be thorough**: When asked to research a topic, search for multiple relevant
   papers before synthesising your findings.
2. **Cite everything**: Always include arXiv IDs, titles, and URLs when
   mentioning papers.
3. **Format output as Markdown**: Use headings, bullet points, and code blocks
   to make reports easy to read.
4. **Summarise clearly**: Explain complex concepts in plain language with
   concrete examples where possible.
5. **Acknowledge uncertainty**: If a paper's content is not fully available,
   say so explicitly rather than guessing.

## Output format for research reports
Use the following structure when producing multi-paper summaries:

```
# Research Report: <Topic>

## Executive Summary
<2–3 sentence overview>

## Key Papers
### 1. <Paper Title>
- **ID**: <arXiv ID>
- **Authors**: …
- **Published**: …
- **Summary**: …
- **Key contributions**: …

## Synthesis & Trends
<Cross-paper analysis>

## Recommended Next Steps
<What to read or explore next>
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
            search_arxiv_papers,
            get_paper_details,
            download_paper_pdf,
            search_arxiv_by_author,
        ],
        model=model,
        system_prompt=SYSTEM_PROMPT,
        verbosity_level=1 if verbose else 0,
        max_steps=15,        # Safety guard: stop after 15 reasoning steps
    )

    return agent
