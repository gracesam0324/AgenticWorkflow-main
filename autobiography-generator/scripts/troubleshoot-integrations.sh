#!/usr/bin/env bash
# ============================================================================
# troubleshoot-integrations.sh — Diagnose & Fix Common Integration Failures
#
# Detects common macOS integration issues and provides exact fix commands.
# Run when verify-integrations.sh reports failures.
#
# Usage:  bash scripts/troubleshoot-integrations.sh
#         bash scripts/troubleshoot-integrations.sh --fix   # Auto-fix where possible
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

AUTO_FIX=false
for arg in "$@"; do
  case "$arg" in
    --fix) AUTO_FIX=true ;;
  esac
done

fix_cmd() {
  if $AUTO_FIX; then
    echo "    [AUTO-FIX] Running: $*"
    eval "$@" || echo "    [AUTO-FIX] Command failed — manual intervention needed"
  else
    echo "    [FIX] $*"
  fi
}

echo "================================================================"
echo "  Integration Troubleshooting Guide"
echo "  Platform: macOS $(uname -m)"
echo "  $(date)"
echo "================================================================"
echo ""

# ── 1. Pandoc Issues ──────────────────────────────────────────────────────
echo "=== 1. PANDOC ISSUES ==="
echo ""

echo "  [CHECK] Pandoc installation..."
if ! command -v pandoc &>/dev/null; then
  echo "  [ISSUE] Pandoc not found"
  fix_cmd 'brew install pandoc'
else
  PANDOC_VER=$(pandoc --version | head -1 | awk '{print $2}')
  echo "  [OK] Pandoc $PANDOC_VER installed"

  # Check version >= 3.0
  PANDOC_MAJOR=$(echo "$PANDOC_VER" | cut -d. -f1)
  if [ "$PANDOC_MAJOR" -lt 3 ]; then
    echo "  [ISSUE] Pandoc version $PANDOC_VER is below required 3.0"
    fix_cmd 'brew upgrade pandoc'
  fi
fi

echo ""
echo "  [COMMON ISSUE] 'Could not find data file' errors"
echo "  [CAUSE] Pandoc cannot find its data directory after upgrade"
echo "  [FIX]   brew reinstall pandoc"
echo ""
echo "  [COMMON ISSUE] EPUB build fails with 'Codec error'"
echo "  [CAUSE] Input markdown has non-UTF8 characters"
echo "  [FIX]   file outputs/chapters/*.md   # Check encoding"
echo "  [FIX]   iconv -f ISO-8859-1 -t UTF-8 input.md > output.md"
echo ""

# ── 2. LaTeX / XeLaTeX Issues ────────────────────────────────────────────
echo "=== 2. LATEX / XELATEX ISSUES ==="
echo ""

echo "  [CHECK] XeLaTeX installation..."
if ! command -v xelatex &>/dev/null; then
  echo "  [ISSUE] XeLaTeX not found"
  echo ""
  echo "  [OPTION A] Install BasicTeX (300MB, minimal):"
  fix_cmd 'brew install --cask basictex'
  echo "  [OPTION B] Install full MacTeX (4GB, everything included):"
  echo "    [FIX] brew install --cask mactex"
  echo ""
  echo "  [IMPORTANT] After installing, add to PATH:"
  echo "    [FIX] export PATH=\"/Library/TeX/texbin:\$PATH\""
  echo "    [FIX] echo 'export PATH=\"/Library/TeX/texbin:\$PATH\"' >> ~/.zshrc"
else
  echo "  [OK] XeLaTeX found at $(which xelatex)"
fi

echo ""
echo "  [CHECK] PATH includes TeX Live..."
if ! echo "$PATH" | grep -q "/Library/TeX/texbin"; then
  echo "  [ISSUE] /Library/TeX/texbin not in PATH"
  echo "  [FIX]   export PATH=\"/Library/TeX/texbin:\$PATH\""
  echo "  [FIX]   echo 'export PATH=\"/Library/TeX/texbin:\$PATH\"' >> ~/.zshrc"
  echo "  [FIX]   source ~/.zshrc"
fi

echo ""
echo "  [COMMON ISSUE] 'File memoir.cls not found'"
echo "  [CAUSE] BasicTeX does not include memoir class by default"
echo "  [FIX]   sudo tlmgr update --self"
echo "  [FIX]   sudo tlmgr install memoir"
echo ""

echo "  [COMMON ISSUE] 'Font TeX Gyre Termes not found'"
echo "  [CAUSE] TeX Gyre fonts not installed"
echo "  [FIX]   sudo tlmgr install tex-gyre"
echo "  [FIX]   sudo tlmgr install collection-fontsrecommended"
echo "  [FIX]   fc-cache -fv   # Rebuild font cache"
echo ""

echo "  [COMMON ISSUE] 'LaTeX Error: File epigraph.sty not found'"
echo "  [CAUSE] Missing LaTeX package (common with BasicTeX)"
echo "  [FIX]   sudo tlmgr install epigraph"
echo "  [FIX]   # For all packages needed by this project:"
echo "  [FIX]   sudo tlmgr install memoir tex-gyre fontspec polyglossia lettrine epigraph booktabs longtable hyperref xcolor graphics etoolbox"
echo ""

echo "  [COMMON ISSUE] 'tlmgr: command not found'"
echo "  [CAUSE] TeX Live not on PATH"
echo "  [FIX]   export PATH=\"/Library/TeX/texbin:\$PATH\""
echo ""

echo "  [COMMON ISSUE] 'tlmgr: Local TeX Live is older than remote repository'"
echo "  [CAUSE] BasicTeX and CTAN repo version mismatch"
echo "  [FIX]   sudo tlmgr update --self --all"
echo "  [ALT]   # If that fails, switch to older repository:"
echo "  [FIX]   sudo tlmgr option repository https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2024/tlnet-final"
echo ""

echo "  [COMMON ISSUE] PDF builds but fonts look wrong"
echo "  [CAUSE] System fonts not visible to XeLaTeX"
echo "  [FIX]   sudo mktexlsr   # Rebuild TeX file database"
echo "  [FIX]   fc-cache -fv    # Rebuild system font cache"
echo "  [FIX]   luaotfload-tool --update   # Update font database"
echo ""

# ── 3. faster-whisper Issues ─────────────────────────────────────────────
echo "=== 3. FASTER-WHISPER ISSUES ==="
echo ""

echo "  [CHECK] faster-whisper import..."
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
PYTHON="${VENV_PYTHON:-python3}"
if [ ! -f "$PYTHON" ]; then
  PYTHON="python3"
fi

if ! "$PYTHON" -c "from faster_whisper import WhisperModel" 2>/dev/null; then
  echo "  [ISSUE] faster-whisper not importable"
  fix_cmd "'$PROJECT_ROOT/.venv/bin/pip' install faster-whisper"
fi

echo ""
echo "  [COMMON ISSUE] 'No module named ctranslate2'"
echo "  [CAUSE] CTranslate2 binary not compatible with current Python"
echo "  [FIX]   pip install --force-reinstall ctranslate2"
echo "  [FIX]   # If that fails, check Python version:"
echo "  [FIX]   python3 --version   # CTranslate2 requires Python 3.8-3.12"
echo ""

echo "  [COMMON ISSUE] CUDA vs CPU vs Metal"
echo "  [INFO]  On macOS Apple Silicon, faster-whisper runs on CPU only"
echo "  [INFO]  There is NO CUDA support on macOS"
echo "  [INFO]  Metal/CoreML acceleration is NOT yet supported by CTranslate2"
echo "  [INFO]  CPU mode on M1/M2/M3/M4 is fast enough (about 10x real-time)"
echo ""
echo "  [RECOMMENDED CONFIG] For macOS Apple Silicon:"
echo "    [CODE] model = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')"
echo "    [INFO] int8 quantization gives best speed on Apple Silicon"
echo "    [INFO] Expected speed: ~10x real-time (6 minutes for 60-min interview)"
echo ""
echo "  [RECOMMENDED CONFIG] For Linux with NVIDIA GPU:"
echo "    [CODE] model = WhisperModel('large-v3-turbo', device='cuda', compute_type='float16')"
echo "    [INFO] Requires: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12"
echo "    [INFO] Expected speed: ~216x real-time (17 seconds for 60-min interview)"
echo ""

echo "  [COMMON ISSUE] 'Model large-v3-turbo not found'"
echo "  [CAUSE] Model needs to download on first use (~1.6GB)"
echo "  [INFO]  First run will auto-download from Hugging Face"
echo "  [FIX]   # Force download:"
echo "  [FIX]   python3 -c \"from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')\""
echo "  [FIX]   # If Hugging Face is blocked, download manually:"
echo "  [FIX]   huggingface-cli download Systran/faster-whisper-large-v3-turbo"
echo ""

echo "  [COMMON ISSUE] 'Memory error' or system freeze during transcription"
echo "  [CAUSE] Model too large for available RAM"
echo "  [FIX]   # Use smaller model:"
echo "  [FIX]   model = WhisperModel('medium', device='cpu', compute_type='int8')   # ~1.5GB RAM"
echo "  [FIX]   model = WhisperModel('small', device='cpu', compute_type='int8')    # ~0.5GB RAM"
echo "  [FIX]   model = WhisperModel('base', device='cpu', compute_type='int8')     # ~0.2GB RAM"
echo ""

# ── 4. Python Version Conflicts ──────────────────────────────────────────
echo "=== 4. PYTHON VERSION CONFLICTS ==="
echo ""

echo "  [CHECK] Python version..."
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo "  [INFO]  System Python: $PY_VER"
echo "  [INFO]  Required: >= 3.11"
echo ""

echo "  [COMMON ISSUE] Multiple Python versions installed"
echo "  [FIX]   which -a python3   # See all installed versions"
echo "  [FIX]   python3.12 --version   # Test specific version"
echo "  [FIX]   # Create venv with specific version:"
echo "  [FIX]   python3.12 -m venv .venv"
echo ""

echo "  [COMMON ISSUE] pip installs to wrong Python"
echo "  [FIX]   # Always use venv pip:"
echo "  [FIX]   source .venv/bin/activate"
echo "  [FIX]   which pip   # Should show .venv/bin/pip"
echo ""

echo "  [COMMON ISSUE] 'python3: No module named venv'"
echo "  [CAUSE] Python installed without venv module (rare on macOS)"
echo "  [FIX]   brew install python@3.12"
echo ""

echo "  [COMMON ISSUE] Pydantic v1 vs v2 conflict"
echo "  [CAUSE] Another package installed pydantic v1"
echo "  [FIX]   pip install 'pydantic>=2.6,<3.0' --force-reinstall"
echo ""

# ── 5. Permission Issues ─────────────────────────────────────────────────
echo "=== 5. PERMISSION ISSUES ==="
echo ""

echo "  [COMMON ISSUE] 'Permission denied' on brew install"
echo "  [FIX]   sudo chown -R \$(whoami) /opt/homebrew"
echo "  [FIX]   # Or for Intel Macs:"
echo "  [FIX]   sudo chown -R \$(whoami) /usr/local"
echo ""

echo "  [COMMON ISSUE] 'Permission denied' on tlmgr install"
echo "  [CAUSE] TeX Live requires root for package installation"
echo "  [FIX]   sudo tlmgr install <package>"
echo ""

echo "  [COMMON ISSUE] 'Operation not permitted' on macOS Ventura+"
echo "  [CAUSE] macOS System Integrity Protection"
echo "  [FIX]   # Grant Terminal full disk access:"
echo "  [FIX]   # System Settings > Privacy & Security > Full Disk Access > Terminal"
echo ""

echo "  [COMMON ISSUE] pip install fails with 'externally-managed-environment'"
echo "  [CAUSE] PEP 668 (Python 3.12+ on macOS)"
echo "  [FIX]   # Always use a virtual environment:"
echo "  [FIX]   python3 -m venv .venv && source .venv/bin/activate && pip install <package>"
echo "  [BAD]   # Do NOT use --break-system-packages"
echo ""

# ── 6. Ollama / ChromaDB Issues ──────────────────────────────────────────
echo "=== 6. OLLAMA / CHROMADB ISSUES ==="
echo ""

echo "  [COMMON ISSUE] 'Connection refused' when pulling models"
echo "  [CAUSE] Ollama server not running"
echo "  [FIX]   ollama serve &"
echo "  [FIX]   # Wait 2 seconds, then:"
echo "  [FIX]   ollama pull nomic-embed-text"
echo ""

echo "  [COMMON ISSUE] ChromaDB 'sqlite3.OperationalError'"
echo "  [CAUSE] SQLite version too old"
echo "  [FIX]   pip install pysqlite3-binary"
echo "  [FIX]   # Then in your code, add before chromadb import:"
echo "  [FIX]   # __import__('pysqlite3'); import sys; sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')"
echo ""

echo "  [COMMON ISSUE] Ollama model takes too long to download"
echo "  [INFO]  nomic-embed-text: ~274MB"
echo "  [INFO]  Expected download time: 1-3 minutes on good connection"
echo "  [FIX]   # If stuck, try direct download:"
echo "  [FIX]   OLLAMA_HOST=http://localhost:11434 ollama pull nomic-embed-text"
echo ""

# ── 7. Nuclear Options ───────────────────────────────────────────────────
echo "=== 7. NUCLEAR OPTIONS (Complete Reinstall) ==="
echo ""

echo "  [OPTION A] Reinstall all Python dependencies:"
echo "    rm -rf .venv"
echo "    python3 -m venv .venv"
echo "    source .venv/bin/activate"
echo "    pip install -e '.[dev]'"
echo "    pip install faster-whisper chromadb textstat"
echo ""

echo "  [OPTION B] Reinstall LaTeX from scratch:"
echo "    brew uninstall --cask basictex"
echo "    brew install --cask basictex"
echo "    export PATH=\"/Library/TeX/texbin:\$PATH\""
echo "    sudo tlmgr update --self"
echo "    sudo tlmgr install memoir tex-gyre fontspec polyglossia lettrine epigraph booktabs longtable hyperref xcolor graphics etoolbox collection-fontsrecommended collection-latexrecommended"
echo ""

echo "  [OPTION C] Reinstall everything:"
echo "    bash scripts/integration-setup.sh"
echo "    bash scripts/verify-integrations.sh"
echo ""

echo "================================================================"
echo "  Run 'bash scripts/verify-integrations.sh' to check status"
echo "================================================================"
