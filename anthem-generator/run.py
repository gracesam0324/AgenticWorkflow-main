#!/usr/bin/env python3
"""Standalone runner — 찬양(praise-worship.v1) 단독 생성.

입력: 본문 · 테마 · 대상 (교보재/lesson_plan 불필요)
선택: --teaching-downstream <path.json> 으로 교보재 downstream을 주입하면 정합 강화.

Usage:
  python anthem-generator/run.py --body "요한복음 3:16" --theme "하나님의 사랑" --audience "중등부"
  python anthem-generator/run.py --body "..." --theme "..." --teaching-downstream ../lesson-package-generator/outputs/teaching/teaching_materials.downstream.json
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

from anthem_generator import run as run_anthem  # noqa: E402
from content_common import write_json  # noqa: E402


def build_intake(body: str, theme: str, audience: str = "중등부") -> dict[str, Any]:
    return {
        "body_text": body,
        "theme": theme,
        "audience": audience,
        "emphasis": theme,
        "volume": "45",
        "locale": "ko",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate praise lyrics + Suno prompt (찬양)")
    parser.add_argument("--body", required=True, help="본문")
    parser.add_argument("--theme", required=True, help="테마")
    parser.add_argument("--audience", default="중등부", help="대상")
    parser.add_argument(
        "--teaching-downstream",
        type=Path,
        default=None,
        help="(선택) 교보재 downstream JSON 경로 — 정합 강화용",
    )
    parser.add_argument("--output-dir", type=Path, default=MODULE_ROOT / "outputs")
    args = parser.parse_args()

    teaching: dict[str, Any] | None = None
    if args.teaching_downstream and args.teaching_downstream.is_file():
        teaching = json.loads(args.teaching_downstream.read_text(encoding="utf-8"))

    intake = build_intake(args.body, args.theme, args.audience)
    praise_dir = args.output_dir / "praise"
    result = run_anthem(intake, praise_dir, lesson_plan=None, prior={"teaching_downstream": teaching})
    write_json(args.output_dir / "intake" / "lesson_intake.json", intake)

    summary = {
        "status": result.get("status"),
        "format": result.get("format"),
        "teaching_used": teaching is not None,
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
