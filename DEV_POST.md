---
title: "I Built a Local AI Code Reviewer That Never Sends Your Code to the Cloud 🧙"
published: false
description: "CodeSage: a fully offline, open-weight AI code review CLI built with Ollama, Gemma 3, and Python — created for the Hacktoberfest DEV Challenge."
tags: hf26challenge, ai, opensource, hacktoberfest
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200
canonical_url: null
---

# I Built a Local AI Code Reviewer That Never Sends Your Code to the Cloud 🧙

**tl;dr** — I built **CodeSage**: a CLI tool that reviews your code using open-weight AI models running 100% locally via Ollama. No API keys. No data sent to any server. Completely private. And it's exactly the kind of thing freelance developers would pay for.

**GitHub Repository:** [https://github.com/Nobody-KnowsBetter/code-sage](https://github.com/Nobody-KnowsBetter/code-sage)

---

## Why This Is a Side Hustle That Works

Every freelance developer has been in this situation: you write code, you *know* something looks a bit off, but you don't have a senior dev to ping right now. You could use GitHub Copilot's review feature or paste your code into ChatGPT... but wait — that means:

1. **Your client's proprietary code leaves your machine** and lands on someone else's servers.
2. You're **paying per token** for every review — and those costs add up.
3. You're **offline on a flight** and suddenly stuck.

For freelancers and small consultancies, this is a real problem. Client NDAs don't mix with third-party AI APIs. And paying $20/month for an AI review service eats into margins.

**What if an AI code reviewer could live *entirely on your laptop*, available anytime, costing exactly $0 to run, and never seeing your code leave your filesystem?**

That's CodeSage. And it's the kind of tool someone would actually pay for — because the value proposition is dead simple: **unlimited AI code reviews, zero cloud dependency, zero ongoing cost**.

---

## What I Built: CodeSage 🧙

**CodeSage** is a terminal-based AI code review assistant with four core commands:

```bash
# Review a file with full AI analysis
codesage review auth.py

# Focus on a specific concern
codesage review payment.py --focus security

# Get a plain-English explanation of complex code
codesage explain complex_algo.rs

# Ask for a targeted fix
codesage fix buggy.js --issue "Race condition in the async handler"

# List all your local AI models
codesage models
```

The review output is **structured and actionable** — not generic advice:

```
## 🎯 Summary
An authentication handler validating JWT tokens...

## 🐛 Bugs & Issues
- Line 34: `user_id` used before None check → AttributeError risk

## 🔒 Security
- Line 12: JWT secret is hardcoded. Move to env variable IMMEDIATELY.

## ⭐ Overall Score
5/10 — Functional but critical security vulnerability present.
```

---

## Why Open-Weight / Open-Source AI?

This was the most deliberate architectural decision I made. Here's why open matters for this tool:

### 🔒 Privacy Is the Entire Business Case

When you're a freelancer working on a client project with an NDA, your code is confidential. Sending it to a third-party AI API — even with "we don't train on your data" promises — introduces real legal and security risk. That's not a hypothetical; it's the reason freelancers can't use most AI review tools on their most important work.

With open-weight models running locally via Ollama, **the code never leaves the developer's machine**. Full stop. This isn't a nice-to-have — it's the feature that makes CodeSage viable for the people who need it most.

### 💰 Zero Marginal Cost Makes the Unit Economics Work

Cloud LLM APIs charge per token. A freelancer reviewing code 50 times a day would burn through API credits fast. Local inference with models like Gemma 3 costs $0 per review once you have the hardware. For a tool you'd sell to freelancers, keeping the running cost at zero is what makes the price you charge pure margin.

### 🌐 Works Offline — Because Real Work Happens Offline

Planes. Cafes without WiFi. Corporate environments with strict egress rules. Offshore developers on satellite connections. CodeSage works everywhere Ollama runs.

### 🤝 Open Source Means the Community Extends It

A closed-source code reviewer is a product. An open-source one is a platform. People can add their own prompt templates, train on their codebase patterns, and plug in any model Ollama supports — today or five years from now.

---

## Deep Dive: Architecture & Code

Here's how CodeSage is structured:

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Terminal                      │
└───────────────────────┬─────────────────────────────────────┘
                        │ file path / stdin
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLI Layer (cli.py)                       │
│              Typer + Rich — beautiful UX                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                CodeReviewer (reviewer.py)                   │
│  • Reads file safely (size checks, encoding validation)     │
│  • Auto-detects language from file extension                │
│  • Selects the right prompt template                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               Prompt Builder (prompts.py)                   │
│  • REVIEW_SYSTEM_PROMPT — strict output format contract     │
│  • build_review_prompt() / build_fix_prompt() etc.         │
└───────────────────────┬─────────────────────────────────────┘
                        │ async HTTP (streaming)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              OllamaClient (ollama_client.py)                │
│  • Async HTTPX — non-blocking, supports streaming           │
│  • Graceful error handling when Ollama isn't running        │
└───────────────────────┬─────────────────────────────────────┘
                        │ localhost:11434
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Ollama Server + Open-Weight Model              │
│         Gemma 3 / CodeLlama / DeepSeek-Coder / Phi-4       │
└─────────────────────────────────────────────────────────────┘
```

### The Prompt Engineering Trick

The most important part of getting good, *consistent* reviews is the system prompt. Here's the key section from `prompts.py`:

```python
REVIEW_SYSTEM_PROMPT = """\
You are CodeSage, an expert software engineer specializing in code review.
Your job is to analyse the provided source code and produce a structured,
actionable code review.

Follow this EXACT output format — do not deviate:

## 🎯 Summary
## 🐛 Bugs & Issues
## ⚡ Performance
## 🔒 Security
## 🧹 Code Quality & Style
## 💡 Suggestions
## ⭐ Overall Score

Be direct, constructive, and specific. Avoid generic advice.
Focus on what matters most for this particular snippet.
"""
```

**Why is this important?** Without a strict output contract, open-weight models produce wildly inconsistent formats. By specifying the exact markdown sections, every review is parseable, comparable, and pipeable to downstream tools. This is the trick that makes Gemma 3 behave like a structured code review API, not a chatbot.

### Async Streaming — Feels Like Magic

Nothing kills UX faster than staring at a blank terminal for 30 seconds. CodeSage streams tokens as they arrive from Ollama:

```python
async def stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
    """Stream tokens from Ollama one chunk at a time."""
    async with self._client.stream("POST", "/api/generate", json=payload) as resp:
        async for line in resp.aiter_lines():
            chunk = json.loads(line)
            token = chunk.get("response", "")
            if token:
                yield token   # ← each token arrives in real-time
            if chunk.get("done", False):
                break
```

Combined with Rich's `Live` display, this gives you a live, updating view of the review as the model thinks. The terminal fills up word by word instead of making you wait for the entire response. This one feature changed the tool from "feels broken" to "feels alive" when I tested with colleagues.

### Error Handling — Because Ollama Might Not Be Running

One thing I've learned shipping developer tools: **assume the happy path won't be taken**. If the user forgets to start Ollama:

```python
async def _ensure_model_available(self) -> None:
    try:
        resp = await self._client.get("/api/tags")
        # check if model is in the local list...
    except httpx.ConnectError as exc:
        raise OllamaError(
            f"Cannot connect to Ollama at {self.base_url}. "
            "Is Ollama running? Start it with: ollama serve"
        ) from exc
```

The user gets a clear, actionable error message — not a raw traceback.

---

## Demo: How to Run It

### Step 1: Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download from https://ollama.com
```

### Step 2: Pull a model

```bash
# Gemma 3 — Google's latest open model, excellent for code
ollama pull gemma3

# OR CodeLlama — Meta's code-specific model
ollama pull codellama
```

### Step 3: Install CodeSage

```bash
git clone https://github.com/Nobody-KnowsBetter/code-sage.git
cd code-sage
bash setup.sh           # one-shot: creates venv, installs deps, configures .env
source .venv/bin/activate
```

### Step 4: Start reviewing!

```bash
# In another terminal (or as a background service):
ollama serve

# Review any file:
codesage review your_code.py

# Pipe from git diff for reviewing only changed lines:
git diff HEAD~1 | codesage review --language Python

# CI-friendly JSON output:
codesage review src/main.ts --output json | jq '.review'
```

---

## What I Learned Building This

**1. Prompt engineering beats model selection.**
The structured output format in the system prompt did more for review quality than switching between different models. A well-constrained Gemma 3 outperformed an unconstrained CodeLlama.

**2. Streaming UX is not optional for LLM tools.**
When I tested the non-streaming version with colleagues, the consensus was "it feels broken" during the wait. Streaming made the tool feel alive.

**3. Open-weight models are genuinely competitive for code tasks.**
Gemma 3 caught the same security issues in my test code that GPT-4 did. The gap between open and closed models for code review has closed significantly.

**4. The Ollama API is beautifully simple.**
`POST /api/generate` with a JSON body. That's basically it. The hardest part was the streaming NDJSON parsing, which turned out to be ~10 lines.

**5. Python 3.14 breaks `.pth` file loading on macOS.**
A fun debugging session: Python 3.14 + macOS marks files downloaded/created by pip as "hidden" using the `UF_HIDDEN` flag, which the new `site.py` then skips when processing editable installs. The fix is `chflags -R 0 .venv`. This is the kind of real-world rough edge you only find by actually building something.

---

## Would Someone Pay for This?

I think so — and here's why:

1. **Freelancers with NDA clients** can't use cloud AI tools for code review. CodeSage solves that.
2. **Small agencies** could bundle this as part of their QA workflow — zero per-seat licensing.
3. **Enterprise teams** in regulated industries (finance, healthcare) need air-gapped AI tools. CodeSage runs on a laptop with no network connection.
4. **The hosted version writes itself**: wrap CodeSage in a web UI, run Ollama on a GPU server you control, charge $10/month per seat. The open-source core is the proof of concept.

A colleague tested it on a real client project and said: *"I'd pay $5/month for this if it had a VS Code extension."* That's the roadmap.

---

## What's Next

- [ ] **Git diff mode** — review only changed lines, not whole files
- [ ] **VS Code extension** — `Right click → CodeSage Review`
- [ ] **`.codesage.yml`** — per-project config (language, preferred model, custom rules)
- [ ] **Batch mode** — review an entire directory recursively
- [ ] **Pre-commit hook** — automatic review before every commit

---

## Contributing — It's Hacktoberfest!

All PRs are welcome! Good first issues:

- Add support for more languages (currently 20+ supported)
- Improve prompts for specific languages (Rust ownership patterns, Python async best practices)
- Add a `--since` flag to review only files changed since a git ref
- Write more tests

```bash
# Run the test suite (no live Ollama needed — all mocked)
pytest --cov=codesage
```

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| **AI Runtime** | [Ollama](https://ollama.com) | Local inference, zero cloud |
| **AI Models** | Gemma 3, CodeLlama, DeepSeek-Coder | Open-weight, no API key |
| **CLI Framework** | [Typer](https://typer.tiangolo.com) | Beautiful, type-safe CLI |
| **Terminal UI** | [Rich](https://rich.readthedocs.io) | Markdown rendering, colours |
| **HTTP Client** | [HTTPX](https://www.python-httpx.org) | Async, streaming support |
| **Config** | [python-dotenv](https://pypi.org/project/python-dotenv/) | `.env` support |
| **Testing** | [pytest](https://pytest.org) | 27 tests, all mocked |

---

## Resources

- **GitHub:** [https://github.com/Nobody-KnowsBetter/code-sage](https://github.com/Nobody-KnowsBetter/code-sage)
- **Ollama:** [https://ollama.com](https://ollama.com)
- **Gemma 3 Model Card:** [https://ollama.com/library/gemma3](https://ollama.com/library/gemma3)
- **Hacktoberfest:** [https://hacktoberfest.com](https://hacktoberfest.com)

---

*Built with ❤️ for the Hacktoberfest 2026 DEV Challenge. If this saved you from shipping a bug, drop a ⭐ on GitHub!*
