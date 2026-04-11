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
