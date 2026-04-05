# Automated AI Researcher

An agentic AI system that autonomously searches, analyses, and formats academic research papers from arXiv.

## Tech Stack (Phase 1)

| Layer | Technology |
|---|---|
| Agent Framework | [Smolagents](https://github.com/huggingface/smolagents) (HuggingFace) |
| LLM | Google Gemini (via LiteLLM) |
| Data Source | [arxiv](https://pypi.org/project/arxiv/) Python package |

## Project Structure

```
automated-AI-Researcher/
├── .env.example          # Copy to .env and add your API key
├── requirements.txt      # All dependencies
├── config.py             # Typed config loader (reads .env)
├── agent.py              # Smolagents CodeAgent factory
├── main.py               # CLI entry point (interactive + one-shot)
├── tools/
│   ├── __init__.py
│   └── arxiv_tools.py    # @tool-decorated arXiv wrappers
├── downloads/            # Downloaded PDFs (auto-created)
└── reports/              # Saved Markdown research reports (auto-created)
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

```bash
copy .env.example .env        # Windows
# or
cp .env.example .env          # Linux/macOS
```

Open `.env` and set your `GEMINI_API_KEY` (get one free at https://aistudio.google.com/app/apikey).

### 3. Run

**Interactive mode** (REPL):
```bash
python main.py
```

**One-shot mode**:
```bash
python main.py "Find 5 recent papers on diffusion models and summarise their key contributions"
```

## Available Tools (Phase 1)

| Tool | Description |
|---|---|
| `search_arxiv_papers` | Search by topic / keywords |
| `get_paper_details` | Full metadata + abstract for a known arXiv ID |
| `download_paper_pdf` | Download PDF to `./downloads/` |
| `search_arxiv_by_author` | Find papers by a specific researcher |

## Example Queries

```
Find the 5 most influential papers on attention mechanisms published in 2023

Summarise the latest research on multimodal large language models

Get the full details for arXiv paper 2303.08774

Find papers by Ilya Sutskever and summarise their key themes
```

## Roadmap

- **Phase 1** ✅ – Agent framework + arXiv search + Gemini LLM
- **Phase 2** – PDF text extraction & full-paper analysis
- **Phase 3** – Structured Markdown/HTML report formatting with templates
- **Phase 4** – Automated scheduling & email/Slack delivery