# Promo Video Generator (홍보영상)

**테마·대상을 입력하면 30–45초 중등 수련회 홍보영상 기획(`promo-video.v1`)을 생성하는 독립 워크플로우 모듈.**

`lesson-package-generator`에서 추출된 독립 모듈로, 단독 실행도 되고 lesson-package가 import해 재사용한다.

---

## 이 모듈이 하는 일

```
[입력: 테마 · 대상 (본문 선택)]  → 홍보영상 기획 → [내레이션·스토리보드·컷별 AI 프롬프트·자막]
```

| 입력 | 출력 (`promo-video.v1`) |
|------|------|
| 테마 / 강조점 | 내레이션 전체 스크립트 + 세그먼트 |
| 대상 (연령) | 스토리보드 컷(컷별 `video_prompt`·`image_prompt`·자막·내레이션) |
| (선택) 본문, `lesson_plan` | `storyboard.json/md` · `subtitles.srt` · `narration_script.md` · 컷별 프롬프트 MD |
| (선택) 교보재·찬양 downstream | 메시지·톤 정합 강화 |

> 영상 자체는 렌더링하지 않는다. **영상 생성 AI(Runway/Pika/Kling)**로 넘길 컷별 프롬프트를 산출한다. (선택) ffmpeg로 클립을 조립하는 `assemble`도 포함.

---

## 핵심 특징

1. **단독 실행** — 테마·대상만으로 동작. 본문·교보재·찬양·수업안은 **선택**(주입 시 정합 강화).
2. **고정 출력 계약** — `promo-video.v1` (버전 고정). 컷 길이 합 30–45초 보장.
3. **중복 0 재사용** — 도메인 로직은 이 모듈에만. lesson-package는 `content-common` + 이 모듈을 import.
4. **디커플링** — 교보재·찬양 의존을 **데이터 주입**으로만. 다른 모듈 출력 폴더에 의존하지 않음.
5. **컷별 영상/이미지 핸드오프 + SRT** + (선택) ffmpeg `assemble`.

---

## 빠른 시작

### 단독 CLI
```bash
python promo-video-generator/run.py --theme "중등 수련회" --audience "중등부"
# 정합 강화(선택): --teaching-downstream <path> --praise-downstream <path>
# ffmpeg 조립(선택): --assemble
# 출력: promo-video-generator/outputs/promo/
```

### 라이브러리로
```python
from promo_video_generator import run, generate_promo_video_package, assemble
result = run(intake, output_dir, lesson_plan=None, prior={"teaching_downstream": None, "praise_downstream": None})
```

> API 모드: `CONTENT_PLACEHOLDER=0` + `ANTHROPIC_API_KEY`. 없으면 placeholder 모드.

---

## 구조

```
promo-video-generator/
├── promo_video_generator/   import 가능한 패키지 (__init__·contract·generate·render·assemble·module)
├── agents/prompts/promo.md
├── schemas/promo.v1.schema.json
├── tests/test_promo.py
├── run.py                   단독 CLI (--teaching-downstream/--praise-downstream/--assemble 선택)
├── workflow.md · PLAN.md
└── outputs/
```

---

## 의존 / 검증

- **공유**: `content-common`만 import. 다른 도메인 모듈 import 0.
- **검증(P1)**: `validate_promo_video_package` — 컷 ≥4, 길이 합 30–45초, 컷별 `video_prompt`.

---

## 문서 안내

| 문서 | 내용 |
|------|------|
| **이 문서 (`PROMO-VIDEO-README.md`)** | 개요·특징·빠른 시작 |
| **[`PROMO-VIDEO-USER-MANUAL.md`](PROMO-VIDEO-USER-MANUAL.md)** | 단독 사용법·입출력·영상/이미지/ffmpeg 핸드오프·트러블슈팅 |
| **[`PROMO-VIDEO-ARCHITECTURE-AND-PHILOSOPHY.md`](PROMO-VIDEO-ARCHITECTURE-AND-PHILOSOPHY.md)** | 설계 철학·데이터 계약·디커플링·ADR |
| [`MODULE-EXTRACTION-PLAN.md`](MODULE-EXTRACTION-PLAN.md) | 모듈 추출 전체 계획 |
| [`LESSON-PACKAGE-README.md`](LESSON-PACKAGE-README.md) | 이 모듈을 호출하는 상위 패키지 |
