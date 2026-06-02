"""Shim — the shared Claude client now lives in `content-common`.

Kept as a thin re-export so existing imports (`from scripts.claude_client import
call_claude, _use_placeholder`) keep working during/after the module extraction.
See MODULE-EXTRACTION-PLAN.md (Phase 0).
"""

from content_common.claude_client import (  # noqa: F401
    DEFAULT_MODEL,
    PLACEHOLDER_ENV,
    _use_placeholder,
    call_claude,
    use_placeholder,
)
