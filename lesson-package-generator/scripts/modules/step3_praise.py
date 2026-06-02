"""Shim — Step 3 (찬양) logic extracted to the standalone `anthem-generator` module.

lesson-package reuses anthem-generator (no duplicated logic). Keeps
`from scripts.modules import step3_praise` + `step3_praise.run(...)` working.
See MODULE-EXTRACTION-PLAN.md (Phase 2).
"""

from anthem_generator import STEP_ID, run  # noqa: F401
