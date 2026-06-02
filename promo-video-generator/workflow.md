# Promo Video Generator — Workflow (홍보영상)

독립 워크플로우. 테마·대상으로 30–45초 중등 수련회 홍보영상 기획(`promo-video.v1`)을 생성한다.
교보재·찬양 downstream과 `lesson_plan`은 **선택**(있으면 메시지·톤 정합). 다른 모듈을 import하지 않음.

## Overview
- **산출물**: `promo-video.v1` (내레이션·스토리보드·컷별 영상/이미지 프롬프트) + `storyboard.json/md` + `subtitles.srt` + `narration_script.md` + 컷별 프롬프트 MD
- **단독 실행**: `python promo-video-generator/run.py --theme "중등 수련회" --audience "중등부"`
- **재사용**: `from promo_video_generator import run, generate_promo_video_package`

## Pipeline (R → P → I)
```
Research      intake(테마·대상[·본문]) 정규화
Planning      교보재·찬양 downstream / lesson_plan(선택) 정합 규칙
Implementation generate → validate(promo-video.v1) → render(storyboard/SRT/cut prompts)
              → (선택) assemble: ffmpeg 조립
```

## 입력 / 출력 계약
- 입력: `{ theme, audience, body_text? }` (+ optional `lesson_plan`, `teaching_downstream`, `praise_downstream` dict)
- 출력: `promo-video.v1` — 컷 길이 합 30–45초, 컷마다 `video_prompt`(+`image_prompt`)

## 외부 AI 핸드오프
- 컷별 `video_prompt` → Runway/Pika/Kling 등 영상 생성 AI / `image_prompt` → 이미지 AI / `subtitles.srt` 자막
- ffmpeg 조립: `assemble(promo_dir, music_path=None)` (assets/cut_XX.* 배치 후). 음원은 찬양 모듈 산출물을 주입.

## 검증 (P1)
- `validate_promo_video_package`: 컷 ≥4, 길이 합 30–45초, 컷별 `video_prompt`

## 디커플링
교보재·찬양 의존은 **데이터 주입**(downstream dict / 명시 dir)으로만. 다른 모듈의 출력 디렉터리 기본경로에 의존하지 않음.
상세: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.
