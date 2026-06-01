"""Step 1 (MAIN) — lesson plan design (수업안 설계).

Produces the canonical ``lesson_plan.json`` (lesson-plan.v1) plus a
teacher-facing ``lesson_plan.md``. This is the core artifact every
supplementary step (2–4) consumes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.io_helpers import write_json, write_text
from scripts.lesson_plan_contract import render_markdown, validate_lesson_plan
from scripts.lesson_plan_generate import generate_lesson_plan

STEP_ID = "step1_lesson_plan"


def run(
    intake: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Design lesson plan; returns canonical ``lesson_plan`` dict."""
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = generate_lesson_plan(intake)

    # Record validation status on the artifact (non-fatal; orchestrator gates).
    errors = validate_lesson_plan(plan)
    plan["validation_errors"] = errors
    plan["status"] = "ok" if not errors else "validation_warning"

    write_json(output_dir / "lesson_plan.json", plan)
    write_text(output_dir / "lesson_plan.md", render_markdown(plan))
    return plan
