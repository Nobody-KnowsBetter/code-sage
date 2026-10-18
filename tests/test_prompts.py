"""
tests/test_prompts.py
~~~~~~~~~~~~~~~~~~~~~
Unit tests for codesage.prompts (pure string logic — no mocking needed).
"""

from codesage.prompts import (
    REVIEW_SYSTEM_PROMPT,
    build_explain_prompt,
    build_fix_prompt,
    build_review_prompt,
)


def test_review_system_prompt_has_sections():
    sections = [
        "Summary",
        "Bugs",
        "Performance",
        "Security",
        "Overall Score",
    ]
    for section in sections:
        assert section in REVIEW_SYSTEM_PROMPT


def test_build_review_prompt_includes_language():
    prompt = build_review_prompt("x = 1", "Python")
    assert "Python" in prompt


def test_build_review_prompt_includes_code():
    code = "def foo(): pass"
    prompt = build_review_prompt(code, "Python")
    assert code in prompt


def test_build_review_prompt_with_filename():
    prompt = build_review_prompt("x=1", "Python", filename="main.py")
    assert "main.py" in prompt


def test_build_review_prompt_with_focus():
    prompt = build_review_prompt("x=1", "Python", focus="security")
    assert "security" in prompt


def test_build_explain_prompt():
    prompt = build_explain_prompt("SELECT * FROM users", "SQL")
    assert "SQL" in prompt
    assert "SELECT" in prompt


def test_build_fix_prompt():
    prompt = build_fix_prompt("x / 0", "Python", "Division by zero")
    assert "Division by zero" in prompt
    assert "Python" in prompt
    assert "x / 0" in prompt
