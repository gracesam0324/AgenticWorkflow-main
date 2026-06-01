"""Fixed output contract: praise-worship.v1 (lyrics + Suno-style music prompt)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FORMAT_VERSION = "praise-worship.v1"
AUDIO_PROVIDER = "suno"


def load_teaching_downstream(teaching_dir: Path) -> dict[str, Any]:
    """Load step-1 (교보재) downstream payload from disk."""
    path = teaching_dir / "teaching_materials.downstream.json"
    if not path.is_file():
        path = teaching_dir / "teaching_materials.v1.json"
    if not path.is_file():
        msg = f"Teaching output not found under {teaching_dir}"
        raise FileNotFoundError(msg)
    return json.loads(path.read_text(encoding="utf-8"))


def validate_praise_package(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("format") != FORMAT_VERSION:
        errors.append(f"format must be {FORMAT_VERSION}")
    song = data.get("song", {})
    lyrics = song.get("lyrics", {})
    for part in ("verse1", "chorus", "verse2", "bridge"):
        if part not in lyrics:
            errors.append(f"missing song.lyrics.{part}")
        elif not lyrics[part].get("lines"):
            errors.append(f"song.lyrics.{part}.lines empty")
    mg = data.get("music_generation", {})
    if not mg.get("prompt_combined"):
        errors.append("music_generation.prompt_combined required")
    if not mg.get("prompt_structured", {}).get("bpm"):
        errors.append("music_generation.prompt_structured.bpm required")
    return errors


def build_downstream_payload(
    package: dict[str, Any],
    artifact_paths: dict[str, str],
) -> dict[str, Any]:
    song = package.get("song", {})
    chorus_lines = song.get("lyrics", {}).get("chorus", {}).get("lines", [])
    mg = package.get("music_generation", {})
    return {
        "format": FORMAT_VERSION,
        "song_title": song.get("title", ""),
        "theme": package.get("inputs", {}).get("theme", ""),
        "key_message": package.get("inputs", {}).get("key_message", ""),
        "chorus_preview": chorus_lines[:4],
        "suno_prompt": mg.get("prompt_combined", ""),
        "audio_provider": mg.get("provider", AUDIO_PROVIDER),
        "artifacts": artifact_paths,
        "next_step_note": "Upload Suno MP3 to outputs/praise/audio/song.mp3 when ready",
    }


def placeholder_package(
    intake: dict[str, Any],
    teaching: dict[str, Any] | None = None,
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    theme = intake.get("theme") or intake.get("emphasis", "하나님의 사랑")
    body = intake.get("body_text", "")
    # Plan 핵심메시지 takes precedence so the song stays aligned to Step 1.
    key_message = (lesson_plan or {}).get("sections", {}).get("key_message") or ""
    if not key_message and teaching:
        key_message = teaching.get("key_message") or teaching.get("summary", {}).get(
            "key_message", ""
        )
    if not key_message:
        key_message = f"{theme} — 말씀을 노래로 기억합니다."

    title = f"{theme} (중등 찬양)"

    lyrics = {
        "verse1": {
            "label": "1절",
            "lines": [
                "어두운 마음에 빛이 와",
                "사랑이름 부르시네",
                "세상 끝까지 품으시는",
                "그 사랑 오늘 받네",
            ],
        },
        "chorus": {
            "label": "후렴",
            "lines": [
                "주 사랑해요, 믿어요",
                "영원한 약속 붙들고",
                "중등 우리도 노래해",
                "그 사랑 안에서",
            ],
            "repeat": True,
        },
        "verse2": {
            "label": "2절",
            "lines": [
                "말씀 속에 길이 보여",
                "서로 손잡고 걸어가",
                "작은 믿음도 자라나게",
                "주님 손에 맡기네",
            ],
        },
        "bridge": {
            "label": "브릿지",
            "lines": [
                "두려움은 물러가고",
                "소망만 남아요",
                "오늘 이 자리에서",
                "주께 맡깁니다",
            ],
        },
    }

    structured = {
        "genre": "contemporary worship pop",
        "mood": "warm, hopeful, youth-friendly",
        "bpm": 92,
        "vocal": "Korean youth worship vocal, clear and bright, male-female ensemble optional",
        "instruments": "acoustic guitar, light drums, piano, subtle pad",
        "style_tags": ["worship", "youth", "Korean", "mid-tempo"],
    }
    prompt_combined = (
        f"{structured['genre']}, {structured['mood']}, {structured['bpm']} BPM. "
        f"{structured['vocal']}. {structured['instruments']}. "
        f"Theme: {theme}. Key message: {key_message}. "
        f"Lyrics language: Korean. Suitable for middle school church worship."
    )

    return {
        "format": FORMAT_VERSION,
        "meta": {
            "target_grade_band": "middle_school",
            "audio_provider": AUDIO_PROVIDER,
            "generated_by": "placeholder",
            "lyrics_original": True,
        },
        "inputs": {
            "body_text": body,
            "theme": theme,
            "audience": intake.get("audience", "중등부"),
            "key_message": key_message,
            "teaching_format": teaching.get("format") if teaching else None,
        },
        "song": {
            "title": title,
            "structure": ["verse1", "chorus", "verse2", "chorus", "bridge", "chorus"],
            "lyrics": lyrics,
            "scripture_anchor": body[:120] if body else "",
            "copyright_notice": "오리지널 가사 — 수업/예배용. CCLI 등록 전 외부 배포 금지.",
        },
        "music_generation": {
            "provider": AUDIO_PROVIDER,
            "delivery": "external",
            "prompt_combined": prompt_combined,
            "prompt_structured": structured,
            "workflow": [
                "1. Open Suno (or compatible music AI).",
                "2. Paste music/suno_prompt.txt into the style/description field.",
                "3. Paste full lyrics from lyrics/full_lyrics.md into lyrics field.",
                "4. Generate and download MP3.",
                "5. Save as outputs/praise/audio/song.mp3 (optional manual step).",
            ],
        },
        "leader_notes": {
            "when_to_use": "말씀 정리 후, 마무리 직전 3–4분",
            "suggested_key": "G major",
            "tempo": f"{structured['bpm']} BPM",
            "teaching_tip": "후렴만 먼저 익힌 뒤 전체 진행.",
        },
    }
