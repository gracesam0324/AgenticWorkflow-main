#!/usr/bin/env python3
"""Run 찬양 생성 only (user-facing 2단계).

Requires step-1 teaching output under --teaching-dir (default: outputs/teaching).

Usage:
  python scripts/run_praise_worship.py \\
    --body "요한복음 3:16" \\
    --theme "하나님의 사랑" \\
    --teaching-dir outputs/teaching
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
from scripts.modules import step3_praise


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
    parser = argparse.ArgumentParser(description="Generate praise lyrics + Suno prompt")
    parser.add_argument("--body", required=True)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--audience", default="중등부")
    parser.add_argument(
        "--teaching-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "teaching",
        help="Directory with teaching_materials.downstream.json",
    )
    parser.add_argument("--project-dir", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    if not (args.teaching_dir / "teaching_materials.downstream.json").is_file():
        print(f"Missing teaching output in {args.teaching_dir}", file=sys.stderr)
        return 1

    intake = build_intake(args.body, args.theme, args.audience)
    dirs = ensure_output_dirs(args.project_dir)

    result = step3_praise.run(
        intake,
        dirs["praise"],
        lesson_plan=None,
        teaching_dir=args.teaching_dir,
    )
    write_json(dirs["intake"] / "lesson_intake.json", intake)

    out = {
        "status": result.get("status"),
        "format": result.get("format"),
        "artifacts": result.get("artifacts"),
        "suno_prompt": result.get("downstream", {}).get("suno_prompt", "")[:200] + "...",
    }
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
