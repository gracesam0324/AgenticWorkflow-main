#!/usr/bin/env python3
"""P1 quality gate for Step 1 — validate lesson_plan.json (LP1–LP10).

Usage:
  python scripts/validate_lesson_plan.py [path/to/lesson_plan.json]

Exit code 0 = pass, 1 = validation errors, 2 = file/parse error.
Default path: outputs/lesson_plan/lesson_plan.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lesson_plan_contract import validate_lesson_plan  # noqa: E402


def main(argv: list[str]) -> int:
    default = PROJECT_ROOT / "outputs" / "lesson_plan" / "lesson_plan.json"
    target = Path(argv[1]) if len(argv) > 1 else default

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    if not target.is_file():
        print(f"[LP] file not found: {target}")
        return 2
    try:
        plan = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[LP] invalid JSON: {exc}")
        return 2

    errors = validate_lesson_plan(plan)
    if not errors:
        print(f"[LP] PASS — {target.name} satisfies LP1–LP10")
        return 0

    print(f"[LP] FAIL — {len(errors)} violation(s) in {target.name}:")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
