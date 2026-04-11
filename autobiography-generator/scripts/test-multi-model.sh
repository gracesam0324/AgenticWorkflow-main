#!/usr/bin/env bash
# ============================================================================
# test-multi-model.sh — Verify Claude / OpenAI / Gemini Access
#
# Tests the FASTEST way to confirm each AI model API works.
# This project runs on Claude Code locally — Claude is the primary model.
# OpenAI and Gemini are optional fallbacks / evaluation models.
#
# Usage:  bash scripts/test-multi-model.sh
# Flags:  --claude-only   Skip OpenAI and Gemini tests
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

CLAUDE_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --claude-only) CLAUDE_ONLY=true ;;
  esac
done

echo "================================================================"
echo "  Multi-Model Access Verification"
echo "  Time: $(date)"
echo "================================================================"
echo ""

# ── 1. Claude (Primary — via Claude Code CLI) ────────────────────────────
echo "[1/3] Claude (Primary Model — Claude Code CLI)..."
echo ""

# Method A: Claude Code CLI (subscription-based, no API key needed)
echo "  Testing Claude Code CLI (subscription access)..."
if command -v claude &>/dev/null; then
  CLAUDE_TEST=$(claude --print --max-turns 1 "Reply with exactly: CLAUDE_OK" 2>/dev/null | head -5)
  if echo "$CLAUDE_TEST" | grep -qi "CLAUDE_OK" 2>/dev/null; then
    echo "  [PASS] Claude Code CLI works (subscription access)"
    echo "  [INFO] Model: Claude Opus 4.6 (1M context) available via CLI"
  else
    echo "  [WARN] Claude responded but output unexpected: $CLAUDE_TEST"
    echo "  [INFO] CLI is connected — may need to check model routing"
  fi
else
  echo "  [FAIL] Claude Code CLI not found"
  echo "  [FIX]  Install: npm install -g @anthropic-ai/claude-code"
  echo "  [FIX]  Then authenticate: claude login"
fi
echo ""

# Method B: Anthropic API directly (for scripts that call API)
echo "  Testing Anthropic API (direct, for validation scripts)..."
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  API_TEST=$(curl -s https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{
      "model": "claude-sonnet-4-20250514",
      "max_tokens": 10,
      "messages": [{"role": "user", "content": "Reply OK"}]
    }' 2>/dev/null || echo '{"error":"connection failed"}')

  if echo "$API_TEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'content' in d else 'FAIL:'+d.get('error',{}).get('message','unknown'))" 2>/dev/null | grep -q "OK"; then
    echo "  [PASS] Anthropic API key works"
  else
    echo "  [WARN] API key set but request failed"
    echo "  [INFO] Check: echo \$ANTHROPIC_API_KEY | head -c 10"
  fi
else
  echo "  [INFO] ANTHROPIC_API_KEY not set (optional — CLI subscription works without it)"
  echo "  [INFO] Only needed if calling API directly from scripts"
  echo "  [SET]  export ANTHROPIC_API_KEY='sk-ant-...'"
fi
echo ""

if $CLAUDE_ONLY; then
  echo "  Skipping OpenAI and Gemini (--claude-only flag)"
  exit 0
fi

# ── 2. OpenAI (Optional — evaluation / comparison) ───────────────────────
echo "[2/3] OpenAI (Optional — for LLM-as-judge evaluation)..."
echo ""

# Method A: ChatGPT Plus subscription via API (most common)
echo "  Testing OpenAI API..."
if [ -n "${OPENAI_API_KEY:-}" ]; then
  OPENAI_TEST=$(curl -s https://api.openai.com/v1/chat/completions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "gpt-4o-mini",
      "max_tokens": 10,
      "messages": [{"role": "user", "content": "Reply OK"}]
    }' 2>/dev/null || echo '{"error":"connection failed"}')

  if echo "$OPENAI_TEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'choices' in d else 'FAIL:'+d.get('error',{}).get('message','unknown'))" 2>/dev/null | grep -q "OK"; then
    echo "  [PASS] OpenAI API works"
    echo "  [INFO] Available for LLM-as-judge evaluation (scripts/judge.py)"
  else
    ERROR_MSG=$(echo "$OPENAI_TEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','unknown error'))" 2>/dev/null || echo "parse error")
    echo "  [FAIL] OpenAI API error: $ERROR_MSG"
    echo ""
    echo "  Possible fixes:"
    echo "    - Billing not set up:  Visit https://platform.openai.com/account/billing"
    echo "    - Wrong key format:    Key should start with 'sk-'"
    echo "    - Rate limited:        Wait 60 seconds and retry"
  fi
else
  echo "  [SKIP] OPENAI_API_KEY not set"
  echo "  [SET]  export OPENAI_API_KEY='sk-...'"
  echo "  [GET]  https://platform.openai.com/api-keys"
  echo "  [NOTE] Only needed for LLM-as-judge evaluation, not core pipeline"
fi
echo ""

# Method B: Check if openai Python package is installed
echo "  Testing openai Python package..."
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
  PYTHON="$VENV_PYTHON"
else
  PYTHON="python3"
fi

if "$PYTHON" -c "import openai; print(openai.__version__)" 2>/dev/null; then
  echo "  [PASS] openai package installed"
else
  echo "  [INFO] openai package not installed"
  echo "  [FIX]  pip install openai    # Only if you want LLM-as-judge evaluation"
fi
echo ""

# ── 3. Gemini (Optional — evaluation / comparison) ───────────────────────
echo "[3/3] Gemini (Optional — for competitive analysis)..."
echo ""

# Method A: Gemini API with API key
echo "  Testing Gemini API..."
if [ -n "${GEMINI_API_KEY:-}" ]; then
  GEMINI_TEST=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "contents": [{"parts": [{"text": "Reply OK"}]}],
      "generationConfig": {"maxOutputTokens": 10}
    }' 2>/dev/null || echo '{"error":"connection failed"}')

  if echo "$GEMINI_TEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'candidates' in d else 'FAIL')" 2>/dev/null | grep -q "OK"; then
    echo "  [PASS] Gemini API works"
  else
    echo "  [FAIL] Gemini API error"
    echo "  [FIX]  Check key at: https://aistudio.google.com/apikey"
  fi
elif [ -n "${GOOGLE_API_KEY:-}" ]; then
  echo "  [INFO] GOOGLE_API_KEY found (may work for Gemini)"
  echo "  [TIP]  Also set: export GEMINI_API_KEY=\$GOOGLE_API_KEY"
else
  echo "  [SKIP] GEMINI_API_KEY not set"
  echo "  [SET]  export GEMINI_API_KEY='AI...'"
  echo "  [GET]  https://aistudio.google.com/apikey (free tier: 15 RPM)"
  echo "  [NOTE] Only needed for competitive analysis, not core pipeline"
fi
echo ""

# Method B: Gemini CLI (subscription-based, Google One AI Premium)
echo "  Testing Gemini CLI..."
if command -v gemini &>/dev/null; then
  echo "  [PASS] Gemini CLI found"
  echo "  [INFO] Test with: gemini -p 'Reply OK'"
else
  echo "  [INFO] Gemini CLI not installed (optional)"
  echo "  [FIX]  npm install -g @anthropic-ai/gemini-cli  # if available"
  echo "  [ALT]  pip install google-generativeai          # Python SDK"
fi
echo ""

# ── Summary ───────────────────────────────────────────────────────────────
echo "================================================================"
echo "  MULTI-MODEL SUMMARY"
echo "================================================================"
echo ""
echo "  Model       Access Method              Required?"
echo "  ─────────   ────────────────────────   ──────────"
echo "  Claude      Claude Code CLI (sub)       YES (primary)"
echo "  Claude      Anthropic API key           Optional (for scripts)"
echo "  OpenAI      API key                     Optional (LLM-judge)"
echo "  Gemini      API key / CLI               Optional (comparison)"
echo ""
echo "  This project runs 100% on Claude Code."
echo "  OpenAI/Gemini are only for evaluation and comparison."
echo ""
echo "  Environment variables to set (in ~/.zshrc or ~/.bashrc):"
echo "    export ANTHROPIC_API_KEY='sk-ant-...'     # Optional"
echo "    export OPENAI_API_KEY='sk-...'             # Optional"
echo "    export GEMINI_API_KEY='AI...'              # Optional"
echo "================================================================"
