# Church Retreat App — Infrastructure Build (Implementation Blueprint)

> **This document is the single authoritative implementation blueprint for building the execution infrastructure of `workflow.md`.**
> All agents, hooks, skills, commands, and scripts described here are written and operated in **English**.
> User-facing messages remain in **Korean** (as defined by workflow.md AC2).

---

## 0. Document Hierarchy & Reading Order

```
soul.md                  ← WHY (philosophy, DNA)
AGENTS.md                ← HOW (cross-project rules)
CLAUDE.md                ← WHAT (project-level config, TOC)
prompt/workflow.md        ← DOMAIN (church retreat app workflow definition)
prompt/workflow-coding.md ← THIS FILE (implementation blueprint for workflow.md)
```

**Relationship to workflow.md**: `workflow.md` defines *what* the workflow does (phases, steps, quality gates, user interaction). This document defines *how* to build the Claude Code infrastructure that *executes* workflow.md — the agents, hooks, scripts, skills, commands, SOT, TDD, and fallback mechanisms.

---

## 1. Absolute Criteria (Inherited — Non-Negotiable)

These are inherited verbatim from `AGENTS.md §2` and `soul.md §0`. Every implementation decision in this document is subordinate to them.

| # | Criterion | Application in This Build |
|---|-----------|--------------------------|
| **AC-1** | Quality above all | Token cost and speed are irrelevant. Agent count, hook count, verification depth — all increase if quality improves. |
| **AC-2** | Single-file SOT | `app-state.json` is the sole shared state file. Only the orchestrator writes to it. |
| **AC-3** | Code Change Protocol | Every code generation/modification follows CCP 3-step (Intent → Ripple → Plan) + CAP-1~4. |
| **AC-4** | English-First Execution | All agent reasoning, intermediate artifacts, and reports are produced in **English** first. A dedicated `@app-translator` agent then generates Korean `.ko` translation pairs. AI performs best in English; this maximizes output quality (serves AC-1). |

### AC-4 English-First Execution — Full Definition

```
When a workflow execution command is issued:

  1. All agent reasoning and chain-of-thought: ENGLISH
  2. All agent-to-agent communication (SendMessage): ENGLISH
  3. All intermediate artifacts (reports, plans, logs, architecture docs): ENGLISH
  4. All Git commit messages: ENGLISH
  5. All SOT field keys: ENGLISH (values in original language of data)
  6. After each phase, @app-translator creates Korean .ko pair for every English artifact.
  7. English original + Korean translation are always kept as a pair — never one without the other.

Exceptions (Korean is the original language — NOT translated from English):
  • Direct conversation with 사역자 — workflow.md AC2 (한국어 전용) takes precedence
  • App UI text (buttons, menus, instructions) — the app's end-users are Korean middle-schoolers
  • App content provided by 사역자 (quiz questions, schedule, lyrics) — user-supplied Korean data
  • .bat console messages — read by 사역자 on-site
  • Emergency response card — printed Korean reference for 사역자
  • QR instruction page — shown to students

Rationale:
  AI models produce higher-quality reasoning, analysis, and code in English.
  By working in English first and translating afterward, we get the best of both worlds:
  maximum AI performance (English) + full accessibility (Korean translations).
  This directly serves AC-1 (Quality above all).
```

### English-First Scope Matrix

| Scope | Language | Rationale |
|-------|----------|-----------|
| Agent prompts & reasoning | **English** | AC-4: AI performance |
| Agent-to-agent messages | **English** | AC-4 |
| Phase reports (`reports/*.md`) | **English original** → `.ko` pair | AC-4 + translation |
| Quality gate results | **English** → `.ko` pair | AC-4 + translation |
| Git commit messages | **English** | AC-4 |
| SOT keys & structure | **English** | AC-4 |
| Code (JS/CSS/HTML structure) | **English** | Standard practice |
| App Korean content (user-supplied) | **Korean** (original) | User data |
| App UI text | **Korean** | End-user language |
| Conversation with 사역자 | **Korean** | AC2 + North Star |
| .bat / emergency card / QR page | **Korean** | 사역자 on-site use |

**Priority**: AC-1 (Quality) > AC-2 (SOT) = AC-3 (CCP) = AC-4 (English-First). AC-2, AC-3, AC-4 are co-equal instruments serving AC-1. When AC-4 (English-First) conflicts with user-facing Korean requirements (workflow.md AC2), the user-facing Korean wins — because the North Star itself is a quality criterion.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      USER (사역자)                             │
│           Korean conversation / /start-app / /resume-app      │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│              ORCHESTRATOR AGENT                               │
│  church-app-orchestrator.md                                   │
│                                                               │
│  Responsibilities:                                            │
│   • SOT exclusive write (app-state.json)                      │
│   • Phase routing & transition decisions                      │
│   • Sub-agent spawning & result collection                    │
│   • Agent Team coordination (Phase 3, 4)                      │
│   • Fallback tier decisions                                   │
│   • pACS scoring & gate pass/fail decisions                   │
│   • Task lifecycle management (TaskCreate/Update)             │
│   • Human checkpoint routing (Phase 1 confirm, Phase 5 fb)    │
│   • AC-4 English-First enforcement across all agents          │
│   • Translation scheduling after each phase (@app-translator) │
│   • Translation pACS collection and SOT recording             │
│                                                               │
│  NEVER delegates:                                             │
│   • SOT writes                                                │
│   • Phase transitions                                         │
│   • Fallback tier decisions                                   │
│   • Human checkpoint routing                                  │
│   • Translation scheduling decisions                          │
└──┬───────┬───────┬───────┬───────┬───────┬───────┬──────────┘
   │       │       │       │       │       │       │
   ▼       ▼       ▼       ▼       ▼       ▼       ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│ CG  │ │ CDG │ │ DS  │ │ QC  │ │ DM  │ │ TDD │ │TRNS │
│Guide│ │Coder│ │Desgn│ │Check│ │Dploy│ │Guard│ │ late │
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘
 P0,1,5  P2,3,5   P3      P4      P6     All    P1-P6
                                                 (post)
```

### 2.1 Agent Roster

| Agent File | Name | Model | Tools | Active Phases | Max Turns |
|------------|------|-------|-------|---------------|-----------|
| `conversation-guide.md` | conversation-guide | opus | Read, Write, Bash, Glob, Grep, Agent | P0, P1 | 60 |
| `code-generator.md` | code-generator | opus | Read, Write, Edit, Bash, Glob, Grep | P2, P3, P5 (fix) | 80 |
| `design-system-agent.md` | design-system | opus | Read, Write, Edit, Bash, Glob, Grep | P3 (parallel with code-generator) | 40 |
| `quality-checker.md` | quality-checker | opus | Read, Bash, Glob, Grep | P4 | 40 |
| `deployment-manager.md` | deployment-manager | opus | Read, Write, Edit, Bash, Glob, Grep | P6 | 40 |
| `tdd-guard.md` | tdd-guard | sonnet | Read, Write, Edit, Bash, Glob, Grep | All (on code change) | 30 |
| `app-translator.md` | app-translator | opus | Read, Write, Glob, Grep | P1-P6 (post-phase translation) | 25 |

### 2.2 Phase → Agent Mapping

```
Phase 0 (Environment Setup):
  → orchestrator checks prerequisites directly (no sub-agent needed)
  → human step — orchestrator presents checklist to user

Phase 1 (Conversation & Content):
  → orchestrator spawns @conversation-guide
  → conversation-guide handles Steps 2-4 (menu, content, confirmation)
  → conversation-guide writes reports/phase1-intent-report.md (English, AC-4)
  → results returned to orchestrator → SOT write
  → orchestrator spawns @app-translator → .ko pair (NON-BLOCKING)

Phase 2 (Project Initialization):
  → orchestrator spawns @code-generator
  → code-generator POPULATES existing project folder (created at activation, DG-1):
    npm init + package.json + npm install + architecture planning
  → code-generator writes reports/phase2-architecture-plan.md (English, AC-4)
  → orchestrator writes planning_complete to SOT
  → (translation DEFERRED to batch after Phase 6 — A3-3)

Phase 3 (Code Generation):             ⭐ SEQUENTIAL (default) | AGENT TEAM (종합 앱 3+ features)
  → DEFAULT (single apps 1-8, or 종합 앱 with <3 features):
    Sequential sub-agents: @tdd-guard → @code-generator → @design-system → @tdd-guard
    Each agent SEES previous agent's output → zero integration gaps (§5.4)
  → UPGRADE (종합 앱 with 3+ features, Agent Teams available):
    Agent Team: 3 teammates in parallel (§5.2) + T-3.11 integration verification
  → orchestrator merges results → SOT write
  → (translation DEFERRED to batch after Phase 6 — A3-3)

Phase 4 (Quality Verification):        ⭐ TWO-PASS (P1 SCRIPTS)
  → PASS 1: orchestrator runs P1 scripts directly (NO agents, NO AI reasoning)
    → validate_gates.py + validate_design_gates.py + validate_app_specific.py
    → validate_content_insertion.py → merge JSON → PASS/FAIL per gate
  → PASS 2: for each FAIL gate, orchestrator spawns @quality-checker (AI fix only)
    → sequential fix → re-run script → confirm → max 3 retries
  → (translation DEFERRED to batch after Phase 6 — A3-3)

Phase 5 (Preview & Feedback):     ⚠ ORCHESTRATOR HANDLES DIRECTLY (DG-2)
  → orchestrator opens browser + QR → presents to user
  → orchestrator DIRECTLY interacts with user (no sub-agent for Phase 5)
    WHY: Phase 5 requires rapid read-modify-verify cycles.
    Spawning a sub-agent for each user message adds latency and context loss.
    Orchestrator already has full context (SOT + all Phase 1-4 history).
    User-facing messages use Korean (AC2). Internal reasoning uses English (AC-4).
  → orchestrator uses classify_modification() + detect_completion_signal() (H2-3, H2-4)
  → user feedback → orchestrator routes:
    [A style fix] → @code-generator (skip QA)
    [B feature add] → @code-generator → Phase 4 re-run
    [C rollback] → orchestrator git checkout → SOT sync
    [? uncertain] → orchestrator asks clarifying question in Korean
  → when detect_completion_signal() returns True:
    → orchestrator asks EXPLICIT confirmation: "이대로 배포할까요?" (A1-5 safety)
    → user confirms ("네"/"좋아요") → proceed to Phase 6
    → user declines → stay in feedback loop
    → orchestrator compiles reports/phase5-modification-log.md (English, AC-4)

Phase 6 (Deployment):
  → orchestrator spawns @deployment-manager
  → LAN server + QR + .bat + emergency card
  → orchestrator writes deployed=true to SOT
  → BATCH TRANSLATION (A3-3): spawn @app-translator ONCE for ALL reports/phase2-6
  → T1-T3 translation gates (all .ko pairs exist + pACS ≥ 70)
```

---

## 3. Source of Truth (SOT) Design

### 3.1 SOT File & Lifecycle

**File**: `app-state.json`

**Writer**: Orchestrator agent ONLY — exclusive write access.

**Readers**: All sub-agents — read-only access.

**SOT Lifecycle (resolves the project-folder timing problem):**

```
ACTIVATION (before any Phase):
  Orchestrator creates MINIMAL project folder immediately:
    → Determine folder path (Desktop > Documents > C:\ priority, per workflow.md)
    → mkdir <project-folder>
    → Write initial app-state.json with workflow metadata + empty sections
    → Git init + initial commit: "[init] SOT initialized"
  Result: app-state.json EXISTS from the very start. All phases can read/write.

Phase 0-1 (Research):
  SOT location: <project-folder>/app-state.json (already exists)
  Writes: intent.*, content.*, status.research_complete

Phase 2 (Planning):
  SOT location: same file, same folder
  Additional: npm init, package.json, dependency install INTO the existing folder
  The folder was created at activation — Phase 2 POPULATES it, not creates it.

Phase 3-6 (Implementation):
  SOT location: same file
  P1 scripts copied to <project-folder>/scripts/ in Phase 3
```

> **Why create the folder at activation, not Phase 2?**
> The SOT must be writable from Phase 1 (content collection writes intent data).
> If the folder only existed from Phase 2, Phase 1 would have nowhere to write.
> Creating a minimal folder (just app-state.json + .git) at activation solves this
> with zero impact on the user — the folder is created silently in the background.

### 3.2 Write Protocol

```
Sub-agent completes task
  → returns result to orchestrator (via Agent tool result or SendMessage)
  → orchestrator validates result
  → orchestrator performs atomic write to app-state.json:
      1. Read current state
      2. Merge new data
      3. Validate merged data:
         python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/validate_app_state_schema.py \
           --schema "$CLAUDE_PROJECT_DIR"/.claude/schemas/app-state.schema.json \
           --data <merged_json>
         → INFRASTRUCTURE-LEVEL script (not in generated project — always available)
         → Works from Phase 0 onward (no dependency on generated project folder)
         → If schema invalid: ABORT write, log error, fix data structure
         (P1: deterministic schema check prevents malformed SOT writes)
      4. Write to app-state.tmp.json
      5. Rename app-state.tmp.json → app-state.json (atomic)
      6. Git checkpoint if phase transition
```

### 3.3 SOT Schema

```jsonc
// app-state.json — Full schema definition
{
  "workflow": {
    "name": "church-retreat-app",
    "version": "1.0",
    "created_at": "",                    // ISO 8601
    "blueprint": "prompt/workflow-coding.md",
    "parent_genome": {
      "source": "AgenticWorkflow",
      "inherited_dna": [
        "absolute-criteria", "sot-pattern", "3-phase-structure",
        "4-layer-qa", "safety-hooks", "context-preservation"
      ]
    }
  },
  "intent": {
    "app_type": "",                      // "quiz" | "score" | "schedule" | etc.
    "app_types_combined": [],            // for 종합 앱
    "team_count": 0,
    "team_names": [],
    "team_colors": [],
    "design_palette": "A",              // "A" | "B" | "C"
    "features": [],
    "admin_password": ""
  },
  "content": {
    "quiz_questions": [],
    "schedule": [],
    "lyrics": [],
    "missions": [],
    "bible_passages": [],
    "custom_data": {}
  },
  "architecture": {
    "deployment_type": "",               // "lan" | "static" | "hybrid"
    "tech_stack": "",                    // "static" | "node-ws" | "node-hybrid"
    "url_routes": [],
    "data_sync": "",                     // "realtime" | "static" | "hybrid"
    "has_admin": false,
    "has_screen": false,
    "has_pwa": true
  },
  "status": {
    "current_phase": 0,
    "research_complete": false,
    "planning_complete": false,
    "code_generated": false,
    "quality_passed": false,
    "deployed": false,
    "project_folder": "",
    "modification_count": 0,
    "in_preview_loop": false,
    "pending_action": null,
    "server_port": null,
    "server_url": "",
    "qr_path": "",
    "bat_path": "",
    "github_pages_url": null,
    "last_git_checkpoint": "",
    "agent_team_active": false,
    "fallback_tier": 1                   // 1=team, 2=sequential, 3=direct, 4=human
  },
  "quality": {
    "q_gates": {},                       // {"Q1": "PASS", "Q2": "FAIL:reason", ...}
    "d_gates": {},                       // {"D1": "PASS", ...}
    "app_specific_gates": {},
    "pacs": {
      "F": 0,                           // Content accuracy (0-100)
      "C": 0,                           // Feature completeness (0-100)
      "L": 0                            // Code correctness (0-100)
    },
    "pacs_score": 0,                     // min(F, C, L)
    "last_verified": "",
    "retry_count": 0,
    "verify_log": []                     // [{timestamp, gates_passed, gates_failed, action}]
  },
  "history": {
    "modifications": [],                 // [{timestamp, type, description, git_commit}]
    "exports": [],
    "archive_path": null,
    "fallback_events": []                // [{timestamp, from_tier, to_tier, reason}]
  },
  "tdd": {
    "test_files": [],                    // ["tests/test_server.js", ...]
    "last_run": "",
    "pass_count": 0,
    "fail_count": 0,
    "coverage_percent": 0
  },
  "translation": {
    "glossary_path": "translations/glossary.yaml",
    "phases": {
      "1": {
        "english_original": "reports/phase1-intent-report.md",
        "korean_translation": "reports/phase1-intent-report.ko.md",
        "pacs": { "Ft": 0, "Ct": 0, "Nt": 0 },  // Fidelity, Completeness, Naturalness
        "pacs_score": 0,                           // min(Ft, Ct, Nt)
        "status": "pending"                        // "pending"|"in_progress"|"completed"|"skipped"
      },
      "2": {
        "english_original": "reports/phase2-architecture-plan.md",
        "korean_translation": "reports/phase2-architecture-plan.ko.md",
        "pacs": { "Ft": 0, "Ct": 0, "Nt": 0 },
        "pacs_score": 0,
        "status": "pending"
      },
      "3": {
        "english_original": "reports/phase3-codegen-report.md",
        "korean_translation": "reports/phase3-codegen-report.ko.md",
        "pacs": { "Ft": 0, "Ct": 0, "Nt": 0 },
        "pacs_score": 0,
        "status": "pending"
      },
      "4": {
        "english_original": "reports/phase4-quality-report.md",
        "korean_translation": "reports/phase4-quality-report.ko.md",
        "pacs": { "Ft": 0, "Ct": 0, "Nt": 0 },
        "pacs_score": 0,
        "status": "pending"
      },
      "5": {
        "english_original": "reports/phase5-modification-log.md",
        "korean_translation": "reports/phase5-modification-log.ko.md",
        "pacs": { "Ft": 0, "Ct": 0, "Nt": 0 },
        "pacs_score": 0,
        "status": "pending"
      },
      "6": {
        "english_original": "reports/phase6-deployment-report.md",
        "korean_translation": "reports/phase6-deployment-report.ko.md",
        "pacs": { "Ft": 0, "Ct": 0, "Nt": 0 },
        "pacs_score": 0,
        "status": "pending"
      }
    },
    "t_gates": {                                   // Translation quality gates
      "T1": "pending",                             // All .ko files exist
      "T2": "pending",                             // All translation pACS >= 70
      "T3": "pending"                              // Glossary consistency verified
    },
    "total_translated_files": 0,
    "glossary_entries_count": 0,
    "last_translation": ""                         // ISO 8601 timestamp
  }
}
```

---

## 4. Agent Definitions (Implementation Spec)

> All agent `.md` files live in `.claude/agents/` and are written entirely in **English**.
> Each definition follows the standard frontmatter format.

### AC-4 Enforcement — Common Rules for ALL Agents

Every sub-agent definition file MUST include the following section:

```markdown
## English-First Execution (AC-4)

All internal reasoning, chain-of-thought, and intermediate outputs MUST be in English.
Write all reports and documentation in English to the `reports/` folder.
All Git commit messages MUST be in English.

Exceptions (use Korean — these are NOT translated FROM English, they ARE Korean originals):
  - Direct conversation with 사역자 (conversation-guide only, per workflow.md AC2)
  - App UI text content (code-generator: Korean strings in HTML for end-users)
  - .bat console messages (deployment-manager: Korean for 사역자)
  - Emergency response card text (deployment-manager: Korean for on-site use)
  - QR instruction page text (deployment-manager: Korean for students)
```

### 4.1 church-app-orchestrator.md

```yaml
---
name: church-app-orchestrator
description: "Master coordinator for Church Retreat App workflow — owns SOT, manages phases, routes tasks, handles fallback"
model: opus
tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
maxTurns: 200
---
```

> **maxTurns rationale:** 6 phases × ~25 turns/phase (spawn + validate + SOT + translate) = 150 base. Phase 5 feedback loop can add 30+ turns. Phase 3 Agent Team coordination adds ~20 turns. 200 provides safe margin. If Phase 5 exceeds 10 modification cycles, orchestrator triggers context checkpoint (save to SOT + Git + snapshot) and can resume in a new session via RLM recovery (§12.3).

**Phase 5 Long-Loop Checkpoint:**
```
if status.modification_count > 5:    # A1-4: lowered from 10 to prevent context overflow
    save_context_checkpoint()    # SOT + Git + context snapshot
    notify_user("진행 상황을 저장했어요. 계속 수정하실 수 있어요.")
    # Can safely resume from this checkpoint if session ends
```

**Core Logic (pseudocode):**

```python
PHASE_MAP = {
    0: ("research",       step_0_env_setup),         # human
    1: ("research",       step_1_conversation),       # @conversation-guide
    2: ("planning",       step_2_project_init),       # @code-generator
    3: ("implementation", step_3_code_generation),     # Agent Team
    4: ("implementation", step_4_quality_verify),      # Parallel Fork
    5: ("implementation", step_5_preview_feedback),    # human + agents
    6: ("implementation", step_6_deployment),          # @deployment-manager
}

def execute_phase(phase_num):
    mode = choose_execution_mode(phase_num)
    try:
        if mode == "agent_team":
            result = run_agent_team(phase_num)
            run_integration_verification()   # M3: mandatory post-merge check
        elif mode == "two_pass_fork":
            detections = run_parallel_detection(phase_num)  # Pass 1: detect only
            result = run_sequential_autofix(detections)     # Pass 2: fix one-by-one
        else:
            result = run_subagent(phase_num)
        
        validate_result(result)
        score_phase_pacs(phase_num, result)  # L1.5: per-phase quality self-check
        write_sot(result)
        schedule_translation(phase_num)  # AC-4: BLOCKING P1, DEFERRED BATCH at P6 (A3-3)
        
        if phase_num == 6:
            run_translation_gates()      # T1-T3 final check
        
        if phase_num < 6:
            execute_phase(phase_num + 1)
    
    except AgentFailure:
        handle_fallback(phase_num)

def schedule_translation(phase_num):
    """Phase 1 = BLOCKING (template validation).
    Phase 2-6 = DEFERRED (batch after Phase 6 — A3-3)."""
    report_path = f"reports/phase{phase_num}-*.md"
    if not report_exists(report_path):
        return
    
    if phase_num == 1:
        # BLOCKING: validate translation template quality
        result = spawn_blocking(
            agent="app-translator",
            prompt=f"Translate {report_path} to Korean .ko pair."
        )
        if result.pacs_score < 70:
            retry_translation(phase_num, max_retries=2)
        write_sot_translation(phase_num, result)
    elif phase_num == 6:
        # BATCH: translate ALL remaining reports (Phase 2-6) in one session
        result = spawn_blocking(
            agent="app-translator",
            prompt="Translate ALL reports/phase2-*.md through phase6-*.md to .ko pairs. "
                   "Use glossary.yaml + church-app-glossary.yaml for consistency. "
                   "Score translation pACS (Ft/Ct/Nt) for each report."
        )
        for p in range(2, 7):
            write_sot_translation(p, result.per_phase[p])
    # Phase 2-5: no action — deferred to Phase 6 batch (A3-3)

def run_translation_gates():
    """Post-deployment T1-T3 check. Does NOT block deployment."""
    spawn_subagent(
        agent="quality-checker",
        prompt="Run T1-T3 translation gates on reports/ folder."
    )

def score_phase_pacs(phase_num, result):
    """L1.5 pACS self-scoring after EVERY phase (4-layer QA gene).
    
    P1 HALLUCINATION PREVENTION:
    Objective data is extracted by deterministic Python script (compute_pacs_data.py).
    AI orchestrator only applies SUBJECTIVE weighting to the objective numbers.
    AI never "estimates" match rates or coverage — the script measures them exactly.
    """
    # H-MAJOR: script extracts objective data, AI applies judgment
    pacs_data = run_script("compute_pacs_data.py", f"--phase {phase_num}")
    # pacs_data = {"F_data": {"match_rate": 0.95, "missing": [...]},
    #              "C_data": {"coverage_rate": 1.0, "unimplemented": []},
    #              "L_data": {"gate_pass_rate": 0.87, "failing": ["D7"]}}
    
    # DETERMINISTIC GUARDRAILS — prevent AI score inflation (H2-1)
    # AI judgment is BOUNDED by objective data. AI can refine within the band,
    # but CANNOT exceed the ceiling derived from measured rates.
    #
    # Guardrail formula: ceiling = round(rate * 100)
    #   If match_rate = 0.50 → AI score ≤ 50 (RED zone, period)
    #   If match_rate = 0.85 → AI score ≤ 85 (AI can score 70-85, not 86+)
    #   If match_rate = 1.00 → AI score ≤ 100 (AI can score 90-100)
    # AI can score LOWER than ceiling (judgment: "technically 100% but quality is poor")
    # AI can NEVER score HIGHER than ceiling (no inflation possible)
    
    f_ceiling = round(pacs_data["F_data"]["match_rate"] * 100)
    c_ceiling = round(pacs_data["C_data"]["coverage_rate"] * 100)
    l_ceiling = round(pacs_data["L_data"]["gate_pass_rate"] * 100)
    
    pacs = {
        "F": min(judge_content_score(pacs_data["F_data"]), f_ceiling),
        "C": min(judge_completeness_score(pacs_data["C_data"]), c_ceiling),
        "L": min(judge_correctness_score(pacs_data["L_data"]), l_ceiling),
    }
    pacs["score"] = min(pacs["F"], pacs["C"], pacs["L"])
    pacs["ceilings"] = {"F": f_ceiling, "C": c_ceiling, "L": l_ceiling}
    pacs["raw_data"] = pacs_data  # preserve objective evidence in SOT
    write_sot(f"quality.phase_{phase_num}_pacs", pacs)
    
    if pacs["score"] < 50:  # RED
        log_warning(f"Phase {phase_num} pACS RED ({pacs['score']}). Consider rework.")
    # GREEN/YELLOW: proceed (Phase 4 will do thorough verification)

def choose_execution_mode(phase_num):
    """
    QUALITY-DRIVEN mode selection (AC-1).
    The choice between agent_team, parallel_fork, and subagent is based on
    which mode produces the HIGHEST QUALITY result for each phase.
    Speed is irrelevant. Token cost is irrelevant. Only quality matters.
    """
    if phase_num == 3:
        # QUALITY-DRIVEN DECISION (ADR-012):
        # Sequential execution is the DEFAULT because:
        #   - HTML/CSS/JS are tightly coupled (circular dependency)
        #   - Sequential: each agent SEES previous agent's output → 0 integration gaps
        #   - Parallel: agents CAN'T see each other → T-3.11 post-merge fix needed
        #   - For simple apps (1-8), sequential quality > parallel quality
        #
        # Agent Team is ONLY used for 종합 앱 (type 9, combining 3+ features):
        #   - Large enough codebase to benefit from deep specialization (P2)
        #   - T-3.11 integration verification handles the cross-agent gaps
        #   - Quality benefit of specialization outweighs integration risk at scale
        app_type = read_sot_app_type()
        combined_count = len(read_sot_combined_features())
        if app_type == "combined" and combined_count >= 3 and agent_teams_available():
            return "agent_team"       # 종합 앱 3+ features: specialization wins
        else:
            return "subagent"         # Default: sequential quality is superior
    elif phase_num == 4:
        # 2-Pass Fork: parallel DETECTION (speed of identification) →
        # sequential FIX (prevents cross-fix conflicts).
        # Quality benefit: fixes are applied one at a time, each accounting
        # for prior fixes. No conflicting auto-repairs.
        return "two_pass_fork"        # Quality: conflict-free auto-fix
    else:
        return "subagent"             # Phases 0,1,2,5,6: focused single-agent
```

**SOT Write Responsibilities:**

| Trigger | SOT Fields Updated |
|---------|-------------------|
| Phase 1 complete | `intent.*`, `content.*`, `status.research_complete=true` |
| Phase 2 complete | `architecture.*`, `status.planning_complete=true`, `status.project_folder` |
| Phase 3 complete | `status.code_generated=true`, `status.last_git_checkpoint` |
| Phase 4 complete | `quality.*`, `status.quality_passed=true` |
| Phase 5 modification | `history.modifications[]`, `status.modification_count++` |
| Phase 6 complete | `status.deployed=true`, `status.server_url`, `status.qr_path`, `status.bat_path` |
| Fallback event | `status.fallback_tier`, `history.fallback_events[]` |
| TDD run | `tdd.*` |
| Translation complete | `translation.phases.{N}.*`, `translation.total_translated_files`, `translation.last_translation` |
| T-gates check | `translation.t_gates.*` |

### 4.2 conversation-guide.md

```yaml
---
name: conversation-guide
description: "Korean conversation specialist — collects user intent, content, and confirmation through natural dialog"
model: opus
tools: [Read, Write, Bash, Glob, Grep, Agent]
maxTurns: 60
---
```

**Language Protocol (AC-4 + AC2 reconciliation):**
- External (to 사역자): **Korean** — workflow.md AC2, North Star requirement
- Internal (reasoning, agent-to-orchestrator reports): **English** — AC-4
- Phase report output: **English** → `reports/phase1-intent-report.md`
- Korean content from 사역자 (quiz questions, schedule, etc.): stored AS-IS in Korean in SOT
- Example report line: `"User selected quiz app type with 4 teams named 1조-4조. Design palette: A."`

**Key Behaviors:**

1. Present 수련회 앱 메뉴판 (9 app types) in Korean
2. Detect app type through natural conversation
3. Collect content per Content Matrix (workflow.md Step 3)
4. Handle file input for large content sets (11+ items)
5. Present structure preview and wait for confirmation signal
6. During Phase 5: collect modification feedback. **Use `classify_modification()` from `_church_app_lib.py` (H2-3)** for deterministic classification BEFORE AI interpretation. Only use AI judgment when classifier returns `"uncertain"`.
7. During Phase 5: detect completion signal. **Use `detect_completion_signal()` from `_church_app_lib.py` (H2-4)** for deterministic Korean pattern matching. AI confirms, but the deterministic detector is the primary signal.
8. **Write English phase report** to `reports/` folder upon phase completion (AC-4)

**Conversation Rules (from workflow.md AC2):**
- Korean only (no English error messages, no tech jargon)
- Max 2 questions per turn
- Technical decisions automated (no "which database?")
- Result-oriented communication
- Progress indicator: `[1/3]`, `[2/3]`, `[3/3]`

**Output Format:**
```json
{
  "phase": 1,
  "step": "intent_detection",
  "result": {
    "app_type": "quiz",
    "team_count": 4,
    "team_names": ["1조", "2조", "3조", "4조"],
    "design_palette": "A",
    "features": ["buzzer", "score_board", "admin"],
    "admin_password": "1234"
  },
  "content": {
    "quiz_questions": [...],
    "team_colors": [...]
  },
  "confirmation": true
}
```

### 4.3 code-generator.md

```yaml
---
name: code-generator
description: "Full-stack code generator — HTML/CSS/JS + Node.js server + WebSocket for church retreat apps"
model: opus
tools: [Read, Write, Edit, Bash, Glob, Grep]
maxTurns: 80
---
```

**File Ownership (when in Agent Team):**
- `server.js`, `*.html` (structure/content), `app.js`, `routes/*.js`
- `data.json`, `package.json`, `regenerate-qr.js`
- NEVER touches: `styles.css`, `animations.css`, `manifest.json`, `service-worker.js` (owned by design-system)
- NEVER touches: `tests/*`, `verify-app.js` (owned by tdd-guard)

**Code Generation Order (from workflow.md Step 7) — Git messages in English (AC-4):**
```
[1] Project skeleton → Git checkpoint: "[init] Project skeleton created"
[2] Content insertion → Git checkpoint: "[content] {type} inserted"
[3] (delegated to design-system in team mode)
[4] Functionality — WebSocket, admin, offline → Git checkpoint: "[feature] {name} implemented"
[5] Polish — data export, error handling → Git checkpoint: "[polish] Final touches complete"
```

**English Report Output (AC-4):**
- Phase 2: writes `reports/phase2-architecture-plan.md` (project structure, tech stack decisions, dependency rationale)
- Phase 3: writes `reports/phase3-codegen-report.md` (code generation summary, files created, Git checkpoints)
- Phase 5 (fix): appends to `reports/phase5-modification-log.md` (change description, files modified, QA skip/re-run decision)

**Server Code Patterns (mandatory):**
```javascript
// 1. In-memory state + periodic JSON snapshot (NOT lowdb direct)
const state = { teams: {}, scores: {} };
setInterval(() => {
  fs.writeFileSync('data.json', JSON.stringify(state, null, 2));
}, 5000);

// 2. Native WebSocket (ws library) + HTTP polling fallback
// 3. Admin password protection for /admin
// 4. path.join() for all file paths (Korean path safety)
// 5. XSS sanitization for all user input
```

**Technology Stack Rules:**
- ALLOWED: express, ws, lowdb (read-only), qrcode, open
- FORBIDDEN: SQLite, node-gyp, Python-dependent, native compilation packages
- FONT: Pretendard subset (~50KB) + system font fallback
- ICONS: Inline SVG only (no external CDN)

### 4.4 design-system-agent.md

```yaml
---
name: design-system
description: "Design system specialist — CSS variables, animations, micro-interactions, PWA, dark mode for church retreat apps"
model: opus
tools: [Read, Write, Edit, Bash, Glob, Grep]
maxTurns: 40
---
```

**File Ownership (when in Agent Team):**
- `styles.css`, `animations.css`, `manifest.json`, `service-worker.js`
- PWA icons (192x192, 512x512 PNG generation)
- NEVER touches: `server.js`, `app.js`, `*.html` (structure), `tests/*`

**English Report Output (AC-4):** Contributes design section to `reports/phase3-codegen-report.md` (palette applied, animations count, PWA manifest details). In Agent Team mode, sends design summary to orchestrator via SendMessage; orchestrator compiles the final Phase 3 report.

**Design System Defaults (from workflow.md Step 6):**

```css
/* Palette A (default) */
--primary: #4F46E5;  --secondary: #10B981;
--gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Glassmorphism */
--glass-bg: rgba(255, 255, 255, 0.15);
--glass-blur: blur(12px);
--glass-border: 1px solid rgba(255, 255, 255, 0.2);

/* Typography — Pretendard subset */
--font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
--font-size-base: 16px;  --font-size-xl: 24px;  --font-size-3xl: 48px;

/* Spacing */
--radius: 16px;  --max-width: 480px;

/* Animation (REQUIRED) */
--transition-fast: 150ms ease-out;
--transition-normal: 250ms ease-out;
--transition-slow: 400ms ease-out;
```

**Mandatory Design Patterns:**
- D1: Card UI with border-radius >= 12px + box-shadow + glassmorphism
- D2: >= 2 transitions with duration >= 150ms + page transition
- D3: Dark mode via `prefers-color-scheme`
- D4: CSS variables only, 0 hardcoded colors
- D5: Fixed header + bottom tab nav (for 종합/퀴즈)
- D6: Font >= 16px body, >= 24px headings, Pretendard loaded
- D7: Button tap scale(0.95) + list stagger animation
- D8: Skeleton UI or spinner for data loading
- D9: Score change effects + confetti + sound (for /screen)

**PWA Implementation (from workflow.md Step 6):**
```json
// manifest.json
{
  "display": "standalone",
  "theme_color": "<palette primary>",
  "background_color": "#F9FAFB",
  "icons": [{"src": "icon-192.png", ...}, {"src": "icon-512.png", ...}],
  "start_url": "/",
  "name": "{수련회 이름} 앱",
  "short_name": "{수련회 이름}"
}
```

### 4.5 quality-checker.md

```yaml
---
name: quality-checker
description: "Automated quality verification — Q1-Q11 technical gates + D1-D9 design gates + app-type-specific gates"
model: opus
tools: [Read, Bash, Glob, Grep]
maxTurns: 40
---
```

**Execution Model — P1 Hallucination Prevention Protocol:**

> **CRITICAL: This agent NEVER "reasons about" whether a gate passes.**
> It calls deterministic Python scripts (§9.5) and reads the JSON results.
> The agent's role is LIMITED to: (1) running scripts, (2) reading PASS/FAIL results,
> (3) applying creative fixes for FAIL items, (4) re-running scripts to confirm fixes.

```
quality-checker workflow:
  [1] Run: python3 scripts/validate_gates.py --project-dir . --json
      → Read JSON output → DO NOT re-interpret. Trust the script.
  [2] Run: python3 scripts/validate_design_gates.py --project-dir . --json
      → Read JSON output → DO NOT re-interpret. Trust the script.
  [3] For each gate where "pass": false:
      → READ the "detail" field from JSON (exact failure reason)
      → APPLY a fix (this is the AI's creative contribution)
      → Re-run ONLY the specific gate script to confirm fix
  [4] Report all results to orchestrator
```

**English Report Output (AC-4):** Orchestrator compiles `reports/phase4-quality-report.md` from script JSON outputs (all gate results, pACS data, auto-fix actions, retry count). Also runs T1-T3 translation gates post-Phase 6.

When spawned by orchestrator in two-pass mode:
- **Pass 1 (Detection):** Runs scripts, collects JSON, reports PASS/FAIL — NO fixes
- **Pass 2 (Fix):** Receives FAIL list from orchestrator, fixes one gate at a time

**Gate Definitions (from workflow.md Step 8):**

| Gate | Pass Criteria | On Failure |
|------|--------------|------------|
| Q1 | HTTP 200 from localhost:PORT | Port change + retry |
| Q2 | No render-blocking HTML errors | Auto-fix + recheck |
| Q3 | 0 external scripts | Inline or remove |
| Q4 | Bundle <= 300KB target / <= 500KB hard limit (gzip) | Compress → split → reduce |
| Q5 | No broken Korean text | Add font fallback |
| Q6 | All buttons >= 44x44px | Auto-add min-height/width |
| Q7 | QR decodes to correct URL | Regenerate QR |
| Q8 | /admin requires password | Add auth middleware |
| Q9 | `<script>` in input neutralized | Add escape function |
| Q10 | (deferred to Phase 5 — human) | N/A |
| Q11 | WebSocket roundtrip <= 100ms | Optimize handlers |
| D1 | border-radius >= 12px + box-shadow + glass | CSS fix |
| D2 | >= 2 transitions >= 150ms + page transition | CSS fix |
| D3 | prefers-color-scheme media query exists | Add dark mode |
| D4 | CSS variables only, 0 hardcoded colors | Replace hardcoded |
| D5 | Fixed header + bottom tab (type-dependent) | HTML/CSS fix |
| D6 | font-size >= 16px body, >= 24px headings | CSS fix |
| D7 | Button tap scale + list stagger animation | CSS/JS fix |
| D8 | Skeleton UI or spinner present | Add loading UX |
| D9 | /screen effects + confetti + AudioContext | JS fix |

**Translation Quality Gates (AC-4 enforcement — checked after Phase 6):**

| Gate | Pass Criteria | Verification Method | On Failure |
|------|--------------|--------------------|-----------| 
| **T1** | Every `reports/phase*.md` has a corresponding `.ko.md` file | File existence check | Spawn @app-translator for missing files |
| **T2** | All translation pACS scores >= 70 (GREEN) | Read `pacs-logs/phase*-translation-pacs.md` | Re-translate weak sections (max 2 retries) |
| **T3** | All glossary terms used consistently across translations | Cross-search glossary.yaml terms in .ko files | @app-translator corrects inconsistent terms |

> T1-T3 are checked ONCE after Phase 6 deployment completes. They do NOT block individual phases.
> If all T-gates fail after retries, English originals remain valid — translation failure does not block deployment.

**App-Type-Specific Gates (from workflow.md):**

| App Type | Gate | Verification |
|----------|------|-------------|
| 성경 퀴즈 | 35-user buzzer simulation | 35 WS connections → simultaneous message → 0 drops |
| 종합 앱 | WS message type routing | quiz/score/lyrics messages route to correct handlers |
| 스탬프 랠리 | QR scan → mission auth | All mission QR decode to valid URLs |
| 찬양 가사 | Beam+phone sync | /screen and / show same lyrics simultaneously |
| 팀 점수판 | Admin → screen reflection | Score change on /admin reflects on /screen within 1s |

**Output Format:**
```json
{
  "gate_range": "Q1-Q6",
  "results": {
    "Q1": {"status": "PASS", "detail": "HTTP 200 on port 3000"},
    "Q2": {"status": "PASS", "detail": "No HTML errors"},
    "Q3": {"status": "FAIL", "detail": "Found external script: https://cdn.example.com/lib.js", "auto_fix": "inline"},
    ...
  },
  "overall": "FAIL",
  "fail_count": 1,
  "auto_fix_applied": true
}
```

### 4.6 deployment-manager.md

```yaml
---
name: deployment-manager
description: "Deployment specialist — LAN server, QR code, .bat file, WiFi detection, GitHub Pages for church retreat apps"
model: opus
tools: [Read, Write, Edit, Bash, Glob, Grep]
maxTurns: 40
---
```

**English Report Output (AC-4):** Writes `reports/phase6-deployment-report.md` (server URL, port, WiFi IP, QR path, .bat path, GitHub Pages URL if applicable, environment detection results).

**Deployment Steps:**
1. Environment detection (WiFi IP, available port, disk space, Korean path)
2. LAN server background execution (Bash `run_in_background`)
3. QR code PNG generation (correct URL)
4. Print-ready HTML page (A4, church name + QR + instructions)
5. "앱 실행.bat" creation on desktop
6. Emergency response card (A4 HTML)
7. Browser auto-open
8. (Optional) GitHub Pages deployment if user consented

**Port Selection Order:** 3000 → 3009 → 8080 → 49152 → 49162

**WiFi IP Detection:**
```javascript
// Priority: hotspot (192.168.137.x) > regular WiFi (192.168.x.x)
const os = require('os');
const interfaces = os.networkInterfaces();
// ... detect and prioritize
```

### 4.7 tdd-guard.md

```yaml
---
name: tdd-guard
description: "TDD automation agent — writes tests before code, validates test-first development cycle, generates verify-app.js"
model: sonnet
tools: [Read, Write, Edit, Bash, Glob, Grep]
maxTurns: 30
---
```

**TDD Cycle:**
```
[RED]    tdd-guard writes failing tests first
           → tests/test_server.js, tests/test_routes.js, etc.
           → Run tests → confirm ALL FAIL (expected behavior)

[GREEN]  code-generator implements minimum code to pass tests
           → Run tests → confirm ALL PASS

[REFACTOR] quality-checker verifies code quality
           → Tests still pass + quality gates pass
```

**Test Categories:**

| Category | Test File | What It Tests |
|----------|-----------|--------------|
| Server | `tests/test_server.js` | HTTP responses, port binding, static serving |
| WebSocket | `tests/test_websocket.js` | Connection, message routing, broadcast, reconnection |
| Admin | `tests/test_admin.js` | Password protection, unauthorized access rejection |
| Content | `tests/test_content.js` | Korean text rendering, content insertion correctness |
| Security | `tests/test_security.js` | XSS prevention, input sanitization |
| Bundle | `tests/test_bundle.js` | File sizes, no external dependencies |
| PWA | `tests/test_pwa.js` | manifest.json validity, service worker registration |

**verify-app.js Generation:**

tdd-guard generates `verify-app.js` — a unified verification script that runs all Q1-Q11 + D1-D9 gates in a single execution:

```javascript
// verify-app.js (generated by tdd-guard)
// Runs ALL quality gates and returns JSON report
// Usage: node verify-app.js
// Output: { "Q1": "PASS", ..., "D9": "FAIL:reason", "overall": "PASS|FAIL" }
```

### 4.8 app-translator.md

```yaml
---
name: app-translator
description: "English-to-Korean translation specialist for church retreat app workflow — creates .ko pairs for all English-first artifacts with glossary-based consistency"
model: opus
tools: [Read, Write, Glob, Grep]
maxTurns: 25
---
```

**Inherited DNA:** This agent inherits the complete translation protocol from the parent `translator.md` (AgenticWorkflow genome). The 7-step protocol (Load Glossary → Read Source → Translate → Self-Review + pACS → Update Glossary → Write Output → Write pACS Log) is executed identically.

**Church-App Domain Additions:**
- Domain glossary: `translations/church-app-glossary.yaml` (merged with parent `translations/glossary.yaml`)
- Domain terms: 수련회, 버저, 팀 점수판, 성경 퀴즈, QT 가이드, 스탬프 랠리, etc.

**Translation Protocol (inherited from parent translator.md):**
```
Step 1: Load translations/glossary.yaml + translations/church-app-glossary.yaml
Step 2: Read English source file completely
Step 3: Translate with quality standards (terminology, style, structure)
Step 4: Self-Review + Translation pACS (Ft/Ct/Nt) — Pre-mortem Protocol
Step 5: Update glossary with new terms
Step 6: Write .ko.md file (same directory as English original)
Step 7: Write pACS log to pacs-logs/
```

**File Classification — What to Translate vs Skip:**

```python
TRANSLATE = [
    "reports/*.md",          # Phase reports (English originals)
]

NEVER_TRANSLATE = [
    "*.js", "*.css", "*.html",   # Code files
    "*.json", "*.yaml",          # Config/data files
    "*.bat",                     # Batch files (already Korean)
    "*.png", "*.jpg",            # Images
    "app-state.json",            # SOT
    "glossary.yaml",             # Glossary itself
    "verify-app.js",             # Verification script
    "tests/*",                   # Test files
    "reports/*.ko.md",           # Already-translated files
]
```

**Output Format:**
```
English original:  reports/phase3-codegen-report.md
Korean translation: reports/phase3-codegen-report.ko.md
pACS log:          pacs-logs/phase3-translation-pacs.md
```

**Translation pACS Dimensions:**

| Dimension | Name | What It Measures |
|-----------|------|-----------------|
| Ft | Fidelity | Accuracy of meaning transfer from English to Korean (0-100) |
| Ct | Translation Completeness | No paragraphs, sentences, or footnotes omitted (0-100) |
| Nt | Naturalness | Reads as originally authored Korean, not translated text (0-100) |

**Scoring:** `Translation pACS = min(Ft, Ct, Nt)`

| Score | Color | Action |
|-------|-------|--------|
| >= 70 | GREEN | Proceed — translation accepted |
| 50-69 | YELLOW | Proceed with flag in SOT |
| < 50 | RED | Re-translate weak sections (max 2 retries) |

**Execution Mode — Phase 1 BLOCKING + Phase 2-6 DEFERRED BATCH (A3-3 optimization):**

```
Phase 1 translation: BLOCKING (template validation)
  → First translation validates the template quality.
  → If pACS >= 70 (GREEN): translation pipeline is proven → proceed.
  → If pACS < 70: re-translate until GREEN (max 2 retries).
  → Orchestrator waits for Phase 1 translation to complete before Phase 2.

Phase 2-6 translations: DEFERRED BATCH (after Phase 6 deployment)
  → During Phases 2-6: NO translation agent is spawned. Zero overhead.
  → English reports are written to reports/ folder as each phase completes.
  → After Phase 6 deployment completes, orchestrator spawns @app-translator ONCE:
    "Translate ALL reports/phase2-*.md through phase6-*.md to Korean .ko pairs."
  → Single batch translation is more efficient than 5 separate spawns.
  → Translation quality verified by T1-T3 gates immediately after batch completes.

WHY DEFERRED BATCH (A3-3):
  → 사역자 never reads phase reports — they are internal artifacts.
  → Spawning @app-translator 5 times during workflow execution adds latency and token cost
    with zero user-visible benefit.
  → Single batch after deployment: same quality, 5× fewer agent spawns.
  → Phase 1 BLOCKING is preserved (template validation still needed early).
```

**Fallback:** If @app-translator fails, the orchestrator applies the standard fallback tiers: Tier 2 (retry as sequential sub-agent) → Tier 3 (orchestrator translates directly) → Tier 4 (skip translation, note in SOT). English originals always exist regardless of translation status.

---

## 5. Agent Teams Configuration

### 5.1 Environment Setup

**Required setting** in `~/.claude.json` (or project `.claude/settings.json`):

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 5.2 Phase 3 — Code Generation Team (종합 앱 3+ features ONLY)

> **This section applies ONLY when `choose_execution_mode()` returns `"agent_team"`.**
> For single apps (types 1-8) and small combinations, the DEFAULT is sequential
> execution (§5.4 Tier 2 Protocol). Agent Team is an UPGRADE for complex 종합 앱,
> not the default. See ADR-012 for the quality rationale.

```
Team Name: "code-gen-team"
Team Lead: orchestrator (spawns and coordinates)

Teammates:
  [A] code-generator   → HTML structure + JS logic + server code
  [B] design-system    → CSS + animations + PWA manifest + service worker
  [C] tdd-guard        → Test suite generation + verify-app.js

Task List (with dependencies):
  T1: "Create project skeleton"           → Owner: A
  T2: "Setup design system CSS variables"  → Owner: B
  T3: "Write skeleton tests"              → Owner: C, blockedBy: [T1]
  T4: "Insert content into HTML"          → Owner: A, blockedBy: [T1]
  T5: "Implement styling & animations"    → Owner: B, blockedBy: [T2]
  T6: "Implement WebSocket & functionality"→ Owner: A, blockedBy: [T4]
  T7: "Write functionality tests"         → Owner: C, blockedBy: [T6]
  T8: "Implement PWA (manifest + SW)"     → Owner: B, blockedBy: [T5]
  T9: "Copy P1 template scripts to project"→ Owner: C, blockedBy: [T7, T8]
       (verify-app.js removed — orchestrator calls P1 scripts directly, §9.4)
  T10: "Polish & error handling"          → Owner: A, blockedBy: [T6]

  T11: "Integration verification (P1 deterministic)"  → Owner: orchestrator, blockedBy: [T9, T10]
       Purpose: Post-merge quality check via deterministic Python script.
       Execution:
         orchestrator runs: python3 scripts/validate_integration.py --project-dir . --json
       The script deterministically checks (NO AI reasoning):
         - Every CSS class referenced in HTML exists in styles.css/animations.css
         - Every DOM element referenced in JS exists in HTML
         - Every route in manifest.json start_url exists as a file/endpoint
         - Every WebSocket message type in client JS has a handler in server.js
         - Service worker caches all actual static assets (no missing files)
       On failure: orchestrator READS the JSON failure detail (exact orphan list),
                   spawns the responsible teammate to fix ONLY the listed items,
                   then re-runs the script. Max 3 cycles.
       P1 compliance: AI never "looks at files to judge" — script outputs exact gaps.

File Conflict Prevention:
  A owns: server.js, *.html (structure), app.js, routes/*.js, data.json
  B owns: styles.css, animations.css, manifest.json, service-worker.js, icons/
  C owns: tests/*, verify-app.js
  Shared read-only: app-state.json, package.json

Git Strategy (AC-4 — English commit messages):
  Each teammate commits to the SAME branch with prefixed messages:
    A: "[code] ..."
    B: "[design] ..."
    C: "[test] ..."
  Orchestrator resolves any merge issues after team completes.
```

### 5.3 Phase 4 — Two-Pass Quality Verification (Quality-Driven Design)

> **Why 2-pass instead of parallel auto-fix?**
> If 3 forks each auto-fix simultaneously, Fix A may conflict with Fix B (e.g., A deletes code for bundle size, B optimizes the same code for latency). Sequential fixing ensures each fix accounts for all prior fixes. **Quality of the fix** > speed of detection.

```
PASS 1 — Deterministic DETECTION (P1 scripts, NO AI reasoning):
  Purpose: Identify all PASS/FAIL gates with 100% accuracy, zero hallucination.
  Method: Orchestrator directly runs Python scripts via Bash tool.
          No @quality-checker agent needed for detection — scripts are deterministic.

  PRE-CONDITION — Server Startup (DG-4):
    Q1, Q8, Q9, Q11 require a running HTTP/WebSocket server.
    Orchestrator starts the server BEFORE running P1 scripts:
      node server.js &    (background, via Bash run_in_background)
      sleep 2             (wait for server to bind port)
      → If server fails to start: log error, skip Q1/Q8/Q9/Q11, mark as FAIL
    After all P1 scripts complete:
      kill server process  (cleanup via port-based process lookup)
    For STATIC apps (no server.js): skip Q1/Q8/Q9/Q11 (not applicable)

  orchestrator runs (sequentially — order matters for server-dependent gates):
    python3 scripts/validate_gates.py --project-dir . --json
    python3 scripts/validate_design_gates.py --project-dir . --json
    python3 scripts/validate_app_specific.py --project-dir . --type {app_type} --json
    python3 scripts/validate_content_insertion.py --project-dir . --json

  POST-CONDITION — Server Shutdown:
    orchestrator kills background server process

  → orchestrator merges all JSON outputs → unified detection report
  → ZERO AI reasoning involved in detection. Pure deterministic computation.
  → This is the hallucination prevention core: scripts measure, not agents.

PASS 2 — Sequential AUTO-FIX (orchestrator-directed, one at a time):
  Purpose: Fix each failing gate in isolation, verifying after each fix.
  Constraint: One fix at a time. Re-verify affected gates after each fix.

  for each FAIL gate in priority order (Q-gates first, then D-gates):
      orchestrator spawns @quality-checker:
          "Fix gate {gate_id}: {failure_detail}.
           Apply minimal fix. Re-run this gate to confirm PASS.
           Also re-run any gates that could be affected by this fix."
      → if fix succeeds: mark gate PASS, continue to next FAIL
      → if fix fails after 3 retries: log failure, continue to next FAIL
      → if 3+ gates remain unfixable: Git rollback → report to user

  → orchestrator writes final quality report to SOT
```

### 5.4 Tier 2: Sequential Sub-agent Protocol (DEFAULT for Phase 3)

> **This is the DEFAULT execution path for Phase 3.**
> Used for app types 1-8 and small 종합 앱 (<3 features).
> Also the FALLBACK when Agent Team fails.

```
Sequential Execution Order:
  Each agent runs AFTER the previous one completes.
  Each agent CAN READ all files written by previous agents.
  This eliminates integration gaps entirely.

  STEP A: @tdd-guard — Write BEHAVIORAL tests FIRST (TDD RED)  [DG-3]
    Input:  SOT (app_type, features, content)
    Action: Generate BEHAVIORAL test files — tests that define WHAT the app does,
            NOT how it looks. These tests can be written without seeing any code.
    Test Scope (Step A — behavioral only):
      ✅ test_server.js:    "GET / returns 200" (HTTP behavior)
      ✅ test_admin.js:     "GET /admin without auth returns 401" (auth behavior)
      ✅ test_security.js:  "POST <script> returns sanitized" (security behavior)
      ✅ test_websocket.js: "WS connect succeeds" (connection behavior)
      ✅ test_content.js:   "Response body contains Korean text" (content presence)
      ✅ test_bundle.js:    "Total file size < 500KB" (size constraint)
      ❌ test_integration:  DEFERRED to Step D (needs HTML/CSS to exist)
      ❌ test_pwa.js:       DEFERRED to Step D (needs manifest.json to exist)
    Output: tests/*.js (behavioral only — all FAIL at this point)
    Git:    "[test] RED — behavioral test suite created"

  STEP B: @code-generator — Implement code (TDD GREEN)
    Input:  SOT + tests/*.js (reads test expectations) + reports/phase2-*.md
    Action: Write HTML structure, server.js, app.js, routes, content insertion
            Must pass ALL tests from Step A
    Output: server.js, *.html, app.js, routes/*.js, data.json, package.json
    Git:    "[code] GREEN — implementation passes tests"

  STEP C: @design-system — Apply design (reads Step B output)
    Input:  ALL files from Step B (reads actual HTML structure, class names, IDs)
    Action: Write CSS that matches EXACT HTML from Step B
            Animations for EXACT DOM elements from Step B
            manifest.json with CORRECT routes from Step B
            service-worker.js caching ACTUAL files from Step B
    Output: styles.css, animations.css, manifest.json, service-worker.js, icons/
    Git:    "[design] Design system applied"
    NOTE:   ZERO integration gaps because design-system SEES code-generator's output

  STEP D: @tdd-guard — Add STRUCTURAL tests + verify + copy P1 scripts  [DG-3]
    Input:  ALL files from Steps A+B+C
    Action:
      D.1: Add STRUCTURAL tests (now possible — HTML/CSS/JS exist):
           ✅ test_pwa.js:        manifest.json validity, SW registration
           ✅ test_integration.js: CSS classes match HTML, JS refs match DOM
           These tests could NOT be written in Step A (code didn't exist).
      D.2: Run ALL tests (behavioral from Step A + structural from D.1) → confirm PASS
      D.3: Copy P1 template scripts from .claude/skills/.../templates/scripts/ → project/scripts/
      D.4: Start server (background) → Run P1 scripts as pre-check → Stop server
           (same server startup protocol as Phase 4 — DG-4)
    Output: tests/*.js (complete), scripts/*.py (copied), test report
    Git:    "[test] REFACTOR — all tests pass, P1 scripts ready"

Context Passing Between Steps:
  Each agent is spawned with a prompt that includes:
    - Current SOT contents (app-state.json)
    - List of files created by previous steps
    - Phase-specific section from workflow.md
    - §4 AC-4 Common Rules (English-First)
  Agent reads the actual files from disk — no context relay needed.
  This is why sequential quality > parallel quality for tightly-coupled code.

Git Strategy:
  Single branch. Each step commits with prefixed message.
  Orchestrator can rollback to any step's checkpoint.
  Full history: [test] RED → [code] GREEN → [design] applied → [test] REFACTOR

Integration Verification:
  NOT NEEDED in sequential mode.
  Step C (@design-system) reads Step B's output directly.
  Step D (@tdd-guard) verifies everything together.
  T-3.11 validate_integration.py is still RUN as a safety net,
  but in practice it finds 0 issues in sequential mode.
```

### 5.5 Fork Usage Strategy

| Use Case | Fork Purpose | When |
|----------|-------------|------|
| Phase 3 design | A/B palette comparison | When user didn't specify preference strongly |
| Phase 4 verification | Two-pass: P1 script detection → sequential AI fix | Always |
| Phase 5 modification | Simulate change before apply | Feature additions (type B mods) |
| TDD cycle | Test-first in isolated branch | Every code generation sub-step |

---

## 6. Fallback System

### 6.1 Fallback Tiers

```
Tier 1: Agent Team (parallel execution)
  │ Failure conditions:
  │  • Teammate unresponsive for > 5 minutes
  │  • Task dependency deadlock
  │  • File conflict between teammates
  │  • Agent Teams feature unavailable
  │
  ▼
Tier 2: Sequential Sub-agents (one at a time)
  │ Failure conditions:
  │  • Sub-agent returns error after 3 retries
  │  • Sub-agent output fails validation
  │  • Sub-agent exceeds maxTurns
  │
  ▼
Tier 3: Orchestrator Direct Execution
  │ Failure conditions:
  │  • Orchestrator itself cannot complete the task
  │  • Context window overflow
  │  • Unrecoverable code generation error
  │
  ▼
Tier 4: Human Escalation
  → Present issue to user in Korean
  → Offer specific action choices
  → Wait for user decision
```

### 6.2 Fallback Detection & Transition

```python
# Pseudocode for fallback logic in orchestrator

MAX_RETRIES_PER_TIER = 3

def execute_with_fallback(phase, tier=1):
    for attempt in range(MAX_RETRIES_PER_TIER):
        try:
            if tier == 1:
                result = run_agent_team(phase)
            elif tier == 2:
                result = run_sequential_subagents(phase)
            elif tier == 3:
                result = run_orchestrator_direct(phase)
            elif tier == 4:
                result = escalate_to_human(phase)
                return result  # human always succeeds (or aborts)
            
            validate_result(result)
            return result
        
        except (AgentTimeout, AgentError, ValidationError) as e:
            log_fallback_event(tier, attempt, e)
            # A1-2: ALWAYS show Korean progress message during retries
            notify_user_korean(f"잠깐 다시 해보고 있어요. 조금만 기다려 주세요. ({attempt+1}/3)")
            if attempt == MAX_RETRIES_PER_TIER - 1:
                # Escalate to next tier
                write_sot_fallback(tier, tier + 1, str(e))
                return execute_with_fallback(phase, tier + 1)
```

### 6.3 Specific Fallback Scenarios

| Scenario | Detection | Fallback Action |
|----------|-----------|----------------|
| Agent Team feature not available | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` not set | Skip to Tier 2 (sequential) immediately |
| Teammate idle > 5 min | TeammateIdle hook | Reassign task to another teammate or Tier 2 |
| File conflict in team | Git merge conflict detected | Orchestrator resolves conflict manually |
| Quality gate fails 3x | retry_count >= 3 in SOT | Git rollback to last checkpoint → report to user |
| npm install fails | Non-zero exit code | Mirror registry → offline install → Tier 4 |
| Port all occupied | All 3000-3009, 8080, 49152-49162 fail | Prompt user to close conflicting program |
| Context window overflow | Compact triggered | Save state to SOT → resume from checkpoint |
| @app-translator fails | Sub-agent error or pACS RED after 2 retries | Tier 2 (retry sequential) → Tier 3 (orchestrator translates directly) → Tier 4 (skip translation, English originals remain) |
| Translation .ko file malformed | validate_translation_pair.py exit 2 | @app-translator re-translates the specific file (max 2 retries) |

---

## 7. Hooks Configuration

### 7.1 Inherited Hooks (from AgenticWorkflow)

These hooks are already defined in `.claude/settings.json` and are inherited as-is:

| Event | Script | Purpose |
|-------|--------|---------|
| PreToolUse(Bash) | `block_destructive_commands.py` | Block dangerous commands |
| PreToolUse(Edit\|Write) | `block_test_file_edit.py` | TDD guard — protect test files |
| PreToolUse(Edit\|Write) | `predictive_debug_guard.py` | Warn on error-prone files |
| PostToolUse(Bash\|Read) | `output_secret_filter.py` | Detect secrets in output |
| PostToolUse(Edit\|Write) | `security_sensitive_file_guard.py` | Warn on security file edits |
| Stop | `context_guard.py --mode=stop` | Context snapshot |
| PreCompact | `context_guard.py --mode=pre-compact` | Save before compression |
| SessionStart | `context_guard.py --mode=restore` | Restore context |
| SessionEnd | `save_context.py` | Full snapshot on /clear |

### 7.2 New Workflow-Specific Hooks

| Event | Script | Purpose | Exit Code |
|-------|--------|---------|-----------|
| PreToolUse(Write\|Edit) | `sot_write_guard.py` | **Block non-orchestrator writes to app-state.json** — enforces AC-2 single-writer rule structurally | 2 = block |
| PreToolUse(Bash) | `validate_ac_constraints.py` | Enforce AC1 (no external data transfer), AC4 (no ngrok/tunnel) | 2 = block |
| PostToolUse(Write\|Edit) | `enforce_design_system.py` | Detect hardcoded CSS colors (D4 violation prevention) | 0 = warn |
| PostToolUse(Write\|Edit) | `bundle_size_guard.py` | Check cumulative project size against 500KB limit | 2 = block if > 500KB |
| TaskCompleted | `quality_gate_check.py` | Run relevant quality gates after task completion | 2 = block + feedback |
| TeammateIdle | `teammate_health_check.py` | Detect idle teammates, trigger fallback | 0 = log |
| Stop | `sot_snapshot.py` | Snapshot app-state.json with timestamp | 0 |
| PreToolUse(Write\|Edit) | `file_ownership_guard.py` | **Agent Team file ownership enforcement** — blocks teammate from writing files owned by another teammate (§5.2 ownership map) | 2 = block |
| PostToolUse(Write) | `validate_translation_pair.py` | Verify .ko file matches English original structure (section count, code blocks untranslated, glossary terms) | 0 = warn, 2 = block if critical |

### 7.3 Hook Implementation Details

**_church_app_lib.py — Shared Library for ALL Church-App Hooks:**
```python
"""
Shared utility library for church-retreat-app workflow hooks.
Lives at: .claude/hooks/scripts/_church_app_lib.py

WHY a separate library (not extending _context_lib.py):
  _context_lib.py is the PARENT genome's shared library — used by
  autobiography-generator and all other workflows. Modifying it
  would create a ripple effect across the entire AgenticWorkflow project.
  _church_app_lib.py is church-app-specific, imports FROM _context_lib
  where needed, and adds church-app-specific utilities.

Dependencies: _context_lib.py (read-only import for atomic_write, capture_sot)
"""

import json
import sys
import os

# Re-export from parent library (verified to exist)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _context_lib import atomic_write  # only import what we actually use (A2-3 fix)

def parse_tool_input():
    """Parse Claude Code hook stdin JSON. Returns (tool_name, tool_input) tuple.
    All PreToolUse/PostToolUse hooks receive JSON on stdin."""
    try:
        data = json.load(sys.stdin)
        return data.get("tool_name", ""), data.get("tool_input", {})
    except (json.JSONDecodeError, IOError):
        return "", {}

def get_agent_name():
    """Read current agent name from CLAUDE_AGENT_NAME env var."""
    return os.environ.get("CLAUDE_AGENT_NAME", "unknown")

def get_project_dir():
    """Read project directory from CLAUDE_PROJECT_DIR env var."""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def read_sot(project_dir=None):
    """Read app-state.json from project folder. Returns dict or None."""
    pdir = project_dir or get_project_dir()
    sot_path = os.path.join(pdir, "app-state.json")
    if not os.path.exists(sot_path):
        return None
    with open(sot_path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_agent_team_active(project_dir=None):
    """Check if Agent Team mode is active (from SOT)."""
    sot = read_sot(project_dir)
    if sot and "status" in sot:
        return sot["status"].get("agent_team_active", False)
    return False

def match_file_pattern(filepath, patterns):
    """Check if filepath matches any glob-like pattern in the list."""
    import fnmatch
    basename = os.path.basename(filepath)
    for pattern in patterns:
        if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(filepath, pattern):
            return True
    return False

# --- H2-3: Deterministic modification classifier (Phase 5) ---

# Keyword patterns for each modification type.
# AI orchestrator calls classify_modification(user_text) FIRST,
# then only uses AI judgment if classification is UNCERTAIN.
STYLE_PATTERNS = [
    r'색상|색깔|컬러|color|배경|background|글씨|폰트|font|크기|size|굵기|bold',
    r'간격|margin|padding|둥글|radius|그림자|shadow|투명|opacity',
    r'다크\s?모드|dark\s?mode|밝[게기]|어둡[게기]|테마|theme',
]
FEATURE_PATTERNS = [
    r'추가|넣어|만들어|기능|타이머|timer|버튼|button|페이지|page',
    r'실시간|websocket|알림|notification|소리|sound|효과음|effect',
    r'점수|score|랭킹|ranking|순위|팀|team|새로운|new',
]
ROLLBACK_PATTERNS = [
    r'아까|이전|전[에으]|돌려|되돌|롤백|rollback|원래|처음|복구|restore',
]

import re

def classify_modification(user_text):
    """Deterministic Phase 5 modification classifier (H2-3).
    Returns: ("A", "style") | ("B", "feature") | ("C", "rollback") | ("?", "uncertain")
    AI should ONLY be consulted when result is ("?", "uncertain").
    This prevents: style change misclassified as feature (unnecessary QA re-run)
                   feature change misclassified as style (QA skip = quality risk)
    """
    text = user_text.lower()
    rollback_score = sum(1 for p in ROLLBACK_PATTERNS if re.search(p, text))
    feature_score = sum(1 for p in FEATURE_PATTERNS if re.search(p, text))
    style_score = sum(1 for p in STYLE_PATTERNS if re.search(p, text))
    
    if rollback_score > 0 and rollback_score >= feature_score:
        return ("C", "rollback")
    if feature_score > style_score:
        return ("B", "feature")
    if style_score > 0:
        return ("A", "style")
    return ("?", "uncertain")  # AI fallback

# --- H2-4: Deterministic completion signal detector (Phase 5) ---

COMPLETION_SIGNALS = [
    r'완성', r'좋아요', r'이대로', r'시작해', r'끝', r'괜찮', r'오케이', r'ok',
    r'배포', r'deploy', r'이걸로', r'충분', r'만족', r'진행',
]

# A1-5 FIX: Negative trailing patterns that NEGATE a completion signal.
# "괜찮은데 버튼이..." = NOT complete. "좋아요 근데..." = NOT complete.
NEGATION_TRAILING = [
    r'인데', r'지만', r'근데', r'그런데', r'대신', r'말고',
    r'하지만', r'그래도', r'다만', r'대신에',
]

def detect_completion_signal(user_text):
    """Deterministic Phase 5 completion signal detector (H2-4, A1-5 fix).
    Returns: True ONLY if completion pattern found AND no negation trailing pattern.
    
    CRITICAL: Even when True, orchestrator MUST ask explicit confirmation
    before Phase 6 transition: "이대로 배포할까요? (네/아니요)"
    This prevents false-positive premature deployment.
    """
    text = user_text.lower().strip()
    has_signal = any(re.search(p, text) for p in COMPLETION_SIGNALS)
    if not has_signal:
        return False
    has_negation = any(re.search(p, text) for p in NEGATION_TRAILING)
    return not has_negation  # "괜찮은데..." → False, "괜찮아요!" → True
```

**file_ownership_guard.py:**
```python
"""
PreToolUse(Write|Edit) hook — enforces Agent Team file ownership rules (§5.2).

Only active when agent_team_active is true in app-state.json.
When inactive (non-team phases), all writes pass through (exit 0).

Ownership map (from §5.2):
  code-generator:  server.js, *.html, app.js, routes/*.js, data.json, package.json
  design-system:   styles.css, animations.css, manifest.json, service-worker.js, icons/*
  tdd-guard:       tests/*, verify-app.js
  orchestrator:    app-state.json (also protected by sot_write_guard.py)
  app-translator:  reports/*.ko.md, pacs-logs/*.md, translations/*.yaml

Detection: reads CLAUDE_AGENT_NAME env var + tool_input.file_path from stdin JSON.
If file_path matches another teammate's ownership pattern → exit 2 + stderr explanation.

Dependency: from _church_app_lib import parse_tool_input (church-app shared library)
Input: JSON on stdin with {"tool_name": "Write|Edit", "tool_input": {"file_path": "..."}}
Output: exit 0 (allowed or non-team mode) or exit 2 + stderr (ownership violation)
"""

OWNERSHIP_MAP = {
    "code-generator": ["server.js", "*.html", "app.js", "routes/*.js", "data.json", "package.json", "regenerate-qr.js"],
    "design-system":  ["styles.css", "animations.css", "manifest.json", "service-worker.js", "icons/*"],
    "tdd-guard":      ["tests/*", "verify-app.js", "scripts/*"],
    "app-translator": ["reports/*.ko.md", "pacs-logs/*", "translations/*.yaml"],
}
```

**sot_write_guard.py:**
```python
"""
PreToolUse(Write|Edit) hook — enforces AC-2 SOT single-writer rule.

Blocks ANY Write or Edit operation targeting app-state.json UNLESS the caller
is the orchestrator agent. This is the structural enforcement of the
"Orchestrator ONLY — exclusive write access" rule.

Detection method:
  - Reads tool_input.file_path from stdin JSON
  - If file_path ends with "app-state.json" → check caller identity
  - Caller identity: reads CLAUDE_AGENT_NAME env var (set by Claude Code runtime)
  - If caller is "church-app-orchestrator" → allow (exit 0)
  - If caller is any other agent → block (exit 2 + stderr explanation)
  - If file_path is NOT app-state.json → allow (exit 0, not our concern)

Input: JSON on stdin with {"tool_name": "Write|Edit", "tool_input": {"file_path": "..."}}
Output: exit 0 (allow) or exit 2 + stderr (block with explanation)
"""

from _church_app_lib import parse_tool_input  # church-app shared library

SOT_FILENAME = "app-state.json"
ALLOWED_WRITERS = ["church-app-orchestrator"]
```

**validate_ac_constraints.py:**
```python
"""
PreToolUse(Bash) hook — enforces workflow.md Absolute Constraints.

Blocks:
  AC1: External data transfer (curl, wget to non-localhost, ngrok, tunnel)
  AC4: Security violations (API keys in generated code)

Input: JSON on stdin with {"tool_name": "Bash", "tool_input": {"command": "..."}}
Output: exit 0 (allow) or exit 2 + stderr message (block)
"""

from _church_app_lib import parse_tool_input  # church-app shared library

BLOCKED_PATTERNS = [
    r'ngrok',
    r'localtunnel',
    r'cloudflared',
    r'curl\s+(?!.*localhost)(?!.*127\.0\.0\.1)',
    r'wget\s+(?!.*localhost)(?!.*127\.0\.0\.1)',
]
# Exception: npm registry, GitHub API (for Pages deployment)
ALLOWED_EXCEPTIONS = [
    r'npm\s+(install|ping|config)',
    r'gh\s+(repo|api|auth)',
    r'git\s+(push|pull|clone|fetch)',
]
```

**enforce_design_system.py:**
```python
"""
PostToolUse(Write|Edit) hook — detects hardcoded CSS colors.

Scans modified CSS/HTML files for color values not using CSS variables.
Reports warnings (does not block).

Input: JSON on stdin with {"tool_name": "Write", "tool_input": {"file_path": "..."}}
Output: exit 0 + stderr warning if violations found
"""

from _church_app_lib import parse_tool_input  # church-app shared library

HARDCODED_COLOR_PATTERN = r'(?<!var\()#[0-9A-Fa-f]{3,8}\b'
CSS_VARIABLE_PATTERN = r'var\(--[\w-]+\)'
```

**bundle_size_guard.py:**
```python
"""
PostToolUse(Write|Edit) hook — enforces bundle size limits.

Measures total project size (excluding node_modules, .git, tests).
Target: 300KB. Hard limit: 500KB.

Input: JSON on stdin
Output: exit 0 (under limit) or exit 2 (over hard limit)
         stderr warning if over target but under hard limit
"""

from _church_app_lib import parse_tool_input  # church-app shared library

TARGET_KB = 300
HARD_LIMIT_KB = 500
EXCLUDE_DIRS = ['node_modules', '.git', 'tests', 'archives', 'results', 'reports', 'pacs-logs']
```

**quality_gate_check.py:**
```python
"""
TaskCompleted hook — runs quality gates relevant to the completed task.

Maps task subjects to gate ranges and executes verify-app.js with filters.
Only runs when the project has verify-app.js generated.

Input: JSON on stdin with task metadata
Output: exit 0 (pass) or exit 2 + stderr feedback (fail)
"""
```

**teammate_health_check.py:**
```python
"""
TeammateIdle hook — monitors teammate activity.

Checks if any teammate has been idle for > 300 seconds.
Logs the event and prints recommendation to stderr.

Input: JSON on stdin with teammate info
Output: exit 0 + stderr warning
"""

from _church_app_lib import parse_tool_input  # church-app shared library

IDLE_THRESHOLD_SECONDS = 300
```

**sot_snapshot.py:**
```python
"""
Stop hook — creates timestamped snapshot of app-state.json.

Copies app-state.json to .claude/context-snapshots/app-state-{timestamp}.json
Keeps last 10 snapshots, deletes older ones.

Input: None (reads project dir from CLAUDE_PROJECT_DIR)
Output: exit 0
"""

from _church_app_lib import atomic_write  # church-app shared library (wraps _context_lib.atomic_write)

MAX_SNAPSHOTS = 10
```

**validate_translation_pair.py:**
```python
"""
PostToolUse(Write) hook — validates Korean translation files (.ko.md).

Triggered when @app-translator writes a .ko.md file.
Performs structural verification against the English original.

Checks:
  1. Section count in .ko.md == section count in English original
  2. Code blocks in .ko.md are NOT translated (must match English exactly)
  3. All glossary.yaml terms are used consistently
  4. No empty sections (translation completeness)

Input: JSON on stdin with {"tool_name": "Write", "tool_input": {"file_path": "...ko.md"}}
Output: exit 0 (pass or non-.ko file) or exit 2 + stderr (critical mismatch)

Only activates for files matching pattern: *.ko.md
Other files pass through with exit 0 immediately.
"""

from _church_app_lib import parse_tool_input  # church-app shared library

GLOSSARY_PATH = "translations/glossary.yaml"
CHURCH_GLOSSARY_PATH = "translations/church-app-glossary.yaml"
```

### 7.4 Complete settings.json — New Hook Entries (Final)

> **This is the COMPLETE list of new hook entries to APPEND to the existing settings.json.**
> Array order = execution priority. Within the same event, hooks execute top-to-bottom.
> If a hook returns exit 2 (deny), subsequent hooks for the same event still run but the tool call is blocked.

```jsonc
// APPEND these entries to the existing arrays in .claude/settings.json "hooks":
// Existing hooks (inherited from AgenticWorkflow) are UNCHANGED — these are ADDITIONS.

{
  "hooks": {
    "PreToolUse": [
      // --- EXISTING (do not modify): block_destructive_commands.py, block_test_file_edit.py, predictive_debug_guard.py ---
      
      // [NEW #1 — HIGHEST PRIORITY] SOT single-writer enforcement (AC-2)
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/sot_write_guard.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/sot_write_guard.py; fi",
          "timeout": 5
        }]
      },
      // [NEW #2] Agent Team file ownership enforcement (§5.2)
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/file_ownership_guard.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/file_ownership_guard.py; fi",
          "timeout": 5
        }]
      },
      // [NEW #3] Absolute constraint enforcement (AC1/AC4)
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/validate_ac_constraints.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/validate_ac_constraints.py; fi",
          "timeout": 10
        }]
      }
    ],
    "PostToolUse": [
      // --- EXISTING (do not modify): context_guard.py, output_secret_filter.py, security_sensitive_file_guard.py ---
      
      // [NEW #4] Design system compliance warning (D4)
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/enforce_design_system.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/enforce_design_system.py; fi",
          "timeout": 10
        }]
      },
      // [NEW #5] Bundle size enforcement (Q4)
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/bundle_size_guard.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/bundle_size_guard.py; fi",
          "timeout": 10
        }]
      },
      // [NEW #6] Translation pair structural validation (AC-4)
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/validate_translation_pair.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/validate_translation_pair.py; fi",
          "timeout": 15
        }]
      }
    ],
    "Stop": [
      // --- EXISTING (do not modify): context_guard.py --mode=stop ---
      
      // [NEW #7] SOT snapshot backup
      {
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/sot_snapshot.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/sot_snapshot.py; fi",
          "timeout": 10
        }]
      }
    ],
    "TaskCompleted": [
      // [NEW #8] Quality gate check on task completion
      {
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/quality_gate_check.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/quality_gate_check.py; fi",
          "timeout": 30
        }]
      }
    ],
    "TeammateIdle": [
      // [NEW #9] Agent Team health monitoring
      {
        "hooks": [{
          "type": "command",
          "command": "if test -f \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/teammate_health_check.py; then python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/teammate_health_check.py; fi",
          "timeout": 10
        }]
      }
    ]
  }
}
```

**Execution Order Summary (within same event):**

| Event | Order | Script | Priority Rationale |
|-------|-------|--------|--------------------|
| PreToolUse(Write\|Edit) | 1st | `sot_write_guard.py` | SOT integrity is non-negotiable (AC-2) |
| PreToolUse(Write\|Edit) | 2nd | `file_ownership_guard.py` | Team file conflicts are second-most critical |
| PreToolUse(Write\|Edit) | 3rd | `block_test_file_edit.py` (inherited) | TDD protection |
| PreToolUse(Write\|Edit) | 4th | `predictive_debug_guard.py` (inherited) | Warning only (exit 0) |
| PreToolUse(Bash) | 1st | `block_destructive_commands.py` (inherited) | Safety first |
| PreToolUse(Bash) | 2nd | `validate_ac_constraints.py` | AC enforcement |
| PostToolUse(Write\|Edit) | 1st | `enforce_design_system.py` | Design compliance |
| PostToolUse(Write\|Edit) | 2nd | `bundle_size_guard.py` | Size enforcement |
| PostToolUse(Write) | 3rd | `validate_translation_pair.py` | Translation validation |

---

## 8. Skills & Commands

### 8.1 Skill: church-retreat-app

**Directory Structure:**
```
.claude/skills/church-retreat-app/
├── SKILL.md                      ← Entry point (WHY + triggers)
└── references/
    ├── workflow-phases.md         ← Phase-by-phase execution details
    ├── quality-gates.md           ← Q1-Q11 + D1-D9 definitions
    ├── design-system.md           ← CSS variables + animation patterns
    ├── error-handling.md          ← Error recovery tree + Korean messages
    └── content-matrix.md          ← App type → required content mapping
```

**SKILL.md Content Structure:**

```markdown
---
name: church-retreat-app
description: "Generate church youth retreat web apps through Korean conversation"
---

# Church Retreat App Generator

## Trigger Patterns
- "수련회 앱", "앱 만들어줘", "교회 앱", "retreat app"

## What This Skill Does
1. Reads prompt/workflow.md for domain rules
2. Activates church-app-orchestrator agent
3. Orchestrator manages the 7-phase pipeline (P0-P6)
4. Produces: Complete web app + LAN server + QR code + .bat file

## Activation Flow
trigger → load SKILL.md → spawn @church-app-orchestrator
  → orchestrator reads workflow.md core rules (~300 lines)
  → orchestrator starts Phase 1 (or resumes from SOT)

## References (loaded on-demand per phase)
- references/workflow-phases.md — current phase details
- references/quality-gates.md — Phase 4 only
- references/design-system.md — Phase 3 only
- references/error-handling.md — on error
- references/content-matrix.md — Phase 1 only
```

### 8.2 Commands

**`.claude/commands/start-app.md`:**
```markdown
---
description: "Start church retreat app generation workflow from Phase 1"
---

Read prompt/workflow.md and prompt/workflow-coding.md.
Activate the church-app-orchestrator agent.
Start from Phase 1 (App Menu Presentation).
Present the 수련회 앱 메뉴판 to the user in Korean.
Follow all instructions in workflow.md and workflow-coding.md exactly.
Quality is the absolute criterion — never compromise for speed or token cost.
```

**`.claude/commands/resume-app.md`:**
```markdown
---
description: "Resume interrupted church retreat app generation"
---

Read prompt/workflow.md and prompt/workflow-coding.md.
Check for existing project:
  1. Read %USERPROFILE%\.last-church-app-path for project path
  2. If not found, search: Desktop > Documents > C:\ > D:\ for church-app folder
  3. Read app-state.json from the project folder
  4. Determine current phase from status fields
  5. Resume from the indicated phase
Tell the user in Korean: "이전에 만들던 앱이 있어요. 이어서 할까요?"
If server was running, restart server + regenerate QR (IP may have changed).
```

**`.claude/commands/deploy-app.md`:**
```markdown
---
description: "Deploy completed church retreat app (Phase 6)"
---

Read prompt/workflow.md Step 10 (Deployment) and prompt/workflow-coding.md §4.6.
Activate the deployment-manager agent.
Execute deployment for the current project.
Generate QR code, .bat file, emergency card.
Auto-open browser with QR page.
```

**`.claude/commands/app-status.md`:**
```markdown
---
description: "Show current workflow status and quality report"
---

Read app-state.json from the current project.
Display in Korean:
  - Current phase and step
  - Quality gate results (if available)
  - pACS scores (F, C, L)
  - Modification count
  - Server status (running/stopped)
  - Fallback tier history (if any)
```

**`.claude/commands/app-verify.md`:**
```markdown
---
description: "Run quality verification manually (Phase 4 gates)"
---

Read prompt/workflow-coding.md §4.5 (quality-checker spec).
Run verify-app.js in the project folder.
Display results: PASS/FAIL for each gate.
If FAIL: suggest fixes and ask user whether to auto-fix.
```

---

## 9. TDD Automation System

### 9.1 TDD Workflow Integration

```
Every code generation sub-step follows this cycle:

  [1] Orchestrator creates task: "Write tests for {feature}"
      → Assigns to @tdd-guard

  [2] tdd-guard writes test file(s)
      → Tests define expected behavior
      → Tests must FAIL at this point (no implementation yet)
      → tdd-guard runs tests → confirms all FAIL → reports to orchestrator

  [3] Orchestrator creates task: "Implement {feature} to pass tests"
      → Assigns to @code-generator

  [4] code-generator implements minimum code
      → Runs tests → confirms all PASS → reports to orchestrator

  [5] Orchestrator verifies:
      → All tests pass
      → Code meets quality gates
      → Git checkpoint created
```

### 9.2 TDD Guard Hook Integration

The existing `block_test_file_edit.py` hook (from AgenticWorkflow) protects test files:

```
.tdd-guard file present in project root:
  → Edit/Write to tests/* is BLOCKED for code-generator
  → Only tdd-guard can modify test files
  → Ensures tests aren't weakened to pass

.tdd-guard file absent:
  → Normal editing allowed
```

**Toggle mechanism:**
```bash
# tdd-guard creates the file before writing tests
touch .tdd-guard

# orchestrator removes it after TDD cycle completes
rm .tdd-guard
```

### 9.3 Test Framework

**Runtime:** Node.js built-in `node:test` + `node:assert` (zero dependency)

```javascript
// tests/test_server.js — Example structure
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Server', () => {
  it('responds with 200 on GET /', async () => {
    const res = await fetch('http://localhost:3000/');
    assert.equal(res.status, 200);
  });
  
  it('serves Korean text without broken characters', async () => {
    const res = await fetch('http://localhost:3000/');
    const html = await res.text();
    assert.match(html, /[\uAC00-\uD7AF]/); // Contains Korean
  });
  
  it('rejects unauthenticated /admin access', async () => {
    const res = await fetch('http://localhost:3000/admin');
    assert.equal(res.status, 401);
  });
});
```

### 9.4 P1 Script Execution Model (A1-6/A2-2 — No verify-app.js Wrapper)

> **DESIGN CHANGE (A1-6/A2-2):** verify-app.js previously called Python scripts via `execSync('python3 ...')`.
> On Windows, `python3` may not be on the system PATH. Node.js child processes inherit system PATH,
> NOT Claude Code's internal Python. This makes `execSync` calls UNRELIABLE on the target platform.
>
> **NEW MODEL:** Orchestrator calls Python scripts DIRECTLY via Claude Code's Bash tool.
> Claude Code's Bash tool uses its OWN Python runtime (guaranteed available).
> verify-app.js is ELIMINATED — orchestrator handles result merging directly.

```
Orchestrator P1 execution (replaces verify-app.js):

  [1] orchestrator runs via Bash tool (Claude Code's Python — guaranteed):
      python3 scripts/validate_gates.py --project-dir . --json
      → captures stdout → parses JSON → stores as q_results

  [2] orchestrator runs via Bash tool:
      python3 scripts/validate_design_gates.py --project-dir . --json
      → captures stdout → parses JSON → stores as d_results

  [3] orchestrator runs via Bash tool:
      python3 scripts/validate_app_specific.py --project-dir . --type {app_type} --json
      → captures stdout → parses JSON → stores as app_results

  [4] orchestrator runs via Bash tool:
      python3 scripts/validate_content_insertion.py --project-dir . --json
      → captures stdout → parses JSON → stores as content_results

  [5] orchestrator merges all JSON results in-memory:
      all_results = {**q_results, **d_results, **app_results, content: content_results}
      fail_gates = [gate for gate in all_results if gate.pass == false]
      overall = "PASS" if len(fail_gates) == 0 else "FAIL"

  [6] orchestrator writes merged results to reports/phase4-quality-report.md (English)

WHY THIS IS BETTER:
  - Python is called by Claude Code's Bash tool → uses Claude Code's guaranteed Python
  - No Node.js → Python interop issues (no execSync, no PATH dependency)
  - No verify-app.js file to generate/maintain (one less moving part)
  - Orchestrator already has all results in context → immediate decision-making
  - Each script is independently runnable: python3 scripts/validate_gates.py --json
```

> **For /app-verify command (manual user trigger):** The command spec in §8.2 runs the same
> Python scripts via Bash tool directly, not through verify-app.js.

### 9.5 P1 Deterministic Validation Script Suite (Hallucination Prevention)

> **P1 Principle Applied:** "코드로 사전 계산 가능한 연관관계는 미리 처리 → AI가 판단·분석에 집중"
>
> Every verification that can be computed deterministically MUST be implemented as a Python/Node.js script. AI agents NEVER "reason about" whether a gate passes — they READ the script's JSON output and ACT on it. This eliminates hallucination from all repeatable, accuracy-critical checks.

#### Hallucination Risk Classification

| Risk Level | Definition | Policy |
|------------|-----------|--------|
| **H-CRITICAL** | Result must be identical on every run. AI reasoning can vary. | **Deterministic script ONLY** — AI must not judge |
| **H-MAJOR** | Judgment needed, but input data must be exact. | **Script extracts data → AI judges the data** |
| **H-SAFE** | Inherently creative/subjective. | **AI agent appropriate** |

#### Script Architecture

P1 validation scripts are **infrastructure templates** managed in the AgenticWorkflow repo. During Phase 3, the orchestrator copies them into the generated project's `scripts/` folder and @tdd-guard configures app-type-specific parameters.

**Why templates, not generated code (ADR-011):**
- Templates are version-controlled, testable, and reusable across projects.
- @tdd-guard doesn't "invent" validation logic (hallucination risk) — it configures proven scripts.
- Bug fixes to templates propagate to all future projects automatically.

```
INFRASTRUCTURE (AgenticWorkflow repo — version-controlled):
.claude/skills/church-retreat-app/templates/scripts/
├── validate_gates.py                     ← Q1-Q11 technical gates (H-CRITICAL)
├── validate_design_gates.py              ← D1-D9 design gates (H-CRITICAL)
├── validate_integration.py               ← T-3.11 HTML↔CSS↔JS cross-ref (H-CRITICAL)
├── validate_translation_gates.py         ← T1-T3 translation gates (H-CRITICAL)
├── validate_content_insertion.py          ← SOT content ↔ HTML content (H-CRITICAL)
├── validate_app_specific.py              ← App-type gates: buzzer sim, etc. (H-CRITICAL)
└── compute_pacs_data.py                  ← pACS objective data extraction (H-MAJOR)

INFRASTRUCTURE (AgenticWorkflow repo — shared across all workflows):
.claude/hooks/scripts/validate_app_state_schema.py  ← SOT schema check (infrastructure-level, S3)
.claude/schemas/app-state.schema.json         ← JSON Schema draft-07 definition

RUNTIME (generated project — created during Phase 3):
<project>/scripts/                        ← Copied from templates + configured
├── validate_gates.py                     (copied, port number injected)
├── validate_design_gates.py              (copied, palette config injected)
├── validate_integration.py               (copied as-is)
├── validate_translation_gates.py         (copied as-is)
├── validate_content_insertion.py          (copied, app-type config injected)
├── validate_app_specific.py              (copied, app-type selected)
└── compute_pacs_data.py                  (copied as-is)
```

**Phase 3 Copy Protocol:**
```
orchestrator (during Phase 3, after T-3.1 project skeleton):
  1. Copy .claude/skills/church-retreat-app/templates/scripts/*.py → <project>/scripts/
  2. Inject app-specific config from SOT (port, app_type, palette, features)
  3. @tdd-guard generates verify-app.js wrapper (T-3.9) that calls these scripts
  4. Scripts are now project-local and executable: python3 scripts/validate_gates.py
```

**Common Interface (all scripts):**
```
Usage:    python3 scripts/<script>.py --project-dir . [--gates Q1,Q3] [--json]
Input:    Reads project files directly (no stdin)
Output:   JSON to stdout — {"<gate>": {"pass": bool, "value": <measured>, "threshold": <expected>, "detail": "..."}, ...}
Exit:     0 = completed (check "pass" fields), 1 = script error
SOT:      Read-only — scripts NEVER write to app-state.json or any project file
```

#### Script Specifications

> **Path convention in specs below:** `scripts/<name>.py` refers to both the template
> (`.claude/skills/church-retreat-app/templates/scripts/<name>.py`) and the project copy
> (`<project>/scripts/<name>.py`). The code is identical — the project copy has app-specific
> config injected (port, app_type, etc.). Exception: `validate_app_state_schema.py` lives ONLY at
> infrastructure level (`.claude/hooks/scripts/`).

**`validate_gates.py` — Q1-Q11 (H-CRITICAL):**
```python
# Q1:  HTTP GET localhost:PORT → response.status_code == 200 (integer comparison)
# Q2:  Parse HTML with html.parser → collect errors list → len == 0
# Q3:  regex r'<script[^>]+src=["\']https?://' on all .html files → count == 0
# Q4:  sum(os.path.getsize(f) for f in project_files) → bytes ≤ 512000 (500KB)
# Q5:  scan .html for \uFFFD (replacement char) → 0 found
#      AND scan for [\uAC00-\uD7AF] (Korean) → >0 found
# Q6:  parse CSS for min-height/min-width/padding on button/a/[role=button]
#      → compute effective size → all ≥ 44px
# Q7:  decode QR PNG with qrcode library → compare URL string to expected
# Q8:  HTTP GET /admin without auth header → status_code == 401
# Q9:  HTTP POST user input "<script>alert(1)</script>" → response body
#      does NOT contain unescaped <script> (regex check)
# Q10: SKIP (human — deferred to Phase 5)
# Q11: WebSocket connect → send timestamped ping → measure pong delta → ≤ 100ms
```

**`validate_design_gates.py` — D1-D9 (H-CRITICAL):**
```python
# D1:  regex r'border-radius:\s*(\d+)' on CSS → all values ≥ 12
#      AND r'box-shadow:' exists in CSS
# D2:  regex r'transition[^;]*(\d+)ms' → count ≥ 2 AND all durations ≥ 150
#      AND (r'@keyframes\s+\w+' exists OR r'animation[^;]*:' exists)  # page transition
# D3:  r'prefers-color-scheme:\s*dark' exists in CSS
# D4:  extract all color values: r'#[0-9a-fA-F]{3,8}', r'rgb\(', r'rgba\(', r'hsl\('
#      EXCLUDE those inside var() declarations or :root definitions
#      remaining count == 0
# D5:  r'position:\s*fixed' in CSS for header element
#      AND (r'<nav' with bottom-related positioning) for applicable app types
# D6:  parse CSS font-size values → body ≥ 16 (px or rem×16) → headings ≥ 24
#      AND r'Pretendard' in font-family declaration
# D7:  r'transform:\s*scale' in CSS/JS (button tap feedback)
#      AND (r'animation-delay' OR r'stagger' OR sequential delay pattern) exists
# D8:  r'\.skeleton|\.loading|\.spinner' in HTML class attributes
# D9:  r'confetti|AudioContext|playSound|new Audio' in JS files
```

**`validate_integration.py` — T-3.11 (H-CRITICAL):**
```python
# 1. Extract HTML classes:  regex r'class=["\']([^"\']+)["\']' → split → Set A
# 2. Extract CSS selectors:  regex r'\.([a-zA-Z][\w-]*)' from CSS files → Set B
# 3. Orphaned classes = Set A - Set B (used in HTML but not defined in CSS)
#    → FAIL if non-empty (list the orphans)
# 4. Extract JS DOM refs: regex r'getElementById\(["\'](\w+)' and
#    r'querySelector\(["\']([^"\']+)' → Set C
# 5. Extract HTML IDs: regex r'id=["\']([^"\']+)["\']' → Set D
# 6. Dangling refs = Set C - Set D → FAIL if non-empty
# 7. manifest.json start_url → file/route exists check
# 8. service-worker.js cache list → all listed files exist on disk
# 9. WebSocket message types in client JS ↔ server.js handler mapping
```

**`validate_translation_gates.py` — T1-T3 (H-CRITICAL):**
```python
# T1: for phase in 1..6: os.path.exists(f"reports/phase{phase}-*.ko.md") → all True
# T2: for each pacs-logs/phase*-translation-pacs.md:
#       parse "pACS = " line → extract integer → ≥ 70
# T3: load glossary.yaml + church-app-glossary.yaml → term list
#     for each .ko.md: for each term: if English term in source,
#       Korean term must appear in .ko.md (not a different translation)
```

**`validate_app_state_schema.py` — Schema Enforcement (H-CRITICAL, INFRASTRUCTURE-LEVEL):**
```python
# LOCATION: .claude/hooks/scripts/validate_app_state_schema.py (NOT in generated project)
# REASON: Must work from Phase 0 onward, before generated project folder exists.
#
# SCHEMA FILE: .claude/schemas/app-state.schema.json (JSON Schema draft-07)
#   → Single Source of Truth for the SOT's own structure
#   → Schema changes require updating this ONE file only
#
# Usage: python3 .claude/hooks/scripts/validate_app_state_schema.py \
#          --schema .claude/schemas/app-state.schema.json --data <json_string_or_file>
#
# Checks: required fields exist, types match, enums valid,
#          phase number 0-6, pACS scores 0-100, status booleans.
# Called by orchestrator after EVERY SOT write (§3.2 step 3).
#
# Dependency: from _church_app_lib import read_sot, get_project_dir
# Dependency: jsonschema library (pip install jsonschema)
# NOTE: _context_lib.py already has validate_sot_schema() for state.yaml (parent genome).
#        This script validates app-state.json (different schema). No name collision.
```

**`validate_content_collection.py` — Phase 1→2 Gate (H-CRITICAL, INFRASTRUCTURE-LEVEL):**
```python
# LOCATION: .claude/hooks/scripts/validate_content_collection.py
# PURPOSE: Deterministically verify that ALL required fields for the chosen app type
#          are present in app-state.json BEFORE Phase 2 starts.
#          Prevents conversation-guide from "claiming" collection is complete
#          when required fields are actually missing (hallucination prevention).
#
# Called by orchestrator at Phase 1→2 transition.
#
# Logic:
#   1. Read app-state.json → intent.app_type
#   2. Load CONTENT_MATRIX (required fields per app type):
#        quiz:    [team_count > 0, team_names non-empty, quiz_questions length > 0, design_palette set]
#        score:   [team_count > 0, team_names non-empty, team_colors non-empty]
#        schedule:[schedule length > 0]
#        lyrics:  [lyrics length > 0]
#        stamps:  [missions length > 0]
#        qt:      [bible_passages length > 0]
#        combined:[features length > 0, + each selected feature's requirements]
#   3. For each required field: check presence AND non-empty in SOT
#   4. Output JSON: {"complete": true/false, "missing": ["team_colors", ...], "app_type": "quiz"}
#
# Dependency: from _church_app_lib import read_sot
```

**`validate_content_insertion.py` — Content Accuracy (H-CRITICAL):**
```python
# Reads app-state.json → content section (quiz_questions, schedule, lyrics, etc.)
# Reads generated HTML files → extracts visible text content
# Comparison:
#   quiz: len(sot.quiz_questions) == count of quiz DOM elements in HTML
#         each question text appears verbatim in HTML (substring match)
#   schedule: each schedule item text in HTML
#   lyrics: each song title in HTML
# Output: {"match_rate": 0.95, "total_in_sot": 20, "found_in_html": 19,
#           "missing": ["Question 15 text..."], "extra": []}
```

**`validate_app_specific.py` — App-Type Gates (H-CRITICAL):**
```python
# --type quiz:    spawn 35 WebSocket connections → send simultaneous buzzer
#                 messages → count received by server → dropped == 0
# --type score:   change score via /admin API → GET /screen → verify
#                 score updated (within 1 second)
# --type lyrics:  change current song via /admin → verify /screen and /
#                 show same lyrics (string comparison)
# --type stamps:  decode all mission QR PNGs → verify each URL resolves
# --type combined: run all applicable sub-checks based on features in SOT
```

**`compute_pacs_data.py` — Objective Data for pACS (H-MAJOR):**
```python
# Extracts OBJECTIVE data. Does NOT score (AI does that).
#
# F_data (Content Accuracy):
#   calls validate_content_insertion.py → gets match_rate
#   {"match_rate": 0.95, "missing_items": [...]}
#
# C_data (Feature Completeness):
#   reads SOT features list → scans server.js routes + HTML files
#   for each feature, checks if corresponding route/element exists
#   {"coverage_rate": 1.0, "implemented": [...], "unimplemented": [...]}
#
# L_data (Code Correctness):
#   calls validate_gates.py + validate_design_gates.py → counts pass/fail
#   {"gate_pass_rate": 0.87, "passing": ["Q1","Q2",...], "failing": ["D7"]}
#
# AI orchestrator reads this JSON and assigns 0-100 scores with judgment
# (e.g., match_rate 0.95 with 1 missing non-critical item → F=90)
```

#### Execution Protocol — Who Calls What

```
Phase 1→2 Transition (Content Collection Gate):
  orchestrator runs: python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/validate_content_collection.py
  → if "complete": false → orchestrator re-spawns @conversation-guide to collect missing fields
  → if "complete": true → proceed to Phase 2
  → INFRASTRUCTURE-LEVEL script (available before project folder exists)

Phase 3 (T-3.11 Integration):
  orchestrator runs: python3 scripts/validate_integration.py --project-dir .
  → reads JSON result → if FAIL: assigns fix task to responsible teammate

Phase 4 (Two-Pass Quality):
  Pass 1 — orchestrator runs:
    python3 scripts/validate_gates.py --project-dir . --json
    python3 scripts/validate_design_gates.py --project-dir . --json
    python3 scripts/validate_app_specific.py --project-dir . --type {type} --json
    python3 scripts/validate_content_insertion.py --project-dir . --json
  → merges all JSON → identifies FAIL gates
  Pass 2 — for each FAIL gate:
    orchestrator spawns @quality-checker with FAIL detail
    @quality-checker applies fix (this is AI — creative judgment)
    orchestrator re-runs ONLY the failed gate script to confirm fix

SOT Schema (all phases — infrastructure-level, S3):
  orchestrator runs: python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/validate_app_state_schema.py \
    --schema "$CLAUDE_PROJECT_DIR"/.claude/schemas/app-state.schema.json --data <merged>
  → after EVERY SOT write (integrated into write_sot() function, §3.2)
  → NOT in project scripts/ — lives at infrastructure level (available from Phase 0)

Phase 4 (pACS):
  orchestrator runs: python3 scripts/compute_pacs_data.py --project-dir .
  → reads JSON → applies subjective judgment → scores F/C/L 0-100

Post-Phase 6 (Translation):
  orchestrator runs: python3 scripts/validate_translation_gates.py --project-dir .
  → T1/T2/T3 results → SOT translation.t_gates
```

---

## 10. Task Management Strategy

### 10.1 Task Lifecycle

```
Orchestrator creates tasks at each phase transition:

  TaskCreate(subject, description, owner=<agent-name>)
    → status: pending

  Agent picks up task:
    → TaskUpdate(taskId, status="in_progress")

  Agent completes task:
    → TaskUpdate(taskId, status="completed")
    → quality_gate_check.py hook fires
    → If gate fails: TaskUpdate(taskId, status="in_progress") + retry

  Orchestrator reviews completed task:
    → Validates output
    → Writes results to SOT
    → Creates next phase tasks
```

### 10.2 Task Templates by Phase

**Phase 1 Tasks:**
```
T-1.1: "Detect app type from user conversation"
  owner: conversation-guide
  description: "Present menu, detect type, collect team config, palette"

T-1.2: "Collect app content"
  owner: conversation-guide
  blockedBy: [T-1.1]
  description: "Collect quiz questions, schedule, lyrics per content matrix"

T-1.3: "Get user confirmation on app structure"
  owner: conversation-guide
  blockedBy: [T-1.2]
  description: "Present structure preview, wait for confirmation signal"
```

**Phase 2 Tasks:**
```
T-2.1: "Initialize project dependencies and architecture"
  owner: code-generator
  description: "Populate existing project folder (created at activation, DG-1):
                npm init, package.json, npm install, architecture planning.
                Folder + git + app-state.json already exist from activation."
```

**Phase 3 Tasks (Agent Team):**
```
T-3.1: "Create project skeleton (HTML + base CSS + empty JS)"
  owner: code-generator

T-3.2: "Setup design system CSS variables and animations"
  owner: design-system

T-3.3: "Write skeleton tests (TDD RED phase)"
  owner: tdd-guard
  blockedBy: [T-3.1]

T-3.4: "Insert content into HTML (quiz questions, schedule, etc.)"
  owner: code-generator
  blockedBy: [T-3.1]

T-3.5: "Implement styling, animations, dark mode"
  owner: design-system
  blockedBy: [T-3.2]

T-3.6: "Implement WebSocket and real-time functionality"
  owner: code-generator
  blockedBy: [T-3.4]

T-3.7: "Write functionality tests (TDD RED phase)"
  owner: tdd-guard
  blockedBy: [T-3.6]

T-3.8: "Implement PWA (manifest + service worker)"
  owner: design-system
  blockedBy: [T-3.5]

T-3.9: "Copy P1 template scripts to project/scripts/"
  owner: tdd-guard
  blockedBy: [T-3.7, T-3.8]
  note: "verify-app.js removed (§9.4) — orchestrator calls scripts directly"

T-3.10: "Polish: data export, error handling, reconnection"
  owner: code-generator
  blockedBy: [T-3.6]

T-3.11: "Integration verification (post-merge)"
  owner: orchestrator
  blockedBy: [T-3.9, T-3.10]
  description: "Verify HTML↔CSS class match, JS↔DOM references, manifest routes,
                WS message type routing, service worker asset list. Fix gaps."
```

**Phase 4 Tasks (Two-Pass — aligned with §5.3):**
```
T-4.D: "Run P1 detection scripts (all gates)"
  owner: orchestrator (direct Bash execution — no agent needed)
  description: "Run validate_gates.py + validate_design_gates.py +
                validate_app_specific.py + validate_content_insertion.py.
                Collect JSON results. NO fixes. Detection only."

T-4.F-{N}: "Fix gate {gate_id}: {failure_detail}"
  owner: quality-checker (dynamically created per FAIL gate)
  blockedBy: [T-4.D]
  description: "Apply creative fix for {gate_id}. Re-run the specific
                P1 script to confirm PASS. Max 3 retries per gate."
  note: "These tasks are DYNAMICALLY CREATED by orchestrator based on
         T-4.D detection results. Number of tasks = number of FAIL gates.
         If T-4.D returns all PASS, no T-4.F tasks are created."
```

**Phase 6 Tasks:**
```
T-6.1: "Deploy LAN server and generate QR"
  owner: deployment-manager

T-6.2: "Create .bat file and emergency card"
  owner: deployment-manager
  blockedBy: [T-6.1]

T-6.3: "Auto-open browser and present to user"
  owner: deployment-manager
  blockedBy: [T-6.2]
```

**Translation Tasks (AC-4 — Phase 1 BLOCKING + Phase 6 DEFERRED BATCH, A3-3):**
```
T-1.T: "Translate Phase 1 intent report to Korean (BLOCKING — template validation)"
  owner: app-translator
  blockedBy: [T-1.3]
  description: "Translate reports/phase1-intent-report.md → .ko.md pair.
                Use glossary.yaml + church-app-glossary.yaml.
                Score translation pACS (Ft/Ct/Nt). Write pACS log.
                BLOCKING: must score GREEN (≥70) before Phase 2 starts.
                This validates the translation template quality."

T-BATCH: "Batch translate ALL Phase 2-6 reports to Korean (after deployment)"
  owner: app-translator
  blockedBy: [T-6.3]
  description: "After Phase 6 deployment completes, translate ALL remaining
                English reports (phase2 through phase6) to .ko.md pairs
                in a SINGLE agent session. Score pACS for each.
                Phase 1 .ko already exists (T-1.T).
                This is a deferred batch — NOT per-phase spawning (A3-3)."

T-FINAL: "Run T1-T3 translation quality gates"
  owner: orchestrator (runs P1 scripts directly)
  blockedBy: [T-BATCH]
  description: "Run validate_translation_gates.py via Bash tool.
                T1: all .ko files exist. T2: all pACS >= 70. T3: glossary consistent.
                Non-critical — deployment already complete.
                Results recorded in SOT translation.t_gates."
```

> **DEFERRED BATCH principle (A3-3)**: Translation does NOT run during Phases 2-5. English reports accumulate in `reports/`. After Phase 6 deployment, ONE batch translation covers all reports. This reduces agent spawns from 6 to 2 (Phase 1 BLOCKING + Phase 6 BATCH) with zero quality loss — 사역자 never reads these reports directly.

---

## 11. Code Standards Documents

> These 3 documents are created BEFORE any code implementation begins.
> They serve as the quality baseline for all generated code.

### 11.1 docs/code-convention.md

```markdown
# Code Convention — Church Retreat App

## Naming

### Files
- Kebab-case: `quiz-buzzer.js`, `team-score.css`
- Test files: `test_<module>.js` (snake_case with test_ prefix)
- Entry points: `server.js`, `index.html`, `app.js`

### Variables & Functions
- camelCase: `teamScore`, `handleBuzzer()`
- Constants: UPPER_SNAKE: `MAX_TEAMS`, `WS_RECONNECT_INTERVAL`
- DOM elements: prefix with `el`: `elBuzzerBtn`, `elScoreBoard`
- Event handlers: prefix with `handle` or `on`: `handleBuzzerPress()`, `onWsMessage()`

### CSS
- CSS Custom Properties: `--primary`, `--font-size-base`
- BEM-like classes: `card`, `card__title`, `card--active`
- Utility classes: `text-center`, `mt-4`, `hidden`
- Animation classes: `fade-in`, `slide-up`, `pulse`

## Formatting

### JavaScript
- 2-space indentation
- Single quotes for strings
- Semicolons required
- Template literals for multi-line strings and interpolation
- Arrow functions for callbacks
- `const` by default, `let` when reassignment needed, NEVER `var`

### CSS
- 2-space indentation
- One property per line
- CSS custom properties at :root level
- Media queries at bottom of file, grouped by breakpoint
- Mobile-first: base styles for 375px, `@media (min-width: ...)` for larger

### HTML
- 2-space indentation
- Double quotes for attributes
- Self-closing tags for void elements: `<img />`, `<br />`
- Semantic elements: `<header>`, `<main>`, `<nav>`, `<section>`, `<article>`
- Korean text always in UTF-8

## Structure

### Project Layout
project-root/
├── index.html          ← Main entry point (student view)
├── admin.html          ← Admin console (password protected)
├── screen.html         ← Projector view (score/lyrics display)
├── server.js           ← Express + WebSocket server
├── app.js              ← Client-side main logic
├── styles.css          ← Design system + all styles
├── animations.css      ← Micro-interactions + transitions
├── manifest.json       ← PWA manifest
├── service-worker.js   ← PWA service worker
├── data.json           ← Persistent data snapshot
├── package.json        ← Dependencies
├── app-state.json      ← SOT (workflow state)
├── (verify-app.js removed — orchestrator calls P1 scripts directly via Bash, §9.4)
├── regenerate-qr.js    ← QR regeneration script
├── scripts/            ← P1 Deterministic Validation Scripts (copied from templates in Phase 3)
│   ├── validate_gates.py              (Q1-Q11)
│   ├── validate_design_gates.py       (D1-D9)
│   ├── validate_integration.py        (HTML↔CSS↔JS cross-ref)
│   ├── validate_translation_gates.py  (T1-T3)
│   ├── validate_content_insertion.py   (SOT↔HTML content match)
│   ├── validate_app_specific.py       (app-type-specific gates)
│   └── compute_pacs_data.py           (pACS objective data extraction)
│   # NOTE: validate_app_state_schema.py is NOT here — it lives at infrastructure level
│   #        (.claude/hooks/scripts/) because it must work before this project exists.
├── tests/              ← Test files
│   ├── test_server.js
│   ├── test_websocket.js
│   ├── test_admin.js
│   ├── test_content.js
│   ├── test_security.js
│   └── test_pwa.js
├── reports/            ← English phase reports + .ko translations (AC-4)
│   ├── phase1-intent-report.md
│   ├── phase1-intent-report.ko.md
│   └── ...
├── pacs-logs/          ← Translation pACS score logs (AC-4)
├── results/            ← Data export output
├── archives/           ← App archive for reuse
└── assets/
    ├── icon-192.png
    ├── icon-512.png
    └── qr-code.png

## Comments

- Comment WHY, not WHAT
- Korean comments allowed for user-facing message explanations
- JSDoc for public API functions only (server routes, WebSocket handlers)
- No comments on self-explanatory code

## Error Handling

- User-facing errors: Korean message, no technical details
- Server errors: console.error with English technical detail
- WebSocket: auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- HTTP fallback: 5-second polling when WebSocket unavailable

## Security

- ALL user input sanitized before DOM insertion (XSS prevention)
- No eval(), no innerHTML with user data (use textContent)
- Admin routes require password middleware
- No API keys in client-side code
- No data sent outside project folder
```

### 11.2 docs/architectural-decision-records.md

```markdown
# Architectural Decision Records (ADR)

## ADR-001: Single-Session Role Switching vs Agent Team Hybrid

**Date**: 2026-04-09
**Status**: Accepted
**Context**: workflow.md originally specified single-session role switching (no agent teams). User requested infrastructure build using agent teams, swarm, and orchestrator pattern.
**Decision**: Sequential-first approach (ADR-012). Phase 3 DEFAULT is sequential sub-agents. Agent Team is an UPGRADE for 종합 앱 with 3+ combined features only. Phase 4 uses two-pass (P1 script detection → sequential AI fix). Other phases use focused sequential sub-agents.
**Rationale**: For tightly-coupled HTML/CSS/JS (most church retreat apps), **sequential execution produces higher integration quality** than parallel execution. In sequential mode, each agent sees the previous agent's complete output — zero integration gaps. In parallel mode, agents work blind to each other's output, requiring post-merge integration verification (T-3.11) which is a "fix after the fact" approach. **Sequential is quality-superior for simple apps.** For complex 종합 앱 (3+ features), the codebase is large enough that expert specialization (P2) outweighs integration risk — Agent Team is justified. For Phase 4, **conflict-free auto-fix** (sequential) is quality-superior: each repair accounts for all prior repairs.
**Consequences**: Sequential is the common path (most apps are types 1-8). Agent Team is rare (only type 9 with 3+ features AND experimental feature available). This simplifies the common case and reserves complexity for where it adds quality.

## ADR-002: app-state.json as SOT (not state.yaml)

**Date**: 2026-04-09
**Status**: Accepted
**Context**: AgenticWorkflow uses state.yaml for autobiography pipeline. Church retreat app generates JavaScript apps.
**Decision**: Use app-state.json (JSON format) instead of state.yaml.
**Rationale**: Generated apps use JSON for data persistence. Using the same format reduces cognitive overhead and allows the app itself to reference SOT if needed. JSON is natively parseable in both Node.js and Python (hooks).
**Consequences**: Hooks that expect YAML need JSON parsing. All SOT read/write uses JSON.

## ADR-003: Node.js Built-in Test Runner (not Jest/Mocha)

**Date**: 2026-04-09
**Status**: Accepted
**Context**: TDD requires a test framework. Jest and Mocha are popular but add dependencies.
**Decision**: Use Node.js built-in `node:test` module + `node:assert`.
**Rationale**: Zero additional dependencies. Keeps bundle small. Available in Node.js >= 18. Aligned with AC1 (minimal external dependency) and AC3 (bundle size constraint).
**Consequences**: Less rich assertion library than Jest. Sufficient for the scope of this project.

## ADR-004: Pretendard Font Subset (~50KB) Over System Fonts Only

**Date**: 2026-04-09
**Status**: Accepted
**Context**: System fonts (Malgun Gothic) look "Windows-like" to students. Full Pretendard is ~5MB.
**Decision**: Include Pretendard subset (2350 common Korean chars + Latin + numbers, ~50KB) in project.
**Rationale**: Eliminates "Windows smell" that makes students perceive app as "just a website". 50KB fits within 300KB bundle target. Quality (AC-1) over minimalism.
**Consequences**: Font file included in project. Service worker caches it. Fallback to system fonts if load fails.

## ADR-005: In-Memory State + Periodic JSON Snapshot (not lowdb)

**Date**: 2026-04-09
**Status**: Accepted
**Context**: 35 simultaneous quiz buzzer presses cause race condition with lowdb file writes.
**Decision**: All runtime state managed in-memory (JS object). JSON file is a periodic snapshot (every 5 seconds, debounced).
**Rationale**: In-memory operations are atomic within Node.js event loop. File I/O is async and can conflict. Snapshot provides crash recovery without real-time file contention.
**Consequences**: Data loss window of up to 5 seconds on server crash. Acceptable for quiz/score context.

## ADR-006: Native WebSocket (ws) + HTTP Polling Fallback

**Date**: 2026-04-09
**Status**: Accepted
**Context**: Socket.io adds ~100KB to bundle and has complex fallback logic. Some church WiFi networks block WebSocket.
**Decision**: Use native `ws` library for WebSocket. Auto-detect WS failure and switch to HTTP polling at 5-second intervals.
**Rationale**: ws library is ~25KB. HTTP polling is universal fallback. Students experience slight delay (5s) but functionality is preserved.
**Consequences**: Must implement reconnection logic manually. Must implement polling endpoint on server.

## ADR-007: Two-Pass Quality Verification (Detection → Fix)

**Date**: 2026-04-09 (revised 2026-04-10)
**Status**: Accepted (supersedes original 3-fork design)
**Context**: Q1-Q11 + D1-D9 + app-specific gates = 20+ checks. Original design used 3 parallel AI forks, but this created cross-fix conflicts (Fork A's fix breaks Fork B's gate) and relied on AI reasoning for gate detection (hallucination risk).
**Decision**: Two-pass architecture: Pass 1 runs P1 deterministic scripts (NO AI) for 100% accurate detection. Pass 2 uses AI @quality-checker sequentially for creative fixes on FAIL gates only. Each fix accounts for all prior fixes.
**Rationale**: Pass 1 eliminates hallucination from detection (P1 principle). Pass 2's sequential design eliminates cross-fix conflicts. Quality of detection (deterministic) AND quality of fixes (conflict-free) both improve. This serves AC-1 (quality).
**Consequences**: Pass 1 is faster than 3-fork (scripts run in seconds vs. agent spawn overhead). Pass 2 may be slower (sequential fixes), but fix quality is higher. Net quality improvement justifies the design.

## ADR-008: English-First Execution + Translation Pairs (AC-4)

**Date**: 2026-04-09
**Status**: Accepted
**Context**: AI models produce higher-quality reasoning, analysis, and code when operating in English. The workflow generates artifacts (reports, plans, quality assessments) that benefit from maximum AI performance. However, the 사역자 (user) communicates exclusively in Korean, and the end-users (students) interact with a Korean app.
**Decision**: Introduce AC-4 (English-First Execution) as a new absolute criterion. All agent reasoning, intermediate artifacts, and reports are produced in English first. A dedicated @app-translator agent creates Korean .ko translation pairs after each phase. Translation is NON-BLOCKING — it runs in parallel with the next phase.
**Rationale**: English-first maximizes AI reasoning quality (serves AC-1). Korean translation pairs ensure full accessibility. NON-BLOCKING design prevents translation from slowing the critical path. The existing translator.md genome (from AgenticWorkflow parent) provides a proven translation protocol with pACS self-scoring.
**Consequences**: 
  - New agent (app-translator) added to roster — 7 sub-agents total.
  - New SOT section (translation.*) tracks per-phase translation status.
  - New quality gates (T1-T3) verify translation completeness post-deployment.
  - New hook (validate_translation_pair.py) validates .ko file structure.
  - New glossary file (church-app-glossary.yaml) for domain-specific terms.
  - Token cost increases ~15-20% due to translation work. Acceptable per AC-1.
  - Existing workflow phases, agents, hooks, and quality gates are UNCHANGED — translation is purely additive.

## ADR-009: NON-BLOCKING Translation (not Sequential Gating)

**Date**: 2026-04-09
**Status**: Accepted
**Context**: Translation after each phase could block the workflow's critical path, adding latency to Phase 1→2→3→4→5→6 execution.
**Decision**: Translation tasks run in parallel (NON-BLOCKING). Phase N+1 starts immediately after Phase N completes, without waiting for Phase N's translation to finish. Translation quality is verified only once at the end (T1-T3 gates after Phase 6).
**Rationale**: The critical path is app generation (P1→P6). Translation quality, while important, does not affect the app's functionality. English originals always exist as the authoritative source. Even if all translations fail, the app is still fully deployed and functional.
**Consequences**: Translation quality is checked late (post-Phase 6). If translation fails, English originals remain. No deployment delay due to translation.

## ADR-010: P1 Deterministic Validation Scripts (Hallucination Prevention)

**Date**: 2026-04-10
**Status**: Accepted
**Context**: Quality gates (Q1-Q11, D1-D9, T1-T3, T-3.11, content insertion, SOT schema) require 100% accurate, repeatable results. AI agents performing these checks can hallucinate — e.g., "border-radius appears to be 12px" when it's actually 8px, or "all quiz questions are present" when 2 are missing. This is the parent genome's P1 principle: "코드로 사전 계산 가능한 연관관계는 미리 처리 → AI가 판단·분석에 집중."
**Decision**: Implement 8 deterministic Python validation scripts (§9.5) that perform ALL repeatable verification. AI agents are structurally prohibited from "reasoning about" gate pass/fail — they MUST call the scripts and read the JSON output. AI's role is limited to: (1) running scripts, (2) reading results, (3) applying creative fixes for failures. Detection is deterministic; only repair is AI-driven.
**Rationale**: A Python regex `r'border-radius:\s*(\d+)'` extracting "8" is 100% accurate on every run. An AI agent reading CSS and stating "12px" can hallucinate. For repeatable accuracy-critical tasks, code is categorically superior to AI reasoning. This separation (scripts DETECT, agents FIX) maximizes both accuracy (scripts) and creativity (agents). It directly serves AC-1 (quality) by eliminating the largest source of quality gate unreliability.
**Consequences**:
  - 8 new Python scripts + 8 test files added to project (Priority H + I in manifest).
  - verify-app.js redesigned as thin wrapper calling Python scripts.
  - Phase 4 Two-Pass redesigned: Pass 1 runs scripts directly (no AI), Pass 2 uses AI for fixes only.
  - score_phase_pacs() uses compute_pacs_data.py for objective data, AI only for subjective scoring.
  - validate_app_state_schema.py runs after every SOT write (prevents malformed state).
  - T-3.11 Integration Verification calls validate_integration.py (deterministic cross-ref).
  - Total file count: 42 → 58. Token cost increase is irrelevant per AC-1.
  - All scripts are read-only (never modify project files) and SOT-compliant (never write to app-state.json).

## ADR-011: P1 Scripts as Infrastructure Templates (not Generated Code)

**Date**: 2026-04-10
**Status**: Accepted
**Context**: P1 validation scripts (validate_gates.py etc.) were originally specified as living "inside the generated project folder, created by @tdd-guard during Phase 3." This created three problems: (1) scripts in the generated project need Python, but only Node.js is guaranteed on the 사역자's machine; (2) @tdd-guard "generating" validation logic means an AI is writing deterministic verification code — itself a hallucination risk; (3) the file manifest confused infrastructure files with generated files.
**Decision**: P1 scripts are **infrastructure templates** stored at `.claude/skills/church-retreat-app/templates/scripts/`. During Phase 3, the orchestrator copies them into the generated project's `scripts/` folder and injects app-specific configuration (port, app_type, palette). @tdd-guard generates only verify-app.js (the thin wrapper) and app-specific test files. validate_app_state_schema.py is promoted to infrastructure-level (`.claude/hooks/scripts/`) since it must work from Phase 0 before any project folder exists. A JSON Schema file (`.claude/schemas/app-state.schema.json`) serves as the Single Source of Truth for the SOT's own structure.
**Rationale**: Templates are version-controlled, testable, and reusable. Bug fixes propagate to all future projects. AI agents don't "invent" validation logic — they configure proven scripts. Python execution is guaranteed through Claude Code's runtime (not the 사역자's machine). Separation of infrastructure (templates) from generated output (project files) follows the dependency inversion principle.
**Consequences**:
  - P1 script templates live in .claude/skills/ (infrastructure, version-controlled)
  - validate_app_state_schema.py lives in .claude/hooks/scripts/ (infrastructure-level)
  - .claude/schemas/app-state.schema.json added (SOT schema definition)
  - file_ownership_guard.py added (Agent Team enforcement, S4)
  - All new hooks depend on _context_lib.py shared library (S5)
  - settings.json has explicit execution order for hook priority (S6)
  - Total files: 63 (from 58, +5: _church_app_lib.py, file_ownership_guard, JSON Schema, validate_app_state_schema, _church_app_lib test)

## ADR-012: Sequential-First Execution for Phase 3 (Team as Upgrade)

**Date**: 2026-04-10
**Status**: Accepted (supersedes ADR-001's default team mode)
**Context**: HTML, CSS, and JavaScript have circular dependencies — HTML references CSS classes that CSS must define, CSS targets HTML elements that HTML must contain, JS manipulates DOM elements that HTML must declare. In Agent Team mode, code-generator and design-system work in parallel without seeing each other's output. This creates integration gaps that T-3.11 must repair after the fact. In sequential mode, each agent reads the previous agent's complete output — zero integration gaps by construction.
**Decision**: Sequential sub-agent execution is the DEFAULT for Phase 3. Agent Team is an UPGRADE used ONLY for 종합 앱 (type 9) with 3 or more combined features, where the codebase is large enough that expert specialization (P2) outweighs integration risk.
**Rationale**: For a quiz app (~5 files, ~500 lines total), parallel specialization adds no quality — but integration risk is real. For a 종합 앱 with quiz + score + lyrics + schedule + stamps (~15+ files, ~2000+ lines), specialization depth matters and T-3.11 integration verification is worth the overhead. **Quality of integration** (sequential) vs. **quality of specialization** (parallel) — the tipping point is at 3+ combined features.
**Consequences**:
  - §5.4 added: full Tier 2 Sequential Protocol (TDD RED → code GREEN → design → verify REFACTOR).
  - §5.2 Agent Team now labeled "종합 앱 3+ features ONLY".
  - choose_execution_mode() checks app_type + combined_count before selecting team mode.
  - Fallback path (team → sequential) is now the SAME as the default path — reducing complexity.
  - Most workflow executions (~80% of use cases) will use the simpler sequential path.
```

### 11.3 docs/code-quality-guide.md

```markdown
# Code Quality Guide — Church Retreat App

## Quality Pyramid

```
              ┌─────────┐
              │ UX Feel │  ← D1-D9 design gates
             ┌┴─────────┴┐
             │ Functional │  ← Q1-Q11 technical gates
            ┌┴───────────┴┐
            │   Correct    │  ← TDD tests pass
           ┌┴─────────────┴┐
           │    Secure      │  ← XSS, auth, no data leak
          ┌┴───────────────┴┐
          │   Structured     │  ← Code convention compliance
         └───────────────────┘
```

## Quality Evaluation Criteria

### Tier 1: Correctness (Must Pass)
- [ ] Server starts without errors
- [ ] All HTML renders without broken characters
- [ ] All JavaScript executes without runtime errors
- [ ] Korean text displays correctly across all pages
- [ ] Navigation works on mobile (375px viewport)

### Tier 2: Security (Must Pass)
- [ ] XSS: `<script>` tags in user input are neutralized
- [ ] Auth: /admin requires password, rejects unauthorized access
- [ ] Data: No data sent outside project folder
- [ ] Keys: No API keys in client-side code
- [ ] Input: All user input (nickname, prayer requests) sanitized

### Tier 3: Functionality (Must Pass)
- [ ] WebSocket connects and maintains connection
- [ ] HTTP polling fallback activates on WS failure
- [ ] QR code decodes to correct server URL
- [ ] Admin actions reflect on student screens
- [ ] PWA installs and works offline (cached content)
- [ ] Bundle size <= 500KB hard limit

### Tier 4: Design (Must Pass for "진짜 앱" feel)
- [ ] Card UI with rounded corners and shadows
- [ ] Smooth animations (>= 150ms transitions)
- [ ] Dark mode support
- [ ] Consistent color scheme (CSS variables only)
- [ ] Touch targets >= 44x44px
- [ ] Mobile-native feel (fixed header, bottom nav)
- [ ] Loading states (skeleton UI or spinner)
- [ ] Micro-interactions (button press feedback)
- [ ] Projector screen effects (confetti, sound)

### Tier 5: Polish (Should Pass)
- [ ] Font: Pretendard loads, Korean readable
- [ ] Responsive: works 375px to 1920px
- [ ] Offline: graceful degradation when disconnected
- [ ] Reconnection: auto-reconnect within 30 seconds
- [ ] Error messages: Korean, friendly, actionable
- [ ] Bundle target <= 300KB (gzip)

## pACS Scoring

| Dimension | Full Name | What It Measures |
|-----------|-----------|-----------------|
| F | Content Accuracy | Does the app contain exactly what the user requested? |
| C | Feature Completeness | Are all requested features implemented and working? |
| L | Code Correctness | Does the app run without errors and pass quality gates? |

**Score Calculation**: `pACS = min(F, C, L)`

| Score | Color | Action |
|-------|-------|--------|
| >= 70 | GREEN | Auto-proceed to next phase |
| 50-69 | YELLOW | Proceed with flag, note in SOT |
| < 50 | RED | Rework required, do not proceed |

## Code Review Checklist (for quality-checker)

### Before marking any code generation complete:
1. [ ] All test files exist and pass (`node --test tests/`)
2. [ ] verify-app.js exists and returns overall: "PASS"
3. [ ] No TODO/FIXME/HACK comments in production code
4. [ ] No console.log in production code (use proper logging)
5. [ ] No hardcoded Korean strings in JavaScript logic (use data attributes or constants)
6. [ ] All CSS colors use CSS custom properties
7. [ ] All file paths use path.join() (Windows compatibility)
8. [ ] Package.json has no unnecessary dependencies
9. [ ] Git checkpoint exists for the completed step
10. [ ] app-state.json updated with completion status

## "Beautiful Code" Standards (예쁜 코드 기준)

### Readability
- Function length: <= 30 lines (extract if longer)
- Nesting depth: <= 3 levels (extract or early return)
- Variable names: self-documenting (no single-letter except loop indices)
- Consistent patterns: same problem → same solution pattern

### Simplicity
- One function, one responsibility
- No premature abstraction (3 similar blocks > 1 forced generic)
- No speculative features ("might need this later")
- Prefer built-in APIs over library imports

### Consistency
- Same formatting everywhere (2-space indent, single quotes)
- Same error handling pattern everywhere
- Same naming convention everywhere
- Same file structure for all app types

### Maintainability
- New app type = add content + routes (no core changes needed)
- Style change = modify CSS variables only (no hunting through code)
- Content update = modify data file or HTML content section only
```

---

## 12. Context Loading Strategy

> workflow.md is ~28K tokens. Loading it all at once wastes context for code generation.

### 12.1 Loading Rules

```
[Always Loaded — Core Rules ~300 lines — EXACT SECTIONS]

  From workflow.md (~150 lines):
    → "The North Star" section (~20 lines)
    → "Absolute Constraints" AC1-AC4 (~50 lines)
    → "Role Definitions" 4 roles (~50 lines)
    → Current Phase step definition only (~30 lines, varies by phase)

  From workflow-coding.md (~120 lines):
    → §1 Absolute Criteria table + AC-4 Scope Matrix (~40 lines)
    → §2.1 Agent Roster table (~10 lines)
    → §3.1-3.2 SOT File + Write Protocol (~15 lines)
    → §4 AC-4 Common Rules block (~15 lines)
    → §6.1 Fallback Tiers (~20 lines)
    → §9.5 Execution Protocol "Who Calls What" (~20 lines)

  From runtime (~30 lines):
    → app-state.json current state (full SOT contents)

  Total: ~300 lines ≈ ~1,500 tokens
  Remaining budget: ~183,500 tokens for actual agent work

  EVERYTHING ELSE in workflow.md and workflow-coding.md is loaded
  on-demand per Phase (see below) or accessed via file Read when needed.

[On-Demand per Phase]
  → Phase 1: Conversation flow rules, content matrix, menu template
  → Phase 2: Tech stack selection, folder priority, design system defaults
  → Phase 3: Code generation order, server patterns, realtime architecture
  → Phase 4: Q1-Q11 + D1-D9 gate definitions (quality-gates.md reference)
  → Phase 5: Modification loop rules, rollback mechanism
  → Phase 6: .bat spec, network strategy, deployment messages

[Never Loaded at Runtime]
  → Activation Mechanism (already activated)
  → Adversarial Review Tracking (document history)
  → Distill Verification Checklist (document history)
```

### 12.2 Phase Transition Protocol

```
On phase transition (e.g., Phase 2 → Phase 3):
  1. Orchestrator saves current phase results to SOT
  2. Orchestrator creates Git checkpoint
  3. generate_context_summary.py fires (Stop hook) → Knowledge Archive snapshot
  4. Previous phase detail is released from context
  5. Next phase detail is loaded from workflow.md (specific line range)
  6. app-state.json is re-read to confirm state
  7. Next phase sub-agent(s) are spawned with phase-specific context
```

### 12.3 RLM (Recursive Language Model) Pattern Integration

> **This section preserves the RLM gene from the parent genome (AGENTS.md, soul.md §0).**
> RLM treats work artifacts as "external memory objects" that persist across sessions and context compressions. Without RLM, a context compact or session restart destroys the reasoning chain — the agent knows WHAT happened (from SOT) but not WHY.

**RLM Components in This Workflow:**

```
┌─────────────────────────────────────────────────────────┐
│  RLM External Memory Objects (persist across sessions)   │
│                                                          │
│  1. app-state.json (SOT)                                 │
│     → WHAT: current phase, gate results, content data    │
│     → Written by: orchestrator only                      │
│                                                          │
│  2. reports/phase*.md (English originals)                 │
│     → WHY: reasoning, decisions, trade-offs per phase    │
│     → Written by: each phase's primary agent             │
│                                                          │
│  3. .claude/context-snapshots/ (auto-generated)           │
│     → HOW: incremental snapshots of agent working state  │
│     → Written by: generate_context_summary.py (Stop hook)│
│     → Read by: restore_context.py (SessionStart hook)    │
│                                                          │
│  4. Git history (commit messages + diffs)                 │
│     → WHEN: chronological record of every change         │
│     → Written by: all agents at checkpoints              │
│                                                          │
│  5. translations/glossary.yaml + church-app-glossary.yaml │
│     → TERMS: persistent terminology memory for translator │
│     → Written by: @app-translator (append-only)          │
└─────────────────────────────────────────────────────────┘
```

**Session Resume Protocol (RLM Pointer Recovery):**

```
When a session starts (SessionStart hook fires):

  [1] restore_context.py reads .claude/context-snapshots/
      → Finds latest snapshot → extracts RLM pointers:
         - Last active phase number
         - Modified file paths
         - Pending tasks
         - Error history (Predictive Debugging cache)

  [2] Orchestrator reads app-state.json (SOT)
      → Determines current_phase, deployed status, quality results

  [3] Orchestrator reads reports/phase{N}-*.md
      → Recovers WHY context: what decisions were made and why

  [4] Orchestrator resumes from the correct phase
      → If mid-phase: re-reads phase-specific workflow.md section
      → If between phases: starts next phase
      → If Phase 5 loop: re-enters feedback loop

  Result: Full context recovery without any information loss.
```

**Context Compression Survival (PreCompact/Stop):**

```
When context compression is triggered:

  [1] save_context.py (PreCompact hook) → saves full snapshot
  [2] generate_context_summary.py (Stop hook) → incremental Knowledge Archive:
      - Session metadata (duration, phases covered)
      - Key decisions made (from reports/*.md)
      - Files modified (from Git diff)
      - Quality gate results (from SOT)
      - Dynamic RLM query hints (Grep patterns for recovery)

  After compression:
  [3] restore_context.py reads snapshot → injects recovery pointers
  [4] Orchestrator re-reads app-state.json + latest report
  [5] Workflow continues without loss
```

**RLM + Translation Memory:**

`translations/glossary.yaml` and `translations/church-app-glossary.yaml` are RLM external memory objects for the @app-translator agent. They persist terminology decisions across sessions, ensuring translation consistency even if the translator agent is re-spawned in a new session.

---

## 13. Execution Flow (End-to-End)

```
USER: "수련회 앱 만들어줘" (or /start-app)
  │
  ▼
[SKILL TRIGGER] → church-retreat-app SKILL.md loaded
  │
  ▼
[ORCHESTRATOR ACTIVATED]
  ├── Read workflow.md core rules (~300 lines)
  ├── Read workflow-coding.md (this file)
  ├── Create minimal project folder (§3.1 Lifecycle — DG-1)
  │   → mkdir <project-folder> at priority location
  │   → Write initial app-state.json (empty sections + workflow metadata)
  │   → git init + commit "[init] SOT initialized"
  │   → SOT is now writable for all subsequent phases
  │
  ├── PHASE 0: Environment Check ─────────────────────
  │   └── Orchestrator checks Node.js, disk, npm directly
  │       → If missing: present Korean guide to user
  │       → SOT: status.current_phase = 0
  │
  ├── PHASE 1: Conversation ──────────────────────────
  │   ├── TaskCreate("Detect app type", owner=conversation-guide)
  │   ├── Spawn @conversation-guide (Korean dialog + English reasoning per AC-4)
  │   │   └── Menu → intent detection → content collection → confirmation
  │   │   └── Writes reports/phase1-intent-report.md (English, AC-4)
  │   ├── Receive result → validate → SOT write
  │   │   → intent.*, content.*, status.research_complete = true
  │   ├── Run validate_content_collection.py (P1 deterministic — H2-2)
  │   │   → if missing fields: re-spawn @conversation-guide to collect them
  │   ├── Git checkpoint: "[research] Intent collection complete"
  │   └── Spawn @app-translator (⚠ BLOCKING — template validation)
  │       → .ko pair + pACS. Must score GREEN (≥70) before Phase 2 starts.
  │       → This ONE blocking check prevents 5× rework if template is bad.
  │
  ├── PHASE 2: Project Init ──────────────────────────
  │   ├── TaskCreate("Initialize project", owner=code-generator)
  │   ├── Spawn @code-generator (English reasoning per AC-4)
  │   │   └── Populate existing folder: package.json → npm install → architecture
  │   │       (folder + git + SOT already exist from activation — DG-1)
  │   │   └── Writes reports/phase2-architecture-plan.md (English, AC-4)
  │   ├── Receive result → validate → SOT write
  │   │   → architecture.*, status.planning_complete = true
  │   └── Git checkpoint: "[init] Project initialized"
  │       (translation DEFERRED to batch after Phase 6 — A3-3)
  │
  ├── PHASE 3: Code Generation ─────────────────────
  │   ├── choose_execution_mode() → sequential (default) or agent_team (종합 앱 3+)
  │   │
  │   │   DEFAULT — Sequential (§5.4, most apps):
  │   │   ├── Step A: @tdd-guard writes tests (TDD RED)
  │   │   ├── Step B: @code-generator implements code (TDD GREEN)
  │   │   │   └── Reads tests from Step A → must pass all
  │   │   ├── Step C: @design-system applies design
  │   │   │   └── Reads HTML/JS from Step B → zero integration gaps
  │   │   ├── Step D: @tdd-guard verifies + generates verify-app.js (REFACTOR)
  │   │   └── validate_integration.py as safety net (expects 0 issues)
  │   │
  │   │   UPGRADE — Agent Team (§5.2, 종합 앱 3+ features only):
  │   │   ├── 3 teammates parallel + T-3.11 integration verification
  │   │   └── Fallback to sequential if team fails
  │   │
  │   ├── SOT: status.code_generated = true
  │   └── Git checkpoint: "[codegen] App code generation complete"
  │       (translation DEFERRED to batch after Phase 6 — A3-3)
  │
  ├── PHASE 4: Quality Verification (TWO-PASS, P1 SCRIPTS) ──
  │   ├── PRE: Start server in background (DG-4): node server.js &
  │   ├── PASS 1 — Deterministic Detection (NO AI reasoning):
  │   │   ├── run python3 scripts/validate_gates.py --json
  │   │   ├── run python3 scripts/validate_design_gates.py --json
  │   │   ├── run python3 scripts/validate_app_specific.py --json
  │   │   ├── run python3 scripts/validate_content_insertion.py --json
  │   │   └── Merge JSON → unified detection report (100% accurate)
  │   ├── POST-PASS1: Stop background server
  │   │
  │   ├── PASS 2 — Sequential AI Fix (only for FAIL gates):
  │   │   ├── For each FAIL: spawn @quality-checker with exact failure detail
  │   │   ├── @quality-checker applies creative fix → re-run script to confirm
  │   │   └── Max 3 retries per gate → still failing → Git rollback → report
  │   │
  │   ├── Hallucination boundary: scripts DETECT, agents FIX
  │   │
  │   ├── pACS scoring: F, C, L → min score
  │   │   ├── GREEN (>=70) → auto-proceed
  │   │   ├── YELLOW (50-69) → proceed with flag
  │   │   └── RED (<50) → rework
  │   │
  │   ├── SOT: quality.*, status.quality_passed = true
  │   └── Git checkpoint: "[verify] Quality gates passed"
  │       (translation DEFERRED to batch after Phase 6 — A3-3)
  │
  ├── PHASE 5: Preview & Feedback ────────────────────
  │   ├── Auto-open browser with app
  │   ├── Display QR for mobile testing
  │   ├── Wait for user feedback
  │   │   ├── [A] Style change → @code-generator fix → skip QA → return
  │   │   ├── [B] Feature add → @code-generator → Phase 4 re-run → return
  │   │   ├── [C] Rollback → git checkout → SOT sync → return
  │   │   └── [DONE] "완성" / "좋아요" → proceed to Phase 6
  │   │
  │   ├── SOT: history.modifications[], status.modification_count
  │   ├── Git checkpoint: "[modify] {description}"
  │   └── Compile reports/phase5-modification-log.md (English, AC-4)
  │       (translation DEFERRED to batch after Phase 6 — A3-3)
  │
  └── PHASE 6: Deployment ────────────────────────────
      ├── TaskCreate("Deploy app", owner=deployment-manager)
      ├── Spawn @deployment-manager
      │   ├── Start LAN server (background)
      │   ├── Detect WiFi IP (regular vs hotspot)
      │   ├── Generate QR code PNG
      │   ├── Create print-ready HTML (A4)
      │   ├── Create "앱 실행.bat" on desktop
      │   ├── Create emergency response card
      │   ├── Auto-open browser
      │   └── (Optional) GitHub Pages deployment
      │
      ├── SOT: status.deployed = true, server_url, qr_path, bat_path
      ├── Git checkpoint: "[deploy] Final build complete"
      │
      ├── BATCH TRANSLATION (A3-3): Spawn @app-translator ONCE
      │   → Translate ALL reports/phase1-6 English originals → .ko pairs
      │   → Phase 1 .ko already exists (BLOCKING at Phase 1)
      │   → Batch covers Phase 2-6 reports in single agent session
      │   → Score translation pACS for each report
      │
      ├── T-GATE CHECK (post-batch-translation):
      │   ├── T1: All .ko files exist for phases 1-6?
      │   ├── T2: All translation pACS >= 70?
      │   ├── T3: Glossary terms consistent across all .ko files?
      │   └── Results → SOT: translation.t_gates.*
      │       (Deployment NOT rolled back even if T-gates fail)
      │
      └── USER MESSAGE:
          "앱이 완성됐어요!
           학생들에게 이 QR코드를 보여주세요.
           바탕화면에 '수련회 앱 실행' 아이콘을 만들었어요."
```

---

## 14. File Manifest (All Files to Create)

### Priority A — Foundation (create first)

| # | File | Purpose |
|---|------|---------|
| 1 | `docs/code-convention.md` | Code formatting and naming standards |
| 2 | `docs/architectural-decision-records.md` | Architecture decisions log |
| 3 | `docs/code-quality-guide.md` | Quality evaluation criteria |

### Priority B — Agent Definitions

| # | File | Purpose |
|---|------|---------|
| 4 | `.claude/agents/church-app-orchestrator.md` | Master coordinator |
| 5 | `.claude/agents/conversation-guide.md` | Korean conversation specialist |
| 6 | `.claude/agents/code-generator.md` | Full-stack code generator |
| 7 | `.claude/agents/design-system-agent.md` | Design system specialist |
| 8 | `.claude/agents/quality-checker.md` | Quality gate runner |
| 9 | `.claude/agents/deployment-manager.md` | Deployment specialist |
| 10 | `.claude/agents/tdd-guard.md` | TDD automation |
| 11 | `.claude/agents/app-translator.md` | English→Korean translation specialist (AC-4) |

### Priority C — Hook Scripts

| # | File | Purpose |
|---|------|---------|
| 12 | `.claude/hooks/scripts/_church_app_lib.py` | Shared library for ALL church-app hooks (C-1) |
| 13 | `.claude/hooks/scripts/sot_write_guard.py` | AC-2 SOT single-writer enforcement |
| 14 | `.claude/hooks/scripts/file_ownership_guard.py` | Agent Team file ownership enforcement (S4) |
| 15 | `.claude/hooks/scripts/validate_ac_constraints.py` | AC1/AC4 enforcement |
| 16 | `.claude/hooks/scripts/enforce_design_system.py` | Hardcoded color detection |
| 17 | `.claude/hooks/scripts/bundle_size_guard.py` | Bundle size enforcement |
| 18 | `.claude/hooks/scripts/quality_gate_check.py` | Task completion gate |
| 19 | `.claude/hooks/scripts/teammate_health_check.py` | Agent team health |
| 20 | `.claude/hooks/scripts/sot_snapshot.py` | SOT backup |
| 21 | `.claude/hooks/scripts/validate_translation_pair.py` | Translation .ko file structural validation |
| 22 | `.claude/hooks/scripts/validate_app_state_schema.py` | SOT JSON Schema validation (infrastructure-level, S3) |
| 23 | `.claude/hooks/scripts/validate_content_collection.py` | Phase 1→2 content completeness gate (H2-2) |

### Priority D — Hook Tests (TDD)

| # | File | Purpose |
|---|------|---------|
| 23 | `.claude/hooks/scripts/tests/test_church_app_lib.py` | Shared library tests (C-1) |
| 24 | `.claude/hooks/scripts/tests/test_sot_write_guard.py` | SOT write protection tests |
| 25 | `.claude/hooks/scripts/tests/test_file_ownership_guard.py` | File ownership tests (S4) |
| 26 | `.claude/hooks/scripts/tests/test_validate_ac.py` | AC constraint tests |
| 27 | `.claude/hooks/scripts/tests/test_enforce_design.py` | Design system tests |
| 28 | `.claude/hooks/scripts/tests/test_bundle_size.py` | Bundle size tests |
| 29 | `.claude/hooks/scripts/tests/test_quality_gate.py` | Quality gate tests |
| 30 | `.claude/hooks/scripts/tests/test_teammate_health.py` | Health check tests |
| 31 | `.claude/hooks/scripts/tests/test_validate_translation.py` | Translation hook tests |
| 32 | `.claude/hooks/scripts/tests/test_validate_app_state_schema.py` | SOT schema validation tests |

### Priority E — Skill & Commands

| # | File | Purpose |
|---|------|---------|
| 33 | `.claude/skills/church-retreat-app/SKILL.md` | Skill entry point |
| 34 | `.claude/skills/church-retreat-app/references/workflow-phases.md` | Phase details |
| 35 | `.claude/skills/church-retreat-app/references/quality-gates.md` | Gate definitions |
| 36 | `.claude/skills/church-retreat-app/references/design-system.md` | CSS patterns |
| 37 | `.claude/skills/church-retreat-app/references/error-handling.md` | Error recovery |
| 38 | `.claude/skills/church-retreat-app/references/content-matrix.md` | Content by app type |
| 39 | `.claude/commands/start-app.md` | /start-app command |
| 40 | `.claude/commands/resume-app.md` | /resume-app command |
| 41 | `.claude/commands/deploy-app.md` | /deploy-app command |
| 42 | `.claude/commands/app-status.md` | /app-status command |
| 43 | `.claude/commands/app-verify.md` | /app-verify command |

### Priority F — Configuration & Schema

| # | File | Purpose |
|---|------|---------|
| 44 | `.claude/settings.json` | Updated with new hooks (§7.4 complete version) |
| 45 | `.claude/schemas/app-state.schema.json` | SOT JSON Schema draft-07 definition (S3) |
| 46 | `CLAUDE.md` | Updated skill trigger table |

### Priority G — Translation Infrastructure (AC-4)

| # | File | Purpose |
|---|------|---------|
| 47 | `translations/church-app-glossary.yaml` | Church/retreat domain terminology for @app-translator |
| 48 | `reports/.gitkeep` | Reports folder initialization (English originals + .ko pairs) |
| 49 | `pacs-logs/.gitkeep` | Translation pACS log folder initialization |

### Priority H — P1 Deterministic Validation Script Templates (Hallucination Prevention)

> These are **infrastructure templates** stored in the AgenticWorkflow repo.
> During Phase 3, orchestrator copies them into the generated project's `scripts/` folder.
> See §9.5 for the copy protocol and app-type configuration injection.

| # | File | Purpose |
|---|------|---------|
| 50 | `.claude/skills/church-retreat-app/templates/scripts/validate_gates.py` | Q1-Q11 technical gates (H-CRITICAL) |
| 51 | `.claude/skills/church-retreat-app/templates/scripts/validate_design_gates.py` | D1-D9 design gates (H-CRITICAL) |
| 52 | `.claude/skills/church-retreat-app/templates/scripts/validate_integration.py` | T-3.11 HTML↔CSS↔JS cross-ref (H-CRITICAL) |
| 53 | `.claude/skills/church-retreat-app/templates/scripts/validate_translation_gates.py` | T1-T3 translation gates (H-CRITICAL) |
| 54 | `.claude/skills/church-retreat-app/templates/scripts/validate_content_insertion.py` | SOT↔HTML content match (H-CRITICAL) |
| 55 | `.claude/skills/church-retreat-app/templates/scripts/validate_app_specific.py` | App-type gates (H-CRITICAL) |
| 56 | `.claude/skills/church-retreat-app/templates/scripts/compute_pacs_data.py` | pACS objective data extraction (H-MAJOR) |

### Priority I — P1 Script Template Tests (TDD)

| # | File | Purpose |
|---|------|---------|
| 57 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_validate_gates.py` | Q1-Q11 script tests |
| 58 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_validate_design_gates.py` | D1-D9 script tests |
| 59 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_validate_integration.py` | Integration check tests |
| 60 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_validate_translation_gates.py` | T1-T3 script tests |
| 61 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_validate_content.py` | Content insertion tests |
| 62 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_validate_app_specific.py` | App-specific gate tests |
| 63 | `.claude/skills/church-retreat-app/templates/scripts/tests/test_compute_pacs_data.py` | pACS data extraction tests |

**Total: 64 files**

---

## 15. Implementation Order

```
STEP 1: Foundation Documents (Priority A)
  → docs/code-convention.md
  → docs/architectural-decision-records.md
  → docs/code-quality-guide.md
  → These establish the quality baseline BEFORE any code is written.

STEP 2: Orchestrator Agent (Priority B)
  → church-app-orchestrator.md
  → The brain must exist before the limbs.

STEP 3: Sub-Agent Definitions (Priority B)
  → All 7 sub-agents in parallel (independent files)
  → conversation-guide, code-generator, design-system, quality-checker,
    deployment-manager, tdd-guard, app-translator
  → Each follows the spec in this document §4.

STEP 4: Hook Tests First (Priority D)
  → TDD: write tests BEFORE hook implementations
  → 10 test files: _church_app_lib + 10 hooks
  → test_church_app_lib.py FIRST (shared library must work before hooks)

STEP 5: Shared Library + Hook Scripts (Priority C)
  → FIRST: _church_app_lib.py (shared library — all hooks depend on it)
  → THEN: 10 hooks to pass tests from Step 4.
  → Critical order: sot_write_guard.py (AC-2) → file_ownership_guard.py (S4) → rest.
  → All hooks import from _church_app_lib.py (NOT _context_lib.py directly).

STEP 6: Skill & Commands (Priority E)
  → Skill entry point + 5 reference files
  → 5 slash commands (start-app, resume-app, deploy-app, app-status, app-verify)

STEP 7: Configuration Integration (Priority F)
  → Update settings.json with new hooks (§7.4 complete version with execution order)
  → Create .claude/schemas/app-state.schema.json (SOT schema, S3)
  → Update CLAUDE.md skill trigger table.

STEP 8: Translation Infrastructure (Priority G)
  → church-app-glossary.yaml with domain terms
  → reports/ and pacs-logs/ folder initialization

STEP 9: P1 Validation Script Tests First (Priority I)
  → TDD: write tests BEFORE P1 script implementations
  → 8 test files for 8 validation scripts
  → Each test verifies deterministic behavior: same input → same output, every time.

STEP 10: P1 Validation Scripts (Priority H)
  → Implement 8 deterministic Python scripts to pass tests from Step 9.
  → Each script follows spec in §9.5.
  → CRITICAL: These scripts are the hallucination prevention core.
  → Scripts output JSON, never modify project files (read-only).
  → verify-app.js (already created in Step 3 by tdd-guard) wraps these scripts.

STEP 11: Integration Test
  → Run /start-app end-to-end
  → Verify: orchestrator activates → agents spawn → SOT updates
  → Verify: fallback tiers work when agents fail
  → Verify: hooks fire at correct events
  → Verify: TDD cycle completes for a simple app type
  → Verify: @app-translator creates .ko pairs after each phase (AC-4)
  → Verify: T1-T3 translation gates pass after Phase 6
  → Verify: all Git commit messages are in English (AC-4)
  → Verify: P1 scripts produce identical results on repeated runs (determinism)
  → Verify: Phase 4 uses scripts for detection, AI only for fixes (hallucination boundary)
  → Verify: validate_app_state_schema.py runs after every SOT write (schema enforcement)
```

---

## 16. Workflow Preservation Verification

> AC-4 and the translation system are **additive changes**. This section proves that no existing workflow feature is broken, altered, or degraded.

### 16.1 Preserved Features — Verification Matrix

| Feature | Status | Evidence |
|---------|--------|----------|
| North Star (사역자 + Korean dialog + "진짜 앱") | **PRESERVED** | AC-4 explicitly exempts user-facing Korean (§1 Exceptions). conversation-guide speaks Korean to 사역자. App UI remains Korean. |
| 6-Phase Structure (P0-P6) | **PRESERVED** | No phases added, removed, or reordered. Translation tasks are inserted BETWEEN phases, not replacing them. |
| SOT single-writer (Orchestrator only) | **PRESERVED** | `translation.*` fields are written by Orchestrator, not by @app-translator. @app-translator reports results; Orchestrator writes to SOT. |
| 4-Tier Fallback | **PRESERVED** | @app-translator uses same fallback tiers. Translation failure falls back to Tier 3 (orchestrator direct) → Tier 4 (skip). |
| Agent Team (Phase 3) | **PRESERVED** | Translation runs AFTER Phase 3 completes, not during. No interference with team coordination. |
| Parallel Fork (Phase 4) | **PRESERVED** | Translation runs AFTER fork merge. No interference with quality verification. |
| Quality Gates Q1-Q11 | **PRESERVED + STRENGTHENED** | Gate definitions and pass criteria unchanged. Execution upgraded from AI-reasoning to deterministic P1 scripts (§9.5). Same gates, more accurate detection. |
| Design Gates D1-D9 | **PRESERVED + STRENGTHENED** | Gate definitions and pass criteria unchanged. Execution upgraded to deterministic P1 scripts. Same gates, zero hallucination risk. |
| App-Type-Specific Gates | **PRESERVED** | Zero changes. |
| TDD Cycle (RED→GREEN→REFACTOR) | **PRESERVED** | Translation is not code — TDD does not apply to .ko.md files. |
| Hooks (6 inherited + 10 new) | **PRESERVED** | All 6 inherited hooks unchanged. 10 new workflow-specific hooks: sot_write_guard, file_ownership_guard, validate_ac_constraints, enforce_design_system, bundle_size_guard, quality_gate_check, teammate_health_check, sot_snapshot, validate_translation_pair, validate_app_state_schema. All import from _church_app_lib.py (church-app shared library). |
| Skills & Commands (5 commands) | **PRESERVED** | All 5 commands unchanged. Skill entry point unchanged. |
| Context Loading Strategy | **PRESERVED** | Translation reports are NOT loaded into agent context. They exist as files only. |
| Git Checkpoint Strategy | **CHANGED (non-breaking)** | Commit messages changed from Korean to English per AC-4. Commit frequency and checkpoint strategy unchanged. |
| .bat / Emergency Card | **PRESERVED** | Korean text preserved. AC-4 explicitly exempts these as user-facing Korean. |
| App Content (Korean) | **PRESERVED** | Quiz questions, schedule, lyrics, etc. remain Korean originals. NOT translated from English. |
| Error Handling / Recovery Tree | **PRESERVED** | All error handling patterns unchanged. Translation errors handled by standard fallback tiers. |
| Session Interruption & Resume | **PRESERVED** | app-state.json contains translation status — resume includes translation state. |

### 16.2 Non-Destructive Design Guarantees

```
1. ADDITIVE ONLY: New files (.ko.md, pacs-logs/, church-app-glossary.yaml)
   are created. No existing files are modified by the translation system.

2. NON-BLOCKING: Translation never delays the critical path (P1→P6).
   Phase N+1 starts immediately. Translation runs in parallel.

3. SINGLE WRITER: @app-translator writes only to:
   - reports/*.ko.md (translation outputs)
   - pacs-logs/*.md (pACS scores)
   - translations/church-app-glossary.yaml (term additions only, never deletions)
   These paths do NOT overlap with any other agent's file ownership.

4. GRACEFUL DEGRADATION: If translation fails completely:
   - English originals exist (authoritative)
   - App is fully deployed and functional
   - SOT records translation.t_gates as FAIL
   - User is NOT impacted (사역자 never sees reports directly)

5. REVERSIBLE: AC-4 can be disabled by:
   - Removing @app-translator from agent roster
   - Removing translation tasks from orchestrator flow
   - Removing validate_translation_pair.py hook
   - No other files or configurations need to change
```

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| SOT | Single Source of Truth — `app-state.json` |
| pACS | Post-step Autonomous Calibration Scoring (F, C, L dimensions) |
| CCP | Code Change Protocol — 3-step analysis before code changes |
| CAP | Coding Anchor Points — 4 attitude rules for code changes |
| TDD | Test-Driven Development — RED → GREEN → REFACTOR cycle |
| Fork | Parallel sub-agent execution (independent instances) |
| Agent Team | Claude Code experimental feature for coordinated parallel agents |
| Fallback Tier | Escalation level (1=Team → 2=Sequential → 3=Direct → 4=Human) |
| AC-4 | English-First Execution — all agent reasoning/artifacts in English, then translated to Korean |
| Translation Pair | English original (.md) + Korean translation (.ko.md) kept together |
| T-gates | Translation quality gates (T1=existence, T2=pACS≥70, T3=glossary consistency) |
| NON-BLOCKING | Translation runs in parallel — does not delay next phase |
| P1 Scripts | Deterministic Python validation scripts — hallucination prevention |
| H-CRITICAL | Verification that MUST be deterministic (script only, no AI reasoning) |
| H-MAJOR | Data extraction by script, judgment by AI |
| H-SAFE | Inherently creative/subjective — AI appropriate |

## Appendix B: Cross-References

| This Document Section | References |
|----------------------|-----------|
| §1 Absolute Criteria | AGENTS.md §2, soul.md §0 |
| §2 Architecture | workflow.md "Role Definitions" |
| §3 SOT Schema | workflow.md "SOT Schema" |
| §4 Agent Definitions | workflow.md "Claude Code Configuration" |
| §5 Agent Teams | code.claude.com/docs/en/agent-teams |
| §7 Hooks | .claude/settings.json, workflow.md "Hooks" |
| §8 Skill | CLAUDE.md "스킬 사용 판별" |
| §9 TDD | workflow.md Step 8, AGENTS.md §3 |
| §11 Code Standards | AGENTS.md §2 (절대 기준 3, CCP, CAP) |
| §12 Context Loading | workflow.md "Context Loading Strategy" |
| §4.8 app-translator | .claude/agents/translator.md (parent genome), translations/glossary.yaml |
| §9.5 P1 Scripts | AGENTS.md §3 P1 (data refinement), parent hooks/scripts/validate_*.py pattern |
| §16 Preservation | soul.md §0 (DNA inheritance), AGENTS.md §2 (absolute criteria) |
