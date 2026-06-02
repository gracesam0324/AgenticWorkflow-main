# Anthem Generator — PLAN (v1)

> 찬양 독립 모듈. `lesson-package-generator`의 Step 3 로직을 추출(중복 없음).
> 추출 전략·무중단 원칙: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.

## 목적
중등부 오리지널 찬양(`praise-worship.v1`) + Suno 프롬프트를 본문·테마·대상만으로 단독 생성. lesson-package는 import해 재사용.

## 구조
```
anthem-generator/
├── anthem_generator/        (import 가능한 패키지)
│   ├── __init__.py          content-common 부트스트랩 + 재노출(run, generate_anthem_package)
│   ├── contract.py          praise-worship.v1 계약·검증·placeholder·downstream
│   ├── generate.py          Claude/placeholder 생성 (교보재 downstream 선택 주입)
│   ├── render.py            가사 MD·Suno 프롬프트 파일
│   └── module.py            run(intake, output_dir, lesson_plan=None, prior=None, teaching_dir=None)
├── agents/prompts/anthem.md
├── schemas/anthem.v1.schema.json
├── tests/test_anthem.py
├── run.py                   단독 CLI (--teaching-downstream 선택)
└── outputs/
```

## 디커플링 (Phase 2 핵심)
- 기존 `resolve_teaching`의 `lesson-package/outputs/teaching` 기본경로 의존 제거.
- 교보재 컨텍스트는 호출자가 `teaching_downstream` dict(또는 명시 `teaching_dir`)로 주입. 없으면 단독 동작.
- material-generator를 코드로 import하지 않음(데이터 계약만).

## 검증
- 모듈 P1: `validate_anthem_package`.
- 통합: lesson-package 오케스트레이터가 `step3_praise` shim → `anthem_generator.run` 호출, 교보재 downstream을 prior로 주입.

## 상태
- v1: Step 3 추출 + 교보재 경로 의존 제거 완료(Phase 2). lesson-package는 `scripts/modules/step3_praise.py` + `scripts/praise_contract.py` shim으로 호출.
