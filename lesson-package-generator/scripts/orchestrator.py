#!/usr/bin/env python3
"""Lesson Package Generator — orchestrator (PLAN v0.2).

Pipeline:
  intake (body_text, audience, volume, emphasis)
    → Step 1  수업안 설계 (MAIN)
    → [human gate: approve lesson plan]
    → Steps 2–4  부가 산출물 (optional, run_supplementary)
    → Step 5  자기검수

Usage:
  cd lesson-package-generator
  python scripts/orchestrator.py \\
    --body "요 3:16" \\
    --audience "중고등부 25명" \\
    --volume 90 \\
    --emphasis "은혜 강조"

  # 부가 산출물 포함 + 비대화형 (테스트/CI)
  python scripts/orchestrator.py ... --with-teaching --with-praise --auto-approve
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.io_helpers import ensure_output_dirs, project_root_from_script, write_json
from scripts.modules import (
    step1_lesson_plan,
    step2_teaching,
    step3_praise,
    step4_promo,
    step5_self_check,
)
from scripts.pipeline_options import PipelineOptions, RunSupplementary
from scripts.sot_lib import load_state, save_state

GATE_AFTER_INTAKE = "after_intake"
GATE_AFTER_LESSON_PLAN = "after_lesson_plan"


def build_intake(
    *,
    body_text: str,
    audience: str,
    volume: str | int,
    emphasis: str,
    theme: str = "",
    locale: str = "ko",
    constraints: str = "",
) -> dict[str, Any]:
    vol = volume if isinstance(volume, str) else str(volume)
    emph = emphasis or theme
    return {
        "body_text": body_text,
        "audience": audience,
        "volume": vol,
        "emphasis": emph,
        "theme": theme or emph,
        "locale": locale,
        "constraints": constraints,
    }


def _require_human_gate(
    gate_id: str,
    message: str,
    options: PipelineOptions,
) -> bool:
    """Return True if pipeline may continue past this gate."""
    if options.gates_bypassed():
        return True
    print(f"\n[HUMAN GATE: {gate_id}]\n{message}\n")
    print(
        "Pipeline paused. Re-run with --auto-approve or --skip-human-gates "
        "to continue without interactive approval.\n"
    )
    return False


def run_pipeline(
    intake: dict[str, Any],
    project_dir: Path | None = None,
    options: PipelineOptions | None = None,
) -> dict[str, Any]:
    """Run pipeline; may stop early with ``status: waiting_human``."""
    opts = options or PipelineOptions()
    root = project_dir or project_root_from_script()
    dirs = ensure_output_dirs(root)

    write_json(dirs["intake"] / "lesson_intake.json", intake)

    state = load_state(root)
    state.setdefault("workflow", {})
    state.setdefault("run_supplementary", {})
    state["workflow"]["status"] = "in_progress"
    state["workflow"]["pending_gate"] = None
    state["intake"] = {
        "audience": intake["audience"],
        "volume": intake["volume"],
        "emphasis": intake["emphasis"],
        "body_text_ref": str(dirs["intake"] / "lesson_intake.json"),
    }
    state["run_supplementary"] = {
        "teaching": opts.run_supplementary.teaching,
        "praise": opts.run_supplementary.praise,
        "promo": opts.run_supplementary.promo,
    }
    save_state(state, root)

    if not _require_human_gate(
        GATE_AFTER_INTAKE,
        "Confirm intake: body, audience, volume, emphasis.",
        opts,
    ):
        state["workflow"]["status"] = "waiting_human"
        state["workflow"]["pending_gate"] = GATE_AFTER_INTAKE
        save_state(state, root)
        return {"status": "waiting_human", "pending_gate": GATE_AFTER_INTAKE, "intake": intake}

    # Step 1 — lesson plan (MAIN)
    state["workflow"]["current_step"] = 1
    save_state(state, root)
    lesson_plan = step1_lesson_plan.run(intake, dirs["lesson_plan"])
    lesson_plan_path = str(dirs["lesson_plan"] / "lesson_plan.json")

    state["outputs"] = state.get("outputs", {})
    state["outputs"]["step-1"] = lesson_plan_path
    state.setdefault("modules", {})
    state["modules"]["lesson_plan"] = {"version": 1, "artifact": lesson_plan_path}
    save_state(state, root)

    if not _require_human_gate(
        GATE_AFTER_LESSON_PLAN,
        f"Approve lesson plan before supplementary steps:\n  {lesson_plan_path}",
        opts,
    ):
        state["workflow"]["status"] = "waiting_human"
        state["workflow"]["pending_gate"] = GATE_AFTER_LESSON_PLAN
        state["workflow"]["current_step"] = 1
        save_state(state, root)
        return {
            "status": "waiting_human",
            "pending_gate": GATE_AFTER_LESSON_PLAN,
            "intake": intake,
            "lesson_plan": lesson_plan,
            "lesson_plan_path": lesson_plan_path,
        }

    sup = opts.run_supplementary
    teaching: dict[str, Any] | None = None
    praise: dict[str, Any] | None = None
    promo: dict[str, Any] | None = None
    prior_sup: dict[str, Any] = {}

    artifact_paths: dict[str, str] = {
        "intake": str(dirs["intake"] / "lesson_intake.json"),
        "lesson_plan": lesson_plan_path,
    }

    if sup.teaching:
        state["workflow"]["current_step"] = 2
        save_state(state, root)
        teaching = step2_teaching.run(intake, dirs["teaching"], lesson_plan)
        artifact_paths["teaching"] = str(dirs["teaching"] / "teaching_materials.json")
        prior_sup["teaching"] = teaching
        state["modules"]["teaching"] = {
            "version": 1,
            "artifact": artifact_paths["teaching"],
            "skipped": False,
        }
        state["outputs"]["step-2"] = artifact_paths["teaching"]
    else:
        state["modules"]["teaching"] = {"version": 0, "artifact": "", "skipped": True}

    if sup.praise:
        state["workflow"]["current_step"] = 3
        save_state(state, root)
        praise = step3_praise.run(
            intake,
            dirs["praise"],
            lesson_plan,
            prior={
                **prior_sup,
                "teaching_downstream": teaching.get("downstream") if teaching else None,
            },
        )
        artifact_paths["praise"] = str(dirs["praise"] / "praise_package.json")
        prior_sup["praise"] = praise
        state["modules"]["praise"] = {
            "version": 1,
            "artifact": artifact_paths["praise"],
            "skipped": False,
        }
        state["outputs"]["step-3"] = artifact_paths["praise"]
    else:
        state["modules"]["praise"] = {"version": 0, "artifact": "", "skipped": True}

    if sup.promo:
        state["workflow"]["current_step"] = 4
        save_state(state, root)
        promo = step4_promo.run(
            intake,
            dirs["promo"],
            lesson_plan,
            prior={
                **prior_sup,
                "teaching_downstream": teaching.get("downstream") if teaching else None,
                "praise_downstream": praise.get("downstream") if praise else None,
            },
            teaching_dir=dirs["teaching"],
            praise_dir=dirs["praise"],
            assemble=os.environ.get("PROMO_ASSEMBLE", "").strip() in ("1", "true"),
        )
        artifact_paths["promo"] = str(dirs["promo"] / "promo_video.v1.json")
        prior_sup["promo"] = promo
        state["modules"]["promo"] = {
            "version": 1,
            "artifact": artifact_paths["promo"],
            "skipped": False,
        }
        state["outputs"]["step-4"] = artifact_paths["promo"]
    else:
        state["modules"]["promo"] = {"version": 0, "artifact": "", "skipped": True}

    # Step 5 — self-check (always)
    state["workflow"]["current_step"] = 5
    save_state(state, root)
    prior_check = {"lesson_plan": lesson_plan, **prior_sup}
    manifest = step5_self_check.run(
        intake,
        dirs["package"],
        lesson_plan,
        artifact_paths=artifact_paths,
        supplementary=sup,
        prior=prior_check,
    )

    state["workflow"]["current_step"] = 5
    state["workflow"]["status"] = "completed"
    state["workflow"]["pending_gate"] = None
    state["outputs"]["step-5"] = str(dirs["package"] / "lesson_package_manifest.json")
    state["outputs"]["package_bundle"] = str(dirs["package"])
    state["modules"]["integration"] = {
        "version": 1,
        "manifest": state["outputs"]["step-5"],
    }
    save_state(state, root)

    return {
        "status": "completed",
        "intake": intake,
        "lesson_plan": lesson_plan,
        "teaching": teaching,
        "praise": praise,
        "promo": promo,
        "manifest": manifest,
        "artifact_paths": artifact_paths,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run lesson package pipeline (v0.2)")
    parser.add_argument("--body", required=True, help="본문")
    parser.add_argument("--audience", required=True, help="대상")
    parser.add_argument("--volume", required=True, help="분량 (e.g. 90 or 45분×2)")
    parser.add_argument("--emphasis", default="", help="강조점")
    parser.add_argument("--theme", default="", help="테마 (교보재·찬양용, emphasis 없을 때 사용)")
    parser.add_argument("--locale", default="ko")
    parser.add_argument("--constraints", default="")
    parser.add_argument("--project-dir", type=Path, default=None)

    parser.add_argument(
        "--with-teaching",
        action="store_true",
        help="Run step 2 (교보재) after lesson plan approval",
    )
    parser.add_argument("--with-praise", action="store_true", help="Run step 3 (찬양)")
    parser.add_argument("--with-promo", action="store_true", help="Run step 4 (홍보영상)")

    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Bypass human gates (non-interactive)",
    )
    parser.add_argument(
        "--skip-human-gates",
        action="store_true",
        help="Alias for --auto-approve",
    )

    args = parser.parse_args()

    if not args.emphasis and not args.theme:
        parser.error("Provide --emphasis or --theme")

    intake = build_intake(
        body_text=args.body,
        audience=args.audience,
        volume=args.volume,
        emphasis=args.emphasis,
        theme=args.theme,
        locale=args.locale,
        constraints=args.constraints,
    )

    options = PipelineOptions(
        run_supplementary=RunSupplementary(
            teaching=args.with_teaching,
            praise=args.with_praise,
            promo=args.with_promo,
        ),
        auto_approve=args.auto_approve or args.skip_human_gates,
        skip_human_gates=args.skip_human_gates,
    )

    result = run_pipeline(intake, args.project_dir, options)
    out = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(out)
    return 0 if result.get("status") == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
