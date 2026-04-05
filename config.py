"""
config.py – Centralised configuration loader for the Automated AI Researcher.

Reads values from a .env file (or environment variables) and exposes them
as a typed Config dataclass so the rest of the codebase never touches
os.environ directly.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one directory above this file)
_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    # ── LLM ──────────────────────────────────────────────────────────────────
    gemini_api_key: str = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY", "")
    )
    gemini_model: str = field(
        default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini/gemini-2.0-flash")
    )

    # ── arXiv ────────────────────────────────────────────────────────────────
    arxiv_max_results: int = field(
        default_factory=lambda: int(os.environ.get("ARXIV_MAX_RESULTS", "5"))
    )

    # ── Paths ─────────────────────────────────────────────────────────────────
    pdf_download_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("PDF_DOWNLOAD_DIR", "./downloads"))
    )
    reports_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("REPORTS_DIR", "./reports"))
    )

    def validate(self) -> None:
        """Raise ValueError for any missing critical configuration."""
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )

    def ensure_dirs(self) -> None:
        """Create output directories if they don't exist."""
        self.pdf_download_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


# Singleton — import this everywhere
config = Config()
