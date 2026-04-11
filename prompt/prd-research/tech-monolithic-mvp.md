## Tech Direction — Monolithic MVP (local-first desktop/CLI runner)

### Goals & non-goals
- **Goal**: single-process, offline-capable workflow runner that can plan/execute multi-step agent tasks, store artifacts locally, safe-by-default.
- **Non-goal (MVP)**: multi-user, cloud sync, remote execution, plugin marketplace, distributed agents.

### High-level shape (one binary/app, modular inside)
- **UI layer**: CLI as primary (create/run/resume workflows, inspect runs, export bundles). Optional local web UI later.
- **Workflow engine**: workflow spec (YAML/JSON or Markdown+frontmatter), deterministic state machine (`RUNNING/PAUSED/SUCCEEDED/FAILED/CANCELLED`), sequential scheduler first.
- **Agent runtime**: local LLM adaptor (Ollama/local gateway) + optional BYOK keys; capability-based access; strict structured output parsing; safety policies (allowlists, path sandboxing, network off by default, budgets/timeouts).
- **Tooling sandbox**: constrained tools (`read_file`, `write_file`, `run_command`, `search`; `http_fetch` disabled by default). Argument-vector execution (no shell injection), cwd whitelist, deny destructive patterns; workspace-root confinement with explicit extra directory grants.
- **Local persistence**:
  - Run store: SQLite for workflows/runs/steps/events.
  - Artifact store: filesystem for outputs/logs/diffs/exports.
  - Per-run SOT: `state.json` or `state.yaml` updated atomically.
- **Observability**: JSONL logs + timing + tool call trace; “repro bundle” export (spec/state/prompts redacted/tool traces/artifacts).

### Suggested data layout
- `runs/<run_id>/state.json`
- `runs/<run_id>/events.jsonl`
- `runs/<run_id>/artifacts/step-03/output.md`
- `runs/<run_id>/artifacts/step-03/tool-traces.jsonl`
- `runs/<run_id>/exports/repro-bundle.zip`

---

### Stack options (MVP speed)

#### Option A (recommended): Python 3.11+
- CLI: Typer (or Click)
- Persistence: sqlite3 (or SQLModel/SQLAlchemy later)
- Validation: Pydantic v2
- YAML: ruamel.yaml or pyyaml
- LLM: local Ollama HTTP + JSON schema structured outputs
- Packaging: uv + pyinstaller (Windows-friendly)

Trade-off: sandboxing tends to be policy-based rather than hard isolation → requires careful guardrails.

#### Option B: TypeScript (Node 20+)
Great future local UI ergonomics; more risk around safe command execution; often slower to iterate on agentic runner than Python.

#### Option C: Go
Single binary distribution; slower iteration on LLM/prompting ecosystem vs Python.

Pragmatic path: start Python, consider Go rewrite only after product fit if distribution becomes dominant pain.

---

### Scope: MVP vs Phase 2 (with complexity)

**MVP**
- Workflow spec + runner (Medium)
- Local persistence (Medium)
- Tool sandbox core (High)
- Local LLM integration (Medium)
- Auditability (Medium)
- Safety defaults (High)

**Phase 2**
- Local dashboard UI (Medium)
- Limited parallelism (High)
- In-process plugin/tool system (High)
- Multiple local providers/BYOK (Medium)
- Workspace intelligence (indexing/semantic search/caching) (High)

---

### Timeline estimates (1–3 devs)
- **1 dev**: ~8 weeks MVP (runner skeleton → persistence → sandbox hardening → LLM quality + dogfooding)
- **2 devs**: ~5–6 weeks MVP
- **3 devs**: ~4–5 weeks MVP

---

### Top 3 technical risks + verification
1) **Unsafe tool execution**
   - Tests for allow/deny logic (path traversal, symlinks), red-team command suite, default no-network.
2) **Non-deterministic/brittle runs**
   - Atomic writes, crash simulation, event-log replay, repro bundle re-run in clean environment.
3) **Prompt/schema failures cascading**
   - Strict schema validation + bounded repair loop, golden tests, parse-failure tracking.

### What to avoid
- Microservices/distributed agents early.
- “agent can run any command” raw shell.
- Default network access.
- Early plugin marketplace.
- Storing secrets in logs/state.
- Premature parallel execution.

