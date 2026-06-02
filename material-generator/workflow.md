# Material Generator — Workflow (교보재)

독립 워크플로우. 본문·테마·대상만으로 중등부 교보재(`teaching-materials.v1`)를 생성한다.
`lesson_plan`은 선택(있으면 핵심메시지 정합 강화).

## Overview
- **산출물**: `teaching-materials.v1` (도입게임·토의·활동·워크시트·슬라이드) + worksheet HTML/PDF + slides HTML + 컴포넌트 MD + 이미지 프롬프트(`[IMG: …]`)
- **단독 실행**: `python material-generator/run.py --body "..." --theme "..." --audience "중등부"`
- **재사용**: `from material_generator import run, generate_material_package`

## Pipeline (R → P → I)
```
Research      intake(본문·테마·대상) 정규화
Planning      lesson_plan(선택) 정합 규칙 결정
Implementation generate → validate(teaching-materials.v1) → render(HTML/PDF/slides/components)
```

## 입력 / 출력 계약
- 입력: `{ body_text, theme, audience, volume?, emphasis? }` (+ optional `lesson_plan`)
- 출력: `teaching-materials.v1` — downstream(`key_message`, `discussion_questions`, `image_prompts`)을 찬양·홍보영상이 소비

## 검증 (P1)
- `validate_material_package` (= `teaching-materials.v1` 계약): 4종 컴포넌트·슬라이드·본문 존재

## Inherited DNA
부모 `AGENTS.md` 절대 기준 + `content-common` 공유 인프라. 다른 도메인 모듈을 import하지 않음(데이터 계약만).
상세: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.
