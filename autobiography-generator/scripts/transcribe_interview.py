#!/usr/bin/env python3
"""
transcribe_interview.py -- Local STT pipeline for autobiography interviews.

Transcribes audio using faster-whisper, optionally performs speaker diarization
via WhisperX, and outputs structured JSON matching interview_transcript.schema.json.

All processing runs locally. No audio data leaves the machine.

Usage:
    python transcribe_interview.py input.wav --output transcript.json
    python transcribe_interview.py input.wav --diarize --hf-token hf_xxx
    python transcribe_interview.py input.wav --language ko --model large-v3-turbo

Requirements:
    pip install faster-whisper
    pip install whisperx  (only if --diarize is used)
    brew install ffmpeg
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_faster_whisper(model_size: str, compute_type: str, device: str):
    """Load faster-whisper model with the specified configuration."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: faster-whisper not installed.")
        print("  Run: pip install faster-whisper")
        sys.exit(1)

    print(f"[model] Loading {model_size} (device={device}, compute_type={compute_type}) ...")
    t0 = time.time()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print(f"[model] Ready in {time.time() - t0:.1f}s")
    return model


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_audio(
    model,
    audio_path: str,
    language: Optional[str] = None,
    beam_size: int = 5,
    vad_filter: bool = True,
    initial_prompt: Optional[str] = None,
) -> tuple[list, dict]:
    """
    Transcribe an audio file using faster-whisper.

    Returns
    -------
    segments : list[dict]
        Each dict has keys: start, end, text, words, avg_probability.
    info : dict
        Metadata: language, language_probability, duration_seconds, etc.
    """
    print(f"[transcribe] Processing: {audio_path}")
    t0 = time.time()

    kwargs = dict(
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        ),
        word_timestamps=True,
    )
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt

    segments_gen, info = model.transcribe(audio_path, **kwargs)

    detected_lang = info.language
    lang_prob = info.language_probability
    duration = info.duration
    print(f"[transcribe] Detected language: {detected_lang} (p={lang_prob:.2f})")
    print(f"[transcribe] Audio duration: {duration:.1f}s ({duration / 60:.1f} min)")

    # Materialize the generator
    result_segments = []
    for seg in segments_gen:
        words = []
        probs = []
        for w in (seg.words or []):
            words.append({
                "word": w.word,
                "start": round(w.start, 3),
                "end": round(w.end, 3),
                "probability": round(w.probability, 4),
            })
            probs.append(w.probability)

        avg_prob = sum(probs) / len(probs) if probs else 0.0

        result_segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": words,
            "avg_probability": round(avg_prob, 4),
        })

    elapsed = time.time() - t0
    rtf = elapsed / max(duration, 0.001)
    print(f"[transcribe] Done in {elapsed:.1f}s "
          f"({len(result_segments)} segments, RTF={rtf:.2f}x)")

    return result_segments, {
        "language": detected_lang,
        "language_probability": round(lang_prob, 4),
        "duration_seconds": round(duration, 2),
        "transcription_time_seconds": round(elapsed, 2),
    }


# ---------------------------------------------------------------------------
# Speaker diarization (optional, requires WhisperX + pyannote)
# ---------------------------------------------------------------------------

def diarize_audio(audio_path: str, hf_token: str, num_speakers: int = 2) -> list:
    """
    Perform speaker diarization using WhisperX + pyannote.

    Returns a list of dicts: {start, end, speaker}.
    """
    try:
        import whisperx
    except ImportError:
        print("ERROR: whisperx not installed.")
        print("  Run: pip install whisperx pyannote.audio==3.1.1")
        sys.exit(1)

    print(f"[diarize] Running diarization (expecting {num_speakers} speakers) ...")
    t0 = time.time()

    diarize_model = whisperx.DiarizationPipeline(
        use_auth_token=hf_token,
        device="cpu",
    )

    audio = whisperx.load_audio(audio_path)
    diarize_result = diarize_model(audio, num_speakers=num_speakers)

    diarization_segments = []
    for _, row in diarize_result.iterrows():
        diarization_segments.append({
            "start": round(float(row["start"]), 3),
            "end": round(float(row["end"]), 3),
            "speaker": row["speaker"],
        })

    speakers = sorted(set(s["speaker"] for s in diarization_segments))
    print(f"[diarize] Done in {time.time() - t0:.1f}s — "
          f"{len(speakers)} speakers: {', '.join(speakers)}")

    return diarization_segments


def assign_speakers(
    transcript_segments: list,
    diarization_segments: list,
    speaker_map: Optional[dict] = None,
) -> list:
    """
    Merge diarization labels into transcript segments.

    Uses midpoint matching: each transcript segment is assigned the speaker
    whose diarization window contains the segment's temporal midpoint.

    Parameters
    ----------
    speaker_map : dict, optional
        Maps raw labels to readable names.
        Example: {"SPEAKER_00": "interviewer", "SPEAKER_01": "subject"}
    """
    speaker_map = speaker_map or {}

    for seg in transcript_segments:
        seg_mid = (seg["start"] + seg["end"]) / 2.0
        best_speaker = "unknown"
        for d in diarization_segments:
            if d["start"] <= seg_mid <= d["end"]:
                best_speaker = d["speaker"]
                break
        seg["speaker"] = speaker_map.get(best_speaker, best_speaker)

    return transcript_segments


# ---------------------------------------------------------------------------
# Segment grouping
# ---------------------------------------------------------------------------

def group_into_topic_segments(
    transcript_segments: list,
    max_segment_duration: float = 300.0,
    silence_threshold: float = 3.0,
) -> list[list]:
    """
    Group raw whisper segments into larger thematic segments.

    Splits on long silences (> silence_threshold seconds) or when
    the accumulated duration exceeds max_segment_duration.
    """
    if not transcript_segments:
        return []

    groups: list[list] = []
    current_group = [transcript_segments[0]]

    for seg in transcript_segments[1:]:
        prev_end = current_group[-1]["end"]
        gap = seg["start"] - prev_end
        group_duration = seg["end"] - current_group[0]["start"]

        if gap > silence_threshold or group_duration > max_segment_duration:
            groups.append(current_group)
            current_group = [seg]
        else:
            current_group.append(seg)

    if current_group:
        groups.append(current_group)

    return groups


# ---------------------------------------------------------------------------
# Schema-compliant JSON builder
# ---------------------------------------------------------------------------

def build_schema_json(
    groups: list[list],
    transcription_info: dict,
    session_id: str = "INT-001",
    subject_name: str = "Subject",
    interviewer_type: str = "human",
    life_period_label: str = "General",
    start_year: int = 2000,
    end_year: Optional[int] = None,
    themes: Optional[list[str]] = None,
) -> dict:
    """
    Build output conforming to interview_transcript.schema.json.
    """
    segments = []

    for i, group in enumerate(groups, 1):
        seg_id = f"SEG-{i:03d}"

        # Combine text from all whisper segments in this group
        texts = []
        for seg in group:
            prefix = ""
            if "speaker" in seg:
                prefix = f"[{seg['speaker']}] "
            texts.append(f"{prefix}{seg['text']}")

        content = "\n".join(texts)

        segment_entry: dict = {
            "segment_id": seg_id,
            "topic": f"Segment {i}",
            "content": content,
        }

        # Extract high-confidence quotes
        key_quotes = []
        for seg in group:
            if seg.get("avg_probability", 0) > 0.9 and len(seg["text"]) > 30:
                key_quotes.append({
                    "text": seg["text"],
                    "context": (
                        f"Transcribed at {seg['start']:.1f}s-{seg['end']:.1f}s "
                        f"(avg word confidence: {seg['avg_probability']:.2f})"
                    ),
                    "usable_in_chapter": True,
                })

        if key_quotes:
            segment_entry["key_quotes"] = key_quotes[:5]

        segments.append(segment_entry)

    duration_minutes = int(transcription_info["duration_seconds"] / 60)

    life_period: dict = {
        "label": life_period_label,
        "start_year": start_year,
    }
    if end_year:
        life_period["end_year"] = end_year

    result = {
        "meta": {
            "session_id": session_id,
            "subject_name": subject_name,
            "interviewer": interviewer_type,
            "date": date.today().isoformat(),
            "duration_minutes": max(5, duration_minutes),
            "life_period": life_period,
            "themes": themes or ["general"],
            "emotional_tone": "neutral",
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
            "processing_date": date.today().isoformat(),
        },
    }

    return result


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------

def assess_quality(transcript: dict) -> dict:
    """Return quality metrics for the transcript."""
    segments = transcript.get("segments", [])
    stt_meta = transcript.get("_stt_metadata", {})

    total_chars = sum(len(s.get("content", "")) for s in segments)
    total_words = sum(len(s.get("content", "").split()) for s in segments)

    quote_probs = []
    for seg in segments:
        for q in seg.get("key_quotes", []):
            ctx = q.get("context", "")
            if "confidence:" in ctx:
                try:
                    p = float(ctx.split("confidence: ")[1].split(")")[0])
                    quote_probs.append(p)
                except (ValueError, IndexError):
                    pass

    avg_conf = sum(quote_probs) / len(quote_probs) if quote_probs else 0.0
    duration = stt_meta.get("audio_duration_seconds", 1)
    speed = stt_meta.get("transcription_time_seconds", 0)

    grade = (
        "A" if avg_conf > 0.95 else
        "B" if avg_conf > 0.90 else
        "C" if avg_conf > 0.85 else
        "D"
    )

    return {
        "segments": len(segments),
        "total_words": total_words,
        "total_characters": total_chars,
        "key_quotes_found": len(quote_probs),
        "avg_quote_confidence": round(avg_conf, 3),
        "quality_grade": grade,
        "needs_human_review": grade in ("C", "D"),
        "language": stt_meta.get("detected_language", "?"),
        "real_time_factor": round(speed / max(duration, 1), 2),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Transcribe interview audio to structured JSON (local-only).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s interview.wav
  %(prog)s interview.wav -l ko -o transcript.json
  %(prog)s interview.wav --diarize --hf-token $HF_TOKEN
  %(prog)s interview.wav --model small --language en
        """,
    )

    # Required
    p.add_argument("audio_file",
                   help="Path to audio file (WAV, MP3, M4A, etc.)")

    # Output
    p.add_argument("--output", "-o", default=None,
                   help="Output JSON path (default: <input>_transcript.json)")
    p.add_argument("--raw-segments", action="store_true",
                   help="Also save raw whisper segments to a separate file")

    # Model
    p.add_argument("--model", default="large-v3-turbo",
                   choices=["tiny", "base", "small", "medium",
                            "large-v3", "large-v3-turbo"],
                   help="Whisper model size (default: large-v3-turbo)")
    p.add_argument("--compute-type", default="int8",
                   choices=["int8", "float32"],
                   help="Quantization (default: int8, best for Apple Silicon CPU)")
    p.add_argument("--device", default="cpu",
                   choices=["cpu", "auto"],
                   help="Device (default: cpu)")

    # Transcription
    p.add_argument("--language", "-l", default=None,
                   help="Language code (e.g. 'ko', 'en'). None=auto-detect")
    p.add_argument("--beam-size", type=int, default=5,
                   help="Beam search size (default: 5)")
    p.add_argument("--initial-prompt", default=None,
                   help="Prompt to guide transcription (e.g. expected terms)")

    # Diarization
    p.add_argument("--diarize", action="store_true",
                   help="Enable speaker diarization (requires whisperx)")
    p.add_argument("--hf-token", default=None,
                   help="Hugging Face token (or set HF_TOKEN env var)")
    p.add_argument("--num-speakers", type=int, default=2,
                   help="Expected number of speakers (default: 2)")
    p.add_argument("--speaker-map", default=None,
                   help='Speaker mapping JSON, e.g. '
                        '\'{"SPEAKER_00":"interviewer","SPEAKER_01":"subject"}\'')

    # Metadata
    p.add_argument("--session-id", default="INT-001")
    p.add_argument("--subject-name", default="Subject")
    p.add_argument("--interviewer-type", default="human",
                   choices=["human", "ai-guided"])
    p.add_argument("--life-period", default="General")
    p.add_argument("--start-year", type=int, default=2000)
    p.add_argument("--end-year", type=int, default=None)
    p.add_argument("--themes", nargs="+", default=None,
                   help="Theme tags (e.g. family education career)")

    return p.parse_args(argv)


def main(argv: Optional[list] = None) -> dict:
    args = parse_args(argv)

    # --- validate input ---
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    # --- output path ---
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = audio_path.parent / f"{audio_path.stem}_transcript.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- transcribe ---
    model = load_faster_whisper(args.model, args.compute_type, args.device)
    segments, info = transcribe_audio(
        model,
        str(audio_path),
        language=args.language,
        beam_size=args.beam_size,
        initial_prompt=args.initial_prompt,
    )

    # --- raw segments ---
    if args.raw_segments:
        raw_path = audio_path.parent / f"{audio_path.stem}_raw_segments.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump({"segments": segments, "info": info}, f,
                      ensure_ascii=False, indent=2)
        print(f"[raw] Saved: {raw_path}")

    # --- diarization ---
    if args.diarize:
        hf_token = args.hf_token or os.environ.get("HF_TOKEN")
        if not hf_token:
            print("ERROR: --hf-token or HF_TOKEN env var required for diarization.")
            sys.exit(1)

        diar_segments = diarize_audio(str(audio_path), hf_token, args.num_speakers)

        speaker_map = {}
        if args.speaker_map:
            speaker_map = json.loads(args.speaker_map)

        segments = assign_speakers(segments, diar_segments, speaker_map)

    # --- group and structure ---
    groups = group_into_topic_segments(segments)

    result = build_schema_json(
        groups,
        info,
        session_id=args.session_id,
        subject_name=args.subject_name,
        interviewer_type=args.interviewer_type,
        life_period_label=args.life_period,
        start_year=args.start_year,
        end_year=args.end_year,
        themes=args.themes,
    )

    # --- quality check ---
    quality = assess_quality(result)
    result["_quality"] = quality

    # --- write output ---
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # --- summary ---
    print("")
    print("=" * 60)
    print(f"  Transcript saved : {output_path}")
    print(f"  Segments         : {quality['segments']}")
    print(f"  Words            : {quality['total_words']}")
    print(f"  Language         : {quality['language']}")
    print(f"  Quality grade    : {quality['quality_grade']}")
    if quality["needs_human_review"]:
        print(f"  ** Human review recommended (grade {quality['quality_grade']})")
    print(f"  Real-time factor : {quality['real_time_factor']}x")
    print("=" * 60)

    return result


if __name__ == "__main__":
    main()
