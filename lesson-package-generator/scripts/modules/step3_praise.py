"""Step 3 — praise / worship (찬양): original lyrics + Suno music prompt."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.io_helpers import write_json, write_text
from scripts.praise_contract import (
    FORMAT_VERSION,
    build_downstream_payload,
    validate_praise_package,
)
from scripts.praise_generate import generate_praise_package
from scripts.praise_render import write_praise_artifacts

STEP_ID = "step3_praise"


def run(
    intake: dict[str, Any],
    output_dir: Path,
    lesson_plan: dict[str, Any] | None = None,
    prior: dict[str, Any] | None = None,
    teaching_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate praise-worship.v1 from intake + step-1 (교보재) output."""
    output_dir.mkdir(parents=True, exist_ok=True)

    teaching: dict[str, Any] | None = None
    if prior:
        raw = prior.get("teaching_downstream") or prior.get("teaching")
        if isinstance(raw, dict):
            if "downstream" in raw and isinstance(raw["downstream"], dict):
                teaching = raw["downstream"]
            elif raw.get("format") == "teaching-materials.v1":
                teaching = {
                    "key_message": raw.get("summary", {}).get("key_message"),
                    "theme": raw.get("intake", {}).get("theme"),
                    **raw,
                }
            elif "key_message" in raw:
                teaching = raw

    package = generate_praise_package(
        intake,
        teaching=teaching,
        teaching_dir=teaching_dir,
        lesson_plan=lesson_plan,
    )
    errors = validate_praise_package(package)
    status = "ok" if not errors else "validation_warning"

    file_paths = write_praise_artifacts(package, output_dir)
    package_path = output_dir / "praise_worship.v1.json"
    write_json(package_path, package)

    artifact_paths = {"package": str(package_path.relative_to(output_dir)), **file_paths}
    downstream = build_downstream_payload(package, artifact_paths)
    write_json(output_dir / "praise_worship.downstream.json", downstream)

    manifest = {
        "format": FORMAT_VERSION,
        "step_id": STEP_ID,
        "status": status,
        "validation_errors": errors,
        "inputs": {
            "body_text": intake.get("body_text"),
            "theme": intake.get("theme") or intake.get("emphasis"),
            "teaching_consumed": bool(teaching or teaching_dir),
        },
        "artifacts": artifact_paths,
        "downstream_contract": "praise_worship.downstream.json",
        "audio_external": {
            "provider": package.get("music_generation", {}).get("provider", "suno"),
            "prompt_file": file_paths.get("suno_prompt_txt"),
            "expected_audio_path": "audio/song.mp3",
        },
        "next_steps_consume": [
            "step4_promo: use downstream.suno_prompt, song_title, chorus_preview",
            "step5_self_check: use praise_worship.v1.json",
        ],
    }
    write_json(output_dir / "praise_worship.manifest.json", manifest)

    write_json(output_dir / "praise_package.json", manifest)
    write_text(
        output_dir / "praise_package.md",
        f"# Praise ({FORMAT_VERSION})\n\n"
        f"- {file_paths.get('lyrics_md')}\n"
        f"- Suno: `{file_paths.get('suno_prompt_txt')}`\n",
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
