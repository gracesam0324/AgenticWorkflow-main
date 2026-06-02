"""material-generator — 교보재 독립 생성 모듈 (teaching-materials.v1).

단독 실행(본문·테마·대상) 가능하며, lesson-package-generator가 import해서 재사용한다.
이 패키지는 `content-common`만 공유하고 다른 도메인 모듈을 import하지 않는다.
See MODULE-EXTRACTION-PLAN.md.
"""

import sys as _sys
from pathlib import Path as _Path

# Bootstrap (D-2): make the shared `content-common` package importable.
_REPO_ROOT = _Path(__file__).resolve().parents[2]
_CC = _REPO_ROOT / "content-common"
if _CC.is_dir() and str(_CC) not in _sys.path:
    _sys.path.insert(0, str(_CC))

from .contract import (  # noqa: E402,F401
    FORMAT_VERSION,
    build_downstream_payload,
    extract_image_prompts,
    placeholder_package,
    validate_teaching_package,
)
from .generate import generate_teaching_package  # noqa: E402,F401
from .module import STEP_ID, run  # noqa: E402,F401

# Public aliases (domain-named) for external callers.
generate_material_package = generate_teaching_package
validate_material_package = validate_teaching_package

__all__ = [
    "run",
    "generate_material_package",
    "generate_teaching_package",
    "validate_material_package",
    "validate_teaching_package",
    "build_downstream_payload",
    "FORMAT_VERSION",
    "STEP_ID",
]
