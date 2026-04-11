#!/usr/bin/env python3
"""
PreToolUse(Write|Edit) hook — enforces AC-2 SOT single-writer rule.

Blocks ANY Write or Edit targeting app-state.json UNLESS the caller
is the orchestrator agent. Structural enforcement of exclusive write access.

Input: JSON on stdin with {"tool_name": "Write|Edit", "tool_input": {"file_path": "..."}}
Output: exit 0 (allow) or exit 2 + stderr (block)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import parse_tool_input, get_agent_name, SOT_FILES, ALLOWED_SOT_WRITERS


def main():
    tool_input = parse_tool_input()
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    basename = os.path.basename(file_path)

    if basename not in SOT_FILES:
        sys.exit(0)

    agent = get_agent_name()

    # ALLOWED_SOT_WRITERS is a list: ["church-app-orchestrator"]
    if agent in ALLOWED_SOT_WRITERS:
        sys.exit(0)

    # Block: non-orchestrator attempting SOT write
    print(f"BLOCKED: Agent '{agent}' attempted to write to {basename}. "
          f"Only {ALLOWED_SOT_WRITERS} can write to SOT (AC-2).",
          file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
