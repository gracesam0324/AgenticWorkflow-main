# Fallback Paths — 3-Tier Graceful Degradation

## Overview

Every automated step in the pipeline can fail. The fallback system ensures the pipeline degrades gracefully rather than halting. Four tiers of execution are available, from most capable (parallel Agent Teams) to most basic (human intervention).

## Tier Architecture

```
Tier 1: Agent Team (parallel)
  ↓ failure (max retries exhausted)
Tier 2: Sequential Subagents (single-agent)
  ↓ failure (max retries exhausted)
Tier 3: Orchestrator Direct (no agents)
  ↓ failure
Tier 4: Human Escalation (manual intervention)
```

| Tier | Mode | Capability | When Used |
|------|------|-----------|-----------|
| 1 | Agent Team | Full parallel execution | Agent Teams available + parallelizable step |
| 2 | Sequential Subagent | Single-agent sequential | Default for most steps |
| 3 | Orchestrator Direct | Orchestrator handles step itself | Agent spawning fails |
| 4 | Human Escalation | Manual intervention | All automated tiers exhausted |

---

## FallbackController Usage

The `FallbackController` class (in `scripts/fallback_controller.py`) manages state across retries and tier transitions.

### API

```python
from scripts.fallback_controller import FallbackController

fc = FallbackController()
action = fc.handle_failure(
    step="7c",
    agent="chapter-writer",
    error="context overflow"
)

# action.tier      → 2 (next tier to try)
# action.action    → "retry_sequential"
# action.feedback  → human-readable explanation
# action.diagnostic → detailed diagnostic report
```

### Algorithm

```
1. Get current tier for this step
2. Count retries at current tier
3. If retries < max_retries → retry at same tier with feedback
4. If retries >= max_retries → escalate to next tier
5. If already at Tier 4 → return human escalation action
```

### Retry Limits

| Step | Max Retries | Rationale |
|------|-------------|-----------|
| Default | 3 | Standard for most steps |
| 7c-ch01 / chapter-1 | 5 | Chapter 1 is voice calibration anchor |
| Build phase steps | 3 | Infrastructure failures are usually systemic |

---

## Failure Matrix

Complete mapping of failures to fallback actions:

### Build Phase (Steps 0-0.7)

| Failure | Tier 2 Action | Tier 3 Action | Tier 4 Action |
|---------|--------------|--------------|--------------|
| Missing Python dependency | N/A (run sequentially) | Auto-install via pip | Prompt user to install |
| Schema syntax error | N/A | Fix schema and retry | Manual schema repair |
| Script compilation error | N/A | Report specific error | Manual code fix |
| Test failure | N/A | Skip non-critical tests | Manual investigation |
| Missing pandoc/XeLaTeX | N/A | N/A | User installs prerequisites |

### Research Phase (Steps 1-3.5)

| Failure | Tier 2 Action | Tier 3 Action | Tier 4 Action |
|---------|--------------|--------------|--------------|
| `@interviewer` context overflow | Retry with smaller session scope | Orchestrator conducts interview | User provides written answers |
| Schema validation fails | Re-prompt with validation errors | Orchestrator fixes JSON | Manual transcript repair |
| Material too thin | Extend session count | Prompt for supplementary docs | User provides written material |
| Session produces no emotional markers | Re-prompt with sensory cues | Orchestrator adds markers from transcript | Skip markers (degraded quality) |

### Planning Phase (Steps 4-6.5)

| Failure | Tier 2 Action | Tier 3 Action | Tier 4 Action |
|---------|--------------|--------------|--------------|
| `@story-architect` fails | Retry with fewer interviews | Orchestrator builds minimal bible | User creates chapter plan |
| SB validation fails | Re-prompt with specific failures | Orchestrator patches bible | Manual story bible editing |
| Voice calibration insufficient | Request additional sample text | Use default voice profile | User specifies voice parameters |
| Outline rejected at H4 | Return to Step 6 with feedback | N/A | User designs chapter plan |

### Implementation Phase (Steps 7-11)

| Failure | Tier 2 Action | Tier 3 Action | Tier 4 Action |
|---------|--------------|--------------|--------------|
| `@chapter-writer` context overflow | Retry with reduced context | Orchestrator writes minimal draft | Human writes chapter |
| Python gate loops (3 fails) | N/A | N/A | Human reviews diagnostic |
| `@autobiography-reviewer` unavailable | Quality gate only (reduced review) | Orchestrator self-reviews | Flag for human review |
| Review loops (max revisions) | N/A | N/A | Human reviews and decides |
| Build fails (pandoc error) | Retry with simplified template | Markdown-only output | Manual build |
| EPUB validation fails | Rebuild without epubcheck | Markdown-only output | Manual EPUB fix |

---

## @translator Fallback

Translation has its own degradation path:

```
@translator (full quality, pACS >= 70)
  ↓ pACS < 70 after 2 retries
Orchestrator inline translation (Tier 3)
  ↓ Orchestrator pACS also < 70
English + machine-translated Korean with WARNING to user
```

### Translation Retry Budget
- Max 2 retries per translation task at Tier 2
- pACS >= 70 required for human checkpoint translations (BLOCKING)
- Non-checkpoint translations: pACS >= 60 acceptable with warning

---

## Diagnostic Report Format

Every fallback action includes a diagnostic report:

```
== Fallback Diagnostic ==
Step: {step_id}
Agent: {agent_name}
Error: {error_message}
Current Tier: {N}
Retry Count: {count}/{max}
Action: {action_key}

== History ==
- Attempt 1 (Tier 1): {error}
- Attempt 2 (Tier 1): {error}
- Attempt 3 (Tier 1): escalated to Tier 2
- Attempt 4 (Tier 2): {error}
...

== Recommendation ==
{human-readable recommendation}
```

---

## SOT Tracking

Fallback state is persisted in `state.yaml`:

```yaml
orchestration:
  fallback:
    activations:
      - step: "7c-ch03"
        from_tier: 1
        to_tier: 2
        timestamp: "2026-03-18T10:30:00Z"
        error: "context overflow"
    current_tier: 2
```

---

## Emergency Recovery

For catastrophic failures (corrupted SOT, all tiers exhausted):

1. **SOT Recovery**: Load `.claude/state.yaml.bak` (created before every write)
2. **Chapter Recovery**: Check `outputs/chapters/` for latest drafts regardless of SOT status
3. **Manual Override**: User can edit `state.yaml` directly and restart from any step
4. **Full Reset**: Delete `state.yaml`, re-run build phase (Step 0) — loses all progress

The `/fallback` command provides interactive access to these recovery mechanisms.
