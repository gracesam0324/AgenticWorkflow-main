#!/usr/bin/env python3
"""PreToolUse(Write|Edit) hook: Enforce file ownership in Agent Team mode.

Only active when agent_team_active=true in app-state.json.
Each agent may only modify files in their ownership domain.
Exit 0 = allow, Exit 2 = block.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import (
    parse_tool_input, get_agent_name, is_agent_team_active,
    check_file_ownership, get_project_dir,
)


def main():
    if not is_agent_team_active():
        sys.exit(0)

    tool_input = parse_tool_input()
    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    if not file_path:
        sys.exit(0)

    # Make path relative to project dir for matching
    project_dir = get_project_dir()
    rel_path = os.path.relpath(file_path, project_dir) if os.path.isabs(file_path) else file_path

    agent = get_agent_name()
    ok, owner = check_file_ownership(rel_path, agent)

    if ok:
        sys.exit(0)

    result = {
        "decision": "block",
        "reason": f"Agent '{agent}' cannot modify '{rel_path}'. "
                  f"File is owned by '{owner}'. Request the '{owner}' agent to make this change.",
    }
    print(json.dumps(result))
    sys.exit(2)


if __name__ == "__main__":
    main()
