"""Fixed output contract: promo-video.v1 (30–45s retreat promo)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FORMAT_VERSION = "promo-video.v1"
DURATION_MIN = 30
DURATION_MAX = 45


def load_downstream(path: Path) -> dict[str, Any]:
    if not path.is_file():
        msg = f"Missing downstream file: {path}"
        raise FileNotFoundError(msg)
    return json.loads(path.read_text(encoding="utf-8"))


def validate_promo_package(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("format") != FORMAT_VERSION:
        errors.append(f"format must be {FORMAT_VERSION}")
    cuts = data.get("storyboard", {}).get("cuts", [])
    if len(cuts) < 4:
        errors.append("storyboard.cuts need at least 4 items")
    total = sum(c.get("duration_seconds", 0) for c in cuts)
    if total < DURATION_MIN or total > DURATION_MAX:
        errors.append(f"total duration {total}s must be {DURATION_MIN}-{DURATION_MAX}s")
    if not data.get("narration", {}).get("full_script"):
        errors.append("narration.full_script required")
    subs = data.get("subtitles", [])
    if len(subs) < len(cuts):
        errors.append("subtitles count should match cuts")
    for i, cut in enumerate(cuts):
        if not cut.get("scene_description"):
            errors.append(f"cut {i+1} missing scene_description")
        if not (cut.get("video_prompt") or cut.get("image_prompt")):
            errors.append(f"cut {i+1} missing video_prompt or image_prompt")
    return errors


def build_downstream_payload(
    package: dict[str, Any],
    artifact_paths: dict[str, str],
) -> dict[str, Any]:
    return {
        "format": FORMAT_VERSION,
        "theme": package.get("inputs", {}).get("theme", ""),
        "duration_seconds": package.get("meta", {}).get("total_duration_seconds", 0),
        "cut_count": len(package.get("storyboard", {}).get("cuts", [])),
        "cta": package.get("cta", {}).get("text", ""),
        "artifacts": artifact_paths,
        "assembly_output": artifact_paths.get("assembled_mp4", ""),
    }


def placeholder_package(
    intake: dict[str, Any],
    teaching: dict[str, Any] | None = None,
    praise: dict[str, Any] | None = None,
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    theme = intake.get("theme") or intake.get("emphasis", "중등 수련회")
    # Plan 핵심메시지 first, then inherit from teaching/praise downstream.
    key_message = (lesson_plan or {}).get("sections", {}).get("key_message") or ""
    if not key_message and teaching:
        key_message = teaching.get("key_message", "")
    if not key_message and praise:
        key_message = key_message or praise.get("key_message", "")

    cuts = [
        {
            "id": 1,
            "duration_seconds": 5,
            "scene_description": "수련회 장소 외관, 저녁 조명, 학생들이 들어서는 모습",
            "visual_type": "video_ai",
            "video_prompt": (
                "Cinematic 16:9, Korean youth church retreat entrance at dusk, "
                "warm string lights, teens walking in with backpacks, hopeful mood"
            ),
            "image_prompt": "Still: youth retreat gate, evening, welcoming atmosphere",
            "subtitle": f"{theme}",
            "narration": "올해, 우리에게 특별한 만남이 기다리고 있어요.",
        },
        {
            "id": 2,
            "duration_seconds": 6,
            "scene_description": "본문 맥락 — 친구들과 성경 공부하는 클로즈업",
            "visual_type": "video_ai",
            "video_prompt": (
                "Middle school students in small group Bible study, soft daylight, "
                "focus on open Bible and smiling faces, shallow depth of field"
            ),
            "image_prompt": "Bible study circle, Korean teens, warm indoor light",
            "subtitle": "말씀 안에서 만나요",
            "narration": "말씀을 통해 서로의 마음을 나누는 시간.",
        },
        {
            "id": 3,
            "duration_seconds": 5,
            "scene_description": "팀 게임과 웃음, 운동장/체육관 활동",
            "visual_type": "video_ai",
            "video_prompt": (
                "Youth retreat team game outdoors, running and laughter, "
                "slow-motion high-five, energetic but safe"
            ),
            "image_prompt": "Teens playing group game, joyful motion blur",
            "subtitle": "함께 뛰는 기쁨",
            "narration": "함께 뛰고 웃으며 더 가까워지는 밤.",
        },
        {
            "id": 4,
            "duration_seconds": 6,
            "scene_description": "찬양 예배, 손 들고 찬양하는 실루엣",
            "visual_type": "video_ai",
            "video_prompt": (
                "Youth worship night, silhouettes with raised hands, "
                "soft stage lights, acoustic worship band background"
            ),
            "image_prompt": "Worship silhouette, purple-blue stage lighting",
            "subtitle": "찬양으로 드리는 예배",
            "narration": "찬양으로 마음을 열고 예배합니다.",
        },
        {
            "id": 5,
            "duration_seconds": 5,
            "scene_description": "토의 모둠, 진지하지만 편안한 표정",
            "visual_type": "video_ai",
            "video_prompt": (
                "Small group discussion, Korean middle schoolers, "
                "notebooks and snacks, intimate circle, caring facilitator"
            ),
            "image_prompt": "Group discussion close-up, thoughtful teens",
            "subtitle": "솔직한 나눔",
            "narration": "솔직한 질문과 용기 있는 나눔.",
        },
        {
            "id": 6,
            "duration_seconds": 6,
            "scene_description": "핵심 메시지 타이포 + 밤하늘",
            "visual_type": "image_ai",
            "video_prompt": "Text overlay animation on starry night sky, minimal Korean typography",
            "image_prompt": f"Typography poster: {key_message or theme}, stars, navy gradient 16:9",
            "subtitle": key_message or theme,
            "narration": key_message or "하나님의 사랑, 우리 안에 머뭅니다.",
        },
        {
            "id": 7,
            "duration_seconds": 5,
            "scene_description": "CTA — 일시·장소·참가 안내 화면",
            "visual_type": "image_ai",
            "video_prompt": "Clean promo end card, date time location placeholders, modern church youth style",
            "image_prompt": "Event promo end card, bold date/time/location blocks, 16:9",
            "subtitle": "지금 등록하세요",
            "narration": "중등부 수련회, 함께해요. 자세한 안내는 청년부에 문의하세요.",
        },
    ]

    total = sum(c["duration_seconds"] for c in cuts)
    narration_full = " ".join(c["narration"] for c in cuts)
    subtitles = []
    t = 0.0
    for cut in cuts:
        dur = cut["duration_seconds"]
        subtitles.append(
            {
                "cut_id": cut["id"],
                "text": cut["subtitle"],
                "start_seconds": round(t, 2),
                "end_seconds": round(t + dur, 2),
            }
        )
        t += dur

    return {
        "format": FORMAT_VERSION,
        "meta": {
            "target": "retreat_promo",
            "duration_target_seconds": 38,
            "total_duration_seconds": total,
            "aspect_ratio": "16:9",
            "resolution": {"width": 1920, "height": 1080},
            "generated_by": "placeholder",
        },
        "inputs": {
            "theme": theme,
            "body_text": intake.get("body_text", ""),
            "audience": intake.get("audience", "중등부"),
            "key_message": key_message,
        },
        "narration": {
            "full_script": narration_full,
            "language": "ko-KR",
            "segments": [
                {
                    "id": f"n{c['id']}",
                    "cut_id": c["id"],
                    "text": c["narration"],
                    "duration_seconds": c["duration_seconds"],
                }
                for c in cuts
            ],
        },
        "subtitles": subtitles,
        "storyboard": {
            "cuts": cuts,
            "video_ai_workflow": [
                "For each cut with visual_type video_ai: paste video_prompt into Runway/Pika/Kling.",
                f"Save as assets/cut_{{id:02d}}.mp4 under promo output folder.",
                "If only image available, save as assets/cut_XX.png and run assemble script.",
            ],
        },
        "cta": {
            "text": "중등부 수련회 — 함께해요!",
            "on_screen": "지금 등록하세요 · 청년부 문의",
        },
        "assembly": {
            "tool": "ffmpeg",
            "script": "scripts/assemble_promo_video.py",
            "tts_voice": "ko-KR-SunHiNeural",
            "music_track_suggested": "outputs/praise/audio/song.mp3",
            "expected_output": "output/promo_final.mp4",
        },
    }
