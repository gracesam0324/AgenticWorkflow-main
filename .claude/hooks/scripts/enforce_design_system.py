#!/usr/bin/env python3
"""PostToolUse(Write|Edit) hook: Detect hardcoded CSS colors.

Warning only — always exits 0. Reports hardcoded colors that should
use CSS custom properties (design tokens) instead.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import parse_tool_input, detect_hardcoded_colors

CSS_EXTENSIONS = {".css", ".scss", ".less", ".html", ".jsx", ".tsx", ".vue"}


def main():
    tool_input = parse_tool_input()
    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    if not file_path:
        sys.exit(0)

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in CSS_EXTENSIONS:
        sys.exit(0)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        sys.exit(0)

    colors = detect_hardcoded_colors(content)
    if not colors:
        sys.exit(0)

    # Warning only — never block
    warnings = []
    for entry in colors[:10]:  # Limit to first 10
        line_num, color = entry[0], entry[1]
        warnings.append(f"  Line {line_num}: {color}")

    msg = (
        f"[Design System Warning] {len(colors)} hardcoded color(s) found in {os.path.basename(file_path)}:\n"
        + "\n".join(warnings)
    )
    if len(colors) > 10:
        msg += f"\n  ... and {len(colors) - 10} more"
    msg += "\n  Consider using CSS custom properties: var(--color-name)"
    print(msg, file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
