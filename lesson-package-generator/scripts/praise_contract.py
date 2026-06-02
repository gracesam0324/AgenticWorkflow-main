"""Shim — praise-worship.v1 contract moved to `anthem-generator`.

Re-export keeps `from scripts.praise_contract import FORMAT_VERSION,
validate_praise_package` working (tests). See MODULE-EXTRACTION-PLAN.md (Phase 2).
"""

from anthem_generator.contract import (  # noqa: F401
    AUDIO_PROVIDER,
    FORMAT_VERSION,
    build_downstream_payload,
    load_teaching_downstream,
    placeholder_package,
    validate_praise_package,
)
