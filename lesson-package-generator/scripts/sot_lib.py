"""SOT helpers for lesson-package-generator/state.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def sot_path(project_dir: Path | None = None) -> Path:
    root = project_dir or Path(
        os.environ.get("LESSON_PACKAGE_PROJECT_DIR", project_root())
    )
    return root / "state.yaml"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_state(project_dir: Path | None = None) -> dict[str, Any]:
    path = sot_path(project_dir)
    if not path.is_file():
        return default_state()
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else default_state()


def save_state(state: dict[str, Any], project_dir: Path | None = None) -> None:
    path = sot_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".yaml.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    tmp.replace(path)


def default_state() -> dict[str, Any]:
    return {
        "meta": {"package_id": "", "locale": "ko"},
        "workflow": {
            "name": "lesson-package",
            "current_step": 0,
            "status": "not_started",
            "pending_gate": None,
        },
        "intake": {},
        "run_supplementary": {
            "teaching": False,
            "praise": False,
            "promo": False,
        },
        "outputs": {},
        "modules": {
            "lesson_plan": {"version": 0, "artifact": ""},
            "teaching": {"version": 0, "artifact": "", "skipped": True},
            "praise": {"version": 0, "artifact": "", "skipped": True},
            "promo": {"version": 0, "artifact": "", "skipped": True},
            "integration": {"version": 0, "manifest": ""},
        },
    }
