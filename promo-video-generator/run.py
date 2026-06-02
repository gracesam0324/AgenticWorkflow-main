#!/usr/bin/env python3
"""Standalone runner — 홍보영상(promo-video.v1) 단독 생성.

입력: 테마 · 대상 (본문/교보재/찬양/lesson_plan 불필요)
선택: --teaching-downstream / --praise-downstream <path.json> 으로 정합 강화.
      --assemble 시 ffmpeg 조립(설치 + assets 필요).

Usage:
  python promo-video-generator/run.py --theme "중등 수련회" --audience "중등부"
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
from promo_video_generator import run as run_promo  # noqa: E402


def _load(path: Path | None) -> dict[str, Any] | None:
    if path and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate retreat promo video package (홍보영상)")
    parser.add_argument("--theme", required=True, help="테마")
    parser.add_argument("--body", default="", help="본문(선택)")
    parser.add_argument("--audience", default="중등부", help="대상")
    parser.add_argument("--teaching-downstream", type=Path, default=None, help="(선택) 교보재 downstream JSON")
    parser.add_argument("--praise-downstream", type=Path, default=None, help="(선택) 찬양 downstream JSON")
    parser.add_argument("--assemble", action="store_true", help="ffmpeg 조립(가능 시)")
    parser.add_argument("--output-dir", type=Path, default=MODULE_ROOT / "outputs")
    args = parser.parse_args()

    intake: dict[str, Any] = {
        "body_text": args.body,
        "theme": args.theme,
        "audience": args.audience,
        "emphasis": args.theme,
        "volume": "45",
        "locale": "ko",
    }
    prior = {
        "teaching_downstream": _load(args.teaching_downstream),
        "praise_downstream": _load(args.praise_downstream),
    }

    promo_dir = args.output_dir / "promo"
    result = run_promo(intake, promo_dir, lesson_plan=None, prior=prior, assemble=args.assemble)
    write_json(args.output_dir / "intake" / "lesson_intake.json", intake)

    summary = {
        "status": result.get("status"),
        "format": result.get("format"),
        "duration": result.get("package", {}).get("meta", {}).get("total_duration_seconds"),
        "assembly": result.get("assembly"),
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
