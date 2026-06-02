"""Shim — Step 2 (교보재) logic extracted to the standalone `material-generator` module.

lesson-package now reuses material-generator (no duplicated logic). This thin
re-export keeps `from scripts.modules import step2_teaching` + `step2_teaching.run(...)`
working for the orchestrator and tests. See MODULE-EXTRACTION-PLAN.md (Phase 1).
"""

from material_generator import STEP_ID, run  # noqa: F401
