"""Generate teaching-materials.v1 JSON via Claude or placeholder."""

from __future__ import annotations

import json
import re
from typing import Any

from pathlib import Path

from content_common import _use_placeholder, call_claude, read_prompt

from .contract import FORMAT_VERSION, placeholder_package, validate_teaching_package

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "agents" / "prompts"
PROMPT_FILE = "material.md"
STEP_ID = "step2_teaching"


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _minimal_lesson_plan(intake: dict[str, Any]) -> dict[str, Any]:
    """When Step 1 was skipped, derive context from intake only."""
    theme = intake.get("theme") or intake.get("emphasis", "")
    return {
        "sections": {
            "key_message": theme,
            "learning_objectives": [f"{theme}을 이해한다"],
            "discussion_questions": [],
        },
        "derived_from": "intake_only",
    }


def generate_teaching_package(
    intake: dict[str, Any],
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = lesson_plan or _minimal_lesson_plan(intake)
    if _use_placeholder():
        pkg = placeholder_package(intake, plan)
        pkg["lesson_plan_ref"] = {"mode": "intake_only" if plan.get("derived_from") else "step1"}
        return pkg

    system_prompt = read_prompt(PROMPTS_DIR / PROMPT_FILE)
    user_payload: dict[str, Any] = {
        "intake": intake,
        "lesson_plan": plan,
        "required_format": FORMAT_VERSION,
        "target_grade_band": "middle_school",
    }
    raw = call_claude(
        step_id=STEP_ID,
        system_prompt=system_prompt,
        user_payload=user_payload,
        max_tokens=8192,
    )
    try:
        data = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError:
        pkg = placeholder_package(intake)
        pkg["meta"]["generated_by"] = "fallback_parse_error"
        pkg["raw_parse_error"] = raw[:500]
        return pkg

    if data.get("format") != FORMAT_VERSION:
        data["format"] = FORMAT_VERSION
    errors = validate_teaching_package(data)
    if errors:
        pkg = placeholder_package(intake)
        pkg["meta"]["generated_by"] = "fallback_validation"
        pkg["validation_errors"] = errors
        return pkg
    return data
