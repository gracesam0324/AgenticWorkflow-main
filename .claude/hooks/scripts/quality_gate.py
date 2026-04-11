#!/usr/bin/env python3
"""SECONDARY quality gate — Agent Teams TaskCompleted hook.
Same logic as quality_gate_check.py but reads task from stdin JSON.
Only fires when Agent Teams are enabled. Inert in Layer 2 subagent mode."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _resolve_project_dir() -> Path:
    """Resolve the autobiography-generator project root."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def _parse_stdin() -> dict | None:
    """Read and parse the TaskCompleted JSON payload from stdin.

    Expected format (Agent Teams TaskCompleted hook):
        {"task_id": "...", "task": {...}, "result": {...}}

    Returns None if stdin is empty or unparseable.
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


def _extract_step_and_chapter(payload: dict) -> tuple[str | None, int | None]:
    """Extract step_id and optional chapter number from the task payload.

    The task metadata should contain:
        task.metadata.step   — workflow step ID (e.g., "7c")
        task.metadata.chapter — optional chapter number
    """
    task = payload.get("task", {})
    metadata = task.get("metadata", {})

    step_id = metadata.get("step")
    if step_id is None:
        # Fallback: try to infer from task_id pattern like "step-7c" or "build-0.5a"
        task_id = payload.get("task_id", "")
        for prefix in ("step-", "build-", "phase-"):
            if task_id.startswith(prefix):
                step_id = task_id[len(prefix):]
                break

    chapter = metadata.get("chapter")
    if chapter is not None:
        try:
            chapter = int(chapter)
        except (ValueError, TypeError):
            chapter = None

    return step_id, chapter


def main() -> None:
    """Entry point — read TaskCompleted JSON, run quality checks, pass/reject."""
    project_dir = _resolve_project_dir()

    # ── Parse stdin ──────────────────────────────────────────────────
    payload = _parse_stdin()
    if payload is None:
        # No input or parse failure — allow (fail-open for safety)
        sys.exit(0)

    # ── Extract routing info ─────────────────────────────────────────
    step_id, chapter = _extract_step_and_chapter(payload)
    if step_id is None:
        # Cannot determine which step completed — allow
        print(
            "QUALITY GATE HOOK: No step_id found in task metadata — skipping checks.",
            file=sys.stderr,
        )
        sys.exit(0)

    # ── Import and run the PRIMARY quality gate logic ────────────────
    # Add the scripts directory to sys.path so we can import quality_gate_check
    scripts_dir = str(project_dir / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from quality_gate_check import run_checks
    except ImportError as e:
        print(
            f"QUALITY GATE HOOK: Cannot import quality_gate_check — {e}. Allowing.",
            file=sys.stderr,
        )
        sys.exit(0)

    # ── Execute checks ───────────────────────────────────────────────
    try:
        results = run_checks(step_id, project_dir, chapter)
    except Exception as e:
        # Quality gate infrastructure failure — allow to avoid blocking pipeline
        print(
            f"QUALITY GATE HOOK: Check execution error — {e}. Allowing.",
            file=sys.stderr,
        )
        sys.exit(0)

    # ── Evaluate results ─────────────────────────────────────────────
    failures = [r for r in results if not r.passed]

    if failures:
        error_lines = [
            f"QUALITY GATE REJECT — Task '{payload.get('task_id', '?')}' "
            f"failed {len(failures)}/{len(results)} checks for step {step_id}:",
        ]
        for f in failures:
            error_lines.append(f"  [{f.check_id}] {f.message}")
        error_lines.append("")
        error_lines.append("Fix the issues above and retry the task.")
        print("\n".join(error_lines), file=sys.stderr)
        sys.exit(2)  # Reject — blocks task completion

    # All checks passed
    passed_count = len(results)
    print(
        f"QUALITY GATE PASS — Task '{payload.get('task_id', '?')}': "
        f"{passed_count} checks OK for step {step_id}.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
