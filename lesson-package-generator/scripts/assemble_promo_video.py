"""Shim — ffmpeg assembler moved to `promo-video-generator`.

Re-export keeps `from scripts.assemble_promo_video import assemble` working
(tests, step4 lazy import via the module). See MODULE-EXTRACTION-PLAN.md (Phase 3).
"""

from promo_video_generator.assemble import assemble, main  # noqa: F401


if __name__ == "__main__":
    raise SystemExit(main())
