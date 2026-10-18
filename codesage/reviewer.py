"""
codesage.reviewer
~~~~~~~~~~~~~~~~~
Core review orchestration logic.
Reads code, detects language, calls the LLM, and returns structured results.
"""

from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path
from typing import Callable

from codesage.logger import get_logger
from codesage.ollama_client import OllamaClient, OllamaError
from codesage.prompts import (
    REVIEW_SYSTEM_PROMPT,
    build_explain_prompt,
    build_fix_prompt,
    build_review_prompt,
)

logger = get_logger(__name__)

# Extension → language display name mapping
_EXT_TO_LANG: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".sh": "Bash",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".md": "Markdown",
}


def detect_language(path: Path) -> str:
    """Infer the programming language from the file extension.

    Args:
        path: Path to the source file.

    Returns:
        Human-readable language name (e.g. 'Python'), or 'Unknown'.
    """
    return _EXT_TO_LANG.get(path.suffix.lower(), "Unknown")


def read_file_safely(path: Path, max_bytes: int = 100_000) -> str:
    """Read a source file, enforcing a size limit to avoid huge prompts.

    Args:
        path: File to read.
        max_bytes: Maximum file size in bytes (default 100 KB).

    Returns:
        File contents as a string.

    Raises:
        ValueError: If the file is too large or cannot be read.
        FileNotFoundError: If the path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(
            f"File is {size:,} bytes — exceeds the {max_bytes:,} byte limit. "
            "Review a smaller excerpt or increase MAX_BYTES."
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            f"File '{path.name}' is not valid UTF-8. "
            "CodeSage only supports text source files."
        )


class CodeReviewer:
    """High-level orchestrator that drives the AI review pipeline.

    Example::

        reviewer = CodeReviewer()
        result = asyncio.run(reviewer.review_file(Path("main.py")))
        print(result)
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def review_file(
        self,
        path: Path,
        focus: str = "",
        stream_callback: Callable[[str], None] | None = None,
    ) -> str:
        """Synchronous wrapper — reviews a file and returns the LLM output.

        Args:
            path: Path to the source file.
            focus: Optional area to emphasise (e.g. 'security', 'performance').
            stream_callback: If provided, called with each streamed token.

        Returns:
            Full review text from the model.
        """
        return asyncio.run(self._async_review_file(path, focus, stream_callback))

    def review_snippet(
        self,
        code: str,
        language: str = "Python",
        focus: str = "",
        stream_callback: Callable[[str], None] | None = None,
    ) -> str:
        """Synchronous wrapper — reviews a code string directly.

        Args:
            code: Source code text.
            language: Language name for prompt context.
            focus: Optional focus area.
            stream_callback: If provided, called with each streamed token.

        Returns:
            Full review text.
        """
        return asyncio.run(
            self._async_review_snippet(code, language, focus, stream_callback)
        )

    def explain_file(self, path: Path) -> str:
        """Explain what a file does in plain English.

        Args:
            path: Path to the source file.

        Returns:
            Explanation text from the model.
        """
        return asyncio.run(self._async_explain_file(path))

    def suggest_fix(self, path: Path, issue: str) -> str:
        """Ask the model to fix a specific issue in a file.

        Args:
            path: Path to the source file.
            issue: Short description of the problem.

        Returns:
            Fixed code and explanation from the model.
        """
        return asyncio.run(self._async_suggest_fix(path, issue))

    # ------------------------------------------------------------------
    # Private async implementations
    # ------------------------------------------------------------------

    async def _async_review_file(
        self,
        path: Path,
        focus: str,
        stream_callback: Callable[[str], None] | None,
    ) -> str:
        code = read_file_safely(path)
        language = detect_language(path)
        logger.info(
            f"Reviewing [bold]{path.name}[/] as [cyan]{language}[/] "
            f"using model [magenta]{self.model or 'default'}[/]"
        )
        prompt = build_review_prompt(code, language, filename=path.name, focus=focus)
        return await self._call_llm(prompt, REVIEW_SYSTEM_PROMPT, stream_callback)

    async def _async_review_snippet(
        self,
        code: str,
        language: str,
        focus: str,
        stream_callback: Callable[[str], None] | None,
    ) -> str:
        prompt = build_review_prompt(code, language, focus=focus)
        return await self._call_llm(prompt, REVIEW_SYSTEM_PROMPT, stream_callback)

    async def _async_explain_file(self, path: Path) -> str:
        code = read_file_safely(path)
        language = detect_language(path)
        prompt = build_explain_prompt(code, language)
        return await self._call_llm(prompt, system="")

    async def _async_suggest_fix(self, path: Path, issue: str) -> str:
        code = read_file_safely(path)
        language = detect_language(path)
        prompt = build_fix_prompt(code, language, issue)
        return await self._call_llm(prompt, system="")

    async def _call_llm(
        self,
        prompt: str,
        system: str,
        stream_callback: Callable[[str], None] | None = None,
    ) -> str:
        """Send prompt to Ollama and return full response.

        If stream_callback is provided, tokens are yielded as they arrive.
        """
        async with OllamaClient(model=self.model) as client:
            if stream_callback is not None:
                chunks: list[str] = []
                async for token in client.stream(prompt, system=system):
                    stream_callback(token)
                    chunks.append(token)
                return "".join(chunks)
            else:
                return await client.generate(prompt, system=system)
