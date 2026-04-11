---
description: "Start church retreat app generation workflow from Phase 0"
---

# /start-app — 수련회 앱 생성 시작

Start the church retreat app generation workflow from Phase 0 (Environment Setup).

## Execute These Steps

### Step 1: Load Workflow Definitions

Use the **Read tool** to load both workflow files:
1. `prompt/workflow.md` — domain rules (the WHAT)
2. `prompt/workflow-coding.md` — implementation blueprint (the HOW)

Focus on:
- Phase 0-1 definitions (immediate execution)
- Absolute Criteria (AC-1 through AC-4)
- App type table (9 types)
- Content matrix for selected app type

### Step 2: Load Skill References

Use the **Read tool** to load:
1. `.claude/skills/church-retreat-app/SKILL.md` — skill entry point
2. `.claude/skills/church-retreat-app/references/content-matrix.md` — content requirements

### Step 3: Spawn Orchestrator

Activate the `@church-app-orchestrator` agent with the following context:
- Starting from Phase 0 (fresh start)
- No existing project state
- English-first execution (AC-4) for all reasoning
- Korean-only for user-facing messages (AC-2)

### Step 4: Phase 0 — Environment Setup

The orchestrator performs:
1. Verify Node.js, npm, git availability
2. Create project folder: `~/Desktop/church-app-{timestamp}/`
3. Initialize git repo in project folder
4. Create minimal `app-state.json` (SOT)
5. Save project path to `%USERPROFILE%\.last-church-app-path`
6. Git checkpoint: `[환경] 프로젝트 폴더 초기화`

### Step 5: Phase 1 — Present App Menu in Korean

Display the app selection menu to 사역자:

```
🎉 수련회 앱을 만들어 볼까요?

어떤 앱을 만들까요? 번호를 말씀해 주세요!

1. 성경 퀴즈 — 팀별 실시간 대결! 버저 눌러서 정답 맞추기
2. 스탬프 랠리 — QR코드로 미션 클리어! 스탬프 모으기
3. 일정표 & 공지 — 수련회 일정과 공지사항을 한눈에
4. 찬양 가사 — 빔프로젝터 + 핸드폰 동시 가사 표시
5. QT 가이드 — 매일 묵상 말씀과 질문
6. 팀 점수판 — 실시간 팀 점수 관리
7. 사진 갤러리 — 수련회 사진 공유
8. 기도제목 — 함께 나누는 기도제목
9. 종합 앱 — 위 기능 중 원하는 것만 골라서 하나의 앱으로!

💡 잘 모르겠으면 "종합 앱"을 추천해요!
```

Wait for 사역자 response and proceed with content collection per the content matrix.

## Quality Principle

Every decision follows the North Star:
> "코딩 경험 제로인 사역자가 한국어 대화만으로, 중학생이 '이거 진짜 앱이다!'라고 느끼는 수준의 앱을 완성한다."

## Error Handling

| Error | Action |
|-------|--------|
| Node.js not found | Guide installation with Korean instructions |
| Existing project detected | Suggest `/resume-app` instead |
| Permission denied | Try alternative folder location |
| workflow.md not found | Report setup error, suggest re-cloning |

## Constraints

- All agent reasoning in English (AC-4)
- All user-facing messages in Korean (AC-2)
- Quality above all — never compromise for speed (AC-1)
- Single-file SOT — app-state.json only (AC-2)
