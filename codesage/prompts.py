"""
codesage.prompts
~~~~~~~~~~~~~~~~
All system and user prompt templates for CodeSage reviews.
Keeping prompts in one place makes them easy to version and iterate.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System prompt — sets the AI's persona and output contract
# ---------------------------------------------------------------------------

REVIEW_SYSTEM_PROMPT = """\
You are CodeSage, an expert software engineer specializing in code review.
Your job is to analyse the provided source code and produce a structured, \
actionable code review.

Follow this EXACT output format — do not deviate:

## 🎯 Summary
One or two sentences describing what the code does.

## 🐛 Bugs & Issues
List concrete bugs, logic errors, or potential exceptions.
If none, write "✅ No bugs found."

## ⚡ Performance
Identify bottlenecks, inefficient algorithms, or unnecessary allocations.
If none, write "✅ Looks efficient."

## 🔒 Security
Flag injection risks, hardcoded secrets, insecure defaults, or missing input validation.
If none, write "✅ No security concerns."

## 🧹 Code Quality & Style
Comment on readability, naming, duplication (DRY), and adherence to language idioms.

## 💡 Suggestions
Numbered list of prioritised, actionable improvements. Include short code snippets where helpful.

## ⭐ Overall Score
Rate the code from 1–10 with a brief justification.

Be direct, constructive, and specific. Avoid generic advice. \
Focus on what matters most for this particular snippet.
"""


# ---------------------------------------------------------------------------
# User prompt builders
# ---------------------------------------------------------------------------


def build_review_prompt(
    code: str,
    language: str,
    filename: str = "",
    focus: str = "",
) -> str:
    """Build the user-facing prompt for a code review request.

    Args:
        code: The source code to review.
        language: Programming language (e.g., 'Python', 'JavaScript').
        filename: Optional filename for context.
        focus: Optional specific area to focus on (e.g., 'security').

    Returns:
        Formatted prompt string.
    """
    file_context = f"**File:** `{filename}`\n" if filename else ""
    focus_context = (
        f"\n**Focus area:** Please pay extra attention to **{focus}**.\n"
        if focus
        else ""
    )

    return (
        f"{file_context}"
        f"**Language:** {language}\n"
        f"{focus_context}"
        f"\nPlease review the following {language} code:\n\n"
        f"```{language.lower()}\n{code}\n```"
    )


def build_explain_prompt(code: str, language: str) -> str:
    """Build a prompt asking the model to explain what a code snippet does.

    Args:
        code: The source code snippet.
        language: Programming language.

    Returns:
        Formatted prompt string.
    """
    return (
        f"Explain clearly what the following {language} code does, "
        f"step by step, as if teaching a junior developer:\n\n"
        f"```{language.lower()}\n{code}\n```"
    )


def build_fix_prompt(code: str, language: str, issue: str) -> str:
    """Build a prompt asking the model to fix a specific issue in code.

    Args:
        code: The original source code.
        language: Programming language.
        issue: Description of the problem to fix.

    Returns:
        Formatted prompt string.
    """
    return (
        f"Fix the following issue in this {language} code:\n"
        f"**Issue:** {issue}\n\n"
        f"```{language.lower()}\n{code}\n```\n\n"
        "Respond with:\n"
        "1. A brief explanation of the fix.\n"
        "2. The corrected code in a fenced code block."
    )
