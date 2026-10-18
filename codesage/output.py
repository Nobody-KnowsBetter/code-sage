"""
codesage.output
~~~~~~~~~~~~~~~
Rich-powered output rendering for terminal display.
Supports rich, plain text, and JSON output modes.
"""

from __future__ import annotations

import json
import sys

from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from codesage.config import config

console = Console()
err_console = Console(stderr=True)


def print_header(filename: str, model: str, language: str) -> None:
    """Print a decorative header before the review output.

    Args:
        filename: Name of the reviewed file.
        model: Model used for the review.
        language: Detected programming language.
    """
    if config.output_format == "plain":
        print(f"\n=== CodeSage Review: {filename} ===\n")
        return

    if config.output_format == "json":
        return  # Header is skipped for JSON output

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]🔍 CodeSage Review[/bold cyan]\n"
            f"[dim]File:[/dim] [bold]{filename or 'snippet'}[/bold]  "
            f"[dim]Language:[/dim] [cyan]{language}[/cyan]  "
            f"[dim]Model:[/dim] [magenta]{model}[/magenta]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )
    console.print()


def print_review(review_text: str, filename: str = "", as_json: bool = False) -> None:
    """Render and print the model's review output.

    Args:
        review_text: Raw markdown text from the model.
        filename: Source filename (used in JSON output).
        as_json: Emit JSON instead of rendered markdown.
    """
    fmt = config.output_format

    if fmt == "json" or as_json:
        output = {"filename": filename, "review": review_text}
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    if fmt == "plain":
        print(review_text)
        return

    # Rich rendering
    console.print(Markdown(review_text))
    console.print()
    console.print(Rule("[dim]End of CodeSage Review[/dim]", style="dim"))
    console.print()


def print_error(message: str) -> None:
    """Print an error message to stderr.

    Args:
        message: Human-readable error description.
    """
    err_console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Success description.
    """
    if config.output_format == "rich":
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        print(f"OK: {message}")


def print_model_table(models: list[str]) -> None:
    """Print a formatted table of available Ollama models.

    Args:
        models: List of model name strings.
    """
    if config.output_format == "json":
        print(json.dumps({"models": models}))
        return

    if not models:
        console.print("[yellow]No models found. Pull one with: ollama pull gemma3[/yellow]")
        return

    table = Table(title="Available Local Models", border_style="blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model Name", style="cyan bold")
    table.add_column("Notes", style="dim")

    recommended = {"gemma3", "codellama", "deepseek-coder", "phi4", "llama3"}
    for i, name in enumerate(models, 1):
        base = name.split(":")[0]
        note = "⭐ recommended for code" if base in recommended else ""
        table.add_row(str(i), name, note)

    console.print(table)
