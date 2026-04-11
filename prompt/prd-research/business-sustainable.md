## Business Direction — Sustainable Growth (local-first, non-SaaS)

### Sustainable monetization models (and why)
- **Perpetual license (tiered)**
- **Commercial per-seat + free personal**
- **Optional maintenance & updates (annual)**
- **Pro add-ons** (visual builder, advanced tracing, policy packs, signed binaries)
- **Marketplace** (local packages; download-once; no runtime cloud dependency)
- **Services** (onboarding, template creation, enablement workshops)

Recommended mix: **commercial per-seat + optional maintenance**, plus services for first 10–30 customers; add add-ons later; marketplace after core stabilizes.

---

### Distribution channels with low burn
- Dev communities (GitHub, Reddit, Show HN)
- Product-led spread via shareable artifacts (workflows/logs/repro reports)
- Integration-led starter packs (Git/Docker/Python/Node/PowerShell/VS Code tasks)
- Short demo videos
- Partnerships (local LLM runtimes, template authors)
- Targeted outbound (compliance-heavy teams rejecting SaaS)

---

### KPI targets (6 months; staged)
- **Month 1–2**
  - Activation: ≥35% run 3 successful workflows in 7 days
  - Time-to-first-value: median ≤15 minutes
  - Support load: <10% need 1:1 help
- **Month 3–4**
  - Paid conversion (commercial leads): 3–7% of engaged users
  - Revenue: \$5k–\$15k to validate pricing/packaging
  - Refund rate: <5%
- **Month 5–6**
  - New paid seats: 30–80 seats/month (or equivalent revenue)
  - Net revenue: \$10k–\$30k/month (price/services dependent)
  - Retention proxy: ≥60% upgrade/renew maintenance
  - In-org expansion: ≥1.3 avg seats per initial buyer within 60 days

---

### Minimal feature set to reach survivability
- Deterministic workflow engine: retries/timeouts/resume + clear failure modes
- Strong local logs: human-readable + JSONL
- Local-first safety & governance: redaction, permission scoping, no-network default, allowlists
- Reproducibility: pinned tool versions, environment capture, artifact hashing
- Template system (20–40 high-quality templates) + template wizard
- Minimal extensibility: step plugins + local LLM connectors + file-based import/export
- Commercial readiness: offline-friendly licensing, EULA, Windows-first smooth install
- Proof-of-value UX: `init` → `run` → report artifact; dry-run + estimates where possible

---

### Risks and de-risking
- Competes with free scripts → sell reliability/auditability/reuse/governance/support
- Local LLM variability → multi-runtime support, graceful degradation, tested hardware profiles
- Security trust barrier → safe defaults, explicit prompts, signed releases, transparent logs
- Support burden → doctor command, self-diagnosis bundles, docs, limit integrations early
- Pricing mismatch → early paid pilots + services, test 2–3 price points
- Distribution stall → packs + shareable artifacts, demos, community cadence

