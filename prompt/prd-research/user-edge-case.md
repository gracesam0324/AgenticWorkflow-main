## User Research — Edge Case Persona (high-dependency)

### Persona
**Min-jun Park** — Offline-First Incident Response & Forensics Lead for an air‑gapped industrial network

- **Role / context**: Leads a small SOC/IR team supporting critical infrastructure (power/water/manufacturing). Environment is **air‑gapped or intermittently connected**, with strict change-control and evidence-handling requirements. Works from a hardened Windows laptop inside secure facilities.
- **Why “edge case”**: Most automation tools assume internet access, cloud integrations, permissive installs, and weak audit trails. Min-jun’s world has **none** of those—yet the workload is automation-hungry.
- **Day-in-the-life pressure**:
  - Receives a USB-delivered alert bundle or an internal ticket with logs + a suspected compromised host.
  - Must **triage fast**, produce **repeatable evidence**, and generate **exec-ready reports** under time pressure.
  - Every action on the machine may be scrutinized later (regulators, internal audit, legal).
- **Hard constraints**:
  - **Local-first only**: No external network calls, no telemetry, no cloud LLM endpoints.
  - **Deterministic, auditable runs**: Must show what ran, when, on which inputs, and produce reproducible outputs.
  - **Least privilege**: Often cannot run as admin; installs may be blocked; only approved binaries/scripts allowed.
  - **Data sensitivity**: Handles credentials, proprietary configs, personal data, and potentially malware.
- **Pain without it**:
  - Manual, error-prone SOP execution across multiple tools (PowerShell, Sysinternals, custom scripts).
  - Inconsistent results between analysts; hard to reproduce; weak chain-of-custody.
  - Slower containment/remediation → increased downtime + compliance risk.

---

### Top 3 non-negotiable jobs-to-be-done (JTBD) and concrete features

#### 1) JTBD: Run a full incident triage workflow offline, reliably, and fast.
- **Offline execution guarantee**: “no network” mode that hard-blocks outbound connections at runtime for the agent and child processes, with a **proof-of-block** log.
- **Prepackaged local toolchain**: run workflows using **bundled, checksummed tools** (or an organization-approved tool registry) without fetching dependencies.
- **Idempotent runs + resumability**: resume from last verified step without corrupting evidence outputs.

#### 2) JTBD: Produce audit-grade evidence and reports that stand up to review.
- **Chain-of-custody & provenance**: input/output hashes, tool versions, exact commands, timestamps, host identifiers, operator identity into an immutable log.
- **Reproducible case bundle**: stable structure like `inputs/`, `artifacts/`, `logs/`, `reports/` + manifest.
- **Human-readable report generation**: report (Markdown/PDF) referencing artifact paths + hashes; clearly states what was/wasn’t verified.

#### 3) JTBD: Safely automate remediation steps without breaking production or policy.
- **Policy guardrails**: local policy engine (YAML/JSON) restricting actions (e.g., read-only triage vs containment), deny-lists for destructive commands.
- **Dry-run + diff preview**: state-changing steps must show “what will change” preview.
- **Approval checkpoints**: optional explicit confirmation gates for high-risk steps, producing approval records.

---

### Success definition and measurable signals

**Success definition**: In an air-gapped incident, run triage→analysis→report locally end-to-end, generating audit-grade artifacts + decision-ready report, minimal manual intervention, zero policy violations.

**Measurable signals (local, privacy-preserving)**:
- Time-to-triage reduction vs current manual SOP.
- Reproducibility rate: rerun case bundle and match critical outputs/hashes within tolerance.
- Audit completeness: required provenance fields present.
- Policy violations: 0 successful violations; visibility into attempted ones.
- Workflow completion rate without manual repair.
- False containment events: near 0; any occurrence is severe.

---

### Adoption, blockers, churn triggers

**Why adopt**
- Offline-first + compliance-ready.
- Standardization across analysts; reduced variance.
- Automated audit trail.
- Guardrails/previews reduce mistakes under stress.

**Adoption blockers**
- Trust gap (non-determinism fears).
- Security review overhead (code signing/allowlisting).
- Compatibility with approved tools, Windows hardening, limited privileges.
- Evidence contamination risk (unexpected file modifications/timestamps/network).

**Churn triggers**
- Any high-profile failure: network call, evidence modification, unapproved destructive action.
- Opaque behavior: cannot explain step-by-step or reproduce outputs.
- Operational brittleness under constraints (no admin, locked dirs, missing deps).
- Poor change control: updates alter behavior without version pinning/release notes; cannot lock to validated version.

