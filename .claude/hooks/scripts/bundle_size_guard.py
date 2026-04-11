#!/usr/bin/env python3
"""
PostToolUse(Write|Edit) hook — enforces bundle size limits.

Target: 300KB. Hard limit: 500KB.
Exit 0 if under hard limit (warning if over target).
Exit 2 if over hard limit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import calculate_bundle_size, get_project_dir, TARGET_KB, HARD_LIMIT_KB


def main():
    project_dir = get_project_dir()

    # calculate_bundle_size returns (total_kb, file_count, over_target, over_hard_limit)
    total_kb, file_count, over_target, over_hard = calculate_bundle_size(project_dir)

    if over_hard:
        print(
            f"BLOCKED: Bundle size {total_kb:.0f}KB exceeds hard limit of {HARD_LIMIT_KB}KB. "
            f"({file_count} files). Reduce file sizes or remove unnecessary assets.",
            file=sys.stderr,
        )
        sys.exit(2)

    if over_target:
        print(
            f"[Bundle Size Warning] {total_kb:.0f}KB exceeds target of {TARGET_KB}KB "
            f"(hard limit: {HARD_LIMIT_KB}KB). Consider optimizing.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
