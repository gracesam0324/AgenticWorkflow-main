# Material Generator (교보재)

**본문·테마·대상을 입력하면 중등부 교보재(`teaching-materials.v1`)를 생성하는 독립 워크플로우 모듈.**

`lesson-package-generator`에서 추출된 독립 모듈로, 단독 실행도 되고 lesson-package가 import해 재사용한다.

---

## 이 모듈이 하는 일

```
[입력: 본문 · 테마 · 대상]  → 교보재 생성 → [도입게임·토의·활동·워크시트·슬라이드 + 이미지 프롬프트]
```

| 입력 | 출력 (`teaching-materials.v1`) |
|------|------|
| 본문(성경 본문/요약) | 도입게임 · 토의 · 활동 · 워크시트 · 슬라이드 |
| 테마 / 강조점 | worksheet HTML/PDF · slides HTML · 컴포넌트 MD |
| 대상 (연령·인원) | `[IMG: …]` 이미지 생성 프롬프트 |
| (선택) `lesson_plan` | downstream(`key_message`·`discussion_questions`) → 찬양·홍보 모듈이 소비 |

---

## 핵심 특징

1. **단독 실행** — 본문·테마·대상만으로 동작(`lesson_plan` 불필요). 있으면 수업안 핵심메시지에 정합.
2. **고정 출력 계약** — `teaching-materials.v1` (버전 고정). 하위 모듈이 안정적으로 소비.
3. **중복 0 재사용** — 도메인 로직은 이 모듈에만. lesson-package는 `content-common` + 이 모듈을 import.
4. **이미지 핸드오프** — `[IMG: …]` 슬롯을 모아 이미지 생성 AI로 넘김(P3 리소스 정확성).
5. **결정론적 placeholder** — API 키 없이도 구조 데모 산출(오프라인/CI).

---

## 빠른 시작

### 단독 CLI
```bash
python material-generator/run.py --body "요한복음 3:16" --theme "하나님의 사랑" --audience "중등부 20명"
# 출력: material-generator/outputs/teaching/
```

### 라이브러리로
```python
from material_generator import run, generate_material_package
result = run(intake, output_dir, lesson_plan=None)   # 전체 산출물 + 파일
pkg = generate_material_package(intake, lesson_plan)  # teaching-materials.v1 dict
```

> API 모드: `CONTENT_PLACEHOLDER=0` + `ANTHROPIC_API_KEY`. 없으면 placeholder 모드.

---

## 구조

```
material-generator/
├── material_generator/      import 가능한 패키지 (__init__·contract·generate·render·module)
├── agents/prompts/material.md
├── schemas/material.v1.schema.json
├── tests/test_material.py
├── run.py                   단독 CLI
├── workflow.md · PLAN.md
└── outputs/
```

---

## 의존 / 검증

- **공유**: `content-common`만 import (call_claude·io·read_prompt). 다른 도메인 모듈 import 0.
- **검증(P1)**: `validate_material_package` — 4종 컴포넌트·슬라이드·본문 존재.

---

## 문서 안내

| 문서 | 내용 |
|------|------|
| **이 문서 (`MATERIAL-README.md`)** | 개요·특징·빠른 시작 |
| **[`MATERIAL-USER-MANUAL.md`](MATERIAL-USER-MANUAL.md)** | 단독 사용법·입출력·이미지 핸드오프·트러블슈팅 |
| **[`MATERIAL-ARCHITECTURE-AND-PHILOSOPHY.md`](MATERIAL-ARCHITECTURE-AND-PHILOSOPHY.md)** | 설계 철학·데이터 계약·디커플링·ADR |
| [`MODULE-EXTRACTION-PLAN.md`](MODULE-EXTRACTION-PLAN.md) | 모듈 추출 전체 계획 |
| [`LESSON-PACKAGE-README.md`](LESSON-PACKAGE-README.md) | 이 모듈을 호출하는 상위 패키지 |
