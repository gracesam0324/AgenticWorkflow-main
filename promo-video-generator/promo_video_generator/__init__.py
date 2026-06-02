"""promo-video-generator — 홍보영상 독립 생성 모듈 (promo-video.v1).

테마·대상만으로 단독 실행. 교보재·찬양 downstream은 선택 입력으로 주입받되,
다른 도메인 모듈을 import하지 않는다(데이터 계약만). `content-common`만 공유.
ffmpeg 조립(`assemble`)도 이 패키지에 포함. See MODULE-EXTRACTION-PLAN.md.
"""

import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parents[2]
_CC = _REPO_ROOT / "content-common"
if _CC.is_dir() and str(_CC) not in _sys.path:
    _sys.path.insert(0, str(_CC))

from .assemble import assemble  # noqa: E402,F401
from .contract import (  # noqa: E402,F401
    FORMAT_VERSION,
    build_downstream_payload,
    load_downstream,
    placeholder_package,
    validate_promo_package,
)
from .generate import generate_promo_package  # noqa: E402,F401
from .module import STEP_ID, run  # noqa: E402,F401

# Public aliases (domain-named) for external callers.
generate_promo_video_package = generate_promo_package
validate_promo_video_package = validate_promo_package

__all__ = [
    "run",
    "assemble",
    "generate_promo_video_package",
    "generate_promo_package",
    "validate_promo_video_package",
    "validate_promo_package",
    "build_downstream_payload",
    "load_downstream",
    "FORMAT_VERSION",
    "STEP_ID",
]
