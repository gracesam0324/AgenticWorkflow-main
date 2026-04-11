#!/usr/bin/env python3
"""Stop hook: Create a timestamped snapshot of app-state.json.

Keeps the last 10 snapshots in .claude/snapshots/.
Runs on session stop to preserve SOT state.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import create_sot_snapshot, get_project_dir


def main():
    project_dir = get_project_dir()
    sot_path = os.path.join(project_dir, "app-state.json")

    if not os.path.exists(sot_path):
        print("No app-state.json found, skipping snapshot.", file=sys.stderr)
        sys.exit(0)

    snapshot_path = create_sot_snapshot(max_keep=10)

    if snapshot_path:
        print(f"SOT snapshot saved: {snapshot_path}", file=sys.stderr)
    else:
        print("Failed to create SOT snapshot.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
