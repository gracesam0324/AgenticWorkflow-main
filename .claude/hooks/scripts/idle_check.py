#!/usr/bin/env python3
"""TeammateIdle hook — prevents premature teammate idling.
Agent Teams only — inert in Layer 2 subagent mode."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _resolve_project_dir() -> Path:
    """Resolve the autobiography-generator project root."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def _parse_stdin() -> dict | None:
    """Read and parse the TeammateIdle JSON payload from stdin.

    Expected format (Agent Teams TeammateIdle hook):
        {"teammate_id": "...", "teammate_name": "...", "idle_since": "..."}

    Returns None if stdin is empty or unparseable.
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


def _load_state(project_dir: Path) -> dict | None:
    """Load the SOT state.yaml using sot_lib if available, else raw YAML."""
    # Try the canonical sot_lib import
    scripts_dir = str(project_dir / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from sot_lib import load_state
        return load_state()
    except (ImportError, Exception):
        pass

    # Fallback: direct YAML read
    state_path = project_dir / ".claude" / "state.yaml"
    if not state_path.is_file():
        return None

    try:
        import yaml
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (ImportError, Exception):
        return None


def _get_unclaimed_tasks(state: dict) -> list[dict]:
    """Extract unclaimed tasks from the orchestration task pool.

    A task is unclaimed if its status is 'pending' or 'ready' and
    it has no assigned teammate.
    """
    orch = state.get("orchestration", {})
    tasks = orch.get("tasks", {})
    items = tasks.get("items", {})

    unclaimed = []
    for task_id, task_info in items.items():
        if not isinstance(task_info, dict):
            continue

        status = task_info.get("status", "")
        assignee = task_info.get("assigned_to", "")

        # Task is unclaimed if pending/ready and no assignee
        if status in ("pending", "ready", "queued", "unassigned") and not assignee:
            unclaimed.append({"task_id": task_id, **task_info})

    return unclaimed


def main() -> None:
    """Entry point — check if idle teammate should be woken for unclaimed tasks."""
    project_dir = _resolve_project_dir()

    # ── Parse stdin ──────────────────────────────────────────────────
    payload = _parse_stdin()
    if payload is None:
        # No input — allow idle (fail-open)
        sys.exit(0)

    teammate_id = payload.get("teammate_id", "unknown")
    teammate_name = payload.get("teammate_name", teammate_id)

    # ── Load state ───────────────────────────────────────────────────
    state = _load_state(project_dir)
    if state is None:
        # Cannot read state — allow idle (fail-open)
        sys.exit(0)

    # ── Check for unclaimed tasks ────────────────────────────────────
    unclaimed = _get_unclaimed_tasks(state)

    if not unclaimed:
        # No unclaimed tasks — teammate may idle
        sys.exit(0)

    # ── Unclaimed tasks exist — wake the teammate ────────────────────
    task_ids = [t["task_id"] for t in unclaimed[:5]]  # Show up to 5
    remaining = len(unclaimed) - len(task_ids)

    lines = [
        f"IDLE CHECK REJECT — Teammate '{teammate_name}' ({teammate_id}) "
        f"cannot idle: {len(unclaimed)} unclaimed task(s) in the pool.",
        "",
        "Unclaimed tasks:",
    ]
    for tid in task_ids:
        lines.append(f"  - {tid}")
    if remaining > 0:
        lines.append(f"  ... and {remaining} more")
    lines.append("")
    lines.append("Pick up an unclaimed task before going idle.")

    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)  # Reject idle — wake teammate


if __name__ == "__main__":
    main()
