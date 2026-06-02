"""Artifact I/O for lesson-package.

Generic write/read helpers moved to `content-common` (Phase 0); the
module-specific path helpers (`project_root_from_script`, `ensure_output_dirs`)
stay here. Re-exported names keep existing imports working.
See MODULE-EXTRACTION-PLAN.md.
"""

from __future__ import annotations

from pathlib import Path

from content_common.io import read_prompt, write_json, write_text  # noqa: F401


def project_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_output_dirs(base: Path) -> dict[str, Path]:
    dirs = {
        "intake": base / "outputs" / "intake",
        "lesson_plan": base / "outputs" / "lesson_plan",
        "teaching": base / "outputs" / "teaching",
        "praise": base / "outputs" / "praise",
        "promo": base / "outputs" / "promo",
        "package": base / "outputs" / "package",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs
