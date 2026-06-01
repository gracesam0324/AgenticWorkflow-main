"""Generate lesson-plan.v1 JSON via Claude or deterministic placeholder."""

from __future__ import annotations

import json
import re
from typing import Any

from scripts.claude_client import call_claude, _use_placeholder
from scripts.io_helpers import read_prompt
from scripts.lesson_plan_contract import (
    FORMAT_VERSION,
    STEP_ID,
    parse_minutes,
    placeholder_lesson_plan,
    validate_lesson_plan,
)
from scripts.modules._common import prompts_dir

PROMPT_FILE = "step1_lesson_plan.md"


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _finalize(plan: dict[str, Any], intake: dict[str, Any]) -> dict[str, Any]:
    """Normalise required envelope fields the model may omit."""
    plan["step_id"] = STEP_ID
    plan["format"] = FORMAT_VERSION
    plan.setdefault("status", "ok")
    meta = plan.setdefault("meta", {})
    meta.setdefault("volume_minutes", parse_minutes(intake.get("volume")))
    meta.setdefault("locale", intake.get("locale", "ko"))
    plan.setdefault(
        "intake_ref",
        {
            "body_text": intake.get("body_text", ""),
            "audience": intake.get("audience"),
            "volume": intake.get("volume"),
            "emphasis": intake.get("emphasis") or intake.get("theme"),
        },
    )
    return plan


def generate_lesson_plan(intake: dict[str, Any]) -> dict[str, Any]:
    """Return a validated lesson-plan.v1 dict (canonical Step 1 artifact)."""
    if _use_placeholder():
        return placeholder_lesson_plan(intake)

    system_prompt = read_prompt(prompts_dir() / PROMPT_FILE)
    user_payload: dict[str, Any] = {
        "intake": intake,
        "required_format": FORMAT_VERSION,
        "target_grade_band": "middle_school",
        "volume_minutes": parse_minutes(intake.get("volume")),
    }
    raw = call_claude(
        step_id=STEP_ID,
        system_prompt=system_prompt,
        user_payload=user_payload,
        max_tokens=8192,
    )
    try:
        data = _finalize(json.loads(_strip_json_fence(raw)), intake)
    except json.JSONDecodeError:
        plan = placeholder_lesson_plan(intake)
        plan["meta"]["generated_by"] = "fallback_parse_error"
        plan["raw_parse_error"] = raw[:500]
        return plan

    errors = validate_lesson_plan(data)
    if errors:
        plan = placeholder_lesson_plan(intake)
        plan["meta"]["generated_by"] = "fallback_validation"
        plan["validation_errors"] = errors
        return plan
    return data
