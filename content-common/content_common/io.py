"""Artifact I/O helpers — JSON + text, UTF-8, parent-dir safe. Domain-agnostic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
