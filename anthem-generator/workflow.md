# Anthem Generator — Workflow (찬양)

독립 워크플로우. 본문·테마·대상으로 중등부 오리지널 찬양(`praise-worship.v1`) + Suno 음악 프롬프트를 생성한다.
교보재 downstream과 `lesson_plan`은 **선택**(있으면 핵심메시지 정합 강화). 다른 모듈을 import하지 않음.

## Overview
- **산출물**: `praise-worship.v1` (오리지널 가사 verse/chorus/bridge + Suno `prompt_combined`) + `lyrics/full_lyrics.md` + `music/suno_prompt.txt` + 인도자 노트
- **단독 실행**: `python anthem-generator/run.py --body "..." --theme "..." --audience "중등부"`
- **재사용**: `from anthem_generator import run, generate_anthem_package`

## Pipeline (R → P → I)
```
Research      intake(본문·테마·대상) 정규화
Planning      lesson_plan / 교보재 downstream(선택) 정합 규칙
Implementation generate → validate(praise-worship.v1) → render(lyrics/Suno prompt)
```

## 입력 / 출력 계약
- 입력: `{ body_text, theme, audience }` (+ optional `lesson_plan`, `teaching_downstream` dict)
- 출력: `praise-worship.v1` — downstream(`suno_prompt`, `song_title`, `key_message`)을 홍보영상이 소비

## 외부 AI 핸드오프
- Suno(custom): `music/suno_prompt.txt` + `lyrics/full_lyrics.md` → 음원 생성. 음원은 직접 렌더링하지 않음(delivery: external).

## 검증 (P1)
- `validate_anthem_package`: 가사 4부(verse1·chorus·verse2·bridge) + `music_generation.prompt_combined`/bpm

## 디커플링
교보재 의존은 **데이터 주입**(`teaching_downstream` dict)으로만. 다른 모듈의 출력 디렉터리에 의존하지 않음.
상세: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.
