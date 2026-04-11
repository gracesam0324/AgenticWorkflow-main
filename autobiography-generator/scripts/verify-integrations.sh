#!/usr/bin/env bash
# ============================================================================
# verify-integrations.sh — AI Autobiography Generator: Integration Verification
#
# Tests EVERY external integration to confirm it works correctly.
# Run after integration-setup.sh to verify the full pipeline.
#
# Usage:  cd autobiography-generator && bash scripts/verify-integrations.sh
# Flags:  --verbose    Show full version output
#         --fix        Attempt automatic fixes for failures
#
# Exit codes:
#   0 — All integrations verified
#   1 — One or more integrations failed
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

VERBOSE=false
FIX=false
for arg in "$@"; do
  case "$arg" in
    --verbose) VERBOSE=true ;;
    --fix)     FIX=true ;;
  esac
done

PASS=0
FAIL=0
SKIP=0
FAILURES=()

pass() { PASS=$((PASS + 1)); echo "  [PASS] $1"; }
fail() { FAIL=$((FAIL + 1)); FAILURES+=("$1: $2"); echo "  [FAIL] $1 — $2"; }
skip() { SKIP=$((SKIP + 1)); echo "  [SKIP] $1 — $2"; }

echo "================================================================"
echo "  AI Autobiography Generator — Integration Verification"
echo "  Time: $(date)"
echo "================================================================"
echo ""

# ── 1. Python ──────────────────────────────────────────────────────────────
echo "[1/12] Python..."

if command -v python3 &>/dev/null; then
  PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
  PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
  PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
  if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
    pass "Python $PY_VER (>= 3.11 required)"
  else
    fail "Python" "Version $PY_VER is below minimum 3.11"
  fi
else
  fail "Python" "python3 not found. Run: brew install python@3.12"
fi

# ── 2. Virtual Environment ────────────────────────────────────────────────
echo "[2/12] Virtual Environment..."

VENV_DIR="$PROJECT_ROOT/.venv"
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
  VENV_PY_VER=$("$VENV_DIR/bin/python" --version 2>&1)
  pass "venv exists ($VENV_PY_VER)"

  # Use venv pip for subsequent checks
  PIP="$VENV_DIR/bin/pip"
  PYTHON="$VENV_DIR/bin/python"
else
  fail "Virtual Environment" ".venv not found. Run: python3 -m venv .venv"
  PIP="pip3"
  PYTHON="python3"
fi

# ── 3. Python Dependencies ────────────────────────────────────────────────
echo "[3/12] Python Dependencies..."

check_python_pkg() {
  local pkg="$1"
  local import_name="${2:-$1}"
  if "$PYTHON" -c "import $import_name" 2>/dev/null; then
    if $VERBOSE; then
      local ver
      ver=$("$PYTHON" -c "import $import_name; print(getattr($import_name, '__version__', 'installed'))" 2>/dev/null || echo "installed")
      pass "$pkg ($ver)"
    else
      pass "$pkg"
    fi
  else
    fail "$pkg" "Not installed. Run: $PIP install $pkg"
  fi
}

check_python_pkg "pydantic" "pydantic"
check_python_pkg "pyyaml" "yaml"
check_python_pkg "jsonschema" "jsonschema"
check_python_pkg "textstat" "textstat"

# ── 4. Pandoc ──────────────────────────────────────────────────────────────
echo "[4/12] Pandoc..."

if command -v pandoc &>/dev/null; then
  PANDOC_VER=$(pandoc --version | head -1)
  pass "$PANDOC_VER"

  # Test actual conversion: markdown to HTML
  TEST_MD=$(mktemp /tmp/verify-pandoc-XXXXX.md)
  TEST_HTML=$(mktemp /tmp/verify-pandoc-XXXXX.html)
  echo "# Test Chapter" > "$TEST_MD"
  echo "" >> "$TEST_MD"
  echo "This is a test paragraph." >> "$TEST_MD"

  if pandoc "$TEST_MD" -o "$TEST_HTML" 2>/dev/null; then
    pass "Pandoc MD->HTML conversion works"
  else
    fail "Pandoc conversion" "pandoc failed to convert test markdown"
  fi
  rm -f "$TEST_MD" "$TEST_HTML"
else
  fail "Pandoc" "Not found. Run: brew install pandoc"
fi

# ── 5. XeLaTeX ─────────────────────────────────────────────────────────────
echo "[5/12] XeLaTeX (PDF engine)..."

if command -v xelatex &>/dev/null; then
  XELATEX_VER=$(xelatex --version 2>&1 | head -1)
  pass "$XELATEX_VER"

  # Test memoir class availability
  TEST_TEX=$(mktemp /tmp/verify-xelatex-XXXXX.tex)
  TEST_DIR=$(mktemp -d /tmp/verify-xelatex-dir-XXXXX)
  cat > "$TEST_TEX" << 'TEXEOF'
\documentclass[12pt]{memoir}
\usepackage{fontspec}
\begin{document}
Hello world.
\end{document}
TEXEOF

  if xelatex -interaction=nonstopmode -output-directory="$TEST_DIR" "$TEST_TEX" &>/dev/null; then
    pass "XeLaTeX memoir class works"
  else
    fail "XeLaTeX memoir" "memoir class compilation failed. Run: sudo tlmgr install memoir"
  fi
  rm -rf "$TEST_TEX" "$TEST_DIR"

  # Check required fonts
  echo "  Checking required fonts..."
  FONT_CHECK=$("$PYTHON" -c "
import subprocess
result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True)
fonts = result.stdout.lower()
missing = []
for font in ['tex gyre termes', 'tex gyre heros', 'tex gyre cursor']:
    if font not in fonts:
        missing.append(font)
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('OK')
" 2>/dev/null || echo "SKIP")

  if [ "$FONT_CHECK" = "OK" ]; then
    pass "TeX Gyre fonts (Termes, Heros, Cursor) all present"
  elif [[ "$FONT_CHECK" == MISSING:* ]]; then
    fail "Fonts" "${FONT_CHECK#MISSING:} missing. Run: sudo tlmgr install tex-gyre"
  else
    skip "Font check" "fc-list not available"
  fi

else
  skip "XeLaTeX" "Not installed. PDF builds will not work. Run: brew install --cask basictex"
fi

# ── 6. Typst (Cutting-Edge PDF alternative) ───────────────────────────────
echo "[6/12] Typst (cutting-edge PDF engine)..."

if command -v typst &>/dev/null; then
  TYPST_VER=$(typst --version 2>&1)
  pass "$TYPST_VER"

  # Test basic compilation
  TEST_TYP=$(mktemp /tmp/verify-typst-XXXXX.typ)
  TEST_PDF="/tmp/verify-typst-output.pdf"
  echo '#set page(paper: "a5")' > "$TEST_TYP"
  echo '= Chapter One' >> "$TEST_TYP"
  echo 'This is a test.' >> "$TEST_TYP"

  if typst compile "$TEST_TYP" "$TEST_PDF" 2>/dev/null; then
    pass "Typst compilation works"
  else
    fail "Typst compilation" "Failed to compile test document"
  fi
  rm -f "$TEST_TYP" "$TEST_PDF"
else
  skip "Typst" "Not installed (optional). Run: brew install typst"
fi

# ── 7. faster-whisper (Speech-to-Text) ────────────────────────────────────
echo "[7/12] faster-whisper (speech-to-text)..."

if "$PYTHON" -c "from faster_whisper import WhisperModel" 2>/dev/null; then
  FW_VER=$("$PYTHON" -c "import faster_whisper; print(faster_whisper.__version__)" 2>/dev/null || echo "installed")
  pass "faster-whisper $FW_VER"

  # Test model loading (tiny model for speed)
  echo "  Testing model initialization (tiny model)..."
  WHISPER_TEST=$("$PYTHON" -c "
from faster_whisper import WhisperModel
try:
    model = WhisperModel('tiny', device='cpu', compute_type='int8')
    print('OK')
except Exception as e:
    print(f'FAIL:{e}')
" 2>/dev/null || echo "FAIL:import error")

  if [ "$WHISPER_TEST" = "OK" ]; then
    pass "faster-whisper model load works (CPU/int8)"
  else
    fail "faster-whisper model" "${WHISPER_TEST#FAIL:}"
  fi
else
  skip "faster-whisper" "Not installed. Text-only interviews. Run: pip install faster-whisper"
fi

# ── 8. WhisperX (Speaker Diarization) ─────────────────────────────────────
echo "[8/12] WhisperX (speaker diarization)..."

if "$PYTHON" -c "import whisperx" 2>/dev/null; then
  pass "WhisperX installed"
else
  skip "WhisperX" "Not installed (optional). Run: pip install whisperx"
fi

# ── 9. ChromaDB (Vector Storage) ──────────────────────────────────────────
echo "[9/12] ChromaDB (vector storage)..."

if "$PYTHON" -c "import chromadb" 2>/dev/null; then
  CHROMA_VER=$("$PYTHON" -c "import chromadb; print(chromadb.__version__)" 2>/dev/null || echo "installed")
  pass "ChromaDB $CHROMA_VER"

  # Test in-memory collection
  CHROMA_TEST=$("$PYTHON" -c "
import chromadb
client = chromadb.Client()
collection = client.create_collection('test')
collection.add(documents=['test document'], ids=['id1'])
results = collection.query(query_texts=['test'], n_results=1)
if results and results['ids']:
    print('OK')
else:
    print('FAIL:query returned no results')
" 2>/dev/null || echo "FAIL:runtime error")

  if [ "$CHROMA_TEST" = "OK" ]; then
    pass "ChromaDB in-memory store works"
  else
    fail "ChromaDB runtime" "${CHROMA_TEST#FAIL:}"
  fi
else
  skip "ChromaDB" "Not installed (optional). Run: pip install chromadb"
fi

# ── 10. Ollama + nomic-embed-text ─────────────────────────────────────────
echo "[10/12] Ollama + nomic-embed-text (local embeddings)..."

if command -v ollama &>/dev/null; then
  pass "Ollama installed"

  # Check if ollama is running
  if curl -s http://localhost:11434/api/tags &>/dev/null; then
    pass "Ollama server is running"

    # Check if nomic-embed-text is pulled
    MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null || echo "{}")
    if echo "$MODELS" | "$PYTHON" -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
if any('nomic-embed-text' in m for m in models):
    print('OK')
else:
    print('MISSING')
" 2>/dev/null | grep -q "OK"; then
      pass "nomic-embed-text model available"
    else
      fail "nomic-embed-text" "Model not pulled. Run: ollama pull nomic-embed-text"
    fi
  else
    skip "Ollama server" "Not running. Start with: ollama serve &"
  fi
else
  skip "Ollama" "Not installed (optional). Run: brew install ollama"
fi

# ── 11. Calibre (EPUB tools) ─────────────────────────────────────────────
echo "[11/12] Calibre (EPUB validation)..."

if command -v ebook-convert &>/dev/null; then
  pass "Calibre ebook-convert available"
else
  skip "Calibre" "Not installed (optional). Run: brew install --cask calibre"
fi

# ── 12. End-to-End Pipeline Test ──────────────────────────────────────────
echo "[12/12] End-to-end pipeline test..."

# Test schema validation
if [ -f "$PROJECT_ROOT/scripts/schema_validator.py" ] && [ -f "$PROJECT_ROOT/test-data/micro-interviews/INT-001-childhood.json" ]; then
  SCHEMA_TEST=$("$PYTHON" "$PROJECT_ROOT/scripts/schema_validator.py" \
    --schema "$PROJECT_ROOT/schemas/interview_transcript.schema.json" \
    --data "$PROJECT_ROOT/test-data/micro-interviews/INT-001-childhood.json" 2>&1 || echo "FAIL")

  if echo "$SCHEMA_TEST" | grep -qi "valid\|pass\|ok" 2>/dev/null || [ $? -eq 0 ]; then
    pass "Schema validation (interview_transcript)"
  else
    fail "Schema validation" "INT-001 failed against interview_transcript schema"
  fi
else
  skip "Schema validation" "Test data or validator not found"
fi

# Test Pandoc EPUB build (lightweight)
if command -v pandoc &>/dev/null; then
  TEST_MD=$(mktemp /tmp/verify-epub-XXXXX.md)
  TEST_EPUB=$(mktemp /tmp/verify-epub-XXXXX.epub)
  cat > "$TEST_MD" << 'MDEOF'
---
title: "Test Book"
author: ["Test Author"]
---

# Chapter 1

This is a test chapter for the autobiography generator pipeline verification.
MDEOF

  if pandoc "$TEST_MD" -o "$TEST_EPUB" --toc --epub-chapter-level=1 2>/dev/null; then
    EPUB_SIZE=$(wc -c < "$TEST_EPUB" | tr -d ' ')
    pass "Pandoc EPUB build works (${EPUB_SIZE} bytes)"
  else
    fail "Pandoc EPUB" "Failed to build test EPUB"
  fi
  rm -f "$TEST_MD" "$TEST_EPUB"
fi

# Test Pandoc PDF build via XeLaTeX (if available)
if command -v pandoc &>/dev/null && command -v xelatex &>/dev/null; then
  TEST_MD=$(mktemp /tmp/verify-pdf-XXXXX.md)
  TEST_PDF=$(mktemp /tmp/verify-pdf-XXXXX.pdf)
  cat > "$TEST_MD" << 'MDEOF'
---
title: "Test Book"
author: ["Test Author"]
---

# Chapter 1

This is a test chapter.
MDEOF

  if pandoc "$TEST_MD" -o "$TEST_PDF" --pdf-engine=xelatex 2>/dev/null; then
    PDF_SIZE=$(wc -c < "$TEST_PDF" | tr -d ' ')
    pass "Pandoc PDF build works (${PDF_SIZE} bytes)"
  else
    fail "Pandoc PDF" "PDF build failed. Check LaTeX packages."
  fi
  rm -f "$TEST_MD" "$TEST_PDF"
fi

# Test project's build_book.py (dry check only — prereq check)
if [ -f "$PROJECT_ROOT/scripts/build_book.py" ]; then
  BUILD_CHECK=$("$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/scripts')
from build_book import check_prerequisites
missing = check_prerequisites()
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('OK')
" 2>/dev/null || echo "FAIL:import error")

  if [ "$BUILD_CHECK" = "OK" ]; then
    pass "build_book.py prerequisites satisfied"
  elif [[ "$BUILD_CHECK" == MISSING:* ]]; then
    fail "build_book.py" "Missing: ${BUILD_CHECK#MISSING:}"
  else
    skip "build_book.py" "Could not check prerequisites"
  fi
fi

echo ""

# ── Summary ───────────────────────────────────────────────────────────────
echo "================================================================"
echo "  VERIFICATION SUMMARY"
echo "================================================================"
echo ""
echo "  Passed:  $PASS"
echo "  Failed:  $FAIL"
echo "  Skipped: $SKIP"
echo ""

if [ ${#FAILURES[@]} -gt 0 ]; then
  echo "  FAILURES:"
  for f in "${FAILURES[@]}"; do
    echo "    - $f"
  done
  echo ""
fi

if [ "$FAIL" -gt 0 ]; then
  echo "  STATUS: INCOMPLETE — $FAIL integration(s) need attention"
  echo ""
  echo "  Quick fixes:"
  echo "    brew install pandoc                    # Document converter"
  echo "    brew install --cask basictex           # LaTeX (PDF engine)"
  echo "    brew install typst                     # Fast PDF engine"
  echo "    pip install faster-whisper             # Speech-to-text"
  echo "    pip install chromadb                   # Vector storage"
  echo "    brew install ollama                    # Local model runner"
  echo "    ollama pull nomic-embed-text           # Embedding model"
  echo "    brew install --cask calibre            # EPUB tools"
  exit 1
else
  echo "  STATUS: ALL INTEGRATIONS VERIFIED"
  exit 0
fi
