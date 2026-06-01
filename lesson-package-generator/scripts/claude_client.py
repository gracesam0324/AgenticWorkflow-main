#!/usr/bin/env python3
"""Single Claude API entry point for the lesson-package pipeline."""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_MODEL = os.environ.get(
    "LESSON_PACKAGE_MODEL", "claude-sonnet-4-20250514"
)
PLACEHOLDER_ENV = "LESSON_PACKAGE_PLACEHOLDER"


def _use_placeholder() -> bool:
    if os.environ.get(PLACEHOLDER_ENV, "1").strip().lower() in ("0", "false", "no"):
        if os.environ.get("ANTHROPIC_API_KEY"):
            return False
    return True


def call_claude(
    *,
    step_id: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    max_tokens: int = 4096,
) -> str:
    if _use_placeholder():
        return _placeholder_response(step_id, user_payload)

    try:
        import anthropic
    except ImportError as exc:
        msg = "anthropic package required when LESSON_PACKAGE_PLACEHOLDER=0"
        raise RuntimeError(msg) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _placeholder_response(step_id, user_payload)

    client = anthropic.Anthropic(api_key=api_key)
    user_message = json.dumps(user_payload, ensure_ascii=False, indent=2)

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _placeholder_step2_json(user_payload: dict[str, Any]) -> str:
    from scripts.teaching_contract import placeholder_package

    intake = user_payload.get("intake", {})
    return json.dumps(placeholder_package(intake), ensure_ascii=False, indent=2)


def _placeholder_step3_json(user_payload: dict[str, Any]) -> str:
    from scripts.praise_contract import placeholder_package

    intake = user_payload.get("intake", {})
    teaching = user_payload.get("teaching_downstream")
    return json.dumps(
        placeholder_package(intake, teaching), ensure_ascii=False, indent=2
    )


def _placeholder_step4_json(user_payload: dict[str, Any]) -> str:
    from scripts.promo_contract import placeholder_package

    intake = user_payload.get("intake", {})
    return json.dumps(
        placeholder_package(
            intake,
            user_payload.get("teaching_downstream"),
            user_payload.get("praise_downstream"),
        ),
        ensure_ascii=False,
        indent=2,
    )


def _placeholder_response(step_id: str, user_payload: dict[str, Any]) -> str:
    intake = user_payload.get("intake", {})
    audience = intake.get("audience", "(no audience)")
    volume = intake.get("volume", "(no volume)")
    emphasis = intake.get("emphasis", "(no emphasis)")
    prior_keys = [k for k in user_payload if k != "intake"]

    templates = {
        "step1_lesson_plan": (
            f"[PLACEHOLDER step1_lesson_plan - 수업안 설계]\n"
            f"Audience: {audience}\nVolume: {volume}\nEmphasis: {emphasis}\n"
            "Sections: learning_objectives, introduction, body_development, "
            "key_message, application, discussion_questions, closing, time_allocation (stub).\n"
        ),
        "step2_teaching": _placeholder_step2_json(user_payload),
        "step3_praise": _placeholder_step3_json(user_payload),
        "step4_promo": _placeholder_step4_json(user_payload),
        "step5_self_check": (
            f"[PLACEHOLDER step5_self_check]\n"
            f"Prior modules: {prior_keys}\n"
            "Verdict: PASS (stub). Integration manifest pending.\n"
        ),
    }
    return templates.get(
        step_id,
        f"[PLACEHOLDER {step_id}]\n{json.dumps(user_payload, ensure_ascii=False)[:500]}\n",
    )
