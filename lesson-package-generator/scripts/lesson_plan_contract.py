"""Fixed output contract: lesson-plan.v1 (Step 1 MAIN; downstream steps consume this).

The canonical ``lesson_plan.json`` produced by Step 1 must satisfy
``validate_lesson_plan`` (LP1–LP10). Supplementary steps 2–4 read
``sections.key_message``, ``sections.learning_objectives`` and
``sections.discussion_questions`` from this structure, so those keys must
stay stable.
"""

from __future__ import annotations

import re
from typing import Any

FORMAT_VERSION = "lesson-plan.v1"
STEP_ID = "step1_lesson_plan"

# The eight required sections (PLAN v0.2 §1.2). Order is teach-ready.
SECTION_KEYS: tuple[str, ...] = (
    "learning_objectives",  # 학습목표  — list
    "introduction",         # 도입      — str
    "body_development",     # 본문전개  — str
    "key_message",          # 핵심메시지 — str
    "application",          # 적용      — str
    "discussion_questions", # 토의질문  — list
    "closing",              # 마무리    — str
    "time_allocation",      # 시간배분  — list[{segment, minutes}]
)

SECTION_KO = {
    "learning_objectives": "학습목표",
    "introduction": "도입",
    "body_development": "본문전개",
    "key_message": "핵심메시지",
    "application": "적용",
    "discussion_questions": "토의질문",
    "closing": "마무리",
    "time_allocation": "시간배분",
}


def parse_minutes(volume: str | int | None) -> int:
    """Best-effort total-minutes from a ``volume`` field (e.g. 90 or '45분×2')."""
    if volume is None:
        return 45
    if isinstance(volume, int):
        return volume
    text = str(volume)
    # "45분×2" / "45분 x 2" → 90
    combo = re.search(r"(\d+)\s*[분]?\s*[×xX*]\s*(\d+)", text)
    if combo:
        return int(combo.group(1)) * int(combo.group(2))
    digits = re.search(r"\d+", text)
    return int(digits.group()) if digits else 45


def _has_batchim(word: str) -> bool | None:
    """True if the last char is a Hangul syllable with a final consonant (받침).

    Returns None when the last char is non-Hangul (digits/Latin) so callers can
    fall back to the vowel-form particle.
    """
    if not word:
        return None
    code = ord(word[-1])
    if 0xAC00 <= code <= 0xD7A3:  # 가–힣
        return (code - 0xAC00) % 28 != 0
    return None


def josa(word: str, with_batchim: str, without_batchim: str) -> str:
    """Pick the correct Korean particle for ``word`` (은/는, 이/가, 을/를, 과/와).

    Falls back to the vowel form when the ending is unknown (safer for reading).
    """
    batchim = _has_batchim(word)
    if batchim is None:
        return without_batchim
    return with_batchim if batchim else without_batchim


def build_time_allocation(total_minutes: int) -> list[dict[str, Any]]:
    """Distribute ``total_minutes`` across the teaching segments, summing exactly."""
    weights = [
        ("도입", 0.12),
        ("본문전개", 0.33),
        ("토의질문", 0.22),
        ("적용", 0.18),
        ("마무리", 0.15),
    ]
    allocation: list[dict[str, Any]] = []
    assigned = 0
    for label, weight in weights[:-1]:
        minutes = max(1, round(total_minutes * weight))
        allocation.append({"segment": label, "minutes": minutes})
        assigned += minutes
    # Last segment absorbs the rounding remainder so the sum is exact.
    allocation.append({"segment": weights[-1][0], "minutes": max(1, total_minutes - assigned)})
    return allocation


def _total_allocated(time_allocation: Any) -> int:
    if not isinstance(time_allocation, list):
        return 0
    total = 0
    for item in time_allocation:
        if isinstance(item, dict) and isinstance(item.get("minutes"), (int, float)):
            total += int(item["minutes"])
    return total


def validate_lesson_plan(plan: dict[str, Any]) -> list[str]:
    """Return list of LP1–LP10 violations (empty = pass)."""
    errors: list[str] = []
    sections = plan.get("sections")

    # LP1 — step identity
    if plan.get("step_id") != STEP_ID:
        errors.append(f"LP1: step_id must be '{STEP_ID}'")

    # LP2 — sections object present
    if not isinstance(sections, dict):
        errors.append("LP2: 'sections' object missing")
        return errors  # remaining checks need sections

    # LP3 — all eight sections present and non-empty
    for key in SECTION_KEYS:
        value = sections.get(key)
        if value is None or (isinstance(value, (str, list)) and len(value) == 0):
            errors.append(f"LP3: section '{key}' ({SECTION_KO[key]}) missing or empty")

    # LP4 — ≥2 learning objectives
    objectives = sections.get("learning_objectives")
    if not isinstance(objectives, list) or len(objectives) < 2:
        errors.append("LP4: 학습목표 must be a list with ≥2 items")

    # LP5 — ≥3 discussion questions
    questions = sections.get("discussion_questions")
    if not isinstance(questions, list) or len(questions) < 3:
        errors.append("LP5: 토의질문 must be a list with ≥3 items")

    # LP6 — key message is a non-empty string
    key_message = sections.get("key_message")
    if not isinstance(key_message, str) or not key_message.strip():
        errors.append("LP6: 핵심메시지 must be a non-empty string")

    # LP7 — time allocation sums to volume (±5 min tolerance)
    target = plan.get("meta", {}).get("volume_minutes")
    allocated = _total_allocated(sections.get("time_allocation"))
    if allocated <= 0:
        errors.append("LP7: 시간배분 must list segments with positive minutes")
    elif isinstance(target, (int, float)) and abs(allocated - target) > 5:
        errors.append(f"LP7: 시간배분 합 {allocated}분 ≠ volume {int(target)}분 (±5 허용)")

    # LP8 — body development is substantive
    body = sections.get("body_development")
    if not isinstance(body, str) or len(body.strip()) < 80:
        errors.append("LP8: 본문전개 must be substantive (≥80 chars)")

    # LP9 — introduction substantive
    intro = sections.get("introduction")
    if not isinstance(intro, str) or len(intro.strip()) < 40:
        errors.append("LP9: 도입 must be substantive (≥40 chars)")

    # LP10 — application substantive
    application = sections.get("application")
    if not isinstance(application, str) or len(application.strip()) < 40:
        errors.append("LP10: 적용 must be substantive (≥40 chars)")

    return errors


def placeholder_lesson_plan(intake: dict[str, Any]) -> dict[str, Any]:
    """Deterministic, teach-ready lesson plan for placeholder/offline mode.

    Produces real (non-stub) Korean content sized to ``volume`` so the
    pipeline yields a usable plan without an API key, and downstream steps
    receive genuine 핵심메시지/토의질문/학습목표.
    """
    theme = (intake.get("emphasis") or intake.get("theme") or "하나님의 사랑").strip()
    body = (intake.get("body_text") or "").strip()
    audience = (intake.get("audience") or "중등부").strip()
    total = parse_minutes(intake.get("volume"))
    body_short = body[:60] + ("…" if len(body) > 60 else "")

    # Korean particles agreeing with the theme's final character.
    eun = josa(theme, "은", "는")   # topic
    i = josa(theme, "이", "가")     # subject
    eul = josa(theme, "을", "를")   # object
    wa = josa(theme, "과", "와")    # connective

    sections: dict[str, Any] = {
        "learning_objectives": [
            f"본문({body_short})을 통해 '{theme}'의 의미를 자기 언어로 설명할 수 있다.",
            f"'{theme}'{eul} 자신의 일상 한 장면과 연결해 한 가지 적용점을 찾을 수 있다.",
            f"모둠 안에서 본문에 대한 자신의 생각을 존중하는 태도로 나눌 수 있다.",
        ],
        "introduction": (
            f"{audience} 학생들이 부담 없이 입을 열 수 있도록, 오늘 주제 '{theme}'{wa} 맞닿은 "
            f"가벼운 경험을 묻는 질문으로 시작한다. "
            f"예: \"최근 일상에서 '{theme}'{eul} 느끼거나 떠올린 순간이 있었나요?\" "
            f"학생들의 짧은 대답을 칠판에 모아 본문으로 자연스럽게 넘어간다."
        ),
        "body_development": (
            f"본문 \"{body or theme}\"{josa(body or theme, '을', '를')} 함께 읽는다. "
            f"① 먼저 본문이 말하는 상황과 등장 대상을 확인한다. "
            f"② 본문 핵심 구절에서 '{theme}'{i} 어떻게 드러나는지 한 구절씩 짚는다. "
            f"③ 본문 속 표현을 {audience}의 언어로 바꿔보며 의미를 풀어 설명한다. "
            f"본문에서 직접 근거를 3회 이상 인용하여, 해석이 본문을 벗어나지 않도록 안내한다."
        ),
        "key_message": (
            f"{theme}{eun} 멀리 있는 개념이 아니라, 오늘 본문이 우리에게 직접 건네는 약속이다."
        ),
        "application": (
            f"이번 한 주 동안 '{theme}'{eul} 실천할 구체적인 한 가지를 각자 정한다. "
            f"예: 마음이 멀어진 친구에게 먼저 인사하기. "
            f"실천은 측정 가능하고 작게, {audience} 수준에서 부담 없이 할 수 있는 것으로 정한다."
        ),
        "discussion_questions": [
            f"본문에서 '{theme}'{i} 가장 잘 드러난다고 느낀 부분은 어디인가요? 이유도 함께 말해 주세요.",
            f"'{theme}'{eul} 직접 경험했거나 누군가에게 베푼 적이 있다면 이야기해 주세요.",
            f"오늘 본문을 한 문장으로 정리한다면 어떻게 표현하겠어요?",
            f"이번 주에 '{theme}'{eul} 실천할 수 있는 작은 행동 하나는 무엇일까요?",
        ],
        "closing": (
            f"오늘의 핵심 메시지를 학생들이 한 문장으로 다시 말하게 한 뒤, "
            f"각자 정한 실천 약속을 짧게 나눈다. '{theme}'{eul} 구하는 기도로 마무리한다."
        ),
        "time_allocation": build_time_allocation(total),
    }

    return {
        "step_id": STEP_ID,
        "format": FORMAT_VERSION,
        "status": "ok",
        "meta": {
            "generated_by": "placeholder",
            "target_grade_band": "middle_school",
            "locale": intake.get("locale", "ko"),
            "volume_minutes": total,
        },
        "intake_ref": {
            "body_text": body,
            "audience": audience,
            "volume": intake.get("volume"),
            "emphasis": intake.get("emphasis") or intake.get("theme"),
        },
        "sections": sections,
    }


def render_markdown(plan: dict[str, Any]) -> str:
    """Human-readable lesson plan (teacher-facing) from the structured plan."""
    sections = plan.get("sections", {})
    meta = plan.get("meta", {})
    intake = plan.get("intake_ref", {})
    lines: list[str] = ["# 수업안 (Lesson Plan)", ""]
    if intake.get("audience"):
        lines.append(f"- **대상**: {intake['audience']}")
    if meta.get("volume_minutes"):
        lines.append(f"- **분량**: 총 {meta['volume_minutes']}분")
    if intake.get("emphasis"):
        lines.append(f"- **강조점**: {intake['emphasis']}")
    lines.append("")

    def block(title: str, value: Any) -> None:
        lines.append(f"## {title}")
        if isinstance(value, list):
            if value and isinstance(value[0], dict):  # time_allocation
                for item in value:
                    lines.append(f"- {item.get('segment', '')}: {item.get('minutes', '')}분")
            else:
                for item in value:
                    lines.append(f"- {item}")
        else:
            lines.append(str(value))
        lines.append("")

    for key in SECTION_KEYS:
        if key in sections:
            block(SECTION_KO[key], sections[key])

    return "\n".join(lines).rstrip() + "\n"
