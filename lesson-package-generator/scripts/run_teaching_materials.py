#!/usr/bin/env python3
"""Run 교보재 생성 only (user-facing '1단계' entry).

Input: 본문 · 테마 · 대상
Output: teaching-materials.v1 + worksheet HTML/PDF + slides HTML

Usage:
  cd lesson-package-generator
  python scripts/run_teaching_materials.py \\
    --body "요한복음 3:16" \\
    --theme "하나님의 사랑" \\
    --audience "중등부 2학년 20명"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.io_helpers import ensure_output_dirs, write_json
from scripts.modules import step2_teaching


def build_intake(
    *,
    body_text: str,
    theme: str,
    audience: str,
    volume: str = "45",
    emphasis: str = "",
    locale: str = "ko",
) -> dict[str, Any]:
    return {
        "body_text": body_text,
        "theme": theme,
        "audience": audience,
        "volume": volume,
        "emphasis": emphasis or theme,
        "locale": locale,
        "constraints": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate middle-school teaching materials")
    parser.add_argument("--body", required=True, help="본문")
    parser.add_argument("--theme", required=True, help="테마")
    parser.add_argument("--audience", default="중등부", help="대상")
    parser.add_argument("--volume", default="45", help="분량(분)")
    parser.add_argument("--project-dir", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    intake = build_intake(
        body_text=args.body,
        theme=args.theme,
        audience=args.audience,
        volume=args.volume,
    )

    dirs = ensure_output_dirs(args.project_dir)
    result = step2_teaching.run(intake, dirs["teaching"], lesson_plan=None)

    write_json(dirs["intake"] / "lesson_intake.json", intake)

    out = {
        "status": result.get("status"),
        "format": result.get("format"),
        "artifacts": result.get("artifacts"),
        "downstream": str(dirs["teaching"] / "teaching_materials.downstream.json"),
    }
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
