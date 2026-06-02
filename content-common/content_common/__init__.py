"""content-common — domain-agnostic shared infrastructure for the lesson content modules.

Consumed by material-generator, anthem-generator, promo-video-generator, and
lesson-package-generator (no module imports another module; they share this).
See MODULE-EXTRACTION-PLAN.md.
"""

from .claude_client import call_claude, use_placeholder, _use_placeholder  # noqa: F401
from .io import write_json, write_text, read_prompt  # noqa: F401

__all__ = [
    "call_claude",
    "use_placeholder",
    "_use_placeholder",
    "write_json",
    "write_text",
    "read_prompt",
]
