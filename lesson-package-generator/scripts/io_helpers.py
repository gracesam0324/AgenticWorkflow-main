"""Artifact I/O — JSON + markdown under outputs/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_prompt(prompt_path: Path) -> str:
    if not prompt_path.is_file():
        msg = f"Prompt file not found: {prompt_path}"
        raise FileNotFoundError(msg)
    return prompt_path.read_text(encoding="utf-8")
