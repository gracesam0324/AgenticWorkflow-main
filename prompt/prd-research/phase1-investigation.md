# Phase 1 Investigation Archive (Teammates) — PRD Direction Setting

Created: 2026-04-02

## Global Assumption (Important)
- This product is **local-first** and runs on the **user’s local computer**.
- It is **NOT** SaaS / hosted.
- The core value proposition is **reliable, repeatable agentic workflows** with **deterministic verification artifacts** and **local trust & safety**.

## Market Researcher — Branch A (Optimistic View)

### Market size
- **Medium**: developer productivity / AI engineering tools niche.
- Core buyer is indie devs and small teams who want reliable, repeatable multi-step agent workflows (not “chat”, but “workflow that can be trusted and audited”).

### Market entry timing
- **Now (0–12 months)**: reliability/safety gaps in current agent usage are becoming obvious; local-first deployments are increasingly practical.

### Differentiation (3 items)
1. **Deterministic safety + verification gates out-of-the-box**
2. **Local-first context preservation with strict Single Source of Truth** (`state.yaml`)
3. **Repeatability as a product promise** (Anti-Skip guard ensures required artifacts exist and are meaningful)

### Must-have features (Top 3)
1. **`Context Preservation SOT: state.yaml + restore_context.py/save_context.py`**
2. **`L1 Verification Gate`** using `validate_review.py/validate_translation.py/validate_verification.py` with `verification-logs/step-N-verify.md`
3. **`Safety Hook Suite`** using `block_destructive_commands.py + security_sensitive_file_guard.py + predictive_debug_guard.py`

### If we omit must-haves
- Without verification gates → users experience “agent succeeded sometimes”, failures slip through.
- Without safety hooks → local-first users won’t trust it (destructive tool calls + secret exposure risk).
- Without context preservation SOT → workflow resume becomes non-deterministic.

### Key risks (3+)
1. Commoditization pressure as agent ecosystems add reliability features
2. Trust/liability risk if safety/validation misses edge cases
3. Adoption friction (learning curve + configuration complexity)
4. Local-first operational variability (Windows/macOS, permissions)

### What to validate in next 2 weeks
1. Willingness-to-pay + “reliability threshold” (5–10 interviews)
2. Gate efficacy pilot (intentionally broken outputs; confirm `verification-logs` blocks progression)
3. Safety red-team test on Windows (destructive commands + sensitive patterns)

## Market Researcher — Branch B (Cautious View)

### Market size
- **Small (possibly Medium in a narrow niche)**:
  - indie devs/small teams exist, but budgets are limited.
  - agent/workflow market is fragmented; users may only need orchestration.
  - differentiation is narrowed specifically to “reliability + safety + verification”.

### Market entry timing
- **Ambiguous (not yet, but also already late)**:
  - “Not yet”: trust formation is ongoing; local-first has setup friction; safety expectations rising due to public agent failures.
  - “Already late”: many adjacent tools exist (agent frameworks + parts of the promise), compressing willingness-to-pay unless measurable outcomes are shown.

### Differentiation (3 items)
1. **Verification-first execution** (fails closed)
2. **Local-first trust artifacts** (replayable audit packages)
3. **Safety hooks as default behavior** (not optional)

### Must-have features (Top 3)
1. **Deterministic Verification Gate** (artifact-based acceptance criteria; fails closed)
2. **Safety Hooks Pack** (destructive block + secret scanning + constrained tool execution)
3. **Replayable Run Artifacts** (export/import “repro pack” with trace + verification logs)

### If we omit must-haves
- Weak/optional verification → “yet another agent wrapper”.
- Safety not default/proven → adoption trust collapses.
- No replayability/audit → debugging becomes manual; value collapses.

### Key risks (3+)
1. Commoditization risk: differentiation becomes “implementation detail”
2. Trust & evidence gap: failure to prove better outcomes than alternatives
3. Setup friction: local-first + environment diversity
4. Integration surface: must support common tool patterns (shell/files/APIs)
5. Feature creep: diluting the verification/safety thesis

### What to validate in next 2 weeks
1. Failure-mode interviews (8–12 indie devs)
2. Constrained prototype test (destructive commands, secret-like strings, partial outputs)
3. Willingness-to-pay signal (survey / landing-page focused on verification + replayable artifacts + safety)

## User Experience Researcher — Branch A (Edge Case Users)

### Personas (2)
1. **Dr. Mira Kwon** (regulated hospital lab; air-gapped; PHI/PII encrypted; binary allowlists; no egress)
   - Pain: steps can “look correct” but be incomplete/unsafe; secret leakage is unacceptable.
   - Needs: verifiable artifacts; deterministic failures; no secret/network access.
2. **Rahul Park** (safety-critical embedded/robotics verification engineer; deterministic repeatability)
   - Pain: outputs not replayable; no traceability from evidence to claims.
   - Needs: immutable audit trail + validation logs matching PRD criteria.

### Pain points (top)
- Hallucination/completion ambiguity without deterministic proof
- Secret exposure risk
- Non-determinism
- No offline guarantees
- Weak traceability

### Must-have features (Top 5)
1. **Air-Gapped Offline Runner (No Egress Guarantee)**
2. **L0 Anti-Skip Guard (Artifact Presence + Meaningful Size)**
3. **Secret Leak Prevention Filter (Detection + Redaction + Audit)**
4. **Verification Gate (Deterministic criteria-driven validation reports; fails closed)**
5. **Immutable Execution Replay Bundle (context snapshots + validation logs)**

### Success definition
- 0 confirmed secret leaks in stored logs/artifacts on representative tests
- 100% deterministic completeness for steps with outputs and verification criteria
- replay parity: >= 99% validation parity (PASS/FAIL match) and equivalent artifacts within tolerances
- air-gapped reliability: >= 99% runs without network/tool download attempts
- user trust: sign-off threshold (e.g., >= 80/100 internal trust score)

### Final conclusion (essential 3)
- `Secret Leak Prevention Filter`
- `Verification Gate (with L0 Anti-Skip Guard)`
- `Immutable Execution Replay Bundle`
- If missing: **product fails (Y)**

## User Experience Researcher — Branch B (Mainstream Users)

### Personas (3)
1. **Alex “Indie Automation” Kim**: wants local automation with clear trust boundaries; dislikes chat-only “black boxes”.
   - Dislikes: Zapier/Make (local mismatch/debug pain), chat agents (replay/audit hard)
2. **Soojin “Backend Ops” Park**: cares about run reliability + recovery (MTTR), hates drift & unclear causality.
   - Dislikes: IDE agents without explicit plan/diff boundary; n8n needs manual assembly
3. **Minho “Team Tech Lead” Lee**: needs auditability, policy compliance, and operational controls.
   - Dislikes: cloud-first tools with unclear execution scope and shallow logs

### User journey (touchpoints)
1. Onboarding: uncertainty about permissions, network, and reproducible execution.
   - Product role: `Local Execution Sandbox (Scoped IO + Network Toggle)` to confirm safety scope early.
2. Automation design: need plan/diff/approval separation.
   - Product role: `Human-in-the-loop Plan & Diff Review`.
3. Execution: failure debugging and state recovery.
   - Product role: `Deterministic Workflow Runs & Replay`.
4. Review & improvement: replay old runs and understand causes quickly.
   - Product role: `Run Timeline Dashboard (Errors, Artifacts, Step Graph)`.

### Must-have features (Top 5)
1. `Local Execution Sandbox (Scoped IO + Network Toggle)`
2. `Plan → Diff → Approval Human-in-the-loop`
3. `Deterministic Run Logs + Replay`
4. `Run Timeline Dashboard (Errors, Artifacts, Step Graph)`
5. `Reusable Task Templates with Versioning`

### Nice-to-have features (Top 5)
1. `Local Context Memory Snapshots (Inspectable RLM)`
2. `Policy Packs (Privacy/Security Profiles)`
3. `Dry-Run + Impact Estimation`
4. `BYO LLM Connector (Bring Your Own Model/Endpoint)`
5. `Multi-agent Merge with Conflict Resolution`

### Success KPIs
- Indie: time to first safe automation <= 30 min; approval trust rate; debug turn time <= 5 min
- Ops: run reliability; MTTR <= 15 min; drift score stable
- Tech lead: audit completeness 100%; reproducibility rate >= target; policy compliance rate (0 violations)

## Technical Architect — Branch A (Monolithic MVP)

### Feasibility
- Monolithic is feasible in ~6 months: single-process state machine + filesystem-backed orchestrator + deterministic gatekeeping reduces integration surface.

### MVP features (5)
1. **Workflow execution engine (single-process state machine)**
   - SOT persisted to `state.yaml`
   - resume semantics based on verified step artifacts
2. **Safety hooks (minimal blocking + warning set)**
   - hook dispatcher (PreToolUse / PostToolUse / Stop / SessionStart / PreCompact)
   - deterministic blocking for destructive/unsafe actions
3. **Verification gates (L0 + L1 in MVP)**
   - L0 Anti-Skip guard (artifact exists + meaningful size)
   - L1 step-specific completion definitions → verification logs
4. **Context preservation with atomic snapshot/restore**
   - latest-context artifact + archives
   - atomic write patterns and concurrency safety
5. **Observability + operator controls**
   - CLI to start/resume/inspect verification/hook logs
   - export “what ran / what failed gates / what artifacts were produced”

### Defer list
- L2 adversarial review with external fact-checking (heavy, more failure modes)
- Translation pipeline (orthogonal once execution/verification loop stabilizes)
- ULW mode / advanced retry escalation (wait until baseline reliability is proven)

### Timeline (rough)
1. Execution engine + SOT + artifacts: 3–5 weeks
2. Safety hooks: 4–6 weeks
3. Verification gates: 4–6 weeks
4. Context preservation: 4–6 weeks
5. Observability/controls: 2–4 weeks

### Key technical risks
1. Resume correctness failure
2. SOT write discipline / race conditions and snapshot corruption on Windows
3. Hook bypass / false confidence in safety/verification
4. Verification gate flakiness due to non-deterministic agent output

### Validate in next 2 weeks
1. End-to-end skeleton run with 3 steps
2. Safety hook interception reliability on Windows (incl. crash/resume)
3. Snapshot/restore invariants under interruption

## Technical Architect — Branch B (Microservices)
- This branch was **aborted** during execution.
- Saved status: TODO (re-run teammate for microservices modular architecture details).

## Business Strategist — Branch A (Aggressive Growth)

### Target segment (aggressive)
- Early adopters who already believe in local-first privacy and want immediate first-session value:
  - privacy/compliance-driven solo consultants/agencies
  - local-first power users

### Initial pricing model options
1. `Paid License + Updates Subscription` (recommended)
   - $49–$99 license + $19–$39/year updates
   - optional support bundle
2. `Tiered Subscription (updates + premium templates/connectors)`
   - $9–$19/month, offline use allowed; subscription gates advanced content/support

### Growth plan (first 100)
- SEO/YouTube setup content for local-first workflows
- community template drops in local AI/privacy/dev communities
- partnerships/referral onboarding with micro-consultants

### Onboarding funnel
1) Landing → download  
2) setup wizard (minimal choices)  
3) run first template → “first success” moment  
4) upgrade prompt at success  
5) follow-up emails (how-to / unlocked value / support offer)

### First 6 months KPIs (targets)
- ~100 paying customers by month 6
- Activation (first success): 50–65%
- Trial/activated → paid: 8–15% (trial) or 3–6% (no trial)
- 30-day retention: 40–60%; updates conversion within 90 days: 10–20%

### Must-have features (Top 3) for aggressive strategy
1. `10-Minute First Success onboarding wizard + template gallery`
2. `Offline-by-default privacy + export/portability ownership`
3. `Frictionless license activation + offline-friendly upgrade path at first success moment`

### Risks & contingencies (examples)
- conversion underperforms → paid onboarding + killer templates + pricing ladder adjustments
- acquisition channel mismatch → tighter local-first messaging + higher-intent communities
- support burden explosion → deterministic setup profiles + compatibility gating + tiered support

## Business Strategist — Branch B (Sustainable Growth)

### Revenue model options (local-first friendly)
1. Perpetual (tiered) license + optional maintenance/updates + support (recommended mix)
2. Subscription (annual) framed as maintenance + verified updates + policy packs
3. Support/services-first (onboarding/template/policy hardening), marketplace later

### Sustainable growth logic
- Retention via replayability, verified determinism, signed/rollback updates.
- Upsell triggers when customers demand governance, audits, offline reliability, and organization-level policy packs.

### First 6 months KPI targets (rough)
- Activation: >= 35% reach “3 successful workflows within 7 days”
- Time-to-first-value: median <= 15 min
- Paid conversion: 3–7% of engaged users
- Revenue validation: early $5k–$15k cumulative run rate (rough target)
- Renewal/upgrade: >= 60% renew/upgrade maintenance within 90 days

### Top 3 must-have features (business)
1. `Deterministic Workflow Replay Kit` (pinned inputs/outputs hashes + execution logs + replay)
2. `Local Trust & Safety Policy Engine` (policy as config: no-network default, allowlist, redaction, evidence)
3. `Signed Offline Release Channel + Rollback` (reduce update-risk fear)

### Risks & mitigation
- Free/open alternatives pressure → re-position around verification/safety/gov + paid pilots
- Trust failures → default deny, allowlist, redaction+evidence, signed releases+rollback
- Support burden → “doctor command” self-diagnosis bundles + tiered support

---
## Notes / Gaps to cover in subsequent deep dives
- Re-run Tech Architect Branch B (microservices / modular architecture) because it was aborted.
- After adding more deep dives, we will synthesize into:
  - PRD structure (Green/Yellow/Red scope)
  - MVP scope (<= 6 months) and explicit acceptance criteria
  - top risks & validation plan

