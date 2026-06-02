# Promo Video Generator — PLAN (v1)

> 홍보영상 독립 모듈. `lesson-package-generator`의 Step 4 로직을 추출(중복 없음).
> 추출 전략·무중단 원칙: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.

## 목적
30–45초 중등 수련회 홍보영상 기획(`promo-video.v1`)을 테마·대상만으로 단독 생성. lesson-package는 import해 재사용.

## 구조
```
promo-video-generator/
├── promo_video_generator/   (import 가능한 패키지)
│   ├── __init__.py          content-common 부트스트랩 + 재노출(run, generate_promo_video_package, assemble)
│   ├── contract.py          promo-video.v1 계약·검증·placeholder·downstream
│   ├── generate.py          Claude/placeholder 생성 (교보재·찬양 downstream 선택 주입)
│   ├── render.py            storyboard/SRT/narration/cut-prompts
│   ├── assemble.py          ffmpeg 조립(선택)
│   └── module.py            run(intake, output_dir, lesson_plan=None, prior=None, teaching_dir=None, praise_dir=None, assemble=False)
├── agents/prompts/promo.md
├── schemas/promo.v1.schema.json
├── tests/test_promo.py
├── run.py                   단독 CLI (--teaching-downstream/--praise-downstream/--assemble 선택)
└── outputs/
```

## 디커플링 (Phase 3 핵심)
- 기존 `resolve_prior`의 `lesson-package/outputs/{teaching,praise}` 기본경로 의존 제거.
- 교보재·찬양 컨텍스트는 호출자가 downstream dict(또는 명시 dir)로 주입. 없으면 단독 동작.
- material/anthem를 코드로 import하지 않음(데이터 계약만).

## 검증
- 모듈 P1: `validate_promo_video_package`.
- 통합: lesson-package 오케스트레이터가 `step4_promo` shim → `promo_video_generator.run` 호출, 교보재·찬양 downstream을 prior로 주입.

## 상태
- v1: Step 4 추출 + 상위 모듈 경로 의존 제거 + assemble 포함(Phase 3). lesson-package는 `scripts/modules/step4_promo.py` + `scripts/promo_contract.py` + `scripts/assemble_promo_video.py` shim으로 호출.
