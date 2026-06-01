# Lesson Package Generator — Workflow (skeleton v0.2)

## Overview

- **Main**: Step 1 수업안 설계 (`outputs/lesson_plan/`)
- **Supplementary** (optional): Steps 2–4 — require `lesson_plan.json`
- **Integration**: Step 5 self-check

## Pipeline

```
intake → [human: intake] → step1 lesson_plan → [human: approve plan]
  → (optional) step2 teaching, step3 praise, step4 promo
  → step5 manifest
```

## CLI

```bash
# 교보재만 (본문·테마·대상) — HTML/PDF 워크시트 + 슬라이드
python scripts/run_teaching_materials.py --body "..." --theme "..." --audience "중등부"
python scripts/run_praise_worship.py --body "..." --theme "..." --teaching-dir outputs/teaching
python scripts/run_promo_video.py --theme "중등 수련회" --assemble
python scripts/assemble_promo_video.py --promo-dir outputs/promo

python scripts/orchestrator.py --body "..." --audience "..." --volume 90 --theme "..."
python scripts/orchestrator.py ... --with-teaching --with-praise --auto-approve
```

Default: supplementary **off**; human gates **on** (use `--auto-approve` for CI).

## Inherited DNA

See `PLAN.md` and parent `AGENTS.md`.
