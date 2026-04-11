#!/usr/bin/env python3
"""TeammateIdle hook: Warn if a teammate agent has been idle too long.

Threshold: 300 seconds (5 minutes).
Outputs a warning message if idle duration exceeds the threshold.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import parse_tool_input, get_agent_name

IDLE_THRESHOLD_SECONDS = 300


def main():
    tool_input = parse_tool_input()

    agent = tool_input.get("agent_name", get_agent_name())
    idle_since = tool_input.get("idle_since", None)
    idle_duration = tool_input.get("idle_duration_seconds", 0)

    # Calculate idle duration from timestamp if provided
    if idle_since and not idle_duration:
        try:
            idle_ts = float(idle_since)
            idle_duration = time.time() - idle_ts
        except (ValueError, TypeError):
            pass

    if idle_duration < IDLE_THRESHOLD_SECONDS:
        sys.exit(0)

    minutes = idle_duration / 60
    warning = {
        "level": "warning",
        "agent": agent,
        "idle_minutes": round(minutes, 1),
        "message": (
            f"Agent '{agent}' has been idle for {minutes:.1f} minutes "
            f"(threshold: {IDLE_THRESHOLD_SECONDS // 60} min). "
            f"Consider reassigning the task or checking for blocking issues."
        ),
    }
    print(json.dumps(warning, indent=2), file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
