"""
codesage.cli
~~~~~~~~~~~~
Typer-based CLI entrypoint for CodeSage.

Commands:
  review   — Review a source file or piped snippet
  explain  — Explain what a file does in plain English
  fix      — Suggest a fix for a described issue
  models   — List locally available Ollama models
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.text import Text

from codesage import __version__
from codesage.config import config
from codesage.logger import get_logger
from codesage.ollama_client import OllamaClient, OllamaError
from codesage.output import (
    print_error,
    print_header,
    print_model_table,
    print_review,
)
from codesage.reviewer import CodeReviewer, detect_language

app = typer.Typer(
    name="codesage",
    help="🧙 CodeSage — Local AI Code Reviewer powered by Ollama open-weight models.",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Version callback
# ---------------------------------------------------------------------------


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"CodeSage v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show CodeSage version and exit.",
    ),
) -> None:
    """CodeSage — Local AI Code Reviewer powered by Ollama."""


# ---------------------------------------------------------------------------
# `review` command
# ---------------------------------------------------------------------------


@app.command()
def review(
    file: Optional[Path] = typer.Argument(
        None,
        help="Path to the source file to review. Omit to read from stdin.",
        show_default=False,
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Ollama model override (e.g. codellama)."
    ),
    focus: str = typer.Option(
        "", "--focus", "-f", help="Area to focus on: security | performance | style."
    ),
    language: str = typer.Option(
        "", "--language", "-l", help="Language override (auto-detected from extension)."
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Wait for full response instead of streaming."
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format override: rich | plain | json.",
    ),
) -> None:
    """[bold cyan]Review[/bold cyan] a source file or piped code snippet with AI.

    \b
    Examples:
      codesage review main.py
      codesage review app.js --focus security --model codellama
      cat script.sh | codesage review --language Bash
    """
    # Output format override
    if output:
        config.output_format = output  # type: ignore[assignment]

    effective_model = model or config.model

    # Resolve code source
    if file:
        try:
            from codesage.reviewer import read_file_safely
            code = read_file_safely(file)
            lang = language or detect_language(file)
            fname = file.name
        except (FileNotFoundError, ValueError) as exc:
            print_error(str(exc))
            raise typer.Exit(1)
    elif not sys.stdin.isatty():
        code = sys.stdin.read()
        lang = language or "Unknown"
        fname = "<stdin>"
    else:
        print_error("Provide a file path or pipe code via stdin.")
        raise typer.Exit(1)

    print_header(fname, effective_model, lang)

    reviewer = CodeReviewer(model=effective_model)

    try:
        if no_stream or config.output_format in ("json", "plain"):
            result = reviewer.review_snippet(code, lang, focus=focus)
            print_review(result, filename=fname)
        else:
            # Stream tokens live into the terminal
            # Use a list (mutable) so the nested callback can safely append
            buffer: list[str] = []

            def on_token(token: str) -> None:
                buffer.append(token)

            with Live("", refresh_per_second=15, console=console) as live:
                def _refresh_token(token: str) -> None:
                    on_token(token)
                    live.update(Text("".join(buffer)))

                result = reviewer.review_snippet(
                    code, lang, focus=focus, stream_callback=_refresh_token
                )

            # Re-render the final output as proper Rich markdown
            console.clear()
            print_header(fname, effective_model, lang)
            print_review(result, filename=fname)

    except OllamaError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Review cancelled.[/yellow]")
        raise typer.Exit(130)


# ---------------------------------------------------------------------------
# `explain` command
# ---------------------------------------------------------------------------


@app.command()
def explain(
    file: Path = typer.Argument(..., help="Source file to explain."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model override."),
) -> None:
    """[bold cyan]Explain[/bold cyan] what a source file does in plain English.

    \b
    Example:
      codesage explain complex_algorithm.py
    """
    reviewer = CodeReviewer(model=model or config.model)
    lang = detect_language(file)
    print_header(file.name, model or config.model, lang)

    try:
        result = reviewer.explain_file(file)
        print_review(result, filename=file.name)
    except (FileNotFoundError, ValueError, OllamaError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# `fix` command
# ---------------------------------------------------------------------------


@app.command()
def fix(
    file: Path = typer.Argument(..., help="Source file with the issue."),
    issue: str = typer.Option(
        ..., "--issue", "-i", help='Describe the problem, e.g. "Null pointer in line 42".'
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model override."),
) -> None:
    """[bold cyan]Fix[/bold cyan] a specific issue in a source file using AI.

    \b
    Example:
      codesage fix buggy.py --issue "Division by zero when input is 0"
    """
    reviewer = CodeReviewer(model=model or config.model)
    lang = detect_language(file)
    print_header(file.name, model or config.model, lang)

    try:
        result = reviewer.suggest_fix(file, issue)
        print_review(result, filename=file.name)
    except (FileNotFoundError, ValueError, OllamaError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# `models` command
# ---------------------------------------------------------------------------


@app.command()
def models() -> None:
    """[bold cyan]List[/bold cyan] all locally available Ollama models."""

    async def _list() -> list[str]:
        async with OllamaClient() as client:
            return await client.list_models()

    try:
        available = asyncio.run(_list())
        print_model_table(available)
    except OllamaError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
