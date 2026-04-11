#!/bin/bash
# run_stt_pipeline.sh -- End-to-end STT pipeline for one interview session.
#
# Chains: preprocess -> transcribe -> quality check
#
# Usage:
#   ./run_stt_pipeline.sh <audio_file> <session_id> [language] [model]
#
# Examples:
#   ./run_stt_pipeline.sh recordings/interview.m4a INT-001 ko
#   ./run_stt_pipeline.sh recordings/interview.wav INT-002 en small
#   ./run_stt_pipeline.sh recordings/interview.mp3 INT-003 ko large-v3-turbo
#
# Requirements:
#   brew install ffmpeg
#   pip install faster-whisper   (in ~/.venvs/stt or current venv)

set -euo pipefail

# ---- arguments ----
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <audio_file> <session_id> [language] [model]"
    echo ""
    echo "  audio_file  : Path to audio (WAV, MP3, M4A, etc.)"
    echo "  session_id  : e.g. INT-001"
    echo "  language    : 'ko', 'en', or omit for auto-detect (default: ko)"
    echo "  model       : tiny, base, small, medium, large-v3, large-v3-turbo"
    echo "                (default: large-v3-turbo)"
    exit 1
fi

AUDIO_FILE="$1"
SESSION_ID="$2"
LANGUAGE="${3:-ko}"
MODEL="${4:-large-v3-turbo}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${PROJECT_DIR}/outputs"

mkdir -p "$OUTPUT_DIR"

echo ""
echo "================================================================"
echo "  STT Pipeline: ${SESSION_ID}"
echo "================================================================"
echo "  Audio    : $AUDIO_FILE"
echo "  Language : $LANGUAGE"
echo "  Model    : $MODEL"
echo "  Output   : $OUTPUT_DIR"
echo "================================================================"
echo ""

# ---- Step 1: Preprocess ----
echo "[1/3] Preprocessing audio ..."
PROCESSED="${OUTPUT_DIR}/${SESSION_ID}_processed.wav"

"$SCRIPT_DIR/preprocess_audio.sh" "$AUDIO_FILE" "$PROCESSED"

echo ""

# ---- Step 2: Transcribe ----
echo "[2/3] Transcribing with faster-whisper ($MODEL) ..."

# Activate venv if it exists
if [[ -d "$HOME/.venvs/stt" ]]; then
    source "$HOME/.venvs/stt/bin/activate"
fi

python3 "$SCRIPT_DIR/transcribe_interview.py" \
    "$PROCESSED" \
    --output "${OUTPUT_DIR}/${SESSION_ID}_transcript.json" \
    --model "$MODEL" \
    --language "$LANGUAGE" \
    --session-id "$SESSION_ID" \
    --raw-segments

echo ""

# ---- Step 3: Quality summary ----
echo "[3/3] Quality assessment ..."

python3 -c "
import json, sys
with open('${OUTPUT_DIR}/${SESSION_ID}_transcript.json') as f:
    data = json.load(f)

q = data.get('_quality', {})
meta = data.get('_stt_metadata', {})

print(f\"  Language         : {meta.get('detected_language', '?')}\")
print(f\"  Duration         : {meta.get('audio_duration_seconds', 0)/60:.1f} min\")
print(f\"  Transcription    : {meta.get('transcription_time_seconds', 0):.1f}s\")
print(f\"  Segments         : {q.get('segments', 0)}\")
print(f\"  Words            : {q.get('total_words', 0)}\")
print(f\"  Quality grade    : {q.get('quality_grade', '?')}\")

if q.get('needs_human_review'):
    print(f\"  ** HUMAN REVIEW RECOMMENDED\")
"

echo ""
echo "================================================================"
echo "  Pipeline complete"
echo "================================================================"
echo "  Transcript : ${OUTPUT_DIR}/${SESSION_ID}_transcript.json"
echo "  Raw segs   : ${OUTPUT_DIR}/${SESSION_ID}_processed_raw_segments.json"
echo "  Processed  : $PROCESSED"
echo ""
echo "  Next steps:"
echo "    1. Review transcript (especially proper nouns)"
echo "    2. Feed to Interview Agent"
echo "================================================================"
