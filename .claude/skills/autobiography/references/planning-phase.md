# Planning Phase — Story Bible, Calibration, and Outline

## Overview

The Planning phase (Steps 4 through 6.5) transforms raw interview material into structured narrative architecture. It produces the Story Bible (SOT for all narrative facts), calibrates voice and literary style, designs the chapter outline, and runs human checkpoints H2-H4.

## Step Map

| Step | Name | Agent | Output |
|------|------|-------|--------|
| 4 | Story Bible Construction | `@story-architect` | `outputs/story-bible/story_bible.json` |
| 4.5 | H2: Story Bible Review | Human | Decision: approve / revise / restructure |
| 5 | Voice Calibration | `@chapter-writer` | Voice profile in story bible |
| 5.5 | Literary Calibration | `@chapter-writer` | Literary parameters in story bible |
| 6 | Chapter Outline | `@story-architect` | Chapter plan in story bible |
| 6.5 | H4: Outline Approval | Human | Decision: approve / modify |

---

## Step 4: Story Bible Construction

### Input
All interview transcripts from `outputs/interviews/`

### Agent: `@story-architect`

The story architect follows a 6-step protocol:

1. **Ingest All Interviews** — Build working lists of people, places, events, themes
2. **Timeline Construction** — Chronological events, gap detection, contradiction flagging
3. **Character Registry** — Canonical names, importance levels, relationship arcs
4. **Theme Analysis** — 5-10 emergent themes with evolution tracking
5. **Controlling Metaphor Identification** — Physical object recurring 3+ times unprompted
6. **Golden Exemplar Extraction** — 3-5 interview passages with unusual vividness

### Story Bible Components

| Component | Description | Schema Field |
|-----------|-------------|-------------|
| Character Registry | Canonical names, aliases, relationships, arc | `characters[]` |
| Timeline | Chronological events with sort keys | `timeline[]` |
| Place Registry | Locations with sensory details | `places[]` |
| Theme Analysis | Recurring topics with evolution | `themes[]` |
| Chapter Plan | Preliminary chapter structure | `chapter_plan[]` |
| Voice Guide | Subject's speech patterns, vocabulary | `voice_guide` |
| Fact Registry | Verifiable facts for consistency | `fact_registry[]` |
| Controlling Metaphor | Structural thread object | `controlling_metaphor` |
| Golden Exemplars | Vivid interview passages | `golden_exemplars[]` |

### Validation

```bash
# Schema validation
.venv/bin/python3 scripts/schema_validator.py \
  --schema schemas/story_bible.schema.json \
  --data outputs/story-bible/story_bible.json

# Quality gate (SB1-SB10)
.venv/bin/python3 scripts/validate_story_bible.py \
  --story-bible outputs/story-bible/story_bible.json \
  --project-dir .
```

### Minimum Thresholds
- At least 3 characters
- At least 5 timeline events
- At least 3 themes
- At least 3 chapters planned
- Every chapter plan entry must cite source interviews

---

## Step 4.5: H2 Checkpoint — Story Bible Review

### Pre-Checkpoint
1. Story Bible passes SB1-SB10 validation
2. `@autobiography-reviewer` produces adversarial review (`review-logs/RV-story-bible.json`)
3. Review includes: pre-mortem, timeline contradictions, character arc completeness
4. Translation of key findings for user (if needed)

### User Options

| Choice | Action |
|--------|--------|
| **Approve** | Advance to Step 5 (Voice Calibration) |
| **Revise story bible** | Return to Step 4 with specific corrections |
| **Restructure chapters** | Modify chapter plan ordering or scope, return to Step 4 |

---

## Step 5: Voice Calibration

### Purpose
Measure and profile the subject's natural voice from interview transcripts to create quantitative targets for chapter writing.

### Agent: `@chapter-writer` (calibration mode)

Using the Golden Exemplars and interview transcripts, produce a voice profile:

| Metric | Description | Source |
|--------|-------------|--------|
| Average sentence length | Words per sentence (mean, std) | Interview transcripts |
| Dialogue ratio | % of text that is dialogue | Interview transcripts |
| Passive voice % | Target range | Golden exemplars |
| Show:tell ratio | Sensory/embodied vs. declarative | Golden exemplars |
| Vocabulary level | Complexity score | Interview transcripts |
| Favorite expressions | Recurring phrases to preserve | All transcripts |
| Forbidden words | Words the subject would never use | Voice guide |

### Validation: `@voice-calibrator`

```bash
.venv/bin/python3 scripts/check_voice.py \
  --golden-exemplars outputs/story-bible/golden_exemplars.json
```

### SOT Update

```yaml
workflow:
  voice_calibration:
    status: "completed"
    selected_voice: {profile_id}
    golden_exemplars: [...]
```

---

## Step 5.5: Literary Calibration

### Purpose
Establish literary parameters for the specific book — narrative stance, tense conventions, cultural-literary devices.

### Korean Literary Directives (Appendix A)

| Code | Directive | Description |
|------|-----------|-------------|
| A-1 | Temporal Layering | 이중 의식 (dual consciousness) — narrating self vs. experiencing self |
| A-2 | Metaphor Threading | Controlling metaphor woven through chapters |
| A-3 | 여운 Endings | Chapters end with lingering resonance, not summaries |
| A-4 | 침묵 as Narrative | Silence used as content, not absence |
| A-5 | 기승전결 Structure | 4-act structure with perspective shift at 전 |
| A-6 | Embodied Emotion | Show feeling through body, not declaration |
| A-7 | 이중 의식 Ratio | Target 3:1 experiencing-to-narrating ratio |
| A-8 | Honorific Shifts | 존칭/반말 shifts signal relational dynamics |

### Output
Literary parameters appended to voice guide in story bible.

---

## Step 6: Chapter Outline

### Agent: `@story-architect`

Produce detailed chapter plan with:

| Field | Description |
|-------|-------------|
| `chapter_number` | Sequential chapter index |
| `title` | Working title |
| `life_period` | McAdams stage(s) covered |
| `time_range` | Years covered |
| `source_interviews` | INT-{NNN} references |
| `key_characters` | Characters appearing |
| `key_events` | Timeline events covered |
| `themes` | Theme threads active |
| `narrative_technique` | Primary literary device |
| `target_word_count` | Per-chapter word target |
| `opening_strategy` | How the chapter begins (varied per Anti-Homogenization) |
| `closing_strategy` | 여운 type for this chapter |

### Anti-Homogenization Constraint
No two consecutive chapters may share the same opening or closing strategy. `@reviewer-deep` verifies this at Step 8.

### Validation

```bash
.venv/bin/python3 scripts/quality_gate_check.py --step 6
```

---

## Step 6.5: H4 Checkpoint — Outline Approval

### Pre-Checkpoint
1. Chapter outline passes quality gate
2. Total chapter count and word targets displayed
3. Source interview coverage per chapter shown
4. Theme distribution across chapters visualized

### User Options

| Choice | Action |
|--------|--------|
| **Approve** | Advance to Step 7 (Chapter Writing Loop) |
| **Modify chapter plan** | Adjust ordering, merge/split chapters, return to Step 6 |

### SOT Update on Approval

```yaml
workflow:
  current_step: 7
  book_config:
    total_chapters: {N}
    target_word_count: {total}
orchestration:
  current_phase: "implementation"
```

---

## Quality Gates

| Check | Script | When |
|-------|--------|------|
| Story Bible schema | `schema_validator.py` | After Step 4 |
| Story Bible quality (SB1-SB10) | `validate_story_bible.py` | After Step 4 |
| Voice metrics baseline | `check_voice.py` | After Step 5 |
| Outline structure | `quality_gate_check.py --step 6` | After Step 6 |

## Failure Handling

| Failure | Fallback |
|---------|----------|
| `@story-architect` fails | Retry (Tier 2); if persistent, Orchestrator builds minimal bible (Tier 3) |
| Story Bible fails SB validation | Re-prompt `@story-architect` with specific failures |
| Voice calibration insufficient | Request user to provide additional sample text |
| Outline rejected at H4 | Return to Step 6 with user feedback |
