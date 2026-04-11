---
description: "Manually trigger fallback for stuck step"
---

# /fallback — Manual Fallback and Emergency Recovery

Manually trigger fallback for a stuck step or perform emergency recovery operations.

## Execute These Steps

### Step 1: Read Pipeline State and Diagnose

Use the **Read tool** on `.claude/state.yaml`.

Extract:
- `workflow.current_step` — the current (possibly stuck) step
- `workflow.status` — should indicate an issue if fallback is needed
- `orchestration.fallback.current_tier` — current degradation tier (1-4)
- `orchestration.fallback.activations` — history of fallback events
- `orchestration.error_log` — past error entries

### Step 2: Run FallbackController Diagnostic

Use the **Bash tool** to run the fallback diagnostic:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 -c "
from scripts.fallback_controller import FallbackController
import json
fc = FallbackController()
diag = fc.diagnose()
print(json.dumps(diag, indent=2, default=str))
"
```

If the FallbackController or the diagnose method doesn't exist yet, fall back to manual diagnosis using the state.yaml data from Step 1. Determine:
- Which step is stuck
- How many retries have been attempted
- What the last error was
- What the current fallback tier is

### Step 3: Present Options to User

Output the following menu directly:

```
Fallback Recovery — Step {step}
================================

Current Tier:  {tier} ({tier_label})
               Tier 1 = Parallel Subagent
               Tier 2 = Sequential Subagent
               Tier 3 = Orchestrator Direct
               Tier 4 = Human Escalation
Retries:       {count} / {max_for_tier}
Last Error:    {error_message or "No error recorded"}

Options:
  1. Retry at current tier  — attempt the step again at Tier {tier}
  2. Escalate to next tier  — degrade to Tier {tier+1} ({next_tier_label})
  3. Skip step              — mark as skipped (WARNING: quality impact)
  4. Reset step             — clear retry history, restart from Tier 2
  5. SOT recovery           — restore state.yaml from backup (.bak)
  6. Full diagnostic        — detailed error analysis and recommendations

Which option? (1-6)
```

Wait for user to respond with their choice.

### Step 4: Execute the Chosen Option

#### Option 1: Retry at Current Tier

Use the **Bash tool**:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 -c "
from scripts.fallback_controller import FallbackController
fc = FallbackController()
result = fc.retry_step(step={step}, tier={tier})
print(result)
"
```

If the FallbackController doesn't support this method, manually re-trigger the step using the appropriate command (e.g., re-run the script that failed).

Report the outcome to the user.

#### Option 2: Escalate to Next Tier

Use the **Bash tool**:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 -c "
from scripts.fallback_controller import FallbackController
fc = FallbackController()
action = fc.handle_failure(step={step}, agent='{agent}', error='manual_escalation')
print(action)
"
```

If FallbackController is unavailable, use the **Edit tool** on `.claude/state.yaml` to manually increment the tier:
```yaml
orchestration:
  fallback:
    current_tier: {tier + 1}
```

Then re-trigger the step at the new tier.

#### Option 3: Skip Step (Requires Confirmation)

Output a warning:
```
WARNING: Skipping step {step} will degrade output quality.
Affected downstream steps: {list steps that depend on this one}
Type 'yes' to confirm, or anything else to cancel.
```

Wait for user confirmation.

- **If confirmed**: Use the **Edit tool** on `.claude/state.yaml`:
  ```yaml
  workflow:
    current_step: {step + 1}
  orchestration:
    error_log:
      - step: {step}
        action: "skipped"
        timestamp: "{ISO 8601}"
        outcome: "skipped"
        reason: "manual_skip_by_user"
  ```

- **If cancelled**: Report "Skip cancelled." Return to option menu.

#### Option 4: Reset Step

Use the **Edit tool** on `.claude/state.yaml` to:
1. Remove all fallback activation entries for this step from `orchestration.fallback.activations`
2. Reset the tier for this step to Tier 2 (Sequential Subagent):
```yaml
orchestration:
  fallback:
    current_tier: 2
```

Report: "Step {step} reset. Retry history cleared. Will restart at Tier 2 (Sequential Subagent)."

#### Option 5: SOT Recovery

Use the **Bash tool** to check for backup:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && ls -la .claude/state.yaml.bak 2>&1
```

- **If backup exists**: Use the **Bash tool** to show diff:
  ```bash
  cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && diff .claude/state.yaml .claude/state.yaml.bak
  ```
  Display the diff to user. Ask: "Restore from backup? (yes/no)"
  - If confirmed: Use **Bash tool** to `cp .claude/state.yaml.bak .claude/state.yaml`
  - Then re-read state with **Read tool** on `.claude/state.yaml`

- **If no backup**: Report "No backup found at `.claude/state.yaml.bak`."
  Suggest: "Check `outputs/` directory for latest artifacts to reconstruct state, or reset to Step 0."

#### Option 6: Full Diagnostic

Use the **Read tool** on `.claude/state.yaml` for full state. Then use **Glob tool** to check artifact presence. Output:

```
== Full Diagnostic Report ==

Step:   {step}
Phase:  {phase}
Agent:  {agent responsible for this step}

Error History:
  {For each entry in orchestration.error_log for this step:}
  Attempt {N} (Tier {T}): {error} — {timestamp}

SOT Integrity:
  state.yaml exists:     {yes/no}
  state.yaml.bak exists: {yes/no}
  Last modified:         {file mtime}

Output Artifacts:
  Expected: {list files this step should have produced}
  Found:    {list files that actually exist}
  Missing:  {list files that should exist but don't}

Recommendations:
  1. {specific recommendation based on error pattern}
  2. {alternative approach if primary fails}
```

### Step 5: Update SOT After Recovery

After ANY option is executed (except Option 6 which is read-only), use the **Edit tool** on `.claude/state.yaml` to log the fallback action:

```yaml
orchestration:
  error_log:
    - step: {step}
      action: "{chosen_option_name}"
      timestamp: "{ISO 8601}"
      outcome: "{recovered | escalated | skipped | reset | restored}"
```

## Arguments

None. The command interactively determines which step needs recovery. If a specific step is stuck (detectable from state.yaml), it is pre-selected.

## Emergency Recovery Procedures

### Corrupted SOT
1. Use **Bash tool**: `ls -la .claude/state.yaml.bak` — check for backup
2. If backup valid: restore with `cp .claude/state.yaml.bak .claude/state.yaml`
3. If no backup: Use **Glob tool** on `outputs/` to find latest artifacts
4. Reconstruct state from artifacts (chapter files, review logs, interview transcripts)
5. Last resort: Use **Edit tool** to create minimal state.yaml at Step 0

### Context Loss (Session Restart)
1. Context preservation hooks should auto-restore
2. If not: Use **Read tool** on `.claude/context-snapshots/` for latest snapshot
3. Use **Read tool** on `state.yaml` to determine current position

### Agent Spawn Failure
1. Use **Glob tool** to verify agent file exists in `.claude/agents/`
2. Check agent model availability
3. Fall back to Tier 2 (Sequential Subagent execution)
4. If persistent: Tier 3 (Orchestrator direct execution)

## Constraints

- This command NEVER silently skips steps — always requires explicit user confirmation
- All fallback actions are logged to `orchestration.error_log[]`
- SOT backup is created before every state write (automatic)
- The FallbackController persists retry counts across sessions via SOT
- Option 6 (Full Diagnostic) is the only read-only option — all others modify state
