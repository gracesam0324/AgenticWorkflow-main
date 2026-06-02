#!/usr/bin/env python3
"""Shared, domain-agnostic Claude API entry point for the content modules.

Placeholder mode (offline/CI) is controlled by ``CONTENT_PLACEHOLDER``, with a
backward-compatible fallback to ``LESSON_PACKAGE_PLACEHOLDER`` (D-3). Domain
modules short-circuit to their own deterministic placeholder *before* calling
this, so the stub returned here in placeholder mode is a defensive fallback only.
"""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_MODEL = (
    os.environ.get("CONTENT_MODEL")
    or os.environ.get("LESSON_PACKAGE_MODEL")
    or "claude-sonnet-4-20250514"
)
PLACEHOLDER_ENV = "CONTENT_PLACEHOLDER"
LEGACY_PLACEHOLDER_ENV = "LESSON_PACKAGE_PLACEHOLDER"


def use_placeholder() -> bool:
    """True when generation should use deterministic placeholders (no API call)."""
    raw = os.environ.get(PLACEHOLDER_ENV)
    if raw is None:
        raw = os.environ.get(LEGACY_PLACEHOLDER_ENV, "1")
    if raw.strip().lower() in ("0", "false", "no"):
        if os.environ.get("ANTHROPIC_API_KEY"):
            return False
    return True


# Backward-compatible alias used across the existing codebase.
_use_placeholder = use_placeholder


def call_claude(
    *,
    step_id: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    max_tokens: int = 4096,
) -> str:
    """Call Claude once and return the assistant text (or a stub in placeholder mode)."""
    if use_placeholder():
        return _generic_placeholder(step_id)

    try:
        import anthropic
    except ImportError as exc:
        msg = "anthropic package required when CONTENT_PLACEHOLDER=0"
        raise RuntimeError(msg) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _generic_placeholder(step_id)

    client = anthropic.Anthropic(api_key=api_key)
    user_message = json.dumps(user_payload, ensure_ascii=False, indent=2)
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _generic_placeholder(step_id: str) -> str:
    return (
        f"[PLACEHOLDER {step_id}] content-common stub. "
        "Domain modules generate deterministic placeholders directly."
    )
