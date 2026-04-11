---
name: church-retreat-app
description: "Generate church youth retreat web apps through Korean conversation"
---

# Church Retreat App Generator

> **코딩 경험 제로인 사역자가 Claude Code와 한국어 대화만으로, 중학생이 "이거 진짜 앱이다!"라고 느끼는 수준의 수련회 앱을 처음부터 끝까지 자동으로 완성한다.**

## Trigger Patterns

- "수련회 앱", "앱 만들어줘", "교회 앱", "retreat app"
- "퀴즈 앱", "점수판", "가사 앱", "스탬프 랠리"
- "수련회 준비", "앱 시작", "앱 생성"

## What This Skill Does

1. Reads `prompt/workflow.md` for domain rules (the WHAT)
2. Reads `prompt/workflow-coding.md` for implementation blueprint (the HOW)
3. Activates `@church-app-orchestrator` agent
4. Orchestrator manages the 7-phase pipeline (P0-P6)
5. Produces: Complete web app + LAN server + QR code + "앱 실행.bat"

## Supported App Types (9 types)

| # | App Type | Korean | Data Sync | Server Required |
|---|----------|--------|-----------|-----------------|
| 1 | Bible Quiz | 성경 퀴즈 | Realtime (WebSocket) | Yes |
| 2 | Stamp Rally | 스탬프 랠리 | Individual→Server | Yes |
| 3 | Schedule & Notices | 일정표 & 공지 | Static | No (GitHub Pages OK) |
| 4 | Worship Lyrics | 찬양 가사 | Realtime (WebSocket) | Yes |
| 5 | QT Guide | QT 가이드 | Static | No (GitHub Pages OK) |
| 6 | Team Scoreboard | 팀 점수판 | Realtime (WebSocket) | Yes |
| 7 | Photo Gallery | 사진 갤러리 | One-way | Yes |
| 8 | Prayer Requests | 기도제목 | Static+refresh | No (GitHub Pages OK) |
| 9 | Combined App | 종합 앱 | Hybrid | Yes |

## Activation Flow

```
trigger → load SKILL.md → spawn @church-app-orchestrator
  → orchestrator reads workflow.md core rules (~300 lines)
  → orchestrator reads workflow-coding.md for implementation details
  → orchestrator starts Phase 0 (Environment Setup)
  → if existing project detected: prompt resume
  → Phase 1: Korean conversation with 사역자 (content collection)
  → Phase 2-4: Auto-pilot (code generation + quality verification)
  → Phase 5: 사역자 preview & feedback loop
  → Phase 6: Deployment (QR, .bat, emergency card)
```

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    USER (사역자)                       │
│         Korean conversation / /start-app              │
└─────────────────────┬────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────┐
│            ORCHESTRATOR AGENT                         │
│  church-app-orchestrator.md                           │
│  • SOT exclusive write (app-state.json)               │
│  • Phase routing & sub-agent spawning                 │
│  • pACS scoring & gate pass/fail decisions            │
└──┬──────┬──────┬──────┬──────┬──────┬────────────────┘
   │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼
 conv   code   design  quality deploy translator
 guide  gen    system  checker mgr    (post-phase)
```

## References (loaded on-demand per phase)

| Reference | When Loaded | Purpose |
|-----------|-------------|---------|
| `references/workflow-phases.md` | Current phase | Phase-by-phase execution details |
| `references/quality-gates.md` | Phase 4, /app-verify | Q1-Q11 + D1-D9 definitions |
| `references/design-system.md` | Phase 3 | CSS variables + animation patterns |
| `references/error-handling.md` | On error | Error recovery tree + Korean messages |
| `references/content-matrix.md` | Phase 1 | App type → required content mapping |

## P1 Validation Scripts

Template scripts in `templates/scripts/` are copied to the generated project's `scripts/` folder during Phase 3. They provide deterministic, hallucination-free quality verification.

| Script | Hallucination Risk | Gates |
|--------|-------------------|-------|
| `validate_gates.py` | H-CRITICAL | Q1-Q11 |
| `validate_design_gates.py` | H-CRITICAL | D1-D9 |
| `validate_integration.py` | H-CRITICAL | T-3.11 |
| `validate_content_insertion.py` | H-CRITICAL | Content accuracy |
| `validate_app_specific.py` | H-CRITICAL | App-type gates |
| `validate_translation_gates.py` | H-CRITICAL | T1-T3 |
| `compute_pacs_data.py` | H-MAJOR | pACS data extraction |

## Absolute Criteria (Inherited)

| # | Criterion | Application |
|---|-----------|-------------|
| AC-1 | Quality above all | Token cost and speed are irrelevant |
| AC-2 | Single-file SOT | `app-state.json` is the sole shared state |
| AC-3 | Code Change Protocol | CCP 3-step + CAP-1~4 for all code changes |
| AC-4 | English-First Execution | All agent reasoning in English; user-facing in Korean |

## Commands

| Command | Purpose |
|---------|---------|
| `/start-app` | Start workflow from Phase 0 |
| `/resume-app` | Resume interrupted workflow |
| `/deploy-app` | Deploy completed app (Phase 6) |
| `/app-status` | Show current status in Korean |
| `/app-verify` | Manual quality verification |
