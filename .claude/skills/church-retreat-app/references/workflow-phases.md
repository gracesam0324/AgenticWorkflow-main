# Workflow Phases — Church Retreat App (P0-P6)

> Complete phase definitions with agent assignments, inputs, outputs, SOT fields, and git checkpoint format.

---

## Phase 0 — Environment Setup

| Field | Value |
|-------|-------|
| **Agent** | Orchestrator (direct) |
| **Autopilot** | Auto |
| **Inputs** | System environment (Node.js, npm, git) |
| **Outputs** | Verified environment, project folder created, app-state.json initialized |
| **SOT Fields** | `status.phase: 0`, `status.environment_verified: true`, `meta.project_path` |
| **Git Checkpoint** | `[env] Project folder initialized` |

**Steps:**
1. Verify Node.js, npm, git are available
2. Create project folder: `~/Desktop/church-app-{timestamp}/`
3. Initialize git repo
4. Create `app-state.json` with minimal schema
5. Record project path to `%USERPROFILE%\.last-church-app-path`

**Transition Gate:** Environment verified → proceed to Phase 1

---

## Phase 1 — Conversation & Content Collection

| Field | Value |
|-------|-------|
| **Agent** | `@conversation-guide` |
| **Autopilot** | Human interaction required |
| **Inputs** | 사역자의 한국어 대화 |
| **Outputs** | App type, team config, content, design palette, feature list |
| **SOT Fields** | `intent.app_type`, `intent.team_count`, `intent.team_names`, `intent.design_palette`, `content.*`, `intent.features` |
| **Git Checkpoint** | `[research] App type confirmed + content collection complete` |

**Steps:**
1. **T-1.1**: Present app menu (9 types) in Korean → detect app type
2. **T-1.2**: Collect content per content matrix (quiz questions, schedule, lyrics, etc.)
3. **T-1.3**: Confirm app structure with 사역자

**Transition Gate:** `validate_content_collection.py` returns `"complete": true` → proceed to Phase 2

**Korean Messages:**
- Menu: "어떤 앱을 만들까요? 아래에서 골라주세요!"
- Content: "퀴즈 문제를 알려주세요. 파일로 주셔도 돼요!"
- Confirm: "이렇게 만들면 될까요?"

---

## Phase 2 — Project Initialization

| Field | Value |
|-------|-------|
| **Agent** | `@code-generator` |
| **Autopilot** | Auto |
| **Inputs** | SOT intent + content sections |
| **Outputs** | Initialized project with dependencies, architecture plan |
| **SOT Fields** | `status.project_initialized: true`, `architecture.*` |
| **Git Checkpoint** | `[init] Project structure + dependencies installed` |

**Steps:**
1. **T-2.1**: npm init, install dependencies (express, ws, qrcode, lowdb, open)
2. Plan architecture (URL routes, file structure, data flow)
3. Configure design system variables from SOT palette

**Dependency Rules:**
- ALLOWED: express, ws, lowdb, qrcode, open
- FORBIDDEN: SQLite, node-gyp, Python-dependent, native compilation

---

## Phase 3 — Code Generation

| Field | Value |
|-------|-------|
| **Agent** | `@code-generator` + `@design-system` (Agent Team for combined app) |
| **Autopilot** | Auto |
| **Inputs** | Architecture plan, content from SOT, design system config |
| **Outputs** | Complete web app (HTML/CSS/JS), server.js, PWA manifest, service worker |
| **SOT Fields** | `status.code_generated: true`, `files.*` |
| **Git Checkpoint** | `[code] App code generation complete` |

**Task Sequence:**
1. **T-3.1**: Create project skeleton (HTML + base CSS + empty JS)
2. **T-3.2**: Setup design system CSS variables and animations
3. **T-3.3**: Write skeleton tests (TDD RED phase) — `@tdd-guard`
4. **T-3.4**: Insert content into HTML (quiz questions, schedule, etc.)
5. **T-3.5**: Implement styling, animations, dark mode — `@design-system`
6. **T-3.6**: Implement WebSocket and real-time functionality
7. **T-3.7**: Write functionality tests (TDD RED phase) — `@tdd-guard`
8. **T-3.8**: Implement PWA (manifest + service worker) — `@design-system`
9. **T-3.9**: Copy P1 template scripts to `project/scripts/` — `@tdd-guard`
10. **T-3.10**: Polish: data export, error handling, reconnection
11. **T-3.11**: Integration verification (post-merge) — orchestrator

**P1 Script Copy Protocol:**
```
1. Copy .claude/skills/church-retreat-app/templates/scripts/*.py → <project>/scripts/
2. Inject app-specific config from SOT (port, app_type, palette, features)
3. Scripts are now project-local and executable
```

---

## Phase 4 — Quality Verification

| Field | Value |
|-------|-------|
| **Agent** | Orchestrator (P1 scripts) + `@quality-checker` (fixes) |
| **Autopilot** | Auto |
| **Inputs** | Generated code, P1 validation scripts |
| **Outputs** | Quality report, auto-fixed issues, pACS scores |
| **SOT Fields** | `quality.gates.*`, `quality.pacs.*`, `status.quality_passed: true` |
| **Git Checkpoint** | `[verify] Quality verification passed` |

**Two-Pass Execution:**

Pass 1 — Detection (orchestrator runs P1 scripts directly via Bash):
```bash
python3 scripts/validate_gates.py --project-dir . --json
python3 scripts/validate_design_gates.py --project-dir . --json
python3 scripts/validate_app_specific.py --project-dir . --type {type} --json
python3 scripts/validate_content_insertion.py --project-dir . --json
```

Pass 2 — Fix (for each FAIL gate):
- Orchestrator spawns `@quality-checker` with FAIL detail
- `@quality-checker` applies creative fix
- Orchestrator re-runs ONLY the failed gate script to confirm PASS
- Max 3 retries per gate

**pACS Scoring:**
```bash
python3 scripts/compute_pacs_data.py --project-dir .
```
- GREEN (>=70): auto-proceed
- YELLOW (50-69): proceed with flag
- RED (<50): rework

---

## Phase 5 — Preview & Feedback

| Field | Value |
|-------|-------|
| **Agent** | Orchestrator (direct — DG-2) |
| **Autopilot** | Auto-approve after 3 modification cycles |
| **Inputs** | Running app, 사역자 feedback |
| **Outputs** | Approved app (possibly modified) |
| **SOT Fields** | `status.user_approved: true`, `history.modifications[]` |
| **Git Checkpoint** | `[approve] User review complete` |

**Modification Loop:**
- [A] Style/text change → Phase 3 fix → return (QA skip)
- [B] Feature add/change → Phase 3 fix → Phase 4 re-run → return
- [C] Rollback → git checkout → Post-Rollback SOT Sync → return

**Korean Messages:**
- Preview: "앱이 완성되었어요! 한번 확인해 보세요."
- QR: "이 QR코드로 핸드폰에서도 볼 수 있어요."
- Modify: "어디를 수정할까요?"
- Complete: "완성이에요! 배포할까요?"

---

## Phase 6 — Deployment

| Field | Value |
|-------|-------|
| **Agent** | `@deployment-manager` |
| **Autopilot** | Auto |
| **Inputs** | Approved app, deployment config |
| **Outputs** | Running server, QR code, .bat file, emergency card |
| **SOT Fields** | `deployment.*`, `status.deployed: true` |
| **Git Checkpoint** | `[deploy] Final build complete` |

**Deliverables:**
1. LAN server running in background
2. QR code PNG with correct URL
3. Print-ready HTML page (A4, church name + QR + instructions)
4. "앱 실행.bat" on desktop with Korean messages
5. WiFi connection instructions page
6. Emergency response card (Korean)
7. Browser auto-opened with QR page

**Post-Deployment Translation (A3-3):**
```bash
python3 scripts/validate_translation_gates.py --project-dir .
```
- T1: .ko files exist for all phases
- T2: pACS >= 70 for each translation
- T3: Glossary consistency check
