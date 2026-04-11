#!/usr/bin/env python3
"""
PostToolUse Hook — Chapter Progress Tracker

Monitors chapter draft writes and logs progress metrics:
- Word count progression per chapter over draft versions
- Time spent per chapter (based on file modification timestamps)
- Quality gate pass/fail rates

Produces a progress dashboard at outputs/progress_dashboard.json

Exit codes:
    0 — always (informational hook, never blocks)
"""

import json
import os
import re
import sys
from datetime import datetime


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        tool_input = json.loads(tool_input_raw)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Only track chapter-related writes
    basename = os.path.basename(file_path)
    m = re.match(r"ch(\d{2})_draft_v(\d+)\.(md|meta\.json)$", basename)
    if not m:
        sys.exit(0)

    ch_num = int(m.group(1))
    version = int(m.group(2))
    file_type = m.group(3)

    # Load or initialize dashboard
    dashboard_path = os.path.join(project_dir, "outputs", "progress_dashboard.json")
    dashboard = {}
    if os.path.isfile(dashboard_path):
        try:
            with open(dashboard_path, "r", encoding="utf-8") as f:
                dashboard = json.load(f)
        except (json.JSONDecodeError, OSError):
            dashboard = {}

    chapters = dashboard.setdefault("chapters", {})
    ch_key = f"ch-{ch_num}"
    ch_data = chapters.setdefault(ch_key, {
        "versions": [],
        "current_version": 0,
        "total_review_cycles": 0,
        "first_draft_time": None,
        "latest_update_time": None,
    })

    now = datetime.now().isoformat()
    ch_data["latest_update_time"] = now
    ch_data["current_version"] = max(ch_data["current_version"], version)

    if file_type == "md" and version == 1:
        ch_data["first_draft_time"] = ch_data.get("first_draft_time") or now

    # Track version history
    version_entry = {
        "version": version,
        "file_type": file_type,
        "timestamp": now,
    }

    # Add word count for prose files
    if file_type == "md":
        full_path = file_path if os.path.isabs(file_path) else os.path.join(project_dir, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                text = f.read()
            version_entry["word_count"] = len(text.split())
        except OSError:
            pass

    ch_data["versions"].append(version_entry)

    # Update dashboard summary
    dashboard["last_updated"] = now
    dashboard["total_chapters_started"] = len(chapters)
    dashboard["total_draft_versions"] = sum(
        ch.get("current_version", 0) for ch in chapters.values()
    )

    # Write dashboard
    os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
    try:
        with open(dashboard_path, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
