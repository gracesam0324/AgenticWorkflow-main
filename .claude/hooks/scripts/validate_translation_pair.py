#!/usr/bin/env python3
"""
PostToolUse(Write) hook — validates Korean translation files (.ko.md).

When a .ko.md file is written, validates it against the English original.
Checks: section count, code block count, glossary term preservation, empty sections.
Exit 0 with warnings (does not block for minor issues).
Exit 2 for critical structural mismatches.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import parse_tool_input, validate_translation_pair


def main():
    tool_input = parse_tool_input()
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Only process .ko.md files
    if not file_path.endswith(".ko.md"):
        sys.exit(0)

    # Derive English original path: foo.ko.md → foo.md
    en_path = file_path[:-6] + ".md"

    if not os.path.exists(en_path):
        print(
            f"[Translation] No English original found for {os.path.basename(file_path)}. "
            f"Expected: {en_path}",
            file=sys.stderr,
        )
        sys.exit(0)  # Warning only — original might not exist yet

    # validate_translation_pair returns (valid: bool, errors: list)
    valid, errors = validate_translation_pair(en_path, file_path)

    if valid:
        print(f"[Translation] {os.path.basename(file_path)} validates OK.", file=sys.stderr)
        sys.exit(0)

    # Separate critical errors (structural mismatches) from warnings
    critical = [e for e in errors if "mismatch" in e.lower() or "modified" in e.lower()]
    warnings = [e for e in errors if e not in critical]

    if critical:
        print(f"BLOCKED: Translation validation failed for {os.path.basename(file_path)}:", file=sys.stderr)
        for err in critical:
            print(f"  ✗ {err}", file=sys.stderr)
        sys.exit(2)

    if warnings:
        print(f"[Translation Warning] Issues in {os.path.basename(file_path)}:", file=sys.stderr)
        for err in warnings:
            print(f"  ⚠ {err}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
