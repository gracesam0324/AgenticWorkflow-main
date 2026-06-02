"""Step 4 — promo video (홍보영상): storyboard + scripts + optional ffmpeg assemble."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from content_common import write_json, write_text

from .contract import (
    FORMAT_VERSION,
    build_downstream_payload,
    validate_promo_package,
)
from .generate import generate_promo_package
from .render import write_promo_artifacts

STEP_ID = "step4_promo"


def run(
    intake: dict[str, Any],
    output_dir: Path,
    lesson_plan: dict[str, Any] | None = None,
    prior: dict[str, Any] | None = None,
    teaching_dir: Path | None = None,
    praise_dir: Path | None = None,
    assemble: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    teaching = praise = None
    if prior:
        t = prior.get("teaching_downstream") or prior.get("teaching")
        if isinstance(t, dict):
            teaching = t.get("downstream", t) if "downstream" in t else t
        p = prior.get("praise_downstream") or prior.get("praise")
        if isinstance(p, dict):
            praise = p.get("downstream", p) if "downstream" in p else p

    package = generate_promo_package(
        intake,
        teaching=teaching,
        praise=praise,
        teaching_dir=teaching_dir,
        praise_dir=praise_dir,
        prior=prior,
        lesson_plan=lesson_plan,
    )
    errors = validate_promo_package(package)
    status = "ok" if not errors else "validation_warning"

    file_paths = write_promo_artifacts(package, output_dir)
    write_json(output_dir / "promo_video.v1.json", package)

    artifact_paths = {"package": "promo_video.v1.json", **file_paths}
    downstream = build_downstream_payload(package, artifact_paths)
    write_json(output_dir / "promo_video.downstream.json", downstream)

    assembly_result: dict[str, Any] | None = None
    do_assemble = assemble or os.environ.get("PROMO_ASSEMBLE", "").strip() in (
        "1",
        "true",
        "yes",
    )
    if do_assemble and shutil.which("ffmpeg"):
        from .assemble import assemble as ffmpeg_assemble

        music = None
        default_music = output_dir.parent / "praise" / "audio" / "song.mp3"
        if default_music.is_file():
            music = default_music
        try:
            mp4 = ffmpeg_assemble(output_dir, music_path=music)
            artifact_paths["assembled_mp4"] = str(mp4.relative_to(output_dir))
            assembly_result = {"success": True, "path": str(mp4)}
        except Exception as exc:  # noqa: BLE001
            assembly_result = {"success": False, "error": str(exc)}
    elif do_assemble:
        assembly_result = {"success": False, "error": "ffmpeg not in PATH"}

    manifest = {
        "format": FORMAT_VERSION,
        "step_id": STEP_ID,
        "status": status,
        "validation_errors": errors,
        "inputs": {
            "theme": intake.get("theme") or intake.get("emphasis"),
            "duration_seconds": package.get("meta", {}).get("total_duration_seconds"),
        },
        "artifacts": artifact_paths,
        "downstream_contract": "promo_video.downstream.json",
        "assembly": assembly_result,
        "next_steps_consume": [
            "step5_self_check: promo_video.v1.json",
            "Manual: video AI → assets/cut_XX.mp4 → assemble_promo_video.py",
        ],
    }
    write_json(output_dir / "promo_video.manifest.json", manifest)
    write_json(output_dir / "promo_video_spec.json", manifest)
    write_text(
        output_dir / "promo_video_spec.md",
        f"# Promo ({FORMAT_VERSION})\n\n"
        f"- Storyboard: `{file_paths['storyboard_json']}`\n"
        f"- SRT: `{file_paths['subtitles_srt']}`\n"
        f"- Assemble: `python scripts/assemble_promo_video.py --promo-dir {output_dir}`\n",
    )

    return {
        "step_id": STEP_ID,
        "format": FORMAT_VERSION,
        "status": status,
        "package": package,
        "manifest": manifest,
        "artifacts": artifact_paths,
        "downstream": downstream,
        "assembly": assembly_result,
    }
