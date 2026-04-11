#!/usr/bin/env bash
# ============================================================================
# integration-setup.sh — AI Autobiography Generator: External Integration Setup
#
# Installs ALL external dependencies for the full pipeline:
#   1. Document Generation: Pandoc + XeLaTeX (MacTeX) + Typst
#   2. Speech-to-Text: faster-whisper + WhisperX
#   3. Knowledge Management: ChromaDB + nomic-embed-text (via Ollama)
#   4. Python Dependencies: pydantic, pyyaml, jsonschema, etc.
#   5. Optional: Calibre (EPUB validation), promptfoo (eval)
#
# Target: macOS Apple Silicon (arm64)
# Usage:  cd autobiography-generator && bash scripts/integration-setup.sh
# Flags:  --minimal     Skip optional/cutting-edge components
#         --skip-latex   Skip MacTeX (saves 4GB download, EPUB-only builds)
#         --skip-whisper Skip faster-whisper (text-only interviews)
#         --dry-run      Print commands without executing
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Flags ──────────────────────────────────────────────────────────────────
MINIMAL=false
SKIP_LATEX=false
SKIP_WHISPER=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --minimal)     MINIMAL=true ;;
    --skip-latex)  SKIP_LATEX=true ;;
    --skip-whisper) SKIP_WHISPER=true ;;
    --dry-run)     DRY_RUN=true ;;
    --help|-h)
      echo "Usage: bash scripts/integration-setup.sh [--minimal] [--skip-latex] [--skip-whisper] [--dry-run]"
      exit 0
      ;;
  esac
done

run_cmd() {
  if $DRY_RUN; then
    echo "  [DRY-RUN] $*"
  else
    eval "$@"
  fi
}

TOTAL_START=$SECONDS
echo "================================================================"
echo "  AI Autobiography Generator — Integration Setup"
echo "  Platform: macOS $(uname -m)"
echo "  Python:   $(python3 --version 2>&1)"
echo "  Time:     $(date)"
echo "  Flags:    minimal=$MINIMAL skip-latex=$SKIP_LATEX skip-whisper=$SKIP_WHISPER dry-run=$DRY_RUN"
echo "================================================================"
echo ""

# ── 0. Prerequisites Check ────────────────────────────────────────────────
echo "[0/9] Checking prerequisites..."

if ! command -v brew &>/dev/null; then
  echo "  Homebrew not found. Installing..."
  run_cmd '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
fi
echo "  Homebrew: $(brew --version 2>&1 | head -1)"

if ! command -v python3 &>/dev/null; then
  echo "  ERROR: Python 3 not found. Install via: brew install python@3.12"
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
  echo "  WARNING: Python $PYTHON_VERSION detected. Requires >= 3.11"
  echo "  Run: brew install python@3.12"
fi
echo "  Python: $PYTHON_VERSION OK"
echo ""

# ── 1. Pandoc ──────────────────────────────────────────────────────────────
echo "[1/9] Installing Pandoc (document converter)..."
STEP_START=$SECONDS

if command -v pandoc &>/dev/null; then
  echo "  Pandoc already installed: $(pandoc --version | head -1)"
else
  run_cmd 'brew install pandoc'
fi

PANDOC_TIME=$((SECONDS - STEP_START))
echo "  Done (${PANDOC_TIME}s)"
echo ""

# ── 2. LaTeX (XeLaTeX via MacTeX) ─────────────────────────────────────────
echo "[2/9] Installing LaTeX (PDF typesetting engine)..."
STEP_START=$SECONDS

if $SKIP_LATEX; then
  echo "  SKIPPED (--skip-latex flag). PDF builds will not work."
  echo "  EPUB and markdown builds remain available."
  LATEX_TIME=0
else
  if command -v xelatex &>/dev/null; then
    echo "  XeLaTeX already installed: $(xelatex --version 2>&1 | head -1)"
  else
    echo "  Installing BasicTeX (minimal, ~300MB instead of 4GB full MacTeX)..."
    echo "  NOTE: Full MacTeX alternative: brew install --cask mactex (4GB, includes everything)"
    run_cmd 'brew install --cask basictex'

    # Add TeX Live to PATH for current session
    export PATH="/Library/TeX/texbin:$PATH"

    echo "  Installing required LaTeX packages..."
    # Update tlmgr first
    run_cmd 'sudo tlmgr update --self 2>/dev/null || true'

    # memoir class (core document class for the book)
    run_cmd 'sudo tlmgr install memoir'

    # Font packages required by memoir.latex template
    run_cmd 'sudo tlmgr install tex-gyre'
    run_cmd 'sudo tlmgr install tex-gyre-math'

    # fontspec (XeLaTeX font selection)
    run_cmd 'sudo tlmgr install fontspec'

    # polyglossia (multilingual support)
    run_cmd 'sudo tlmgr install polyglossia'

    # lettrine (drop caps)
    run_cmd 'sudo tlmgr install lettrine'

    # epigraph (chapter epigraphs)
    run_cmd 'sudo tlmgr install epigraph'

    # booktabs + longtable (tables)
    run_cmd 'sudo tlmgr install booktabs longtable'

    # hyperref (cross-references)
    run_cmd 'sudo tlmgr install hyperref'

    # xcolor (colors)
    run_cmd 'sudo tlmgr install xcolor'

    # graphicx (images) -- usually included in base
    run_cmd 'sudo tlmgr install graphics'

    # etoolbox (required by many packages)
    run_cmd 'sudo tlmgr install etoolbox'

    # Additional commonly needed packages
    run_cmd 'sudo tlmgr install collection-fontsrecommended'
    run_cmd 'sudo tlmgr install collection-latexrecommended'
  fi

  LATEX_TIME=$((SECONDS - STEP_START))
  echo "  Done (${LATEX_TIME}s)"
fi
echo ""

# ── 3. Typst (Cutting-Edge alternative to LaTeX) ──────────────────────────
echo "[3/9] Installing Typst (fast PDF engine — cutting-edge option)..."
STEP_START=$SECONDS

if $MINIMAL; then
  echo "  SKIPPED (--minimal flag). XeLaTeX will be used for PDF."
else
  if command -v typst &>/dev/null; then
    echo "  Typst already installed: $(typst --version 2>&1)"
  else
    run_cmd 'brew install typst'
  fi
fi

TYPST_TIME=$((SECONDS - STEP_START))
echo "  Done (${TYPST_TIME}s)"
echo ""

# ── 4. faster-whisper (Speech-to-Text) ────────────────────────────────────
echo "[4/9] Installing faster-whisper (local speech-to-text)..."
STEP_START=$SECONDS

if $SKIP_WHISPER; then
  echo "  SKIPPED (--skip-whisper flag). Text-only interview mode."
  WHISPER_TIME=0
else
  # Create a virtual environment if not exists
  VENV_DIR="$PROJECT_ROOT/.venv"
  if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment at .venv..."
    run_cmd "python3 -m venv '$VENV_DIR'"
  fi

  echo "  Installing faster-whisper..."
  run_cmd "'$VENV_DIR/bin/pip' install --upgrade pip"

  # faster-whisper: CPU-optimized for Apple Silicon (no CUDA)
  # Uses CTranslate2 which supports CoreML/Metal on macOS
  run_cmd "'$VENV_DIR/bin/pip' install faster-whisper"

  # WhisperX: speaker diarization (optional, heavier)
  if ! $MINIMAL; then
    echo "  Installing WhisperX (speaker diarization)..."
    run_cmd "'$VENV_DIR/bin/pip' install whisperx" || {
      echo "  WARNING: WhisperX install failed. This is optional."
      echo "  Manual speaker tagging will be used instead."
    }
  fi

  WHISPER_TIME=$((SECONDS - STEP_START))
  echo "  Done (${WHISPER_TIME}s)"
fi
echo ""

# ── 5. Python Project Dependencies ────────────────────────────────────────
echo "[5/9] Installing Python project dependencies..."
STEP_START=$SECONDS

VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "  Creating virtual environment at .venv..."
  run_cmd "python3 -m venv '$VENV_DIR'"
fi

PIP="$VENV_DIR/bin/pip"

# Core dependencies from pyproject.toml
run_cmd "'$PIP' install pydantic>=2.6 pyyaml>=6.0 jsonschema>=4.21"

# Dev dependencies
run_cmd "'$PIP' install pytest>=8.0 pytest-cov>=5.0 pytest-xdist>=3.5 ruff>=0.9 mypy>=1.13 types-PyYAML>=6.0 pre-commit>=4.0"

# textstat for readability metrics (used by check.py, check_voice.py)
run_cmd "'$PIP' install textstat"

PYTHON_TIME=$((SECONDS - STEP_START))
echo "  Done (${PYTHON_TIME}s)"
echo ""

# ── 6. ChromaDB + Ollama (Knowledge Management — Cutting Edge) ────────────
echo "[6/9] Installing ChromaDB + Ollama (vector storage + local embeddings)..."
STEP_START=$SECONDS

if $MINIMAL; then
  echo "  SKIPPED (--minimal flag). Story bible JSON will be used directly."
  CHROMA_TIME=0
else
  # ChromaDB (local vector store, SQLite backend)
  run_cmd "'$PIP' install chromadb"

  # Ollama (local model runner for embeddings)
  if command -v ollama &>/dev/null; then
    echo "  Ollama already installed: $(ollama --version 2>&1)"
  else
    echo "  Installing Ollama..."
    run_cmd 'brew install ollama'
  fi

  # Pull embedding model (nomic-embed-text, ~274MB)
  echo "  Pulling nomic-embed-text model..."
  run_cmd 'ollama pull nomic-embed-text' || {
    echo "  WARNING: Failed to pull nomic-embed-text."
    echo "  Start Ollama first: ollama serve &"
    echo "  Then run: ollama pull nomic-embed-text"
  }

  CHROMA_TIME=$((SECONDS - STEP_START))
  echo "  Done (${CHROMA_TIME}s)"
fi
echo ""

# ── 7. Calibre (EPUB validation — optional) ───────────────────────────────
echo "[7/9] Installing Calibre (EPUB validation — optional)..."
STEP_START=$SECONDS

if $MINIMAL; then
  echo "  SKIPPED (--minimal flag). Pandoc native EPUB will be used."
  CALIBRE_TIME=0
else
  if command -v ebook-convert &>/dev/null; then
    echo "  Calibre already installed"
  else
    echo "  Installing Calibre..."
    run_cmd 'brew install --cask calibre'
  fi

  CALIBRE_TIME=$((SECONDS - STEP_START))
  echo "  Done (${CALIBRE_TIME}s)"
fi
echo ""

# ── 8. Claude Code CLI Verification ───────────────────────────────────────
echo "[8/9] Verifying Claude Code CLI..."
STEP_START=$SECONDS

if command -v claude &>/dev/null; then
  echo "  Claude Code CLI found: $(claude --version 2>&1 || echo 'version unknown')"
else
  echo "  WARNING: Claude Code CLI not found."
  echo "  Install via: npm install -g @anthropic-ai/claude-code"
  echo "  Or:          brew install claude-code"
fi

CLAUDE_TIME=$((SECONDS - STEP_START))
echo "  Done (${CLAUDE_TIME}s)"
echo ""

# ── 9. PATH Configuration ────────────────────────────────────────────────
echo "[9/9] Configuring PATH..."

SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_RC="$HOME/.bashrc"
fi

# Ensure TeX Live is on PATH
if [ -n "$SHELL_RC" ] && ! grep -q "/Library/TeX/texbin" "$SHELL_RC" 2>/dev/null; then
  if ! $SKIP_LATEX; then
    echo "  Adding TeX Live to PATH in $SHELL_RC..."
    run_cmd "echo 'export PATH=\"/Library/TeX/texbin:\$PATH\"' >> '$SHELL_RC'"
  fi
fi

# Tell user about venv activation
echo "  Virtual environment: $VENV_DIR"
echo "  Activate with: source $VENV_DIR/bin/activate"
echo ""

# ── Summary ───────────────────────────────────────────────────────────────
TOTAL_TIME=$((SECONDS - TOTAL_START))

echo "================================================================"
echo "  INSTALLATION SUMMARY"
echo "================================================================"
echo ""
echo "  Component            Status         Time"
echo "  ──────────────────   ────────────   ──────"
printf "  %-22s %-14s %s\n" "Pandoc"          "$(command -v pandoc &>/dev/null && echo 'INSTALLED' || echo 'MISSING')" "${PANDOC_TIME}s"
printf "  %-22s %-14s %s\n" "XeLaTeX"         "$(command -v xelatex &>/dev/null && echo 'INSTALLED' || echo 'SKIPPED')" "${LATEX_TIME}s"
printf "  %-22s %-14s %s\n" "Typst"           "$($MINIMAL && echo 'SKIPPED' || (command -v typst &>/dev/null && echo 'INSTALLED' || echo 'MISSING'))" "${TYPST_TIME}s"
printf "  %-22s %-14s %s\n" "faster-whisper"  "$($SKIP_WHISPER && echo 'SKIPPED' || echo 'INSTALLED')" "${WHISPER_TIME}s"
printf "  %-22s %-14s %s\n" "Python deps"     "INSTALLED" "${PYTHON_TIME}s"
printf "  %-22s %-14s %s\n" "ChromaDB+Ollama" "$($MINIMAL && echo 'SKIPPED' || echo 'INSTALLED')" "${CHROMA_TIME:-0}s"
printf "  %-22s %-14s %s\n" "Calibre"         "$($MINIMAL && echo 'SKIPPED' || (command -v ebook-convert &>/dev/null && echo 'INSTALLED' || echo 'MISSING'))" "${CALIBRE_TIME:-0}s"
printf "  %-22s %-14s %s\n" "Claude Code CLI" "$(command -v claude &>/dev/null && echo 'INSTALLED' || echo 'MISSING')" "${CLAUDE_TIME}s"
echo "  ──────────────────   ────────────   ──────"
echo "  Total                               ${TOTAL_TIME}s"
echo ""
echo "================================================================"
echo "  NEXT STEPS"
echo "================================================================"
echo "  1. Activate venv:    source .venv/bin/activate"
echo "  2. Verify all:       bash scripts/verify-integrations.sh"
echo "  3. Run tests:        python3 -m pytest tests/"
echo "  4. Test build:       python3 scripts/build_book.py --project-dir . --format all --draft"
echo "  5. Start dev loop:   bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json"
echo ""
echo "  Total setup time: ${TOTAL_TIME}s"
echo "================================================================"
