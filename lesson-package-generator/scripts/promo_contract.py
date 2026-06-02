"""Shim — promo-video.v1 contract moved to `promo-video-generator`.

Re-export keeps `from scripts.promo_contract import FORMAT_VERSION,
validate_promo_package` working (tests). See MODULE-EXTRACTION-PLAN.md (Phase 3).
"""

from promo_video_generator.contract import (  # noqa: F401
    DURATION_MAX,
    DURATION_MIN,
    FORMAT_VERSION,
    build_downstream_payload,
    load_downstream,
    placeholder_package,
    validate_promo_package,
)
