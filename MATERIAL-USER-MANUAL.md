# Material Generator 사용자 매뉴얼 (교보재)

> 교보재를 **단독으로** 생성하는 모듈 사용법. (수업안과 함께 쓰려면 `LESSON-PACKAGE-USER-MANUAL.md`의 웹앱을 사용하세요.)

---

## 1. 가장 쉬운 사용법

```bash
python material-generator/run.py \
  --body "요한복음 3:16" \
  --theme "하나님의 사랑" \
  --audience "중등부 20명"
```
끝나면 `material-generator/outputs/teaching/` 에 결과가 생깁니다.

| 옵션 | 필수 | 설명 | 기본 |
|------|------|------|------|
| `--body` | 예 | 본문(성경 구절/요약) | — |
| `--theme` | 예 | 테마/강조점 | — |
| `--audience` | 아니오 | 대상 | 중등부 |
| `--volume` | 아니오 | 분량(분) | 45 |
| `--output-dir` | 아니오 | 출력 폴더 | `material-generator/outputs` |

---

## 2. API 키 (실제 콘텐츠 생성)

기본은 **placeholder 모드**(구조 데모용 결정론적 산출). 실제 본문 맞춤 콘텐츠는 Claude API가 필요합니다.

```bash
# Windows PowerShell
$env:CONTENT_PLACEHOLDER="0"; $env:ANTHROPIC_API_KEY="sk-ant-..."
python material-generator/run.py --body "..." --theme "..." --audience "중등부"
```
(레거시 키 `LESSON_PACKAGE_PLACEHOLDER`도 호환됩니다.)

---

## 3. 출력물

`outputs/teaching/` 아래:

| 파일 | 내용 |
|------|------|
| `teaching_materials.v1.json` | 정규 계약(JSON) — 모든 컴포넌트 |
| `print/worksheet.html`, `print/worksheet.pdf` | 인쇄용 학생 워크시트 |
| `slides/slides.html` | 수업 슬라이드 |
| `components/{intro_game,discussion,activity,worksheet}.md` | 편집용 컴포넌트 MD |
| `teaching_materials.downstream.json` | 찬양·홍보가 소비할 요약(핵심메시지·토의질문·이미지 프롬프트) |

---

## 4. 이미지 핸드오프 (삽화)

산출물 곳곳의 `[IMG: 설명]` 표시는 **이미지 생성 AI에 넣을 프롬프트**입니다.
1. `teaching_materials.downstream.json`의 `image_prompts` 또는 워크시트/슬라이드의 `[IMG: …]`를 복사
2. 이미지 생성 AI에 붙여넣어 삽화 생성
3. 워크시트/슬라이드에 배치

> 음원·영상은 이 모듈의 범위가 아닙니다(찬양=anthem, 홍보영상=promo-video 모듈).

---

## 5. 수업안과 함께 쓰기 (선택)

수업안(`lesson_plan`)을 주면 교보재의 핵심메시지가 수업안과 정합됩니다.
```python
from material_generator import run
run(intake, output_dir, lesson_plan=plan)   # plan.sections.key_message 반영
```
lesson-package-generator 오케스트레이터는 이 호출을 자동으로 수행합니다(웹앱 포함).

---

## 6. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `ModuleNotFoundError: content_common` | 저장소 루트의 `content-common/`이 있는지 확인. `run.py`는 자동으로 경로를 잡습니다 |
| PDF가 안 생김 | `xhtml2pdf` 미설치 — HTML은 정상 생성됨(`pip install xhtml2pdf`로 PDF 활성화) |
| 결과가 본문과 동떨어짐 | placeholder 모드입니다. API 키 설정(§2) 후 재실행 |

---

## 부록: 관련 문서
- [`MATERIAL-README.md`](MATERIAL-README.md) · [`MATERIAL-ARCHITECTURE-AND-PHILOSOPHY.md`](MATERIAL-ARCHITECTURE-AND-PHILOSOPHY.md)
- [`material-generator/workflow.md`](material-generator/workflow.md) · [`material-generator/PLAN.md`](material-generator/PLAN.md)
