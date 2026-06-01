"""Step 2 — teaching materials (교보재): JSON contract + HTML/PDF/slides files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.io_helpers import write_json, write_text
from scripts.teaching_contract import (
    FORMAT_VERSION,
    build_downstream_payload,
    validate_teaching_package,
)
from scripts.teaching_generate import generate_teaching_package
from scripts.teaching_render import write_teaching_artifacts

STEP_ID = "step2_teaching"


def run(
    intake: dict[str, Any],
    output_dir: Path,
    lesson_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate teaching-materials.v1 package and on-disk artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)

    package = generate_teaching_package(intake, lesson_plan)
    errors = validate_teaching_package(package)
    status = "ok" if not errors else "validation_warning"

    file_paths = write_teaching_artifacts(package, output_dir)

    package_path = output_dir / "teaching_materials.v1.json"
    write_json(package_path, package)

    artifact_paths = {
        "package": str(package_path.relative_to(output_dir)),
        **file_paths,
    }
    downstream = build_downstream_payload(package, artifact_paths)
    write_json(output_dir / "teaching_materials.downstream.json", downstream)

    manifest = {
        "format": FORMAT_VERSION,
        "step_id": STEP_ID,
        "status": status,
        "validation_errors": errors,
        "intake_ref": {
            "body_text": intake.get("body_text"),
            "theme": intake.get("theme") or intake.get("emphasis"),
            "audience": intake.get("audience"),
        },
        "artifacts": artifact_paths,
        "downstream_contract": "teaching_materials.downstream.json",
        "next_steps_consume": [
            "step3_praise: use downstream.theme, key_message, discussion_questions",
            "step4_promo: use downstream.artifacts.slides_html",
            "step5_self_check: use teaching_materials.v1.json",
        ],
    }
    write_json(output_dir / "teaching_materials.manifest.json", manifest)

    # Legacy filenames for orchestrator paths
    write_json(output_dir / "teaching_materials.json", manifest)
    write_text(
        output_dir / "teaching_materials.md",
        f"# Teaching materials ({FORMAT_VERSION})\n\n"
        f"- Package: `{package_path.name}`\n"
        f"- Worksheet: `{file_paths.get('worksheet_html', '')}`\n"
        f"- PDF: `{file_paths.get('worksheet_pdf') or '(not generated)'}`\n"
        f"- Slides: `{file_paths.get('slides_html', '')}`\n",
    )

    return {
        "step_id": STEP_ID,
        "format": FORMAT_VERSION,
        "status": status,
        "package": package,
        "manifest": manifest,
        "artifacts": artifact_paths,
        "downstream": downstream,
    }
