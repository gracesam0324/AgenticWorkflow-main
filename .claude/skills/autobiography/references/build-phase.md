# Build Phase — Layer 0-10 Orchestration

## Overview

The Build phase (Steps 0 through 0.7) prepares the project infrastructure before any creative work begins. It validates the environment, creates directory structures, verifies scripts, and runs the full test suite.

## Step Map

| Step | Name | Handler | Parallelizable |
|------|------|---------|----------------|
| 0 | Environment Setup | `step_0_env_setup` | No |
| 0.5a | Schema Validation | `execute_build_phase` | Yes (Track A) |
| 0.5b | Script Syntax Check | `execute_build_phase` | Yes (Track A) |
| 0.5c | Test Suite | `execute_build_phase` | Yes (Track B) |
| 0.5d | Directory Structure | `execute_build_phase` | Yes (Track A) |
| 0.7 | Human Verification | `step_07_human_verify` | No |

## Layer Structure

### Layer 0: Prerequisites

```bash
# Verify Python environment
.venv/bin/python3 --version  # >= 3.11 required

# Verify pandoc for book build
pandoc --version  # >= 3.0 required

# Verify XeLaTeX for PDF
xelatex --version  # Required for PDF output

# Verify project structure
ls schemas/ scripts/ .claude/agents/
```

### Layer 1-5: Schema and Script Validation

```bash
# Validate all JSON schemas are syntactically correct
.venv/bin/python3 scripts/schema_validator.py --validate-schemas

# Check all Python scripts compile without errors
.venv/bin/python3 -m py_compile scripts/*.py

# Verify hook scripts are executable
.venv/bin/python3 scripts/quality_gate_check.py --step 0.5a
```

### Layer 6-9: Test Suite

```bash
# Run the full quality test suite
.venv/bin/python3 scripts/test_quality.py

# Verify golden test data
.venv/bin/python3 scripts/schema_validator.py \
  --schema schemas/interview_transcript.schema.json \
  --data scripts/golden_test_data.json
```

### Layer 10: Directory Scaffolding

Ensure all output directories exist:
```
outputs/
  interviews/
  story-bible/
  chapters/
  builds/
quality/
review-logs/
autopilot-logs/
translations/
```

## Agent Team Parallel Tracks

When Agent Teams are available, the build phase splits into two parallel tracks:

### Track A: Validation (Steps 0.5a, 0.5b, 0.5d)
- Schema validation
- Script syntax checking
- Directory structure creation

### Track B: Testing (Step 0.5c)
- Full test suite execution
- Golden data validation

### Dependency Graph

```
Step 0 (env setup)
  ├─── Track A: [0.5a, 0.5b, 0.5d] (parallel)
  └─── Track B: [0.5c]              (parallel with A)
        └─── Both tracks complete ───→ Step 0.7 (human verify)
```

## Sequential Fallback

When Agent Teams are NOT available (the default):

```
Step 0 → 0.5a → 0.5b → 0.5c → 0.5d → 0.7
```

All steps run sequentially through the Orchestrator. Each step must pass its quality gate before the next begins.

## File Ownership

| File/Directory | Owner | Write Access |
|----------------|-------|-------------|
| `.claude/state.yaml` | Orchestrator | Orchestrator only |
| `schemas/*.json` | Build phase | Read-only after build |
| `scripts/*.py` | Build phase | Read-only after build |
| `outputs/` directories | Build phase creates | Agents write per step |

## Quality Gate

```bash
.venv/bin/python3 scripts/quality_gate_check.py --step 0.5a
.venv/bin/python3 scripts/quality_gate_check.py --step 0.5b
```

Exit code 0 = pass, 1 = fail with diagnostic on stderr.

## SOT Updates

After build phase completion, the Orchestrator writes:

```yaml
workflow:
  current_step: 1
  status: "in_progress"
orchestration:
  current_phase: "research"
  teams:
    build_team:
      status: "completed"
```

## Failure Handling

Build phase failures are critical — the pipeline cannot proceed without passing infrastructure.

| Failure | Action |
|---------|--------|
| Missing Python dependency | Install via `.venv/bin/pip install -r requirements.txt` |
| Schema syntax error | Fix schema file, re-run 0.5a |
| Script compilation error | Fix script, re-run 0.5b |
| Test failure | Fix failing test, re-run 0.5c |
| Missing pandoc/XeLaTeX | Prompt user to install (Tier 4: human) |
