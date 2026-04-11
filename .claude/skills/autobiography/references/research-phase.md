# Research Phase — Interview Sessions and Material Assessment

## Overview

The Research phase (Steps 1 through 3.5) gathers the raw material for the autobiography through structured AI-guided interviews. It covers interview planning, conducting sessions, assessing material richness, and the H1 human checkpoint.

## Step Map

| Step | Name | Agent | Output |
|------|------|-------|--------|
| 1 | Interview Session Planning | Orchestrator | `outputs/interviews/interview_plan.md` |
| 2 | Conduct Interview Sessions | `@interviewer` | `outputs/interviews/INT-{NNN}.json` |
| 3 | Material Assessment | Orchestrator + Python | `quality/material-assessment.json` |
| 3.5 | H1: Interview Review | Human | Decision: approve / more sessions / edit |

---

## Step 1: Interview Session Planning

The Orchestrator creates an interview plan covering all major life periods.

### Requirements
- Life period map covering birth to present (8 McAdams stages)
- At least 5 interview themes identified
- Session schedule: 1 session per major life period (minimum 8 sessions)

### Life Period Framework (McAdams)

| Stage | Age Range | Core Prompts |
|-------|-----------|-------------|
| Early Childhood | 0-5 | Origin scenes, earliest memories |
| Late Childhood | 6-11 | School entry, first friendships |
| Adolescence | 12-17 | Identity formation, pivotal scenes |
| Emerging Adulthood | 18-25 | Leaving home, first love, vocation |
| Young Adulthood | 26-39 | Career, partnership, parenthood |
| Middle Adulthood | 40-55 | Generativity, reassessment |
| Late Adulthood | 56-70 | Meaning-making, legacy |
| Elder Reflection | 70+ | Life review, wisdom narrative |

### Output
- `outputs/interviews/interview_plan.md`
- No translation required

---

## Step 2: Conduct Interview Sessions (Repeating)

### Interview Protocol

Each session is conducted by `@interviewer` following the McAdams Life Story Interview Model augmented with Kvale's 9-type adaptive follow-up system.

**Per-session requirements:**
- Focus on ONE life period or ONE major theme
- At least 3 segments with full transcript text
- At least 1 sensory cue question per session (Rubin protocol)
- Mandatory extraction of: `key_quotes[]`, `people_mentioned[]`, `places_mentioned[]`, `emotional_markers[]`
- Session closing ritual in Korean

**Schema compliance:**
```bash
.venv/bin/python3 scripts/schema_validator.py \
  --schema schemas/interview_transcript.schema.json \
  --data outputs/interviews/INT-{NNN}.json
```

### Thin-Answer Escalation Protocol

When 3+ consecutive answers are under 30 words:
1. Detect semantic-mode lock (subject giving facts, not memories)
2. Redirect to episodic memory using Tulving pivot
3. If still thin after redirect: deploy sensory cue question
4. If persistent: use Kvale indirect type to approach from a different angle

### Kvale Follow-Up State Machine

After every subject response, `@interviewer` classifies the response and selects the optimal follow-up type:

```
[SubjectResponse] → classify(depth, emotion, specificity)
                  → select_kvale_type(1-9)
                  → [NextQuestion]
```

The 9 types: Introducing, Follow-up, Probing, Specifying, Direct, Indirect, Structuring, Silence, Interpreting.

### Session Output
- `outputs/interviews/INT-{NNN}.json` (one per session)
- Must conform to `schemas/interview_transcript.schema.json`
- No translation required (interviews conducted in Korean)

### Session Tracking in SOT

```yaml
workflow:
  interviews:
    total_sessions: 8
    completed_sessions: {N}
    status: "in_progress"
    sessions_processed: ["INT-001", "INT-002", ...]
```

---

## Step 3: Material Assessment

After all planned interview sessions complete, the Orchestrator runs material richness scoring.

### Assessment Script

```bash
.venv/bin/python3 scripts/assess_material.py \
  --interviews-dir outputs/interviews/ \
  --output-dir quality/
```

### Richness Dimensions

| Dimension | Description | Minimum Threshold |
|-----------|-------------|-------------------|
| Episodic Memories | Distinct events described in detail | 3 per life stage |
| Dialogue Instances | Direct quotes or reported speech | 2 per session |
| Setting Descriptions | Specific places with contextual detail | 1 per session |
| Sensory Details | Sights, sounds, smells, textures, tastes | 2 per session |

### Gap Identification

The assessment identifies life stages with insufficient material:
- Stages with 0 episodic memories: **critical gap** — recommend additional session
- Stages with < 2 sensory details: **warning** — recommend targeted follow-up
- Overall coverage < 60%: recommend extending interview count

### Output
- `quality/material-assessment.json` — per-life-stage depth scores and breakdown

---

## Step 3.5: H1 Checkpoint — Interview Review

### Pre-Checkpoint Checklist
1. All planned interview sessions completed
2. Material assessment generated and reviewed
3. Schema validation passes for all transcripts
4. Gap report prepared for user

### Presentation to User

Display in Korean:
- Total sessions completed
- Material richness summary per life stage
- Identified gaps (critical and warning)
- Assessment recommendation (proceed / extend)

### User Options

| Choice | Action |
|--------|--------|
| **Approve** | Advance to Step 4 (Story Bible Construction) |
| **Request additional sessions** | Return to Step 2 with specific topics; increment `total_sessions` |
| **Edit transcripts** | User corrects factual errors in raw data; re-run schema validation |

### SOT Update on Approval

```yaml
workflow:
  current_step: 4
  interviews:
    status: "completed"
orchestration:
  current_phase: "planning"
```

---

## Quality Gates

| Check | Script | When |
|-------|--------|------|
| Interview schema compliance | `schema_validator.py` | After each INT-{NNN}.json |
| Material richness scoring | `assess_material.py` | After all sessions complete |
| Quality gate (step 2) | `quality_gate_check.py --step 2` | After each session |

## Failure Handling

| Failure | Fallback |
|---------|----------|
| `@interviewer` fails mid-session | Retry same session (Tier 2: sequential) |
| Schema validation fails | Re-prompt `@interviewer` with validation errors |
| Material too thin across all stages | Recommend user provide supplementary documents |
| `@interviewer` unavailable | Orchestrator conducts interview directly (Tier 3) |
