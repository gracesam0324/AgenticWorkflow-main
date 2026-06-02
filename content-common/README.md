# content-common

도메인 무관 공유 인프라 패키지. 콘텐츠 생성 모듈들이 **중복 없이** 공유한다.

- 소비자: `material-generator`, `anthem-generator`, `promo-video-generator`, `lesson-package-generator`
- 의존 방향: 이 패키지는 누구에게도 의존하지 않는다(말단). 모듈은 서로 import하지 않고 이 패키지만 공유한다.

## 제공 API (`content_common`)

| 심볼 | 역할 |
|------|------|
| `call_claude(*, step_id, system_prompt, user_payload, max_tokens)` | Claude API 단일 호출 (placeholder 모드 지원) |
| `use_placeholder()` / `_use_placeholder` | placeholder 모드 여부 (`CONTENT_PLACEHOLDER`, 레거시 `LESSON_PACKAGE_PLACEHOLDER` 호환) |
| `write_json(path, data)` / `write_text(path, text)` | UTF-8 산출물 쓰기 |
| `read_prompt(path)` | 프롬프트 파일 로드 |

## import 방식 (D-2: sys.path 부트스트랩)

각 소비 프로젝트의 패키지 `__init__`(예: `lesson-package-generator/scripts/__init__.py`)이
저장소 루트의 `content-common/`을 `sys.path`에 추가한다. 그 후 `import content_common`이 동작한다.
정석(후속 업그레이드): `pip install -e content-common`.

상세: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.
