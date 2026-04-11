#!/usr/bin/env python3
"""SECONDARY translation verification — Agent Teams TaskCompleted hook.

Reads task output from stdin JSON and checks if the completed task was
a translation task. If so, verifies that the translation pACS score
meets the minimum threshold (>= 50).

This is secondary enforcement (Agent Teams only — inert in Layer 2
subagent mode where the Orchestrator enforces quality gates directly).

Exit codes:
    0 — Pass (not a translation task, or pACS >= 50, or fail-open on error)
    2 — Reject (translation pACS < 50)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Minimum pACS score for translation to pass
PACS_THRESHOLD = 50

# Patterns that identify a translation task in the task subject/description
TRANSLATION_TASK_PATTERNS = [
    r"translat",            # translate, translation, translator
    r"@translator",         # agent reference
    r"\.ko\.md",            # Korean output file
    r"english.to.korean",   # explicit language pair
    r"step-\d+-.*translat", # workflow step with translation
    r"glossary.*update",    # glossary maintenance as part of translation
]


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


def _is_translation_task(payload: dict) -> bool:
    """Determine if the completed task was a translation task.

    Checks task_id, task subject, task description, and task metadata
    against known translation patterns.
    """
    searchable_fields = []

    # Collect all text fields to search
    task_id = payload.get("task_id", "")
    searchable_fields.append(task_id)

    task = payload.get("task", {})
    searchable_fields.append(task.get("subject", ""))
    searchable_fields.append(task.get("description", ""))

    metadata = task.get("metadata", {})
    searchable_fields.append(metadata.get("agent", ""))
    searchable_fields.append(metadata.get("type", ""))
    searchable_fields.append(str(metadata.get("step", "")))

    combined = " ".join(searchable_fields).lower()

    for pattern in TRANSLATION_TASK_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True

    return False


def _extract_pacs_from_payload(payload: dict) -> int | None:
    """Try to extract pACS score directly from task result metadata."""
    result = payload.get("result", {})

    # Check result metadata for pACS
    # NOTE: Use explicit 'is not None' checks — pACS=0 is falsy but valid.
    if isinstance(result, dict):
        for key in ("pacs_score", "pacs", "translation_pacs"):
            pacs = result.get(key)
            if pacs is not None:
                try:
                    return int(pacs)
                except (ValueError, TypeError):
                    continue

    # Check task metadata
    task = payload.get("task", {})
    metadata = task.get("metadata", {})
    for key in ("pacs_score", "pacs"):
        pacs = metadata.get(key)
        if pacs is not None:
            try:
                return int(pacs)
            except (ValueError, TypeError):
                continue

    return None


def _find_latest_pacs_log(project_dir: Path) -> int | None:
    """Search pacs-logs/ for the latest translation pACS score.

    Reads pACS log files and extracts the score from the standard format:
        ## Result: Translation pACS = {score} -> {grade}
    """
    pacs_dir = project_dir / "pacs-logs"
    if not pacs_dir.is_dir():
        return None

    # Find all translation pACS logs, sorted by modification time (newest first)
    log_files = sorted(
        pacs_dir.glob("*translation*pacs*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not log_files:
        # Fallback: check any pacs log file
        log_files = sorted(
            pacs_dir.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    for log_file in log_files:
        try:
            content = log_file.read_text(encoding="utf-8")
            # Match: "Translation pACS = 85" or "pACS = 72"
            match = re.search(
                r"(?:Translation\s+)?pACS\s*=\s*(\d+)",
                content,
                re.IGNORECASE,
            )
            if match:
                return int(match.group(1))
        except OSError:
            continue

    return None


def main() -> None:
    """Entry point — read TaskCompleted JSON, verify translation pACS."""
    project_dir = _resolve_project_dir()

    # ── Parse stdin ──────────────────────────────────────────────────
    payload = _parse_stdin()
    if payload is None:
        # No input or parse failure — allow (fail-open)
        sys.exit(0)

    # ── Check if this is a translation task ──────────────────────────
    if not _is_translation_task(payload):
        # Not a translation task — nothing to verify
        sys.exit(0)

    # ── Extract pACS score ───────────────────────────────────────────
    pacs_score = _extract_pacs_from_payload(payload)

    if pacs_score is None:
        # Try reading from pacs-logs directory
        pacs_score = _find_latest_pacs_log(project_dir)

    if pacs_score is None:
        # Cannot determine pACS — allow (fail-open to avoid blocking pipeline)
        print(
            "TRANSLATION VERIFY: No pACS score found — allowing (fail-open).",
            file=sys.stderr,
        )
        sys.exit(0)

    # ── Evaluate pACS threshold ──────────────────────────────────────
    task_id = payload.get("task_id", "unknown")

    if pacs_score >= 70:
        grade = "GREEN"
    elif pacs_score >= PACS_THRESHOLD:
        grade = "YELLOW"
    else:
        grade = "RED"

    if pacs_score >= PACS_THRESHOLD:
        print(
            f"TRANSLATION VERIFY PASS — Task '{task_id}': "
            f"pACS = {pacs_score} ({grade}).",
            file=sys.stderr,
        )
        sys.exit(0)
    else:
        print(
            f"TRANSLATION VERIFY REJECT — Task '{task_id}': "
            f"pACS = {pacs_score} ({grade}). "
            f"Minimum required: {PACS_THRESHOLD}. "
            f"Re-translate weak sections before proceeding.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
