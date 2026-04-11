#!/bin/bash
# record_interview.sh -- Record an interview session via macOS microphone.
#
# Usage:
#   ./record_interview.sh                       # defaults: INT-001, mic index 0
#   ./record_interview.sh INT-003               # specify session ID
#   ./record_interview.sh INT-003 1             # specify session ID + mic index
#   ./record_interview.sh --list-devices        # show available microphones
#
# Output: recordings/<SESSION_ID>_<YYYYMMDD_HHMMSS>.wav (16kHz mono PCM)
# Press Ctrl+C to stop recording.
#
# Requirements: brew install ffmpeg

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RECORDINGS_DIR="${PROJECT_DIR}/recordings"

# ---- list devices mode ----
if [[ "${1:-}" == "--list-devices" ]]; then
    echo "Available audio input devices:"
    echo "------------------------------"
    ffmpeg -f avfoundation -list_devices true -i "" 2>&1 \
        | grep -A 20 "AVFoundation audio devices" \
        | grep "^\[" || true
    echo ""
    echo "Use the device index number as the second argument."
    exit 0
fi

# ---- parameters ----
SESSION_ID="${1:-INT-001}"
MIC_INDEX="${2:-0}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RECORDINGS_DIR"
OUTPUT_FILE="${RECORDINGS_DIR}/${SESSION_ID}_${TIMESTAMP}.wav"

# ---- pre-flight checks ----
if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi

# ---- record ----
echo "========================================"
echo "  Interview Recording"
echo "========================================"
echo "  Session ID : $SESSION_ID"
echo "  Microphone : device index $MIC_INDEX"
echo "  Output     : $OUTPUT_FILE"
echo "  Format     : WAV 16kHz mono 16-bit PCM"
echo "========================================"
echo ""
echo "  Press Ctrl+C to stop recording."
echo ""

ffmpeg -f avfoundation -i "none:${MIC_INDEX}" \
    -ar 16000 \
    -ac 1 \
    -c:a pcm_s16le \
    "$OUTPUT_FILE" \
    -loglevel warning

echo ""
echo "Recording saved: $OUTPUT_FILE"

# ---- show duration ----
if command -v ffprobe &>/dev/null; then
    DURATION=$(ffprobe -v error \
        -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 \
        "$OUTPUT_FILE" 2>/dev/null || echo "unknown")
    if [[ "$DURATION" != "unknown" ]]; then
        MINUTES=$(echo "$DURATION / 60" | bc 2>/dev/null || echo "?")
        echo "Duration: ${DURATION}s (~${MINUTES} min)"
    fi
fi

echo ""
echo "Next steps:"
echo "  1. Preprocess:  ./preprocess_audio.sh $OUTPUT_FILE"
echo "  2. Transcribe:  python transcribe_interview.py ${OUTPUT_FILE%.*}_processed.wav"
