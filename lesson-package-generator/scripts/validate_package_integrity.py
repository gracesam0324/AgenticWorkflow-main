#!/usr/bin/env python3
"""P1 quality gate for Step 5 — validate integrated package (PK1–PK13).

Usage:
  python scripts/validate_package_integrity.py [outputs_dir]

Reconstructs (intake, lesson_plan, supplementary packages) from the outputs
tree and runs the deterministic integrity checks.

Exit code 0 = PASS (no critical failures), 1 = FAIL, 2 = outputs not found.
Default outputs_dir: outputs/
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.package_check import load_from_disk, run_self_check  # noqa: E402


def main(argv: list[str]) -> int:
    outputs_dir = Path(argv[1]) if len(argv) > 1 else PROJECT_ROOT / "outputs"

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    plan_path = outputs_dir / "lesson_plan" / "lesson_plan.json"
    if not plan_path.is_file():
        print(f"[PK] lesson plan not found: {plan_path}")
        return 2

    data = load_from_disk(outputs_dir)
    result = run_self_check(data["intake"], data["lesson_plan"], data["ran"], data["modules"])
    s = result["summary"]

    print(f"[PK] verdict={result['verdict']} — {s['passed']}/{s['total']} passed, "
          f"{s['critical_failures']} critical, {s['warnings']} warning(s)")
    for c in result["checks"]:
        status = "PASS" if c["passed"] else ("N/A" if c["severity"] == "info" else "FAIL")
        if status != "PASS":
            print(f"  [{status}] {c['id']} {c['title']} ({c['severity']}): {c['detail']}")

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
