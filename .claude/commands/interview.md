---
description: "Start or resume an interview session"
---

# /interview — Start or Resume an Interview Session

Start or resume an AI-guided interview session with the subject.

## Execute These Steps

### Step 1: Read Pipeline State

Use the **Read tool** on `.claude/state.yaml` to load the full pipeline state.

Extract these values:
- `workflow.interviews.status` — one of: `not_started`, `in_progress`, `completed`
- `workflow.interviews.completed_sessions` — integer count
- `workflow.interviews.total_sessions` — planned total
- `workflow.interviews.sessions_processed` — list of session IDs already done

### Step 2: Determine Session Number and Branch

Based on `workflow.interviews.status`:

- **If `not_started`**:
  1. Use the **Glob tool** to check if `outputs/interviews/interview_plan.md` exists.
  2. If no plan exists: create the interview plan first (Step 1 of pipeline) covering all 8 McAdams life stages. Use the **Write tool** to create `outputs/interviews/interview_plan.md`.
  3. Set session number to `INT-001`.

- **If `in_progress`**:
  1. Compute next session number: `INT-{completed_sessions + 1}` (zero-padded to 3 digits).
  2. Use the **Read tool** on `outputs/interviews/interview_plan.md` to determine which life period/theme this session covers.
  3. Use the **Glob tool** on `outputs/interviews/INT-*.json` to list previous transcripts.
  4. Use the **Read tool** on the most recent 1-2 transcripts to build cross-reference context.

- **If `completed`**:
  1. Report to user: "All {total_sessions} interview sessions are completed."
  2. Suggest running `/status` for overview. **STOP here — do not proceed.**

### Step 3: Spawn @interviewer Subagent

Use the **Skill tool** or **SendMessage tool** to spawn the `@interviewer` subagent with these parameters:
- Session number: `INT-{NNN}`
- Life period or theme focus (from interview plan)
- Previous sessions summary (key topics already covered, gaps identified)
- Interview plan reference path: `outputs/interviews/interview_plan.md`

Wait for the subagent to complete and produce the transcript at `outputs/interviews/INT-{NNN}.json`.

### Step 4: Post-Session Validation

Use the **Bash tool** to run schema validation:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/schema_validator.py --schema schemas/interview_transcript.schema.json --data outputs/interviews/INT-{NNN}.json
```

- **If validation FAILS**: Re-prompt the @interviewer with the specific validation errors. Do NOT proceed to Step 5 until the transcript passes validation.
- **If validation PASSES**: Continue to Step 5.

### Step 5: Update state.yaml (SOT)

Use the **Edit tool** on `.claude/state.yaml` to update:
```yaml
workflow:
  interviews:
    completed_sessions: {N+1}
    status: "in_progress"  # or "completed" if this was the final session
    sessions_processed: [..., "INT-{NNN}"]
```

If this was the final planned session, set `status: "completed"` instead.

### Step 6: Display Post-Session Report to User

Output the following report directly (no tool needed):

```
Interview Session Complete
==========================
Session:            INT-{NNN}
Life Period:        {period covered}
Key Quotes:         {count extracted from transcript}
People Mentioned:   {count from transcript}
Emotional Markers:  {count from transcript}
Sessions Done:      {completed} / {total}
Sessions Remaining: {remaining}
--------------------------
Recommendation:     {if remaining > 0: "Continue with next session"
                     else: "All sessions complete. Run /status for material assessment."}
```

## Error Handling

| Error | Tool to Use | Action |
|-------|-------------|--------|
| @interviewer fails mid-session | Read tool on partial transcript | Save whatever exists, retry spawn with context of last completed segment |
| Schema validation fails | Bash tool to re-run validator | Display specific errors, re-prompt @interviewer with validation feedback |
| Subject provides thin answers | N/A (automatic) | @interviewer activates Tulving redirect automatically within its protocol |
| state.yaml missing or corrupt | Read tool on `.claude/state.yaml.bak` | Restore from backup, then retry from Step 1 |

## Constraints

- Interview sessions are conducted in Korean (subject's language)
- Each session focuses on ONE life period or ONE major theme
- The closing ritual phrase is mandatory for every session
- After all planned sessions, run `/status` to see material assessment recommendation
- This command NEVER writes to state.yaml before validation passes (Step 4 must succeed before Step 5)
