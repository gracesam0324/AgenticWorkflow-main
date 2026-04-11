#!/bin/bash
# preprocess_audio.sh -- Prepare audio for Whisper transcription.
#
# Applies: highpass -> lowpass -> noise reduction -> loudness normalization
# Outputs: 16kHz mono 16-bit PCM WAV
#
# Usage:
#   ./preprocess_audio.sh input.m4a                   # output: input_processed.wav
#   ./preprocess_audio.sh input.m4a output.wav         # explicit output path
#   ./preprocess_audio.sh input.wav --skip-denoise     # skip noise reduction
#
# Requirements: brew install ffmpeg

set -euo pipefail

# ---- parse arguments ----
INPUT=""
OUTPUT=""
SKIP_DENOISE=false

for arg in "$@"; do
    case "$arg" in
        --skip-denoise) SKIP_DENOISE=true ;;
        *)
            if [[ -z "$INPUT" ]]; then
                INPUT="$arg"
            elif [[ -z "$OUTPUT" ]]; then
                OUTPUT="$arg"
            fi
            ;;
    esac
done

if [[ -z "$INPUT" ]]; then
    echo "Usage: $0 <input_audio> [output.wav] [--skip-denoise]"
    echo ""
    echo "Supported input formats: WAV, MP3, M4A, FLAC, OGG, WebM, etc."
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "ERROR: Input file not found: $INPUT"
    exit 1
fi

if [[ -z "$OUTPUT" ]]; then
    BASENAME="${INPUT%.*}"
    OUTPUT="${BASENAME}_processed.wav"
fi

# ---- pre-flight ----
if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi

echo "========================================"
echo "  Audio Preprocessing"
echo "========================================"
echo "  Input      : $INPUT"
echo "  Output     : $OUTPUT"
echo "  Denoise    : $(if $SKIP_DENOISE; then echo 'SKIPPED'; else echo 'ON'; fi)"
echo "========================================"

# ---- get input info ----
INPUT_DURATION=$(ffprobe -v error \
    -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    "$INPUT" 2>/dev/null || echo "unknown")
INPUT_RATE=$(ffprobe -v error \
    -select_streams a:0 \
    -show_entries stream=sample_rate \
    -of default=noprint_wrappers=1:nokey=1 \
    "$INPUT" 2>/dev/null || echo "unknown")
INPUT_CHANNELS=$(ffprobe -v error \
    -select_streams a:0 \
    -show_entries stream=channels \
    -of default=noprint_wrappers=1:nokey=1 \
    "$INPUT" 2>/dev/null || echo "unknown")

echo ""
echo "  Input info:"
echo "    Duration : ${INPUT_DURATION}s"
echo "    Rate     : ${INPUT_RATE} Hz"
echo "    Channels : ${INPUT_CHANNELS}"
echo ""

# ---- build filter chain ----
# highpass=80Hz   : remove low-frequency rumble (HVAC, traffic)
# lowpass=8000Hz  : remove high-frequency hiss (above speech range)
# afftdn          : FFT-based noise reduction
# loudnorm        : EBU R128 loudness normalization

if $SKIP_DENOISE; then
    FILTER="highpass=f=80,lowpass=f=8000,loudnorm=I=-16:TP=-1.5:LRA=11"
else
    FILTER="highpass=f=80,lowpass=f=8000,afftdn=nr=12:nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11"
fi

echo "Processing ..."

ffmpeg -y -i "$INPUT" \
    -af "$FILTER" \
    -ar 16000 \
    -ac 1 \
    -c:a pcm_s16le \
    "$OUTPUT" \
    -loglevel warning

# ---- verify output ----
OUTPUT_DURATION=$(ffprobe -v error \
    -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    "$OUTPUT" 2>/dev/null || echo "unknown")
OUTPUT_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT" 2>/dev/null || echo "unknown")

echo ""
echo "  Output info:"
echo "    Duration : ${OUTPUT_DURATION}s"
echo "    Format   : WAV 16kHz mono 16-bit PCM"
echo "    Size     : ${OUTPUT_SIZE} bytes"
echo ""
echo "Done: $OUTPUT"
echo ""
echo "Next: python transcribe_interview.py $OUTPUT"
