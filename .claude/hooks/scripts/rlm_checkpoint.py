#!/usr/bin/env python3
"""Stop Hook — RLM Recovery Point.
Creates an RLM recovery point in state.yaml on every Stop event."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _resolve_project_dir() -> Path:
    """Resolve the autobiography-generator project root."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


# Maximum number of recovery points to retain
MAX_RECOVERY_POINTS = 20


def _load_state(project_dir: Path) -> dict | None:
    """Load state.yaml via sot_lib (preferred) or direct YAML read."""
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


def _save_state(state: dict, project_dir: Path) -> bool:
    """Save state.yaml via sot_lib (preferred) or direct YAML write.

    Returns True on success, False on failure.
    """
    scripts_dir = str(project_dir / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from sot_lib import save_state
        save_state(state)
        return True
    except (ImportError, Exception):
        pass

    # Fallback: direct YAML write
    state_path = project_dir / ".claude" / "state.yaml"
    try:
        import yaml
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(
                state, f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        return True
    except (ImportError, Exception):
        return False


def _build_recovery_point(state: dict) -> dict:
    """Build a recovery point dict from the current state.

    Captures:
        - timestamp (ISO 8601 UTC)
        - current workflow step and substep
        - current phase
        - task pool snapshot (counts only)
        - active teams
    """
    now = datetime.now(timezone.utc).isoformat()

    workflow = state.get("workflow", {})
    orchestration = state.get("orchestration", {})

    # Current position in the workflow
    current_step = workflow.get("current_step")
    current_substep = orchestration.get("current_substep")
    current_phase = orchestration.get("current_phase", workflow.get("status", "unknown"))

    # Task pool summary
    tasks = orchestration.get("tasks", {})
    task_summary = {
        "total": tasks.get("total", 0),
        "completed": tasks.get("completed", 0),
        "failed": tasks.get("failed", 0),
        "blocked": tasks.get("blocked", 0),
    }

    # Active teams
    teams = orchestration.get("teams", {})
    active_teams = [
        name for name, info in teams.items()
        if isinstance(info, dict) and info.get("status") in ("active", "in_progress")
    ]

    return {
        "timestamp": now,
        "step": current_step,
        "substep": current_substep,
        "phase": current_phase,
        "task_summary": task_summary,
        "active_teams": active_teams,
    }


def main() -> None:
    """Entry point — create an RLM recovery point on Stop."""
    project_dir = _resolve_project_dir()

    # ── Load state ───────────────────────────────────────────────────
    state = _load_state(project_dir)
    if state is None:
        # No state.yaml yet — nothing to checkpoint
        sys.exit(0)

    # ── Build recovery point ─────────────────────────────────────────
    recovery_point = _build_recovery_point(state)

    # ── Merge into orchestration.rlm atomically ─────────────────────
    # Uses merge_orchestration_section() to prevent logical race
    # with fallback_controller.py writing to orchestration.fallback.
    try:
        from scripts.sot_lib import merge_orchestration_section

        # Build the rlm updates
        rlm = state.get("orchestration", {}).get("rlm", {})
        recovery_points = rlm.get("recovery_points", [])
        if not isinstance(recovery_points, list):
            recovery_points = []
        recovery_points.append(recovery_point)
        if len(recovery_points) > MAX_RECOVERY_POINTS:
            recovery_points = recovery_points[-MAX_RECOVERY_POINTS:]

        sot_path = project_dir / ".claude" / "state.yaml"
        merge_orchestration_section("rlm", {
            "recovery_points": recovery_points,
            "last_snapshot": recovery_point["timestamp"],
            "session_count": rlm.get("session_count", 0) + 1,
        }, sot_path=sot_path)

        print(
            f"RLM CHECKPOINT — Recovery point saved: "
            f"step={recovery_point['step']}, "
            f"phase={recovery_point['phase']}, "
            f"points={len(recovery_points)}/{MAX_RECOVERY_POINTS}",
            file=sys.stderr,
        )
    except Exception as e:
        # Fallback: update state dict directly and save via _save_state
        orch = state.setdefault("orchestration", {})
        rlm = orch.setdefault("rlm", {})
        rp = rlm.setdefault("recovery_points", [])
        if not isinstance(rp, list):
            rp = []
            rlm["recovery_points"] = rp
        rp.append(recovery_point)
        if len(rp) > MAX_RECOVERY_POINTS:
            rlm["recovery_points"] = rp[-MAX_RECOVERY_POINTS:]
        rlm["last_snapshot"] = recovery_point["timestamp"]
        rlm["session_count"] = rlm.get("session_count", 0) + 1

        saved = _save_state(state, project_dir)
        print(
            f"RLM CHECKPOINT — {'Saved' if saved else 'FAILED'} (fallback): {e}",
            file=sys.stderr,
        )

    # Always exit 0 — never block the pipeline
    sys.exit(0)


if __name__ == "__main__":
    main()
