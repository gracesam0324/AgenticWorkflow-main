# Anthem Generator (찬양)

**본문·테마·대상을 입력하면 중등부 오리지널 찬양(`praise-worship.v1`)과 Suno 음악 프롬프트를 생성하는 독립 워크플로우 모듈.**

`lesson-package-generator`에서 추출된 독립 모듈로, 단독 실행도 되고 lesson-package가 import해 재사용한다.

---

## 이 모듈이 하는 일

```
[입력: 본문 · 테마 · 대상]  → 찬양 생성 → [오리지널 가사 + Suno 음악 프롬프트 + 인도자 노트]
```

| 입력 | 출력 (`praise-worship.v1`) |
|------|------|
| 본문(성경 본문/요약) | 오리지널 가사 (1절·후렴·2절·브릿지) |
| 테마 / 강조점 | Suno용 `prompt_combined` + 구조화 프롬프트(genre·mood·bpm…) |
| 대상 (연령) | `lyrics/full_lyrics.md` · `music/suno_prompt.txt` · 인도자 노트 |
| (선택) `lesson_plan`, 교보재 downstream | 핵심메시지 정합 강화 |

> 음원 자체는 만들지 않는다(`delivery: external`). **Suno 등 외부 음악 AI**로 넘길 프롬프트를 산출한다.

---

## 핵심 특징

1. **단독 실행** — 본문·테마·대상만으로 동작. 교보재·수업안은 **선택**(주입 시 정합 강화).
2. **고정 출력 계약** — `praise-worship.v1` (버전 고정). 홍보영상 모듈이 downstream을 소비.
3. **중복 0 재사용** — 도메인 로직은 이 모듈에만. lesson-package는 `content-common` + 이 모듈을 import.
4. **디커플링** — 교보재 의존을 **데이터 주입**(downstream dict)으로만. 다른 모듈의 출력 폴더에 의존하지 않음.
5. **오리지널 가사** — 기존 찬송 복제 금지. CCLI 등록 전 외부 배포 금지 고지 포함.

---

## 빠른 시작

### 단독 CLI
```bash
python anthem-generator/run.py --body "요한복음 3:16" --theme "하나님의 사랑" --audience "중등부"
# 정합 강화(선택): --teaching-downstream <path>/teaching_materials.downstream.json
# 출력: anthem-generator/outputs/praise/
```

### 라이브러리로
```python
from anthem_generator import run, generate_anthem_package
result = run(intake, output_dir, lesson_plan=None, prior={"teaching_downstream": None})
pkg = generate_anthem_package(intake, teaching=None, lesson_plan=plan)
```

> API 모드: `CONTENT_PLACEHOLDER=0` + `ANTHROPIC_API_KEY`. 없으면 placeholder 모드.

---

## 구조

```
anthem-generator/
├── anthem_generator/        import 가능한 패키지 (__init__·contract·generate·render·module)
├── agents/prompts/anthem.md
├── schemas/anthem.v1.schema.json
├── tests/test_anthem.py
├── run.py                   단독 CLI (--teaching-downstream 선택)
├── workflow.md · PLAN.md
└── outputs/
```

---

## 의존 / 검증

- **공유**: `content-common`만 import. 다른 도메인 모듈 import 0.
- **검증(P1)**: `validate_anthem_package` — 가사 4부(verse1·chorus·verse2·bridge) + `music_generation.prompt_combined`/bpm.

---

## 문서 안내

| 문서 | 내용 |
|------|------|
| **이 문서 (`ANTHEM-README.md`)** | 개요·특징·빠른 시작 |
| **[`ANTHEM-USER-MANUAL.md`](ANTHEM-USER-MANUAL.md)** | 단독 사용법·입출력·Suno 핸드오프·트러블슈팅 |
| **[`ANTHEM-ARCHITECTURE-AND-PHILOSOPHY.md`](ANTHEM-ARCHITECTURE-AND-PHILOSOPHY.md)** | 설계 철학·데이터 계약·디커플링·ADR |
| [`MODULE-EXTRACTION-PLAN.md`](MODULE-EXTRACTION-PLAN.md) | 모듈 추출 전체 계획 |
| [`LESSON-PACKAGE-README.md`](LESSON-PACKAGE-README.md) | 이 모듈을 호출하는 상위 패키지 |
