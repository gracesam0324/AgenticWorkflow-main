---
description: "Resume interrupted church retreat app generation"
---

# /resume-app — 중단된 수련회 앱 이어서 만들기

Resume an interrupted church retreat app generation workflow from the last saved state.

## Execute These Steps

### Step 1: Load Workflow Definitions

Use the **Read tool** to load:
1. `prompt/workflow.md` — domain rules
2. `prompt/workflow-coding.md` — implementation blueprint

### Step 2: Find Existing Project

Search for the project folder in this order:

1. Read `%USERPROFILE%\.last-church-app-path` for saved project path
2. If not found, search these locations for `church-app*` folders:
   - `~/Desktop/`
   - `~/Documents/`
   - `C:\`
   - `D:\`
3. If multiple projects found, list them and ask 사역자 to choose

### Step 3: Read SOT State

Use the **Read tool** on `app-state.json` from the project folder.

Parse all status fields:
- `status.phase` — current phase (0-6)
- `status.environment_verified` — Phase 0 complete?
- `status.content_collected` — Phase 1 complete?
- `status.project_initialized` — Phase 2 complete?
- `status.code_generated` — Phase 3 complete?
- `status.quality_passed` — Phase 4 complete?
- `status.user_approved` — Phase 5 complete?
- `status.deployed` — Phase 6 complete?

### Step 4: Determine Resume Point

```
Phase determination logic:
  if not environment_verified → Phase 0
  if not content_collected → Phase 1
  if not project_initialized → Phase 2
  if not code_generated → Phase 3
  if not quality_passed → Phase 4
  if not user_approved → Phase 5
  if not deployed → Phase 6
  if all true → already complete
```

### Step 5: Display Resume Message in Korean

```
이전에 만들던 앱이 있어요! 이어서 할까요?

📱 앱 유형: {intent.app_type}
📍 현재 단계: Phase {N} — {phase_description}
📂 프로젝트 위치: {project_path}
⏰ 마지막 수정: {last_modified_date}

이어서 할까요? (네/아니요)
```

If 사역자 confirms, proceed. If not, offer to start fresh with `/start-app`.

### Step 6: Restart Server if Needed

If the app was in Phase 5 or 6 (server was running):
1. Check if server is still running: `netstat -ano | findstr :{PORT}`
2. If not running, restart: `node server.js` (background)
3. Detect current IP address (may have changed)
4. Regenerate QR code with new IP if changed
5. Korean message: "서버를 다시 시작했어요. QR코드도 새로 만들었어요!"

### Step 7: Spawn Orchestrator and Resume

Activate `@church-app-orchestrator` with:
- Resume mode (not fresh start)
- Current SOT state loaded
- Resume from determined phase
- English-first execution (AC-4)

## Error Handling

| Error | Korean Message | Action |
|-------|---------------|--------|
| No project found | "이전에 만들던 앱을 찾을 수 없어요. 새로 시작할까요?" | Offer `/start-app` |
| app-state.json corrupted | "상태 파일이 손상되었어요. 마지막 Git 체크포인트에서 복구할까요?" | Git restore app-state.json |
| app-state.json missing | "상태 파일이 없어요. 프로젝트 폴더는 있지만 상태를 알 수 없어요." | Reconstruct from git log |
| Multiple projects | "여러 개의 앱 프로젝트가 있어요. 어떤 걸 이어할까요?" | List and let user choose |

## Constraints

- Never start a new project without confirming with 사역자
- Always check IP address change before resuming server
- All reasoning in English (AC-4), all messages in Korean (AC-2)
