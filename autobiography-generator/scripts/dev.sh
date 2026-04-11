#!/usr/bin/env bash
# ============================================================================
# dev.sh — Development Inner Loop for Rapid Prompt Iteration
#
# Usage:
#   ./scripts/dev.sh <agent-name> <test-input-file> [--compare]
#
# Examples:
#   ./scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json
#   ./scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json --compare
#   ./scripts/dev.sh interviewer test-data/subject-profile.yaml
#   ./scripts/dev.sh voice-profiler test-data/micro-interviews/INT-001-childhood.json
#
# What it does:
#   1. Loads the agent prompt from agents/prompts/<agent-name>.md
#   2. Reads the test input file
#   3. Runs Claude Code with the prompt + input
#   4. Saves output with timestamp for version comparison
#   5. Runs basic quality metrics on the output
#   6. (--compare) Shows diff against the previous run
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Args ────────────────────────────────────────────────────────────────────
AGENT_NAME="${1:?Usage: dev.sh <agent-name> <test-input-file> [--compare]}"
TEST_INPUT="${2:?Usage: dev.sh <agent-name> <test-input-file> [--compare]}"
COMPARE_FLAG="${3:-}"

PROMPT_FILE="agents/prompts/${AGENT_NAME}.md"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
OUTPUT_DIR="outputs/drafts"
OUTPUT_FILE="${OUTPUT_DIR}/${AGENT_NAME}-${TIMESTAMP}.md"
METRICS_FILE="${OUTPUT_DIR}/${AGENT_NAME}-${TIMESTAMP}.metrics.json"

# ── Validation ──────────────────────────────────────────────────────────────
if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Agent prompt not found: $PROMPT_FILE"
    echo "Available agents:"
    ls -1 agents/prompts/*.md 2>/dev/null | xargs -I{} basename {} .md
    exit 1
fi

if [ ! -f "$TEST_INPUT" ]; then
    echo "ERROR: Test input not found: $TEST_INPUT"
    exit 1
fi

echo "============================================"
echo "  DEV LOOP: ${AGENT_NAME}"
echo "  Input:    ${TEST_INPUT}"
echo "  Output:   ${OUTPUT_FILE}"
echo "  Time:     $(date)"
echo "============================================"
echo ""

# ── Extract prompt metadata ────────────────────────────────────────────────
PROMPT_VERSION=$(grep -m1 'version:' "$PROMPT_FILE" | awk '{print $2}' || echo "unknown")
TEMPERATURE=$(grep -m1 'temperature:' "$PROMPT_FILE" | awk '{print $2}' || echo "0.7")
MAX_TOKENS=$(grep -m1 'max_tokens:' "$PROMPT_FILE" | awk '{print $2}' || echo "4000")

echo "[info] Prompt version: ${PROMPT_VERSION}"
echo "[info] Temperature: ${TEMPERATURE}, Max tokens: ${MAX_TOKENS}"
echo ""

# ── Load input data ────────────────────────────────────────────────────────
INPUT_CONTENT=$(cat "$TEST_INPUT")

# ── Load voice profile if it exists ────────────────────────────────────────
VOICE_PROFILE=""
if [ -f "agents/voice-profile.yaml" ]; then
    VOICE_PROFILE=$(cat "agents/voice-profile.yaml")
fi

# ── Strip frontmatter from prompt ──────────────────────────────────────────
PROMPT_BODY=$(awk '/^---$/{if(++c==2) next; if(c==1) next} c>=2{print} c<1{print}' "$PROMPT_FILE")

# ── Build the full prompt ──────────────────────────────────────────────────
# Agent-specific input assembly
case "$AGENT_NAME" in
    chapter-writer)
        FULL_PROMPT="$PROMPT_BODY

## Source Transcripts
\`\`\`json
${INPUT_CONTENT}
\`\`\`

## Voice Profile
\`\`\`yaml
${VOICE_PROFILE}
\`\`\`

## Chapter Details
- Chapter number: 1
- Chapter title: Derive an appropriate title from the transcript content
- Previous chapter ending: (This is the first chapter)

Write the chapter now. Output ONLY the chapter text in markdown."
        ;;
    interviewer)
        FULL_PROMPT="$PROMPT_BODY

## Subject Profile
\`\`\`
${INPUT_CONTENT}
\`\`\`

## Target Life Period
Childhood and early formative years.

## Previous Sessions Summary
No previous sessions.

Generate the interview transcript now. Output as JSON matching the interview_transcript schema."
        ;;
    voice-profiler)
        FULL_PROMPT="$PROMPT_BODY

## Transcripts
\`\`\`json
${INPUT_CONTENT}
\`\`\`

Analyze and output the voice profile in YAML format."
        ;;
    chapter-reviewer)
        FULL_PROMPT="$PROMPT_BODY

## Chapter Draft
\`\`\`
${INPUT_CONTENT}
\`\`\`

## Voice Profile
\`\`\`yaml
${VOICE_PROFILE}
\`\`\`

Review the chapter. Output as JSON."
        ;;
    *)
        FULL_PROMPT="$PROMPT_BODY

## Input
\`\`\`
${INPUT_CONTENT}
\`\`\`

Process the input according to your instructions."
        ;;
esac

# ── Run Claude Code ─────────────────────────────────────────────────────────
echo "[run] Executing Claude Code with ${AGENT_NAME} prompt..."
echo ""

START_TIME=$(date +%s)

# Write prompt to temp file for Claude
TEMP_PROMPT=$(mktemp)
echo "$FULL_PROMPT" > "$TEMP_PROMPT"

# Execute via Claude Code SDK (claude command)
# The --print flag runs non-interactively and outputs directly
claude --print \
    --model claude-sonnet-4-20250514 \
    --max-turns 1 \
    "$(cat "$TEMP_PROMPT")" \
    > "$OUTPUT_FILE" 2>/dev/null

rm -f "$TEMP_PROMPT"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "[done] Generation complete in ${ELAPSED}s"
echo "[done] Output saved to: ${OUTPUT_FILE}"
echo ""

# ── Basic Quality Metrics ──────────────────────────────────────────────────
echo "============================================"
echo "  QUICK METRICS"
echo "============================================"

WORD_COUNT=$(wc -w < "$OUTPUT_FILE" | tr -d ' ')
LINE_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
CHAR_COUNT=$(wc -c < "$OUTPUT_FILE" | tr -d ' ')

# Count paragraphs (blocks separated by blank lines)
PARA_COUNT=$(awk 'BEGIN{p=0} /^$/{if(s) p++; s=0} /[^ ]/{s=1} END{if(s) p++; print p}' "$OUTPUT_FILE")

# Check for direct quotes (text in quotation marks)
QUOTE_COUNT=$(grep -oP '"[^"]{10,}"' "$OUTPUT_FILE" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Check for subject name consistency
if [ -f "$TEST_INPUT" ]; then
    SUBJECT_NAME=$(python3 -c "
import json, sys
try:
    with open('$TEST_INPUT') as f:
        data = json.load(f)
    print(data.get('meta', {}).get('subject_name', ''))
except: pass
" 2>/dev/null || echo "")
    if [ -n "$SUBJECT_NAME" ]; then
        NAME_MENTIONS=$(grep -oi "$SUBJECT_NAME" "$OUTPUT_FILE" 2>/dev/null | wc -l | tr -d ' ')
    else
        NAME_MENTIONS="N/A"
    fi
else
    NAME_MENTIONS="N/A"
fi

echo "  Words:       ${WORD_COUNT}"
echo "  Lines:       ${LINE_COUNT}"
echo "  Paragraphs:  ${PARA_COUNT}"
echo "  Characters:  ${CHAR_COUNT}"
echo "  Quotes used: ${QUOTE_COUNT}"
echo "  Name refs:   ${NAME_MENTIONS}"
echo "  Gen time:    ${ELAPSED}s"
echo ""

# Word count target check
if [ "$AGENT_NAME" == "chapter-writer" ]; then
    if [ "$WORD_COUNT" -lt 3500 ]; then
        echo "  [WARN] Below target: ${WORD_COUNT} < 3500 words"
    elif [ "$WORD_COUNT" -gt 5000 ]; then
        echo "  [WARN] Above target: ${WORD_COUNT} > 5000 words"
    else
        echo "  [PASS] Word count in range (3500-5000)"
    fi
fi

# Save metrics as JSON
cat > "$METRICS_FILE" << METRICSEOF
{
  "agent": "${AGENT_NAME}",
  "prompt_version": "${PROMPT_VERSION}",
  "timestamp": "${TIMESTAMP}",
  "input_file": "${TEST_INPUT}",
  "output_file": "${OUTPUT_FILE}",
  "generation_time_seconds": ${ELAPSED},
  "metrics": {
    "word_count": ${WORD_COUNT},
    "line_count": ${LINE_COUNT},
    "paragraph_count": ${PARA_COUNT},
    "char_count": ${CHAR_COUNT},
    "quote_count": ${QUOTE_COUNT},
    "name_mentions": "${NAME_MENTIONS}"
  }
}
METRICSEOF

echo "[saved] Metrics: ${METRICS_FILE}"

# ── Compare with previous run ──────────────────────────────────────────────
if [ "$COMPARE_FLAG" == "--compare" ]; then
    echo ""
    echo "============================================"
    echo "  COMPARISON WITH PREVIOUS RUN"
    echo "============================================"

    # Find the most recent previous output for this agent
    PREV_OUTPUT=$(ls -t "${OUTPUT_DIR}/${AGENT_NAME}"-*.md 2>/dev/null | grep -v "$OUTPUT_FILE" | head -1)

    if [ -n "$PREV_OUTPUT" ] && [ -f "$PREV_OUTPUT" ]; then
        echo "  Comparing against: $(basename "$PREV_OUTPUT")"
        echo ""

        PREV_WORDS=$(wc -w < "$PREV_OUTPUT" | tr -d ' ')
        WORD_DIFF=$((WORD_COUNT - PREV_WORDS))

        echo "  Word count change: ${PREV_WORDS} -> ${WORD_COUNT} (${WORD_DIFF:+${WORD_DIFF}})"
        echo ""
        echo "  --- Content diff (first 30 changes) ---"
        diff --color=auto -u "$PREV_OUTPUT" "$OUTPUT_FILE" | head -60 || true
    else
        echo "  No previous output found for ${AGENT_NAME}. Run again with --compare."
    fi
fi

echo ""
echo "============================================"
echo "  NEXT STEPS"
echo "============================================"
echo "  Edit prompt:   \$EDITOR agents/prompts/${AGENT_NAME}.md"
echo "  Re-run:        bash scripts/dev.sh ${AGENT_NAME} ${TEST_INPUT}"
echo "  Compare:       bash scripts/dev.sh ${AGENT_NAME} ${TEST_INPUT} --compare"
echo "  Full eval:     cd eval/promptfoo && promptfoo eval"
echo "  Quality check: python3 scripts/check.py outputs/drafts/${AGENT_NAME}-${TIMESTAMP}.md"
echo ""
