---
description: "Run full build verification"
---

# /build-verify — Run Full Build Verification

Run the complete build verification suite: schema validation, script syntax checks, test suite, and artifact validation.

## Execute These Steps

### Step 1: Verify Python Environment

Use the **Bash tool** to check the environment:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 --version
```

- **If .venv missing**: Report to user: "Python virtual environment not found. Run `scripts/setup.sh` first." **STOP here.**
- **If present**: Record the Python version. Continue.

### Step 2: Verify Project Structure

Use the **Bash tool** to check required directories exist:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && ls -d schemas/ scripts/ .claude/agents/ 2>&1
```

- **If any directory missing**: Report which directories are missing. **STOP here.**
- **If all present**: Continue. Record result as `STRUCTURE: PASS`.

### Step 3: Schema Validation (Step 0.5a)

Use the **Bash tool**:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/quality_gate_check.py --step 0.5a
```

Record exit code. If non-zero, record `SCHEMAS: FAIL` with the error output. If zero, record `SCHEMAS: PASS` and note how many schemas were checked.

**Do NOT stop on failure** — continue to collect all results.

### Step 4: Script Syntax Check (Step 0.5b)

Use the **Bash tool**:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/quality_gate_check.py --step 0.5b
```

Record exit code. If non-zero, record `SCRIPTS: FAIL` with specific files and line numbers. If zero, record `SCRIPTS: PASS` and note how many scripts were compiled.

**Do NOT stop on failure** — continue.

### Step 5: Test Suite (Step 0.5c)

Use the **Bash tool**:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/test_quality.py 2>&1
```

Record exit code. If non-zero, record `TESTS: FAIL` with test names and failure messages. If zero, record `TESTS: PASS` with passed/total count.

**Do NOT stop on failure** — continue.

### Step 6: Artifact Validation (Conditional)

Use the **Glob tool** to check if any output artifacts exist:
- `outputs/interviews/INT-*.json`
- `outputs/story-bible/story_bible.json`
- `outputs/chapters/ch*_draft_*.md`

**For each category that has files**, use the **Bash tool** to validate:

**Interview Transcripts** (if any INT-*.json files exist):
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && for f in outputs/interviews/INT-*.json; do .venv/bin/python3 scripts/schema_validator.py --schema schemas/interview_transcript.schema.json --data "$f"; done
```

**Story Bible** (if story_bible.json exists):
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/validate_story_bible.py --story-bible outputs/story-bible/story_bible.json --project-dir .
```

**Chapters** (if any chapter drafts exist):
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && for ch in outputs/chapters/ch*_draft_*.md; do N=$(echo "$ch" | grep -o 'ch[0-9]*' | grep -o '[0-9]*'); .venv/bin/python3 scripts/validate_chapter.py --chapter "$N" --project-dir .; done
```

For categories with no files, record as `SKIP` (this is normal during early build phases).

### Step 7: Display Results Summary

Output the following report directly to the user:

```
Build Verification Report
=========================
Python:         {version}
Structure:      PASS
Schemas:        {PASS | FAIL} ({count} checked)
Scripts:        {PASS | FAIL} ({count} compiled)
Tests:          {PASS | FAIL} ({passed}/{total})
Interviews:     {PASS | FAIL | SKIP} ({count} validated)
Story Bible:    {PASS | FAIL | SKIP}
Chapters:       {PASS | FAIL | SKIP} ({count} validated)
-------------------------
Overall:        {PASS if all non-SKIP items passed | FAIL otherwise}
```

If any items FAILED, append a section:

```
Failures Detail
---------------
{For each FAIL: list the specific errors with file names and line numbers}
```

## Arguments

None. Runs the full suite automatically.

## Error Handling

| Error | Tool to Use | Action |
|-------|-------------|--------|
| Missing .venv | Bash tool | Report: "Run `scripts/setup.sh` first." STOP. |
| Schema errors | Bash tool output | List specific schemas with error details in report |
| Script syntax errors | Bash tool output | List specific scripts with line numbers in report |
| Test failures | Bash tool output | Show test names and failure messages in report |
| Missing outputs/ directory | Glob tool | Skip artifact validation — mark as SKIP (not an error) |
| quality_gate_check.py missing | Bash tool | Report: "scripts/quality_gate_check.py not found. Project setup may be incomplete." |

## When to Use

- Before starting a new pipeline run
- After modifying any scripts or schemas
- As a health check when resuming work after a break
- After recovering from a crash or context loss
