"""Lesson Package Generator — pipeline scripts.

Bootstrap (D-2): make the shared `content-common` package importable by adding
the repo-root sibling directory to sys.path. Importing any `scripts.*` module
runs this first, so `import content_common` resolves in every execution context
(orchestrator, standalone runners, pytest). See MODULE-EXTRACTION-PLAN.md.
"""

import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parents[2]
for _sibling in (
    "content-common",
    "material-generator",
    "anthem-generator",
    "promo-video-generator",
):
    _p = _REPO_ROOT / _sibling
    if _p.is_dir() and str(_p) not in _sys.path:
        _sys.path.insert(0, str(_p))
