"""Shim — Step 4 (홍보영상) logic extracted to the standalone `promo-video-generator` module.

lesson-package reuses promo-video-generator (no duplicated logic). Keeps
`from scripts.modules import step4_promo` + `step4_promo.run(...)` working.
See MODULE-EXTRACTION-PLAN.md (Phase 3).
"""

from promo_video_generator import STEP_ID, run  # noqa: F401
