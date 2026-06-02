"""anthem-generator — 찬양 독립 생성 모듈 (praise-worship.v1).

본문·테마·대상만으로 단독 실행. 교보재(downstream dict)는 선택 입력으로 주입받되,
다른 도메인 모듈을 import하지 않는다(데이터 계약만). `content-common`만 공유.
See MODULE-EXTRACTION-PLAN.md.
"""

import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parents[2]
_CC = _REPO_ROOT / "content-common"
if _CC.is_dir() and str(_CC) not in _sys.path:
    _sys.path.insert(0, str(_CC))

from .contract import (  # noqa: E402,F401
    FORMAT_VERSION,
    build_downstream_payload,
    load_teaching_downstream,
    placeholder_package,
    validate_praise_package,
)
from .generate import generate_praise_package  # noqa: E402,F401
from .module import STEP_ID, run  # noqa: E402,F401

# Public aliases (domain-named) for external callers.
generate_anthem_package = generate_praise_package
validate_anthem_package = validate_praise_package

__all__ = [
    "run",
    "generate_anthem_package",
    "generate_praise_package",
    "validate_anthem_package",
    "validate_praise_package",
    "build_downstream_payload",
    "load_teaching_downstream",
    "FORMAT_VERSION",
    "STEP_ID",
]
