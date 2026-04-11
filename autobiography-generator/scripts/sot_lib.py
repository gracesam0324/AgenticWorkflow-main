"""SOT (Single Source of Truth) library — atomic read/write for .claude/state.yaml.

This module is the ONLY authorized write path for the SOT file.
All writers (Orchestrator, hooks, FallbackController) use these functions.
File locking via fcntl.flock() serializes concurrent writes.

Usage:
    from scripts.sot_lib import load_state, save_state, update_state_yaml
"""

from __future__ import annotations

import fcntl
import os
import shutil
from pathlib import Path
from typing import Any

import yaml


def _sot_path() -> Path:
    """Return the path to the SOT file."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    return Path(project_dir) / ".claude" / "state.yaml"


def _sot_bak_path() -> Path:
    """Return the path to the SOT backup file."""
    return Path(str(_sot_path()) + ".bak")


def _sot_lock_path() -> Path:
    """Return the path to the SOT lock file."""
    return Path(str(_sot_path()) + ".lock")


def save_state(state: dict[str, Any], sot_path: Path | None = None) -> None:
    """Atomic write to SOT with crash recovery. Single-writer enforced by file lock.

    Args:
        state: The full state dictionary to write.
        sot_path: Optional override for the SOT file path (for testing).
    """
    path = sot_path or _sot_path()
    bak_path = Path(str(path) + ".bak")
    lock_path = Path(str(path) + ".lock")
    tmp_path = Path(str(path) + ".tmp")

    path.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = open(lock_path, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        # Create .bak for crash recovery
        if path.exists():
            shutil.copy2(path, bak_path)

        # Write to temp file (NOT directly to SOT)
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Atomic rename (os.replace is atomic on POSIX)
        os.replace(tmp_path, path)

        # Verify write succeeded
        with open(path, "r", encoding="utf-8") as f:
            verify = yaml.safe_load(f)
        if verify is None:
            msg = "SOT write verification failed — file is empty after write"
            raise RuntimeError(msg)

    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


def load_state(sot_path: Path | None = None) -> dict[str, Any]:
    """Read SOT. If corrupted, recover from .bak.

    Args:
        sot_path: Optional override for the SOT file path (for testing).

    Returns:
        The parsed state dictionary.
    """
    path = sot_path or _sot_path()
    bak_path = Path(str(path) + ".bak")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                raise yaml.YAMLError("Empty file")
            return data
    except (yaml.YAMLError, FileNotFoundError, OSError):
        if bak_path.exists():
            with open(bak_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is not None:
                    return data
        raise


def merge_orchestration_section(
    section_key: str,
    updates: dict[str, Any],
    sot_path: Path | None = None,
) -> None:
    """Atomically merge updates into ONE orchestration subsection.

    Holds the file lock for the entire load→merge→save cycle,
    preventing the logical race where two writers each load stale state
    and the last writer overwrites the other's changes.

    Args:
        section_key: Orchestration subsection (e.g., "rlm", "fallback").
        updates: Dictionary of key-value pairs to merge into the subsection.
        sot_path: Optional override for the SOT file path (for testing).
    """
    path = sot_path or _sot_path()
    lock_path = Path(str(path) + ".lock")
    bak_path = Path(str(path) + ".bak")
    tmp_path = Path(str(path) + ".tmp")

    path.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = open(lock_path, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        # Load while holding lock
        state: dict[str, Any] = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded and isinstance(loaded, dict):
                    state = loaded

        # Merge into orchestration subsection
        orch = state.setdefault("orchestration", {})
        section = orch.setdefault(section_key, {})
        if isinstance(section, dict):
            section.update(updates)
        else:
            orch[section_key] = updates

        # Backup + atomic write
        if path.exists():
            shutil.copy2(path, bak_path)
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        os.replace(tmp_path, path)

    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


def update_state_yaml(
    key: str,
    sot_path: Path | None = None,
    **kwargs: Any,
) -> None:
    """High-level SOT update — loads, modifies, saves atomically.

    Args:
        key: Dot-separated path under 'workflow' (e.g., "chapters.ch-01").
             Use "orchestration.xxx" to write to orchestration section directly.
        sot_path: Optional override for the SOT file path (for testing).
        **kwargs: Key-value pairs to update at the target path.
    """
    state = load_state(sot_path)

    # Determine root: orchestration keys go directly, others under workflow
    if key.startswith("orchestration"):
        full_key = key
    elif key == "workflow":
        full_key = "workflow"
    else:
        full_key = f"workflow.{key}"

    # Navigate to nested key
    target = state
    parts = full_key.split(".")
    for part in parts:
        if part not in target:
            target[part] = {}
        if isinstance(target[part], dict):
            parent = target
            target = target[part]
        else:
            # Leaf value — update the parent
            parent = target
            parent[part] = kwargs if len(kwargs) > 1 else next(iter(kwargs.values()))
            save_state(state, sot_path)
            return

    target.update(kwargs)
    save_state(state, sot_path)
