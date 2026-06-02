"""Fixed output contract: teaching-materials.v1 (downstream steps consume this)."""

from __future__ import annotations

import re
from typing import Any

FORMAT_VERSION = "teaching-materials.v1"
IMG_PATTERN = re.compile(r"\[IMG:\s*([^\]]+)\]", re.IGNORECASE)


def extract_image_prompts(text: str, prefix: str = "img") -> list[dict[str, str]]:
    slots: list[dict[str, str]] = []
    for idx, match in enumerate(IMG_PATTERN.finditer(text or ""), start=1):
        slots.append({"id": f"{prefix}-{idx}", "prompt": match.group(1).strip()})
    return slots


def _collect_texts(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("intro_game", "discussion", "activity", "worksheet"):
        block = data.get("components", {}).get(key, {})
        if isinstance(block, dict):
            for v in block.values():
                if isinstance(v, str):
                    parts.append(v)
                elif isinstance(v, list):
                    parts.extend(str(x) for x in v)
        elif isinstance(block, str):
            parts.append(block)
    for slide in data.get("slides", []):
        if isinstance(slide, dict):
            parts.extend(str(x) for x in slide.get("bullets", []))
            parts.append(str(slide.get("speaker_notes", "")))
    return "\n".join(parts)


def build_downstream_payload(
    package: dict[str, Any],
    artifact_paths: dict[str, str],
) -> dict[str, Any]:
    """Slim payload for step 3+ (praise, promo, self-check)."""
    intake = package.get("intake", {})
    components = package.get("components", {})
    discussion = components.get("discussion", {})
    questions = discussion.get("questions", []) if isinstance(discussion, dict) else []

    all_text = _collect_texts(package)
    image_prompts = extract_image_prompts(all_text, prefix="teaching")

    return {
        "format": FORMAT_VERSION,
        "intake": {
            "body_text": intake.get("body_text"),
            "theme": intake.get("theme"),
            "audience": intake.get("audience"),
            "target_grade_band": package.get("meta", {}).get("target_grade_band", "middle_school"),
        },
        "theme": intake.get("theme") or intake.get("emphasis", ""),
        "key_message": package.get("summary", {}).get("key_message", ""),
        "discussion_questions": questions,
        "image_prompts": image_prompts,
        "artifacts": artifact_paths,
        "components": {
            "intro_game": components.get("intro_game", {}),
            "discussion": components.get("discussion", {}),
            "activity": components.get("activity", {}),
            "worksheet": components.get("worksheet", {}),
        },
        "slides_count": len(package.get("slides", [])),
    }


def validate_teaching_package(data: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty = OK)."""
    errors: list[str] = []
    if data.get("format") != FORMAT_VERSION:
        errors.append(f"format must be {FORMAT_VERSION}")
    for key in ("intro_game", "discussion", "activity", "worksheet"):
        if key not in data.get("components", {}):
            errors.append(f"missing components.{key}")
    if not data.get("slides"):
        errors.append("slides must be a non-empty list")
    if not data.get("intake", {}).get("body_text"):
        errors.append("intake.body_text required")
    return errors


def placeholder_package(
    intake: dict[str, Any],
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic middle-school package when API/placeholder mode is on.

    When a Step 1 ``lesson_plan`` is supplied, its 핵심메시지 becomes the
    canonical key_message so downstream artifacts stay aligned to the plan.
    """
    theme = intake.get("theme") or intake.get("emphasis", "하나님의 사랑")
    body = intake.get("body_text", "")
    audience = intake.get("audience", "중등부")
    plan_km = (lesson_plan or {}).get("sections", {}).get("key_message") or ""

    return {
        "format": FORMAT_VERSION,
        "meta": {
            "target_grade_band": "middle_school",
            "locale": intake.get("locale", "ko"),
            "generated_by": "placeholder",
        },
        "intake": {
            "body_text": body,
            "theme": theme,
            "audience": audience,
            "volume": intake.get("volume"),
            "emphasis": intake.get("emphasis"),
        },
        "summary": {
            "title": f"{theme} — 중등부 수업 교보재",
            "key_message": plan_km or f"하나님의 사랑은 '{body[:40]}...' 말씀을 통해 분명히 드러납니다.",
            "duration_minutes": _parse_minutes(intake.get("volume")),
        },
        "components": {
            "intro_game": {
                "title": "사랑 연결 고리",
                "duration_minutes": 8,
                "materials": ["스티커", "A4 종이", "펜"],
                "steps": [
                    "둥글게 앉아 이름과 오늘 기분 한 단어를 말합니다.",
                    "본문 핵심 단어(사랑·세상·영생) 카드를 나눠 갖고, 자신과 연결지어 한 문장으로 소개합니다.",
                    "[IMG: 중등부 학생들이 원형으로 앉아 카드 게임하는 밝은 교실 일러스트, 16:9]",
                    "가장 많이 겹친 키워드를 보드에 모아 오늘 주제를 예고합니다.",
                ],
                "leader_notes": "분위기가 딱딱하지 않게 8분 내 마무리.",
            },
            "discussion": {
                "format": "4인 모둠 → 전체 공유",
                "duration_minutes": 15,
                "questions": [
                    "오늘 본문에서 '하나님이 세상을 사랑하사'라는 말이 가장 마음에 남는 이유는 무엇인가요?",
                    "'믿는 자마다'에 해당하는 사람은 어떤 사람일까요? 우리 삶과 연결지어 이야기해 보세요.",
                    "사랑이 '행동'으로 드러난다면, 이번 주에 실천할 수 있는 한 가지는 무엇인가요?",
                    "[IMG: 모둠 토의 장면, 학생 4명과 교사, 말풍선 아이콘, 따뜻한 톤]",
                ],
                "leader_notes": "정답 강요 금지. 성경 구절은 공동번역 또는 개역개정 중 하나로 통일.",
            },
            "activity": {
                "title": "사랑 타임라인 만들기",
                "duration_minutes": 20,
                "steps": [
                    "개인: 지난 한 주를 5칸 타임라인으로 그립니다.",
                    "각 칸에 받은 사랑/베풀 사랑을 한 줄씩 적습니다.",
                    "모둠: 가장 용기 낸 이야기 하나를 골라 전체에 소개합니다.",
                    "[IMG: 타임라인 워크시트 예시, 손글씨 느낌, 중등 수준]",
                ],
                "debrief": [
                    "하나님의 사랑은 우리의 작은 사랑 이야기와 어떻게 닮았나요?",
                    "오늘 말씀을 한 문장으로 정리하면?",
                ],
            },
            "worksheet": {
                "title": "오늘의 말씀 탐구 워크시트",
                "passage_reference": body[:80],
                "sections": [
                    {
                        "heading": "말씀 읽기",
                        "body": f"{body}\n\n[IMG: 본문 핵심 구절을 강조한 성경 페이지 스타일 일러스트, 밑줄 표시]",
                    },
                    {
                        "heading": "나의 이해",
                        "body": "1. 오늘 본문에서 새롭게 알게 된 점:\n\n2. 아직 궁금한 점:\n",
                    },
                    {
                        "heading": "삶으로 옮기기",
                        "body": "이번 주 실천 약속 (구체적으로):\n\n기도 제목:\n",
                    },
                ],
                "leader_answer_key": "2번: 은혜·선물·믿음 강조. 3번: 행동 가능한 작은 실천 유도.",
            },
        },
        "slides": [
            {
                "order": 1,
                "title": theme,
                "bullets": [f"대상: {audience}", "오늘의 여정: 말씀 → 토의 → 활동"],
                "speaker_notes": "환영 인사, 안전한 분위기 안내.",
                "image_slot": "[IMG: 제목 슬라이드 배경, 십자가 실루엣과 부드러운 빛, 16:9]",
            },
            {
                "order": 2,
                "title": "말씀",
                "bullets": ["본문 핵심: 하나님의 사랑", "세상을 향한 선물"],
                "speaker_notes": body[:200],
                "image_slot": "[IMG: 열린 성경과 십자가, 중등부 예배 분위기]",
            },
            {
                "order": 3,
                "title": "토의",
                "bullets": ["모둠 4명", "질문 3가지", "전체 공유"],
                "speaker_notes": "질문지는 워크시트 참고.",
                "image_slot": "[IMG: 토의 아이콘, 말풍선 3개]",
            },
            {
                "order": 4,
                "title": "활동",
                "bullets": ["사랑 타임라인", "개인 → 모둠 → 전체"],
                "speaker_notes": "20분 타이머.",
                "image_slot": "[IMG: 타임라인 스케치 일러스트]",
            },
            {
                "order": 5,
                "title": "정리",
                "bullets": ["핵심 메시지 한 문장", "이번 주 실천"],
                "speaker_notes": "기도로 마무리.",
                "image_slot": "[IMG: 일몰과 기도하는 실루엣, 따뜻한 색감]",
            },
        ],
    }


def _parse_minutes(volume: str | int | None) -> int:
    if volume is None:
        return 45
    if isinstance(volume, int):
        return volume
    digits = re.search(r"\d+", str(volume))
    return int(digits.group()) if digits else 45
