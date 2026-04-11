## User Research — Mainstream Personas (local-first, non-SaaS)

### Personas

#### Persona A — “Pragmatic Builder” (Solo developer / maker)
- **Profile**: 2–7 years experience, ships side projects and internal tools; comfortable with Git/CLI but values time. Uses Cursor/VS Code, Docker occasionally.
- **Goals**: Turn specs into working code fast; keep control of source + secrets; avoid “AI spaghetti” that’s hard to maintain.
- **Context**: CRUD apps, integrations, scripts, small services; frequent iteration.
- **Anxieties**: Hidden changes, breaking existing setup, unclear diffs, dependency mess, non-reproducible runs.

#### Persona B — “Ops-Minded Team Dev” (Engineer in a small company)
- **Profile**: Works in a repo with conventions, CI, security constraints; may not be admin on the machine.
- **Goals**: Automate repetitive implementation tasks while staying compliant; ensure changes are reviewable, testable, revertible.
- **Context**: Deterministic runs, audit trails, safe defaults; integrations with existing services.
- **Anxieties**: Secret leakage, destructive commands, mismatch with team standards, “it worked on my machine,” opaque agent actions.

---

### Must-have vs nice-to-have (top 3 each)

#### Persona A — Pragmatic Builder
- **Must-have**
  - Transparent change control: plan → staged edits → diffs; easy rollback; no surprise file writes.
  - Local-first safety: no network by default; explicit permission gates for web access; secret redaction.
  - Fast iteration loop: “try → observe → fix” with runnable commands and concrete next steps.
- **Nice-to-have**
  - Opinionated templates/starters.
  - Multi-agent parallelism (UI/API/tests/docs) with one merged output.
  - Local context memory of repo conventions and decisions.

#### Persona B — Ops-Minded Team Dev
- **Must-have**
  - Reproducibility: pinned deps, deterministic scripts, environment checks, “one-command” repeatable execution.
  - Auditability: structured logs of actions, approvals, rationale; traceability requirements → diffs/commits.
  - Guardrails: policy enforcement (no destructive ops, no secret exposure, protected files).
- **Nice-to-have**
  - CI integration: PR-ready changes, local tests/linters, CI hints.
  - Policy packs for org conventions.
  - Offline knowledge base (local docs indexing/search).

---

### User journey (intent → setup → execution → iteration → trust)

1) **Intent**
- User expresses outcome + constraints.
- System: restates scope/assumptions; proposes plan + verification; calls out risks early.

2) **Setup**
- Checks prerequisites and repo conventions.
- Minimal local configuration (policy/safety, working dir boundaries).
- Trust: visible no-network default; clear permission prompts for sensitive actions.

3) **Execution**
- Observable artifacts: diffs, commands and outputs, incremental verification.
- Trust: checkpoints/optional commits; diagnosis + targeted retries.

4) **Iteration**
- Updates plan; applies surgical changes; re-verifies.
- Trust: changes remain localized; trade-offs explained.

5) **Trust**
- Adoption increases if: runnable results, respects boundaries, audit trail exists.

---

### Success definition (activation/retention) + what “it works” means

**Activation**: first session reaches a working outcome the user can run locally and understand.
- Setup without manual debugging.
- At least one verified artifact (pass test/build/demo).
- User reviews diff and agrees it matches intent.

**Retention**: user returns because workflow is reliable and controllable.
- Reuse on existing repo.
- Delegates larger tasks over time.
- Uses logs/checkpoints in review.

**“It works”** means:
- Feature exists and behaves as specified locally.
- Verification passes (build/tests/lints) or failures are clearly attributable and addressed.
- Safety: no unexpected network calls; no secret leaks; no destructive actions without approval.
- Maintainability: follows repo conventions; reviewable diffs; rollback path exists.

---

### Validation approach (how to verify these assumptions)
- Discovery interviews (6–10), split solo vs team devs.
- Task-based usability tests (4–6) on “add a feature to an existing repo”.
- Lightweight diary study (1–2 weeks).
- Opt-in local-only instrumentation: completed runs, verification pass/fail, retries, rollback usage.

