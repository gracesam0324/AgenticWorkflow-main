# Branch 2.1: Evolutionary Architecture (Incremental Expansion)

**Architect posture: Start simple, evolve as needed.**

---

## Premise

Local-first constraints — single-writer SOT, local filesystem, append-only artifacts, existing Python hooks, Windows-specific IPC already built — actually **favor** the evolutionary approach because they eliminate the distributed-systems complexity that usually forces big upfront design.

---

## 1. Initial MVP Architecture (6 Months)

### Design Philosophy

**One process. One state file. One append-only log. Everything else is a function call.**

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    cmux-windows Process                         │
│                                                                 │
│  ┌─────────────┐    ┌──────────────────────────────────────┐   │
│  │   CLI/TUI   │───▶│           Workflow Engine            │   │
│  │  (Textual)  │    │                                      │   │
│  └─────────────┘    │  plan() ──▶ validate() ──▶ step()   │   │
│                     │                │               │      │   │
│                     │         HookRunner        ExecutionCtx│  │
│                     │         (in-proc)         (in-proc)  │   │
│                     └──────┬───────────────────────┬───────┘   │
│                            │                       │           │
│              ┌─────────────▼──────┐   ┌───────────▼────────┐  │
│              │   LLM Adapter      │   │  IProcessExecutor  │  │
│              │  (ILLMProvider)    │   │  ConPTY/NamedPipe  │  │
│              │                   │   │  (already built)   │  │
│              │  ┌─────────────┐  │   └────────────────────┘  │
│              │  │ OpenAI shim │  │                            │
│              │  │ Ollama shim │  │                            │
│              │  │ Anthropic   │  │                            │
│              │  └─────────────┘  │                            │
│              └────────────────────┘                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    State Layer                           │  │
│  │                                                          │  │
│  │   state.yaml (single-writer SOT)                        │  │
│  │   artifacts/ (append-only, one file per step)           │  │
│  │   audit.jsonl (append-only structured log)              │  │
│  │   secrets/ (DPAPI SecretStore — already built)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

External:
  LLM API endpoint (local Ollama or remote via API key)
  Python subprocess (hooks/validators — already built)
```

### Technology Per Layer

| Layer | Technology | Rationale |
|---|---|---|
| Execution Engine | Python 3.11+ asyncio | Hooks already Python; avoids FFI boundary. Single event loop = natural single-writer. |
| State Store | state.yaml + filelock (PyYAML + portalocker) | Human-readable, git-diffable, zero infra. Filelock enforces single-writer SOT rule. |
| Artifact Store | artifacts/*.jsonl | Append-only, one file per step |
| LLM Adapter (ILLMProvider) | httpx async client + provider registry dict | Thin shim per provider. Adding new provider = one new class, no framework. |
| Hook Runner | Direct subprocess() call with timeout + captured stdout/stderr | Python validators already exist. Wrap with timeout and structured output parser. No plugin framework yet. |
| IPC (existing) | ConPTY + NamedPipe (already built) | Keep exactly as-is. Do not touch. |
| CLI/TUI | Textual 0.x | Rich async TUI, Windows-native terminal support, no Electron, no web server. |
| Audit Trail | audit.jsonl (append-only) | One JSON line per event. stdlib json. No log framework. |

### Development Complexity: LOW

1. No inter-process coordination. No message queues. No RPC. State changes = sequential writes to one YAML file under filelock.
2. All existing components (DPAPI, ConPTY/NamedPipe, Python hooks) slot in as direct function calls or subprocess calls. Zero integration friction.
3. asyncio handles concurrency within one process without threads — avoids Windows threading edge cases with ConPTY.
4. `IWorkflowPlanStore` interface = dead-simple YAML reader/writer on day one. Swap backing store later without touching callers.

### Why This Is The Right Starting Point

At month six, you will have real usage patterns. You will know which workflows run longest, which hooks are slowest, which LLM providers are used in practice. That knowledge is worth more than any upfront architectural prediction.

The single-writer, local filesystem, append-only constraints are not limitations to engineer around — they are architectural decisions that eliminate entire categories of bugs (split-brain, partial writes, race conditions on state).

---

## 2. Evolution Path (12–24 Months)

### Extraction Priority Order

```
Month 6-9:  Hook Runner ──▶ Out-of-process plugin host
Month 9-12: LLM Adapter ──▶ Local caching + retry orchestrator
Month 10-14: State Store ──▶ SQLite (if query complexity grows)
Month 14-18: Scheduler ──▶ Only if recurring/triggered workflows needed
Month 24+:  Plugin system ──▶ Only if third-party extensibility is real requirement
```

### When To Split Into Separate Processes

**Hook Runner extraction trigger** (any of these):
- A hook crashes and takes down the workflow engine
- Hook execution time exceeds 30 seconds regularly
- Users request sandboxing or resource limits on hooks

Extraction path already designed: NamedPipe IPC already exists. Hook host becomes another process speaking the existing protocol. One-sprint refactor, not an architecture change.

**SQLite migration trigger** (any of these):
- Queries like "show all workflows that touched file X" require more than a grep
- state.yaml grows beyond ~5,000 lines and YAML load time becomes measurable
- Cross-workflow queries needed for reporting or debugging

Migration cost is bounded: `IWorkflowPlanStore` is already an interface. Write `SQLiteWorkflowPlanStore`, run both in parallel for one sprint, flip the default, delete `YAMLWorkflowPlanStore`. The audit.jsonl stays append-only forever — forensic record, never queryable-primary.

### When To Add Scheduling

Trigger: (a) at least three users explicitly cannot accomplish their goal without it AND (b) Windows Task Scheduler workaround is demonstrably inadequate. Implementation: APScheduler in-process, persisting to separate `schedules.yaml`. Does not touch workflow engine internals.

### When NOT To Add a Plugin System

Add only when: external developers exist who want to extend the system AND the current hook/validator extension point is provably insufficient. **Until both conditions are true, the hook runner subprocess model IS your plugin system.**

---

## 3. Architecture Evolution Costs

### Initial Development Cost: LOW

| Component | Estimate |
|---|---|
| Workflow Engine core | 3 weeks |
| ILLMProvider + 3 shims | 1.5 weeks |
| IWorkflowPlanStore (YAML) | 1 week |
| Hook Runner wrapper | 1 week |
| CLI/TUI (Textual) | 2 weeks |
| Audit trail (append-only) | 3 days |
| Integration + test harness | 2 weeks |
| Buffer (Windows quirks) | 1 week |
| **Total MVP** | **~12 weeks** |

12 weeks build + 6 weeks hardening/testing + 6 weeks buffer = fits 6-month window.

### Refactoring Costs: MEDIUM — Specific Estimates

| Refactor | Cost | Risk | Trigger |
|---|---|---|---|
| Hook Runner → separate process | 2 weeks | Low | Month 7-9 |
| YAML → SQLite state store | 3 weeks | Medium | Month 10-14 |
| In-proc scheduler → APScheduler | 1 week | Low | Month 14-18 |
| LLM cache layer | 1 week | Low | Month 9-12 |
| Plugin host protocol | 4 weeks | Medium | Month 20-24+ |
| **Total refactoring (2 years)** | **~11 weeks** | | |

Because `IWorkflowPlanStore`, `ILLMProvider`, and `IProcessExecutor` are interfaces from day one, every refactor is an implementation swap, not an interface change.

### Total 2-Year Cost

| Phase | Engineering Weeks |
|---|---|
| MVP build | 12 weeks |
| MVP hardening | 6 weeks |
| Evolution refactors | 11 weeks (spread across 18 months) |
| Ongoing feature work | ~24 weeks (1 feature/month avg) |
| **Total** | **~53 weeks** |

For 2-person team over 24 months: comfortable. Solo developer: aggressive but achievable because the architecture doesn't fight you.

---

## 4. Risks

### Initial Performance Limitations

Single-event-loop, single-process model will not handle concurrent workflow execution on the same state file.

**Mitigation**: CLI refuses concurrent runs on same state file (early exit with clear error). Design multiple state files in separate directories for independent parallel workflows — still local-first, no shared server needed.

### The Critical Month 8-12 Window

The most dangerous window: MVP has real users, debt accumulates fast, temptation is to add features instead of refactoring. Specific risk: adding scheduler + plugin system + caching simultaneously without first extracting hook runner creates entanglement that costs 2-3x to untangle.

**Mitigation**: Treat refactor triggers as actual gates. Write them down. When trigger fires, next sprint is the refactor, not a new feature.

### SQLite Migration Bug Risk

YAML is the SOT. If migration has a bug, you corrupt workflow history.

**Mitigation**: Keep audit.jsonl as canonical forensic record forever (SQLite = queryable index, not SOT). Run both stores in parallel for 2 weeks comparing outputs. Provide recovery tool that rebuilds SQLite from audit.jsonl — build this before needed.

### Architectural Decay Risk

Each evolution step is locally reasonable, but accumulated result is a system nobody understands.

**Mitigation**: Maintain one-page `ARCHITECTURE.md` tracking current state of each component ("MVP code", "extracted in sprint 14", "scheduled for replacement"). Update every sprint. 30 minutes/sprint prevents months of archaeology.

---

## Conclusion

### Does This Approach Fit This Project?

**Yes. Definitively.**

Your specific constraints — single-writer SOT, local filesystem, append-only artifacts, existing Python hooks, Windows-specific IPC already built — create a system where the evolutionary approach has **lower total cost** than upfront architecture. A microservices or event-sourced architecture would require solving distributed consensus problems that your single-writer constraint already eliminates.

### First 6 Months Dev Time

**12 weeks build + 6 weeks hardening = 18 weeks total effort.**
- 2-person team: 9 calendar weeks (parallelized)
- Solo developer: 18 calendar weeks (fits 6-month window with 2 weeks margin)

### Technical Debt Level

**Low-to-medium, and intentional.**

| Debt Item | Repayment Point | Cost |
|---|---|---|
| No hook sandboxing | Month 7-9 | 2 weeks |
| YAML state (no query) | Month 10-14 | 3 weeks |
| No LLM retry orchestration | Month 9-12 | 1 week |
| No concurrent workflows | Month 14+ | Architecture decision |

Known debts with known repayment schedules ≠ unknown debt from rushed feature work. Discipline: treat trigger conditions as mandatory, not optional.

### The ONE Thing That Could Make This Fail

**Adding a second writer to state.yaml before the single-writer guarantee is formally enforced.**

This sounds trivial. It is not. If state.yaml gets concurrent writes — from a background thread scheduler, from a "just for the dashboard" web API, from two CLI invocations in separate terminals — you will have non-deterministic state corruption that is extremely difficult to reproduce.

The enforcement is **one filelock, acquired at engine startup, released at engine shutdown.** Write it on day one. Never bypass it. That single constraint is what makes everything else in this architecture trustworthy.
