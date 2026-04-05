"""
main.py – Entry point for the Automated AI Researcher (Phase 1).

Run interactively:
    python main.py

Or pass a one-shot query via CLI:
    python main.py "Find 5 recent papers on vision transformers and summarise them"
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from agent import build_agent

console = Console()

BANNER = """
╔══════════════════════════════════════════════════════════╗
║        🤖  Automated AI Researcher  –  Phase 1          ║
║   Smolagents  ·  Google Gemini  ·  arXiv                ║
╚══════════════════════════════════════════════════════════╝
"""


def save_report(content: str, query: str) -> Path:
    """Save the agent's response as a Markdown report."""
    from config import config
    config.ensure_dirs()

    # Sanitise query for filename
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)[:60]
    filename = f"{safe.strip().replace(' ', '_')}.md"
    path = config.reports_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def run_once(query: str) -> None:
    """Run the agent on a single query and save the report."""
    console.print(Panel(f"[bold cyan]Query:[/] {query}", expand=False))

    agent = build_agent(verbose=True)

    console.rule("[bold green]Agent is thinking…")
    result = agent.run(query)

    console.rule("[bold green]Result")
    console.print(result)

    report_path = save_report(str(result), query)
    console.print(f"\n[dim]Report saved → {report_path}[/dim]")


def run_interactive() -> None:
    """Launch an interactive REPL-style session."""
    console.print(Text(BANNER, style="bold magenta"))
    console.print(
        "[dim]Type your research query and press Enter. "
        "Type [bold]exit[/bold] or [bold]quit[/bold] to stop.[/dim]\n"
    )

    agent = build_agent(verbose=True)

    while True:
        try:
            query = Prompt.ask("[bold yellow]Research query[/bold yellow]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting.[/bold red]")
            break

        if query.lower() in {"exit", "quit", "q"}:
            console.print("[bold red]Goodbye![/bold red]")
            break
        if not query:
            continue

        console.rule("[bold green]Agent is thinking…")
        try:
            result = agent.run(query)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[bold red]Error:[/bold red] {exc}")
            continue

        console.rule("[bold green]Result")
        console.print(result)

        report_path = save_report(str(result), query)
        console.print(f"\n[dim]Report saved → {report_path}[/dim]")
        console.print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # One-shot mode: query provided as CLI argument
        run_once(" ".join(sys.argv[1:]))
    else:
        # Interactive REPL mode
        run_interactive()
