# Speech-to-Text Integration Guide for AI Autobiography Generator

> **Scope**: LOCAL-only transcription pipeline for interview audio on macOS (Apple Silicon).
> **Privacy**: All processing runs on-device. No audio leaves the machine.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Complete Installation Guide (macOS Apple Silicon)](#2-complete-installation-guide)
3. [Audio Recording Setup](#3-audio-recording-setup)
4. [Transcription Pipeline Script](#4-transcription-pipeline-script)
5. [Speaker Diarization with WhisperX](#5-speaker-diarization-with-whisperx)
6. [Multilingual Transcription (Korean + English)](#6-multilingual-transcription)
7. [Audio Preprocessing](#7-audio-preprocessing)
8. [Alternative Local STT Options](#8-alternative-local-stt-options)
9. [Quality Assessment](#9-quality-assessment)
10. [Integration with Claude Code Workflow](#10-integration-with-claude-code-workflow)

---

## 1. Architecture Overview

```
┌──────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Interviewer │    │   ffmpeg /   │    │  Audio File     │    │  faster-whisper   │    │  Transcript JSON │
│  + Subject   │───>│   sox rec    │───>│  (.wav 16kHz    │───>│  (large-v3-turbo) │───>│  (interview_     │
│  (speaking)  │    │   (record)   │    │   mono PCM)     │    │  + WhisperX       │    │   transcript     │
└──────────────┘    └──────────────┘    └─────────────────┘    │  (diarization)    │    │   .schema.json)  │
                                                                └─────────────────┘    └────────┬─────────┘
                                                                                                │
                                                                                                v
                                                                                       ┌──────────────────┐
                                                                                       │  Interview Agent │
                                                                                       │  (Claude Code)   │
                                                                                       └──────────────────┘
```

**Pipeline stages**:
1. **Record** -- Capture microphone audio via `ffmpeg` or `sox` on macOS
2. **Preprocess** -- Normalize volume, reduce noise, convert to 16kHz mono WAV
3. **Transcribe** -- Run `faster-whisper` with `large-v3-turbo` model locally on CPU/Metal
4. **Diarize** (optional) -- Identify speakers via WhisperX + pyannote
5. **Structure** -- Convert raw transcript into `interview_transcript.schema.json` format
6. **Deliver** -- Feed structured JSON into the autobiography Interview Agent

---

## 2. Complete Installation Guide

### Prerequisites

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| macOS | 13 Ventura | 14 Sonoma+ |
| Apple Silicon | M1 | M2/M3/M4 |
| Unified Memory | 8 GB | 16 GB+ |
| Python | 3.11 | 3.12 |
| Disk (models) | 2 GB | 6 GB |

### Step 1: System Dependencies

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ffmpeg (audio recording + format conversion)
brew install ffmpeg

# Install sox (optional, alternative recorder)
brew install sox
```

### Step 2: Python Environment

```bash
# Create a dedicated virtual environment (Python 3.12 recommended)
python3.12 -m venv ~/.venvs/stt
source ~/.venvs/stt/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install faster-whisper

```bash
# Core transcription engine
pip install faster-whisper

# CLI wrapper (compatible with openai/whisper CLI interface)
pip install whisper-ctranslate2
```

### Step 4: Install WhisperX (for Speaker Diarization)

```bash
# Install PyTorch first (CPU-only is sufficient on Apple Silicon)
pip install torch torchaudio torchvision

# Install WhisperX
pip install whisperx

# Required for diarization
pip install pyannote.audio==3.1.1
```

### Step 5: Hugging Face Token (required only for diarization)

Speaker diarization uses pyannote models hosted on Hugging Face. You must:

1. Create an account at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens and create a **Read** token
3. Accept the user agreement for the diarization model at:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
4. Store your token:

```bash
# Option A: Environment variable
export HF_TOKEN="hf_your_token_here"

# Option B: huggingface-cli login
pip install huggingface_hub
huggingface-cli login
```

### Step 6: Verify Installation

```bash
# Test faster-whisper loads correctly
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('tiny', device='cpu', compute_type='int8')
print('faster-whisper OK: model loaded')
"

# Test ffmpeg is available
ffmpeg -version | head -1

# List available audio devices
ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A 20 "audio devices"
```

### Step 7: Download the Production Model

```bash
# The model downloads automatically on first use.
# To pre-download, run:
python3 -c "
from faster_whisper import WhisperModel
# large-v3-turbo: best balance of speed and accuracy
# ~1.6 GB download, ~3 GB on disk
model = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')
print('large-v3-turbo model ready')
"
```

### Model Size Reference

| Model | Parameters | Disk Size | RAM (int8) | Speed (10min audio, M2) | Accuracy (WER) |
|-------|-----------|-----------|------------|------------------------|----------------|
| `tiny` | 39M | ~150 MB | ~1 GB | ~10s | ~15% |
| `base` | 74M | ~300 MB | ~1 GB | ~15s | ~12% |
| `small` | 244M | ~950 MB | ~2 GB | ~30s | ~10% |
| `medium` | 769M | ~3 GB | ~5 GB | ~60s | ~8% |
| `large-v3` | 1.55B | ~6 GB | ~10 GB | ~120s | ~7.9% |
| `large-v3-turbo` | 809M | ~3 GB | ~6 GB | ~63s | ~7.8% |

**Recommendation**: Use `large-v3-turbo` for production. It delivers accuracy equivalent to `large-v3` at roughly half the memory and 2x the speed. For quick iteration/testing, use `small`.

---

## 3. Audio Recording Setup

### Method A: ffmpeg (Recommended)

```bash
# Step 1: List available audio input devices
ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -A 10 "audio devices"
# Example output:
#   [AVFoundation input device @ ...] AVFoundation audio devices:
#   [AVFoundation input device @ ...] [0] MacBook Pro Microphone
#   [AVFoundation input device @ ...] [1] External USB Microphone

# Step 2: Record from microphone (device index 0)
# Press Ctrl+C to stop recording
ffmpeg -f avfoundation -i "none:0" \
  -ar 16000 \
  -ac 1 \
  -c:a pcm_s16le \
  interview_raw.wav

# Explanation of flags:
#   -f avfoundation    macOS audio/video capture framework
#   -i "none:0"        no video ("none"), audio device index 0
#   -ar 16000          16 kHz sample rate (optimal for Whisper)
#   -ac 1              mono channel
#   -c:a pcm_s16le     16-bit PCM (standard WAV)
```

### Method B: sox

```bash
# Install sox with support for macOS audio
brew install sox

# Record from default microphone
# Press Ctrl+C to stop
rec -r 16000 -c 1 -b 16 interview_raw.wav
```

### Method C: BlackHole (for System Audio Capture)

Use when recording audio from a video call or other application.

```bash
# Install BlackHole virtual audio driver
brew install blackhole-2ch

# After installation:
# 1. Open Audio MIDI Setup (Applications > Utilities)
# 2. Click "+" at bottom-left > Create Multi-Output Device
# 3. Check both "BlackHole 2ch" and "MacBook Pro Speakers"
# 4. Set Multi-Output Device as system output

# Record system audio routed through BlackHole
ffmpeg -f avfoundation -i "none:BlackHole 2ch" \
  -ar 16000 -ac 1 -c:a pcm_s16le \
  interview_system_audio.wav
```

### Recording Best Practices

| Setting | Value | Rationale |
|---------|-------|-----------|
| Sample rate | 16000 Hz | Whisper's native rate; higher adds no benefit |
| Channels | 1 (mono) | Whisper processes mono; stereo wastes space |
| Bit depth | 16-bit PCM | Standard for speech; lossless |
| Format | WAV | Uncompressed, no transcoding needed |
| Microphone | External USB/headset | Reduces room echo and background noise |
| Environment | Quiet room | Noise degrades WER by 5-15% |
| Duration | 30-60 min per session | Longer files are split automatically by VAD |

### Quick Recording Script

```bash
#!/bin/bash
# record_interview.sh -- Record an interview session
# Usage: ./record_interview.sh [session_id] [mic_device_index]

SESSION_ID="${1:-INT-001}"
MIC_INDEX="${2:-0}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./recordings"

mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="${OUTPUT_DIR}/${SESSION_ID}_${TIMESTAMP}.wav"

echo "Recording interview session: $SESSION_ID"
echo "Microphone device index: $MIC_INDEX"
echo "Output: $OUTPUT_FILE"
echo "Press Ctrl+C to stop recording."
echo "---"

ffmpeg -f avfoundation -i "none:${MIC_INDEX}" \
  -ar 16000 -ac 1 -c:a pcm_s16le \
  "$OUTPUT_FILE" 2>/dev/null

echo ""
echo "Recording saved: $OUTPUT_FILE"
DURATION=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_FILE")
echo "Duration: ${DURATION}s"
```

---

## 4. Transcription Pipeline Script

This is the core Python script that takes an audio file, transcribes it with faster-whisper, and outputs structured JSON matching the `interview_transcript.schema.json` schema.

```python
#!/usr/bin/env python3
"""
transcribe_interview.py -- Local STT pipeline for autobiography interviews.

Transcribes audio using faster-whisper, optionally performs speaker diarization
via WhisperX, and outputs structured JSON matching interview_transcript.schema.json.

Usage:
    python transcribe_interview.py input.wav --output transcript.json
    python transcribe_interview.py input.wav --diarize --hf-token hf_xxx
    python transcribe_interview.py input.wav --language ko --model large-v3-turbo
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional


def load_faster_whisper(model_size: str, compute_type: str, device: str):
    """Load faster-whisper model."""
    from faster_whisper import WhisperModel

    print(f"Loading model: {model_size} (device={device}, compute_type={compute_type})")
    t0 = time.time()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print(f"Model loaded in {time.time() - t0:.1f}s")
    return model


def transcribe_audio(
    model,
    audio_path: str,
    language: Optional[str] = None,
    beam_size: int = 5,
    vad_filter: bool = True,
):
    """
    Transcribe audio file using faster-whisper.

    Returns:
        segments: list of segment dicts with start, end, text
        info: transcription info (language, duration, etc.)
    """
    print(f"Transcribing: {audio_path}")
    t0 = time.time()

    segments_gen, info = model.transcribe(
        audio_path,
        language=language,       # None = auto-detect
        beam_size=beam_size,
        vad_filter=vad_filter,   # Voice Activity Detection to skip silence
        vad_parameters=dict(
            min_silence_duration_ms=500,   # minimum silence to split
            speech_pad_ms=200,             # padding around speech
        ),
        word_timestamps=True,    # enable word-level timestamps
    )

    detected_lang = info.language
    lang_prob = info.language_probability
    duration = info.duration
    print(f"Detected language: {detected_lang} (probability: {lang_prob:.2f})")
    print(f"Audio duration: {duration:.1f}s")

    # Materialize generator into list
    result_segments = []
    for seg in segments_gen:
        result_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": [
                {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                for w in (seg.words or [])
            ],
        })

    elapsed = time.time() - t0
    print(f"Transcription complete in {elapsed:.1f}s ({len(result_segments)} segments)")
    print(f"Real-time factor: {elapsed / duration:.2f}x")

    return result_segments, {
        "language": detected_lang,
        "language_probability": lang_prob,
        "duration_seconds": duration,
        "transcription_time_seconds": elapsed,
    }


def diarize_audio(audio_path: str, hf_token: str, num_speakers: int = 2):
    """
    Perform speaker diarization using WhisperX + pyannote.

    Returns:
        list of dicts with start, end, speaker label
    """
    try:
        import whisperx
    except ImportError:
        print("ERROR: whisperx not installed. Run: pip install whisperx")
        sys.exit(1)

    print(f"Running speaker diarization (expecting {num_speakers} speakers)...")
    t0 = time.time()

    diarize_model = whisperx.DiarizationPipeline(
        use_auth_token=hf_token,
        device="cpu",
    )

    # Load audio
    audio = whisperx.load_audio(audio_path)

    diarize_result = diarize_model(
        audio,
        num_speakers=num_speakers,
    )

    # Convert to list of dicts
    diarization_segments = []
    for _, row in diarize_result.iterrows():
        diarization_segments.append({
            "start": row["start"],
            "end": row["end"],
            "speaker": row["speaker"],
        })

    print(f"Diarization complete in {time.time() - t0:.1f}s")
    speakers = set(s["speaker"] for s in diarization_segments)
    print(f"Identified {len(speakers)} speakers: {', '.join(sorted(speakers))}")

    return diarization_segments


def assign_speakers(
    transcript_segments: list,
    diarization_segments: list,
    speaker_map: Optional[dict] = None,
) -> list:
    """
    Merge diarization labels into transcript segments.

    speaker_map: e.g. {"SPEAKER_00": "interviewer", "SPEAKER_01": "subject"}
    """
    if not speaker_map:
        speaker_map = {}

    for seg in transcript_segments:
        seg_mid = (seg["start"] + seg["end"]) / 2.0
        best_speaker = "unknown"
        for d in diarization_segments:
            if d["start"] <= seg_mid <= d["end"]:
                best_speaker = d["speaker"]
                break
        seg["speaker"] = speaker_map.get(best_speaker, best_speaker)

    return transcript_segments


def group_into_topic_segments(
    transcript_segments: list,
    max_segment_duration: float = 300.0,  # 5 minutes
) -> list:
    """
    Group raw whisper segments into larger thematic segments
    suitable for interview_transcript.schema.json.

    Groups by time proximity. Each group becomes one schema segment.
    """
    if not transcript_segments:
        return []

    groups = []
    current_group = [transcript_segments[0]]

    for seg in transcript_segments[1:]:
        prev_end = current_group[-1]["end"]
        gap = seg["start"] - prev_end
        group_duration = seg["end"] - current_group[0]["start"]

        # Split on long silences (>3s) or when max duration exceeded
        if gap > 3.0 or group_duration > max_segment_duration:
            groups.append(current_group)
            current_group = [seg]
        else:
            current_group.append(seg)

    if current_group:
        groups.append(current_group)

    return groups


def build_schema_json(
    groups: list,
    transcription_info: dict,
    session_id: str = "INT-001",
    subject_name: str = "Subject",
    interviewer_type: str = "human",
    life_period_label: str = "General",
    start_year: int = 2000,
) -> dict:
    """
    Build the interview_transcript.schema.json-compliant output.
    """
    segments = []
    full_text_parts = []

    for i, group in enumerate(groups, 1):
        seg_id = f"SEG-{i:03d}"

        # Combine text from all whisper segments in this group
        texts = []
        for seg in group:
            speaker_prefix = ""
            if "speaker" in seg:
                speaker_prefix = f"[{seg['speaker']}] "
            texts.append(f"{speaker_prefix}{seg['text']}")

        content = "\n".join(texts)
        full_text_parts.append(content)

        segment_entry = {
            "segment_id": seg_id,
            "topic": f"Segment {i}",  # placeholder -- to be refined by Interview Agent
            "content": content,
        }

        # Add key quotes (sentences with high word confidence)
        high_confidence_quotes = []
        for seg in group:
            avg_prob = 0.0
            if seg.get("words"):
                probs = [w["probability"] for w in seg["words"] if w["probability"]]
                avg_prob = sum(probs) / len(probs) if probs else 0
            if avg_prob > 0.9 and len(seg["text"]) > 30:
                high_confidence_quotes.append({
                    "text": seg["text"],
                    "context": f"Transcribed at {seg['start']:.1f}s-{seg['end']:.1f}s "
                               f"(avg word confidence: {avg_prob:.2f})",
                    "usable_in_chapter": True,
                })

        if high_confidence_quotes:
            segment_entry["key_quotes"] = high_confidence_quotes[:5]

        segments.append(segment_entry)

    duration_minutes = int(transcription_info["duration_seconds"] / 60)

    result = {
        "meta": {
            "session_id": session_id,
            "subject_name": subject_name,
            "interviewer": interviewer_type,
            "date": date.today().isoformat(),
            "duration_minutes": max(5, duration_minutes),
            "life_period": {
                "label": life_period_label,
                "start_year": start_year,
            },
            "themes": ["general"],  # placeholder -- to be refined
            "emotional_tone": "neutral",  # placeholder -- to be refined
        },
        "segments": segments,
        "_stt_metadata": {
            "engine": "faster-whisper",
            "model": "large-v3-turbo",
            "detected_language": transcription_info["language"],
            "language_probability": transcription_info["language_probability"],
            "audio_duration_seconds": transcription_info["duration_seconds"],
            "transcription_time_seconds": transcription_info["transcription_time_seconds"],
            "word_timestamps": True,
        },
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe interview audio to structured JSON (local-only)."
    )
    parser.add_argument("audio_file", help="Path to audio file (WAV, MP3, M4A, etc.)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON path (default: <input>_transcript.json)")
    parser.add_argument("--model", default="large-v3-turbo",
                        choices=["tiny", "base", "small", "medium",
                                 "large-v3", "large-v3-turbo"],
                        help="Whisper model size (default: large-v3-turbo)")
    parser.add_argument("--language", "-l", default=None,
                        help="Language code (e.g., 'ko', 'en'). None=auto-detect")
    parser.add_argument("--compute-type", default="int8",
                        choices=["int8", "float32"],
                        help="Quantization type (default: int8, best for Apple Silicon CPU)")
    parser.add_argument("--device", default="cpu",
                        choices=["cpu", "auto"],
                        help="Device (default: cpu)")
    parser.add_argument("--beam-size", type=int, default=5,
                        help="Beam search size (default: 5)")

    # Diarization options
    parser.add_argument("--diarize", action="store_true",
                        help="Enable speaker diarization via WhisperX")
    parser.add_argument("--hf-token", default=None,
                        help="Hugging Face token (or set HF_TOKEN env var)")
    parser.add_argument("--num-speakers", type=int, default=2,
                        help="Expected number of speakers (default: 2)")
    parser.add_argument("--speaker-map", default=None,
                        help='Speaker label mapping as JSON, e.g. '
                             '\'{"SPEAKER_00":"interviewer","SPEAKER_01":"subject"}\'')

    # Metadata options
    parser.add_argument("--session-id", default="INT-001",
                        help="Session identifier (default: INT-001)")
    parser.add_argument("--subject-name", default="Subject",
                        help="Subject's name")
    parser.add_argument("--interviewer-type", default="human",
                        choices=["human", "ai-guided"])
    parser.add_argument("--life-period", default="General",
                        help="Life period label")
    parser.add_argument("--start-year", type=int, default=2000,
                        help="Life period start year")

    # Output options
    parser.add_argument("--raw-segments", action="store_true",
                        help="Also save raw whisper segments to a separate file")

    args = parser.parse_args()

    # Validate input
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = audio_path.with_suffix("").with_name(
            audio_path.stem + "_transcript.json"
        )

    # Load model and transcribe
    model = load_faster_whisper(args.model, args.compute_type, args.device)
    segments, info = transcribe_audio(
        model, str(audio_path),
        language=args.language,
        beam_size=args.beam_size,
    )

    # Save raw segments if requested
    if args.raw_segments:
        raw_path = audio_path.with_suffix("").with_name(audio_path.stem + "_raw.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump({"segments": segments, "info": info}, f,
                      ensure_ascii=False, indent=2)
        print(f"Raw segments saved: {raw_path}")

    # Speaker diarization (optional)
    if args.diarize:
        hf_token = args.hf_token or os.environ.get("HF_TOKEN")
        if not hf_token:
            print("ERROR: --hf-token or HF_TOKEN env var required for diarization")
            sys.exit(1)

        diar_segments = diarize_audio(str(audio_path), hf_token, args.num_speakers)

        speaker_map = {}
        if args.speaker_map:
            speaker_map = json.loads(args.speaker_map)

        segments = assign_speakers(segments, diar_segments, speaker_map)

    # Group into topic segments
    groups = group_into_topic_segments(segments)

    # Build schema-compliant JSON
    result = build_schema_json(
        groups, info,
        session_id=args.session_id,
        subject_name=args.subject_name,
        interviewer_type=args.interviewer_type,
        life_period_label=args.life_period,
        start_year=args.start_year,
    )

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nTranscript saved: {output_path}")
    print(f"  Segments: {len(result['segments'])}")
    print(f"  Language: {info['language']}")
    print(f"  Duration: {info['duration_seconds'] / 60:.1f} min")

    return result


if __name__ == "__main__":
    main()
```

---

## 5. Speaker Diarization with WhisperX

### What Diarization Does

Speaker diarization identifies **who is speaking when**. For autobiography interviews, this distinguishes the **interviewer** from the **subject** -- critical for isolating the subject's own words.

### How It Works

WhisperX integrates pyannote.audio's speaker diarization pipeline:

1. **Segmentation** -- pyannote/segmentation-3.0 detects speech regions and boundaries
2. **Embedding** -- Speaker embeddings are extracted for each speech region
3. **Clustering** -- Embeddings are clustered to assign speaker identities (SPEAKER_00, SPEAKER_01, etc.)
4. **Alignment** -- Speaker labels are merged with whisper transcript timestamps

### Usage

```bash
# Basic diarization (2 speakers: interviewer + subject)
python transcribe_interview.py interview.wav \
  --diarize \
  --hf-token hf_your_token \
  --num-speakers 2 \
  --speaker-map '{"SPEAKER_00": "interviewer", "SPEAKER_01": "subject"}'
```

### Speaker Identification Tips

- **SPEAKER_00** is typically the first person who speaks. If the interviewer opens the session, SPEAKER_00 = interviewer.
- Run a short test clip first to verify which SPEAKER_XX maps to whom.
- The `--speaker-map` flag lets you assign human-readable labels.
- For multi-person interviews (e.g., family sessions), increase `--num-speakers`.

### Accuracy Expectations

| Scenario | Diarization Error Rate (DER) |
|----------|------------------------------|
| 2 speakers, clear turns, quiet room | 5-10% |
| 2 speakers, overlapping speech | 15-25% |
| 3+ speakers | 15-30% |
| Noisy environment | 20-35% |

### Known Limitations

- Diarization on CPU is slower than transcription (expect 0.5-1x real-time)
- Overlapping speech is the hardest case -- segments where both speak simultaneously may be misattributed
- The Hugging Face token requirement means you must accept the model license online (one-time setup)

---

## 6. Multilingual Transcription

### Korean + English Support

Whisper's `large-v3-turbo` supports 99 languages including Korean and English natively.

### Language Detection vs. Explicit Setting

```python
# Auto-detect (works well for monolingual audio)
segments, info = model.transcribe("interview.wav", language=None)

# Force Korean (recommended when you know the language)
segments, info = model.transcribe("interview.wav", language="ko")

# Force English
segments, info = model.transcribe("interview.wav", language="en")
```

**Recommendation**: Always set `language` explicitly when you know the primary language. Auto-detection uses the first 30 seconds and may misidentify in multilingual recordings.

### Code-Switching (Korean and English in Same Interview)

This is the hardest scenario. Whisper handles it with varying success:

| Pattern | Whisper Behavior | Quality |
|---------|-----------------|---------|
| Mostly Korean, occasional English terms | Good -- English terms usually preserved | High |
| Roughly 50/50 Korean/English | Inconsistent -- may force one language | Medium |
| Full sentences alternating languages | Segments may individually detect correct language | Medium |
| Mid-sentence language switches | Weakest case -- may transliterate or mistranscribe | Low |

**Strategies for code-switching**:

1. **Set language to the dominant one** -- If 70%+ Korean, use `--language ko`
2. **Use `initial_prompt` for context** -- Include expected English terms:
   ```python
   segments, info = model.transcribe(
       "interview.wav",
       language="ko",
       initial_prompt="AI, Machine Learning, Claude, startup, 서울대학교, 삼성전자"
   )
   ```
3. **Post-process with Claude** -- Feed the raw transcript to Claude Code for cleanup of code-switched terms

### Korean-Specific Performance

| Metric | Value | Notes |
|--------|-------|-------|
| CER (large-v3-turbo, clean audio) | ~6-10% | Character Error Rate preferred over WER for Korean |
| CER (with noise) | ~12-20% | Degrades faster than English in noisy conditions |
| Spacing accuracy | ~85-90% | Korean spacing (띄어쓰기) often incorrect |
| Punctuation | ~80% | May miss or add incorrect sentence endings |

### Korean Post-Processing

Korean transcription output typically needs spacing correction. Options:

1. **pykospacing** -- Neural network-based Korean spacing corrector:
   ```bash
   pip install pykospacing
   ```
   ```python
   from pykospacing import Spacing
   spacing = Spacing()
   corrected = spacing("이것은띄어쓰기가필요한문장입니다")
   # "이것은 띄어쓰기가 필요한 문장입니다"
   ```

2. **Claude post-processing** -- Feed raw transcript to Claude for natural spacing and punctuation:
   ```
   Fix the Korean spacing and punctuation in this transcript,
   preserving the exact words. Do not paraphrase.
   ```

3. **hanspell** -- Korean spell checker:
   ```bash
   pip install py-hanspell
   ```

---

## 7. Audio Preprocessing

### When to Preprocess

| Audio Quality | Preprocessing Needed? | Steps |
|--------------|----------------------|-------|
| Studio/quiet room, external mic | No | Direct transcription |
| Quiet room, laptop mic | Minimal | Normalize only |
| Moderate background noise | Yes | Noise reduction + normalize |
| Noisy environment | Yes | Full pipeline |

**Caution**: Over-processing clean audio can *degrade* accuracy. Only apply noise reduction when audible noise is present.

### Preprocessing Pipeline with ffmpeg

```bash
# Full preprocessing pipeline
# 1. Convert to 16kHz mono WAV (required format)
# 2. Apply noise reduction (afftdn filter)
# 3. Normalize loudness (loudnorm filter)

ffmpeg -i interview_raw.m4a \
  -af "afftdn=nr=12:nf=-20,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 16000 -ac 1 -c:a pcm_s16le \
  interview_processed.wav

# Explanation:
#   afftdn=nr=12:nf=-20     Noise reduction (nr=strength, nf=floor in dB)
#   loudnorm=I=-16:TP=-1.5  EBU R128 loudness normalization
#   -ar 16000               Resample to 16kHz
#   -ac 1                   Convert to mono
#   -c:a pcm_s16le          16-bit PCM WAV output
```

### Preprocessing Script

```bash
#!/bin/bash
# preprocess_audio.sh -- Prepare audio for Whisper transcription
# Usage: ./preprocess_audio.sh input.m4a [output.wav]

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}_processed.wav}"

if [ -z "$INPUT" ]; then
    echo "Usage: $0 <input_audio> [output.wav]"
    exit 1
fi

echo "Input:  $INPUT"
echo "Output: $OUTPUT"

# Check if noise reduction is needed (analyze noise floor)
echo "Analyzing audio..."
NOISE_LEVEL=$(ffmpeg -i "$INPUT" -af "astats=metadata=1:reset=1" \
  -f null - 2>&1 | grep "RMS level" | tail -1 | awk '{print $NF}')
echo "RMS noise level: $NOISE_LEVEL dB"

# Apply preprocessing
ffmpeg -y -i "$INPUT" \
  -af "highpass=f=80,lowpass=f=8000,afftdn=nr=12:nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 16000 -ac 1 -c:a pcm_s16le \
  "$OUTPUT" 2>/dev/null

echo "Preprocessed audio saved: $OUTPUT"
DURATION=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$OUTPUT")
echo "Duration: ${DURATION}s"
```

### Supported Input Formats

Whisper (via ffmpeg) accepts virtually any audio format:

| Format | Extension | Notes |
|--------|----------|-------|
| WAV | .wav | Preferred, no conversion needed if 16kHz mono |
| MP3 | .mp3 | Common, automatically decoded |
| M4A/AAC | .m4a | iPhone/Mac default recording format |
| FLAC | .flac | Lossless, larger files |
| OGG/Opus | .ogg, .opus | Common in messaging apps |
| WebM | .webm | Browser recordings |

---

## 8. Alternative Local STT Options

### Comparison Matrix

| Feature | faster-whisper | Vosk | Apple SpeechAnalyzer |
|---------|---------------|------|---------------------|
| **Accuracy (English)** | ~7.8% WER | ~10-15% WER | ~8-10% WER (estimated) |
| **Accuracy (Korean)** | ~6-10% CER | ~15-20% CER | Good (Apple optimized) |
| **Speed** | 0.1-0.5x real-time | 0.05-0.1x real-time | Real-time capable |
| **RAM (best model)** | 3-6 GB | 50 MB - 1 GB | System managed |
| **Model download** | 150 MB - 6 GB | 50 MB per language | Pre-installed on macOS |
| **Speaker diarization** | Via WhisperX | No | No |
| **Word timestamps** | Yes | Yes | Yes |
| **Code-switching** | Medium support | Poor | Unknown |
| **Python API** | Yes | Yes | Swift only (bridgeable) |
| **Streaming/real-time** | Limited | Yes | Yes |
| **Setup complexity** | Medium | Low | Low (requires Xcode) |
| **Privacy** | Fully local | Fully local | Fully local |

### Vosk

Best for: real-time transcription, very low resource environments.

```bash
pip install vosk

# Download Korean model (~50 MB)
# https://alphacephei.com/vosk/models
```

```python
import json
import wave
from vosk import Model, KaldiRecognizer

model = Model("vosk-model-small-ko-0.22")
wf = wave.open("interview.wav", "rb")
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)

results = []
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        results.append(json.loads(rec.Result()))
results.append(json.loads(rec.FinalResult()))

for r in results:
    print(r.get("text", ""))
```

**Verdict**: Vosk is 50-100x smaller and streams in real-time, but accuracy is significantly lower than Whisper, especially for Korean. Use it only if RAM is severely constrained (<4 GB) or real-time output is required.

### Apple SpeechAnalyzer (macOS 26+ / iOS 26+)

Apple introduced SpeechAnalyzer at WWDC 2025 as the replacement for SFSpeechRecognizer. It runs entirely on-device, uses Apple's own optimized speech models, and requires no model download (models are stored in system storage).

```swift
// Swift usage (requires Xcode, macOS 26+)
import SpeechAnalyzer

let analyzer = SpeechAnalyzer()
let result = try await analyzer.transcribe(audioFileURL)
for segment in result.segments {
    print("\(segment.startTime) - \(segment.endTime): \(segment.text)")
}
```

**Verdict**: Promising but limited for this use case. No Python API (Swift-only), no speaker diarization, and requires macOS 26+. Better suited as a future fallback than a primary engine.

### Recommendation

**Use faster-whisper (large-v3-turbo) as the primary engine.** It offers the best accuracy-to-resource ratio for batch interview transcription, supports Korean well, and integrates with WhisperX for speaker diarization.

---

## 9. Quality Assessment

### Expected Accuracy by Scenario

| Scenario | English WER | Korean CER | Notes |
|----------|-------------|------------|-------|
| Clean audio, single speaker, quiet room | 5-7% | 6-8% | Best case |
| Clean audio, two speakers, turn-taking | 7-10% | 8-12% | Standard interview |
| Moderate noise, two speakers | 12-18% | 15-22% | Needs preprocessing |
| Elderly speaker, quiet room | 10-15% | 12-18% | Atypical speech patterns |
| Code-switching (Korean/English) | 12-20% | 15-25% | Hardest case |

### Common Transcription Errors

| Error Type | Example | Frequency | Mitigation |
|-----------|---------|-----------|------------|
| Homophones | "there/their/they're" | Medium | Claude post-processing |
| Proper nouns | "Samsung" -> "Sam Sung" | High | Use `initial_prompt` |
| Korean spacing | "서울대학교" spacing errors | High | pykospacing or Claude |
| Filler words | "um", "uh", "그니까" | Medium | Post-filter or keep |
| Hallucinated text | Repeated phrases in silence | Low | VAD filter eliminates most |
| Number formatting | "nineteen eighty-five" | Medium | Regex post-processing |

### When Human Correction Is Needed

| Confidence Threshold | Action |
|---------------------|--------|
| Word probability > 0.9 | Accept as-is |
| Word probability 0.7-0.9 | Flag for optional review |
| Word probability < 0.7 | Flag for human review |
| Proper nouns (names, places) | Always review |
| Key quotes for the book | Always review |

### Quality Validation Script

```python
def assess_transcript_quality(transcript_json: dict) -> dict:
    """Analyze transcript quality metrics."""
    segments = transcript_json.get("segments", [])
    stt_meta = transcript_json.get("_stt_metadata", {})

    total_words = 0
    low_confidence_words = 0
    high_confidence_words = 0
    all_probs = []

    for seg in segments:
        content = seg.get("content", "")
        total_words += len(content.split())

        for quote in seg.get("key_quotes", []):
            ctx = quote.get("context", "")
            if "avg word confidence" in ctx:
                prob = float(ctx.split("confidence: ")[1].rstrip(")"))
                all_probs.append(prob)

    avg_confidence = sum(all_probs) / len(all_probs) if all_probs else 0

    return {
        "total_segments": len(segments),
        "total_words": total_words,
        "average_key_quote_confidence": round(avg_confidence, 3),
        "detected_language": stt_meta.get("detected_language", "unknown"),
        "language_probability": stt_meta.get("language_probability", 0),
        "real_time_factor": round(
            stt_meta.get("transcription_time_seconds", 0) /
            max(stt_meta.get("audio_duration_seconds", 1), 1), 2
        ),
        "needs_human_review": avg_confidence < 0.85,
        "quality_grade": (
            "A" if avg_confidence > 0.95 else
            "B" if avg_confidence > 0.90 else
            "C" if avg_confidence > 0.85 else
            "D (human review recommended)"
        ),
    }
```

---

## 10. Integration with Claude Code Workflow

### How Transcription Fits the Autobiography Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Autobiography Generator Workflow                     │
│                                                                         │
│  ┌────────────┐    ┌──────────────┐    ┌──────────────┐                │
│  │ 1. Record  │───>│ 2. Transcribe│───>│ 3. Structure │                │
│  │ Interview  │    │ (this guide) │    │ (this guide) │                │
│  └────────────┘    └──────────────┘    └──────┬───────┘                │
│                                               │                         │
│                                               v                         │
│                                    ┌──────────────────┐                 │
│                                    │ interview_       │                 │
│                                    │ transcript.json   │                │
│                                    │ (schema-compliant)│                │
│                                    └────────┬─────────┘                │
│                                             │                           │
│                                             v                           │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │             Existing Workflow Stages                          │       │
│  │  Interview Agent -> Story Bible -> Chapter Draft -> ...      │       │
│  └──────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Triggering Transcription from Claude Code

Since the autobiography workflow runs within Claude Code, transcription is invoked via the Bash tool:

```bash
# From within a Claude Code agent session:

# Step 1: Activate the STT virtual environment
source ~/.venvs/stt/bin/activate

# Step 2: Run transcription
python autobiography-generator/scripts/transcribe_interview.py \
  recordings/INT-001_20260317.wav \
  --output autobiography-generator/outputs/INT-001_transcript.json \
  --model large-v3-turbo \
  --language ko \
  --session-id INT-001 \
  --subject-name "Kim Minjun" \
  --life-period "Childhood in Seoul" \
  --start-year 1985 \
  --diarize \
  --hf-token "$HF_TOKEN" \
  --speaker-map '{"SPEAKER_00": "interviewer", "SPEAKER_01": "subject"}'
```

### Workflow Step Configuration

In the autobiography workflow, add an STT step before the Interview Agent step:

```yaml
# In workflow.md or equivalent configuration
steps:
  - id: record-interview
    type: human
    description: "Record interview audio (WAV, 16kHz mono)"
    output: recordings/{session_id}_{timestamp}.wav

  - id: transcribe-interview
    type: bash
    description: "Transcribe interview audio to structured JSON"
    command: |
      source ~/.venvs/stt/bin/activate
      python scripts/transcribe_interview.py \
        {prev.output} \
        --output outputs/{session_id}_transcript.json \
        --model large-v3-turbo \
        --language {language}
    output: outputs/{session_id}_transcript.json

  - id: review-transcript
    type: human
    description: "Review transcript for accuracy (especially proper nouns)"
    input: outputs/{session_id}_transcript.json

  - id: interview-agent
    type: agent
    agent: interviewer
    input: outputs/{session_id}_transcript.json
```

### End-to-End Shell Script

```bash
#!/bin/bash
# run_stt_pipeline.sh -- Complete STT pipeline for one interview session
# Usage: ./run_stt_pipeline.sh <audio_file> <session_id> [language]

set -euo pipefail

AUDIO_FILE="$1"
SESSION_ID="$2"
LANGUAGE="${3:-ko}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="${PROJECT_DIR}/outputs"
SCRIPTS_DIR="${PROJECT_DIR}/scripts"

mkdir -p "$OUTPUT_DIR"

echo "=== STT Pipeline: ${SESSION_ID} ==="
echo "Audio: ${AUDIO_FILE}"
echo "Language: ${LANGUAGE}"
echo ""

# Step 1: Preprocess audio
echo "[1/3] Preprocessing audio..."
PROCESSED="${OUTPUT_DIR}/${SESSION_ID}_processed.wav"
ffmpeg -y -i "$AUDIO_FILE" \
  -af "highpass=f=80,lowpass=f=8000,afftdn=nr=10:nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 16000 -ac 1 -c:a pcm_s16le \
  "$PROCESSED" 2>/dev/null
echo "  Preprocessed: $PROCESSED"

# Step 2: Transcribe
echo "[2/3] Transcribing with faster-whisper..."
source ~/.venvs/stt/bin/activate
python "${SCRIPTS_DIR}/transcribe_interview.py" \
  "$PROCESSED" \
  --output "${OUTPUT_DIR}/${SESSION_ID}_transcript.json" \
  --model large-v3-turbo \
  --language "$LANGUAGE" \
  --session-id "$SESSION_ID" \
  --raw-segments

echo ""

# Step 3: Quality check
echo "[3/3] Quality assessment..."
python -c "
import json
with open('${OUTPUT_DIR}/${SESSION_ID}_transcript.json') as f:
    data = json.load(f)
meta = data.get('_stt_metadata', {})
print(f\"  Language: {meta.get('detected_language', '?')}\")
print(f\"  Duration: {meta.get('audio_duration_seconds', 0)/60:.1f} min\")
print(f\"  Speed: {meta.get('transcription_time_seconds', 0):.1f}s\")
print(f\"  Segments: {len(data.get('segments', []))}\")
"

echo ""
echo "=== Pipeline complete ==="
echo "Transcript: ${OUTPUT_DIR}/${SESSION_ID}_transcript.json"
echo "Next: Review transcript, then feed to Interview Agent."
```

---

## Appendix A: Quick Reference Commands

```bash
# Record interview (Ctrl+C to stop)
ffmpeg -f avfoundation -i "none:0" -ar 16000 -ac 1 -c:a pcm_s16le interview.wav

# Transcribe (Korean, large-v3-turbo)
python transcribe_interview.py interview.wav -l ko -o transcript.json

# Transcribe with diarization
python transcribe_interview.py interview.wav -l ko --diarize --hf-token $HF_TOKEN

# Transcribe (English, fast test with small model)
python transcribe_interview.py interview.wav -l en --model small

# Preprocess noisy audio
ffmpeg -i noisy.m4a -af "afftdn=nr=12,loudnorm" -ar 16000 -ac 1 clean.wav

# List microphones
ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep audio

# Check model is cached
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')"
```

## Appendix B: Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: faster_whisper` | Not in venv | `source ~/.venvs/stt/bin/activate` |
| `float16 not supported` | Apple Silicon CPU limitation | Use `--compute-type int8` |
| Model download hangs | Network/firewall | Pre-download model, or check proxy |
| Korean text has no spaces | Whisper spacing limitation | Post-process with pykospacing |
| Transcript has hallucinated repeats | Silence in audio | Enable VAD filter (default on) |
| `SPEAKER_00` / `SPEAKER_01` wrong | First speaker auto-assigned | Use `--speaker-map` to remap |
| Diarization fails | Missing HF token or model access | Accept model license on HF website |
| Memory crash with large-v3 | Not enough RAM | Use `large-v3-turbo` or `medium` instead |
| FFmpeg "no such device" | Wrong device index | Re-run device listing command |

## Appendix C: Sources

### faster-whisper
- [SYSTRAN/faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [faster-whisper PyPI](https://pypi.org/project/faster-whisper/)
- [whisper-ctranslate2 PyPI](https://pypi.org/project/whisper-ctranslate2/)
- [Whisper Large V3 Turbo -- Hugging Face](https://huggingface.co/openai/whisper-large-v3-turbo)
- [openai/whisper GitHub](https://github.com/openai/whisper)
- [Whisper Model Sizes Explained](https://openwhispr.com/blog/whisper-model-sizes-explained)
- [Whisper Large V3 Turbo -- 5x Faster, Same Accuracy](https://whispernotes.app/blog/introducing-whisper-large-v3-turbo)

### WhisperX and Diarization
- [m-bain/whisperX GitHub](https://github.com/m-bain/whisperX)
- [whisperx PyPI](https://pypi.org/project/whisperx/)
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [Whisper Speaker Diarization Python Tutorial](https://brasstranscripts.com/blog/whisper-speaker-diarization-guide)
- [Speaker Diarization with WhisperX](https://datacurious.hashnode.dev/unlocking-audio-insights-speaker-diarization-with-whisperx-for-who-said-what)

### macOS Audio Recording
- [sox CLI Audio Toolkit](https://notes.nicolasdeville.com/helpers/cli-sox/)
- [BlackHole and ffmpeg](https://github.com/ExistentialAudio/BlackHole/issues/45)
- [Recording System Audio on macOS](https://slinkp.com/record-system-audio-macos-2025.html)
- [Record Mac System Audio with Python and BlackHole](https://medium.com/@mehsamadi/how-to-record-mac-system-audio-using-python-and-blackhole-a45d06eaad0f)

### Korean Speech Recognition
- [Extending Whisper for Korean-English Code-switching](https://www.researchgate.net/publication/390221445_Extending_Whisper_for_Korean-English_Code-switching_Speech_Recognition)
- [Small Models, Big Heat -- Conquering Korean ASR with Low-bit Whisper](https://enerzai.com/resources/blog/small-models-big-heat-conquering-korean-asr-with-low-bit-whisper)
- [Whisper Korean Accuracy Discussion](https://github.com/openai/whisper/discussions/1523)
- [Automatic Word Spacing of Korean](https://www.mdpi.com/2076-3417/11/2/626)

### Audio Preprocessing
- [Enhancing Whisper Transcriptions -- OpenAI Cookbook](https://cookbook.openai.com/examples/whisper_processing_guide)
- [Audio Pre-Processing for Better Transcription](https://medium.com/@developerjo0517/audio-pre-processings-for-better-results-in-the-transcription-pipeline-bab1e8f63334)
- [Whisper Preprocessing Discussion](https://github.com/openai/whisper/discussions/2125)

### Alternatives
- [Vosk for Enterprise Speech Recognition](https://towardsdatascience.com/vosk-for-efficient-enterprise-grade-speech-recognition-an-evaluation-and-implementation-guide-87a599217a6c/)
- [OpenAI Whisper vs Vosk Comparison](https://www.jamy.ai/blog/openai-whisper-vs-other-open-source-transcription-models/)
- [Apple SpeechAnalyzer WWDC 2025](https://developer.apple.com/videos/play/wwdc2025/277/)
- [Apple SpeechAnalyzer and Argmax WhisperKit](https://www.argmaxinc.com/blog/apple-and-argmax)
- [Top Open-Source STT Options 2025](https://www.assemblyai.com/blog/top-open-source-stt-options-for-voice-applications)

### Performance and Benchmarks
- [Whisper Performance on Apple Silicon](https://www.voicci.com/blog/apple-silicon-whisper-performance.html)
- [mac-whisper-speedtest](https://github.com/anvanvan/mac-whisper-speedtest)
- [Benchmarking Top Open-Source Speech Recognition Models](https://www.shunyalabs.ai/blog/benchmarking-top-open-source-speech-recognition-models)
- [Faster-Whisper Turbo v3 Benchmark](https://github.com/SYSTRAN/faster-whisper/issues/1030)
