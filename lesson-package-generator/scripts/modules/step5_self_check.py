"""Step 5 — self-check and integrated package manifest.

Runs deterministic integrity checks (PK1–PK13) over the core lesson plan plus
any supplementary artifacts, then writes the package manifest + a readable
self-check report. The manifest ``verdict`` reflects real checks, not a stub.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.io_helpers import write_json, write_text
from scripts.package_check import render_report, run_self_check
from scripts.pipeline_options import RunSupplementary

STEP_ID = "step5_self_check"


def _module_package(prior: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Extract the supplementary *package* dict from the orchestrator's prior map."""
    result = prior.get(name)
    if not isinstance(result, dict):
        return None
    pkg = result.get("package")
    return pkg if isinstance(pkg, dict) else result


def run(
    intake: dict[str, Any],
    output_dir: Path,
    lesson_plan: dict[str, Any],
    artifact_paths: dict[str, str],
    supplementary: RunSupplementary,
    prior: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    ran = {
        "teaching": supplementary.teaching,
        "praise": supplementary.praise,
        "promo": supplementary.promo,
    }
    modules = {name: _module_package(prior, name) for name in ran}

    result = run_self_check(intake, lesson_plan, ran, modules)

    manifest = {
        "step_id": STEP_ID,
        "status": "ok",
        "verdict": result["verdict"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "core": {
            "lesson_plan": artifact_paths.get("lesson_plan"),
            "is_core": True,
        },
        "intake": {
            "audience": intake.get("audience"),
            "volume": intake.get("volume"),
            "emphasis": intake.get("emphasis"),
        },
        "artifacts": artifact_paths,
        "run_supplementary": ran,
        "skipped": {name: not flag for name, flag in ran.items()},
        "self_check": {
            "summary": result["summary"],
            "checks": result["checks"],
        },
    }

    write_json(output_dir / "lesson_package_manifest.json", manifest)
    write_text(output_dir / "self_check_report.md", render_report(result, intake))
    return manifest
