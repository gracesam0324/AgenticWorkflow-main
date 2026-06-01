"""Generate praise-worship.v1 JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.claude_client import call_claude, _use_placeholder
from scripts.io_helpers import read_prompt, project_root_from_script
from scripts.modules._common import prompts_dir
from scripts.praise_contract import (
    FORMAT_VERSION,
    placeholder_package,
    validate_praise_package,
    load_teaching_downstream,
)

PROMPT_FILE = "step3_praise_worship.md"
STEP_ID = "step3_praise"


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def resolve_teaching(
    teaching: dict[str, Any] | None,
    teaching_dir: Path | None,
) -> dict[str, Any] | None:
    if teaching is not None:
        return teaching
    if teaching_dir is not None:
        return load_teaching_downstream(teaching_dir)
    default_dir = project_root_from_script() / "outputs" / "teaching"
    if (default_dir / "teaching_materials.downstream.json").is_file():
        return load_teaching_downstream(default_dir)
    return None


def generate_praise_package(
    intake: dict[str, Any],
    teaching: dict[str, Any] | None = None,
    teaching_dir: Path | None = None,
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    teaching_ctx = resolve_teaching(teaching, teaching_dir)

    if _use_placeholder():
        pkg = placeholder_package(intake, teaching_ctx, lesson_plan=lesson_plan)
        if lesson_plan:
            pkg["inputs"]["lesson_plan_ref"] = "provided"
        return pkg

    system_prompt = read_prompt(prompts_dir() / PROMPT_FILE)
    user_payload: dict[str, Any] = {
        "intake": intake,
        "teaching_downstream": teaching_ctx,
        "lesson_plan": lesson_plan,
        "required_format": FORMAT_VERSION,
        "requirements": {
            "original_lyrics_only": True,
            "structure": ["verse1", "chorus", "verse2", "chorus", "bridge", "chorus"],
            "grade_band": "middle_school",
            "music_prompt_provider": "suno",
            "single_combined_music_prompt": True,
        },
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
        pkg = placeholder_package(intake, teaching_ctx)
        pkg["meta"]["generated_by"] = "fallback_parse_error"
        return pkg

    if data.get("format") != FORMAT_VERSION:
        data["format"] = FORMAT_VERSION
    errors = validate_praise_package(data)
    if errors:
        pkg = placeholder_package(intake, teaching_ctx)
        pkg["meta"]["generated_by"] = "fallback_validation"
        pkg["validation_errors"] = errors
        return pkg
    return data
