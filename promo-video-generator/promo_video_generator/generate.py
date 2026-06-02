"""Generate promo-video.v1 JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from content_common import _use_placeholder, call_claude, read_prompt

from .contract import (
    FORMAT_VERSION,
    load_downstream,
    placeholder_package,
    validate_promo_package,
)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "agents" / "prompts"
PROMPT_FILE = "promo.md"
STEP_ID = "step4_promo"


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def resolve_prior(
    teaching_dir: Path | None,
    praise_dir: Path | None,
    prior: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    teaching = praise = None
    if prior:
        t = prior.get("teaching_downstream") or prior.get("teaching")
        if isinstance(t, dict):
            teaching = t.get("downstream", t) if "downstream" in t else t
        p = prior.get("praise_downstream") or prior.get("praise")
        if isinstance(p, dict):
            praise = p.get("downstream", p) if "downstream" in p else p

    # Upstream context is optional and caller-supplied (data contract / explicit
    # dir), so this module has no dependency on any other module's output dir.
    if teaching is None and teaching_dir is not None:
        f = teaching_dir / "teaching_materials.downstream.json"
        if f.is_file():
            teaching = load_downstream(f)
    if praise is None and praise_dir is not None:
        f = praise_dir / "praise_worship.downstream.json"
        if f.is_file():
            praise = load_downstream(f)
    return teaching, praise


def generate_promo_package(
    intake: dict[str, Any],
    teaching: dict[str, Any] | None = None,
    praise: dict[str, Any] | None = None,
    teaching_dir: Path | None = None,
    praise_dir: Path | None = None,
    prior: dict[str, Any] | None = None,
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t_ctx, p_ctx = resolve_prior(teaching_dir, praise_dir, prior)
    teaching = teaching or t_ctx
    praise = praise or p_ctx

    if _use_placeholder():
        return placeholder_package(intake, teaching, praise, lesson_plan=lesson_plan)

    system_prompt = read_prompt(prompts_dir() / PROMPT_FILE)
    user_payload: dict[str, Any] = {
        "intake": intake,
        "teaching_downstream": teaching,
        "praise_downstream": praise,
        "lesson_plan": lesson_plan,
        "required_format": FORMAT_VERSION,
        "constraints": {
            "duration_seconds_min": 30,
            "duration_seconds_max": 45,
            "target": "middle_school_retreat_promo",
            "visual_delivery": "video_ai_per_cut",
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
        pkg = placeholder_package(intake, teaching, praise)
        pkg["meta"]["generated_by"] = "fallback_parse_error"
        return pkg

    if data.get("format") != FORMAT_VERSION:
        data["format"] = FORMAT_VERSION
    errors = validate_promo_package(data)
    if errors:
        pkg = placeholder_package(intake, teaching, praise)
        pkg["meta"]["generated_by"] = "fallback_validation"
        pkg["validation_errors"] = errors
        return pkg
    return data
