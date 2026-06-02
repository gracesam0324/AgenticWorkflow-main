# Material Generator — PLAN (v1)

> 교보재 독립 모듈. `lesson-package-generator`의 Step 2 로직을 추출(중복 없음).
> 추출 전략·무중단 원칙: 저장소 루트 `MODULE-EXTRACTION-PLAN.md`.

## 목적
중등부 교보재(`teaching-materials.v1`)를 본문·테마·대상만으로 단독 생성. lesson-package는 이 모듈을 import해 재사용.

## 구조
```
material-generator/
├── material_generator/      (import 가능한 패키지)
│   ├── __init__.py          content-common 부트스트랩 + 재노출(run, generate_material_package)
│   ├── contract.py          teaching-materials.v1 계약·검증·placeholder·downstream
│   ├── generate.py          Claude/placeholder 생성
│   ├── render.py            HTML/PDF/slides/components
│   └── module.py            run(intake, output_dir, lesson_plan=None)
├── agents/prompts/material.md
├── schemas/material.v1.schema.json
├── tests/test_material.py
├── run.py                   단독 CLI
└── outputs/
```

## 의존
- `content-common`만 공유(call_claude·io·read_prompt). 다른 모듈 import 금지.
- 출력 계약 `teaching-materials.v1` 유지(찬양·홍보 downstream 호환).

## 검증
- 모듈 P1: `validate_material_package`.
- 통합: lesson-package 오케스트레이터가 `step2_teaching` shim → `material_generator.run` 호출, 전체 파이프라인 그린.

## 상태
- v1: Step 2 추출 완료(Phase 1). lesson-package는 `scripts/modules/step2_teaching.py` shim으로 호출.
