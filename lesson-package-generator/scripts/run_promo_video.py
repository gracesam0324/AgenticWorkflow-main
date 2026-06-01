#!/usr/bin/env python3
"""Run 3단계 홍보영상 생성 (teaching + praise downstream + theme).

Usage:
  python scripts/run_promo_video.py --theme "중등 수련회" --assemble
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
from scripts.modules import step4_promo


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate retreat promo video package")
    parser.add_argument("--body", default="")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--audience", default="중등부")
    parser.add_argument("--teaching-dir", type=Path, default=PROJECT_ROOT / "outputs" / "teaching")
    parser.add_argument("--praise-dir", type=Path, default=PROJECT_ROOT / "outputs" / "praise")
    parser.add_argument("--assemble", action="store_true", help="Run ffmpeg assemble if available")
    parser.add_argument("--project-dir", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    intake: dict[str, Any] = {
        "body_text": args.body,
        "theme": args.theme,
        "audience": args.audience,
        "emphasis": args.theme,
        "volume": "45",
        "locale": "ko",
    }

    dirs = ensure_output_dirs(args.project_dir)
    result = step4_promo.run(
        intake,
        dirs["promo"],
        lesson_plan=None,
        teaching_dir=args.teaching_dir,
        praise_dir=args.praise_dir,
        assemble=args.assemble,
    )

    write_json(dirs["intake"] / "lesson_intake.json", intake)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(json.dumps(
        {
            "status": result.get("status"),
            "format": result.get("format"),
            "artifacts": result.get("artifacts"),
            "assembly": result.get("assembly"),
            "duration": result.get("package", {}).get("meta", {}).get("total_duration_seconds"),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
