"""
tests/test_reviewer.py
~~~~~~~~~~~~~~~~~~~~~~
Unit tests for codesage.reviewer (file I/O and language detection).
Ollama calls are mocked — no live server needed.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codesage.reviewer import CodeReviewer, detect_language, read_file_safely


# ---------------------------------------------------------------------------
# detect_language tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("main.py", "Python"),
        ("app.js", "JavaScript"),
        ("server.ts", "TypeScript"),
        ("handler.go", "Go"),
        ("lib.rs", "Rust"),
        ("Main.java", "Java"),
        ("unknown.xyz", "Unknown"),
        ("Makefile", "Unknown"),
    ],
)
def test_detect_language(filename: str, expected: str):
    assert detect_language(Path(filename)) == expected


# ---------------------------------------------------------------------------
# read_file_safely tests
# ---------------------------------------------------------------------------


def test_read_file_safely_ok():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("print('hello')")
        path = Path(f.name)
    content = read_file_safely(path)
    assert content == "print('hello')"
    path.unlink()


def test_read_file_safely_not_found():
    with pytest.raises(FileNotFoundError):
        read_file_safely(Path("/nonexistent/path/script.py"))


def test_read_file_safely_too_large():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="wb", delete=False) as f:
        # Write 200 KB of data — above the 100 KB default limit
        f.write(b"x" * 200_000)
        path = Path(f.name)
    with pytest.raises(ValueError, match="exceeds"):
        read_file_safely(path)
    path.unlink()


def test_read_file_safely_directory():
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(ValueError, match="not a file"):
            read_file_safely(Path(d))


# ---------------------------------------------------------------------------
# CodeReviewer tests (mocked LLM)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_ollama(monkeypatch):
    """Patch OllamaClient so no real HTTP calls are made."""
    fake_response = "## 🎯 Summary\nThis code prints hello.\n\n## ⭐ Overall Score\n8/10"

    async def fake_generate(self, prompt, system=""):
        return fake_response

    monkeypatch.setattr(
        "codesage.reviewer.OllamaClient.generate",
        fake_generate,
    )
    monkeypatch.setattr(
        "codesage.reviewer.OllamaClient._ensure_model_available",
        AsyncMock(return_value=None),
    )
    return fake_response


def test_review_snippet_returns_text(mock_ollama):
    reviewer = CodeReviewer()
    result = reviewer.review_snippet("print('hello')", "Python")
    assert "Summary" in result or len(result) > 0


def test_review_file_ok(mock_ollama):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def add(a, b): return a + b")
        path = Path(f.name)

    reviewer = CodeReviewer()
    result = reviewer.review_file(path)
    assert isinstance(result, str)
    assert len(result) > 0
    path.unlink()


def test_review_file_missing(mock_ollama):
    reviewer = CodeReviewer()
    with pytest.raises(FileNotFoundError):
        reviewer.review_file(Path("/no/such/file.py"))
