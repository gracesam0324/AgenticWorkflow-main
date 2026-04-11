## Tech Direction — Componentized / “Local Microservices” Architecture (long-term)

### Core principle (fits SOT + single-writer DNA)
- Keep **Single Source of Truth (SOT)** as a single file (e.g., `state.yaml`) with **one writer** (Orchestrator).
- All other components are **read-only** on SOT and emit **append-only artifacts/logs**.

### Process map (local “microservices” = separate processes)
1) **Orchestrator (controller, single writer)**
   - Owns execution loop, transitions, retry budgets, merges; updates `state.yaml`.
   - Provides a small control API (start/stop/pause/enqueue).
2) **Artifact Store (content-addressed filesystem)**
   - Durable storage for outputs/intermediates/snapshots/logs.
   - Interface: `put/get/list` by SHA256 + named pointers.
3) **Event Journal (append-only)**
   - Structured event log for everything (steps, tools, gates, retries, decisions).
   - Enables debugging, “replay”, timeline UI, derived metrics without mutating SOT.
4) **Gate Runner (deterministic validation service)**
   - Runs deterministic validators / policy-as-code (e.g., validate_* scripts).
   - Separate worker process for responsiveness and safe parallel validation.
5) **Agent Runtime Adapter (LLM/tool boundary)**
   - Standardizes tool execution and sandboxes permissions.
   - Does **not** write SOT; returns artifacts + structured results to Orchestrator.
6) **Plugin Host**
   - Discovery/lifecycle/permissions/versioning for extensions (tools, gates, importers/exporters).

### IPC options (Windows-friendly)
- **HTTP/JSON on localhost**: simplest, debuggable, cross-language. Must secure loopback.
- **gRPC on localhost**: typed contracts, streaming; more tooling.
- **JSON-RPC over stdin/stdout** for plugins: easiest plugin model; needs robust framing/timeouts.

Pragmatic hybrid: core services use HTTP/gRPC, plugins use JSON-RPC subprocess.

---

### Plugin system (minimum standardization)
- **Types**: Tool plugins, Gate plugins, Importer/Exporter plugins.
- **Contract**: manifest (name/version/capabilities/permissions/OS), RPC methods `describe()`, `invoke(input)`, `health()`, `shutdown()`.
- **I/O discipline**: pass **artifact references** (hash IDs + metadata), not huge raw payloads.
- **Isolation**: default subprocess + filesystem allowlists; later WASM or OS sandbox.

---

### Stack options (trade-offs)
1) **Python-first monorepo, modular-by-boundary**
   - Core Python, IPC via FastAPI or grpcio.
   - Pros: fastest iteration; reuse deterministic validators.
   - Cons: perf/concurrency ceiling for heavy workloads.
2) **TypeScript control-plane + Python workers**
   - Node/TS Orchestrator/UI; Python gate/validator workers.
   - Pros: UI/daemon ergonomics; strong JSON tooling.
   - Cons: two runtimes; contract discipline required.
3) **Rust/Go kernel + polyglot workers**
   - Kernel for Orchestrator/Store/Journal; Python validators; TS UI.
   - Pros: long-term reliability/scalability.
   - Cons: highest upfront cost.

Recommendation for 6 months: start with Option 1, but design contracts so later extraction/replacement is possible.

---

### 0–6 months (realistic, high-leverage)
- Module boundaries matching future processes.
- Artifact Store v1 (content-addressed) + Event Journal v1 (append-only JSONL).
- Gate Runner v1 to execute validations and stream results.
- Plugin Host v1 (subprocess JSON-RPC + permissions).
- Replayable runs and minimal local dashboard reading journal/artifacts.

### After 6 months (easier if contracts are right)
- Extract components into daemons, stronger sandboxing (WASM), richer plugin ecosystem (still local).
- Background scheduling, caching policies.
- Optional non-SaaS sync (LAN/Git replication) if ever desired.

---

### Top risks + mitigations
1) **Over-decomposition early**
   - Mitigate: modular monolith first; extract Gate Runner + Plugin Host first if needed.
2) **SOT consistency violations**
   - Mitigate: make SOT write API inaccessible outside Orchestrator; write-audit gate.
3) **Plugin/security surface**
   - Mitigate: subprocess plugins + permission manifests + path allowlists; default-deny network; safety hooks at Runner boundary.

