#!/usr/bin/env bash
# =============================================================================
# setup.sh — One-command setup for CodeSage
# Usage: bash setup.sh
# =============================================================================
set -euo pipefail

PYTHON_MIN="3.10"
VENV_DIR=".venv"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; RESET='\033[0m'

info()    { echo -e "${CYAN}ℹ  $*${RESET}"; }
success() { echo -e "${GREEN}✓  $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠  $*${RESET}"; }
error()   { echo -e "${RED}✗  $*${RESET}" >&2; exit 1; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════╗${RESET}"
echo -e "${CYAN}║   🧙 CodeSage — Setup Script      ║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════╝${RESET}"
echo ""

# ── 1. Check Python version ───────────────────────────────────────────────────
info "Checking Python version..."
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            success "Found Python $VER ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    error "Python $PYTHON_MIN or higher is required. Please install it from https://python.org"
fi

# ── 2. Create virtual environment ─────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    warn "Virtual environment already exists at $VENV_DIR — skipping creation."
else
    info "Creating virtual environment in $VENV_DIR..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    [[ "$OSTYPE" == "darwin"* ]] && chflags -R 0 "$VENV_DIR" 2>/dev/null || true
    success "Virtual environment created."
fi

# Activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 3. Upgrade pip ────────────────────────────────────────────────────────────
info "Upgrading pip..."
pip install --quiet --upgrade pip

# ── 4. Install dependencies ───────────────────────────────────────────────────
info "Installing Python dependencies from requirements.txt..."
pip install --quiet -r requirements.txt
success "Dependencies installed."

# ── 5. Install codesage in editable mode ─────────────────────────────────────
info "Installing CodeSage CLI (editable)..."
pip install --quiet -e .
    if [[ "$OSTYPE" == "darwin"* ]]; then
        chflags -R 0 "$VENV_DIR" 2>/dev/null || true
        chflags 0 "$VENV_DIR"/lib/python*/site-packages/*.pth 2>/dev/null || true
    fi
success "CodeSage installed. Run: codesage --help"

# ── 6. Create .env from .env.example ─────────────────────────────────────────
if [ ! -f ".env" ]; then
    info "Copying .env.example → .env"
    cp .env.example .env
    success ".env created. Edit it to set your preferred model."
else
    warn ".env already exists — skipping."
fi

# ── 7. Check Ollama ───────────────────────────────────────────────────────────
echo ""
info "Checking for Ollama..."
if command -v ollama &>/dev/null; then
    success "Ollama found: $(ollama --version 2>/dev/null || echo 'version unknown')"
    info "Pulling recommended model (gemma3)... this may take a few minutes."
    ollama pull gemma3 || warn "Could not pull gemma3 — you can do it manually: ollama pull gemma3"
else
    warn "Ollama not found. Install it from https://ollama.com then run: ollama pull gemma3"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}║  ✓  CodeSage is ready!                    ║${RESET}"
echo -e "${GREEN}║                                           ║${RESET}"
echo -e "${GREEN}║  Activate your venv:                      ║${RESET}"
echo -e "${GREEN}║    source .venv/bin/activate              ║${RESET}"
echo -e "${GREEN}║                                           ║${RESET}"
echo -e "${GREEN}║  Try it:                                  ║${RESET}"
echo -e "${GREEN}║    codesage review codesage/reviewer.py   ║${RESET}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${RESET}"
echo ""
