#!/usr/bin/env python3
"""Standalone runner — 교보재(teaching-materials.v1) 단독 생성.

입력: 본문 · 테마 · 대상 (lesson_plan 불필요)
출력: teaching-materials.v1 + worksheet HTML/PDF + slides HTML

Usage:
  python material-generator/run.py --body "요한복음 3:16" --theme "하나님의 사랑" --audience "중등부 20명"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODULE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MODULE_ROOT.parent
for _p in (MODULE_ROOT, REPO_ROOT / "content-common"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from content_common import write_json  # noqa: E402
from material_generator import run as run_material  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Generate middle-school teaching materials (교보재)")
    parser.add_argument("--body", required=True, help="본문")
    parser.add_argument("--theme", required=True, help="테마")
    parser.add_argument("--audience", default="중등부", help="대상")
    parser.add_argument("--volume", default="45", help="분량(분)")
    parser.add_argument("--output-dir", type=Path, default=MODULE_ROOT / "outputs")
    args = parser.parse_args()

    intake = build_intake(
        body_text=args.body, theme=args.theme, audience=args.audience, volume=args.volume
    )

    teaching_dir = args.output_dir / "teaching"
    result = run_material(intake, teaching_dir, lesson_plan=None)
    write_json(args.output_dir / "intake" / "lesson_intake.json", intake)

    summary = {
        "status": result.get("status"),
        "format": result.get("format"),
        "artifacts": result.get("artifacts"),
    }
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
