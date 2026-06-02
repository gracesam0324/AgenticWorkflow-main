"""Shared helper for pipeline step modules — prompt directory resolution.

(`run_step` was removed in module-extraction Phase 4: Step 1 uses
`lesson_plan_generate` and Step 5 uses `package_check` directly, so the old
single-call stub helper had no callers.)
"""

from __future__ import annotations

from pathlib import Path

from scripts.io_helpers import project_root_from_script


def prompts_dir() -> Path:
    return project_root_from_script() / "agents" / "prompts"
