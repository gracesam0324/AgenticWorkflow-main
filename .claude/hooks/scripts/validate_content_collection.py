#!/usr/bin/env python3
"""
Phase 1→2 Content Collection Gate — H-CRITICAL deterministic validator.

Validates that ALL required content fields for the chosen app type
are populated in SOT (app-state.json) before allowing Phase 2.

Usage:
  python validate_content_collection.py --project-dir /path/to/project --json

Output (JSON to stdout):
  {
    "complete": true/false,
    "app_type": "quiz",
    "missing": ["content.quiz_questions", ...],
    "field_count": 4,
    "validated_count": 4
  }

Exit codes:
  0 — all required fields present (gate PASS)
  1 — missing fields or SOT error (gate FAIL)
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import validate_content_collection, read_sot, get_project_dir


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1→2 Content Collection Gate (H-CRITICAL)"
    )
    parser.add_argument(
        "--project-dir", default=None,
        help="Path to project directory containing app-state.json"
    )
    parser.add_argument(
        "--json", action="store_true", default=True,
        help="Output as JSON (default)"
    )
    args = parser.parse_args()

    project_dir = args.project_dir or get_project_dir()
    sot_data = read_sot(project_dir)

    if not sot_data:
        result = {
            "complete": False,
            "app_type": "unknown",
            "missing": ["app-state.json not found or empty"],
            "field_count": 0,
            "validated_count": 0,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # validate_content_collection returns (complete: bool, missing: list, app_type: str)
    complete, missing, app_type = validate_content_collection(sot_data, project_dir)

    # Count required fields for this app type
    from _church_app_lib import CONTENT_MATRIX
    matrix = CONTENT_MATRIX.get(app_type, {})
    field_count = len(matrix.get("required_fields", {}))

    result = {
        "complete": complete,
        "app_type": app_type,
        "missing": missing,
        "field_count": field_count,
        "validated_count": field_count - len(missing),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if complete else 1)


if __name__ == "__main__":
    main()
