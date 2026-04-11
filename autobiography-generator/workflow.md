# AI Autobiography Generator

Transform life stories into professionally typeset books through AI-guided interviews, narrative architecture, and automated publishing.

## Overview

- **Input**: Subject's life experiences (via AI-guided interview sessions)
- **Output**: Complete autobiography as PDF (memoir-class) + EPUB, with story bible and fact registry
- **Frequency**: On-demand (one book per subject)
- **Steps**: 12 (Research 1-4 → Planning 5-8 → Implementation 9-12)
- **Human Gates**: 4 checkpoints (Steps 3, 4, 7, 11) — Autopilot auto-approves Steps 3, 7, 11
- **pACS**: enabled (self-assessment at every production step)
- **Language**: English-first workflow. All agents work in English. @translator produces Korean paired output at every step.
- **Absolute Criterion**: Quality over speed. Token cost and execution time are irrelevant.

---

## Inherited DNA (Parent Genome)

> This workflow inherits the complete genome of AgenticWorkflow.
> Purpose varies by domain; the genome is identical. See `soul.md §0`.

**Constitutional Principles** (adapted to autobiography generation):

1. **Quality Absolutism** — The only measure of success is a book worth reading. Speed, token cost, and word count targets are secondary to prose quality, factual accuracy, and emotional authenticity.
2. **Single-File SOT** — `.claude/state.yaml` holds all shared state. The story bible (`story_bible.json`) is the SOT for narrative facts. Only the Orchestrator writes to state; only `@story-architect` writes to the story bible.
3. **Code Change Protocol** — All script modifications follow intent-analysis-design. Coding Anchor Points (CAP-1 through CAP-4) govern validation script changes.

**Inherited Patterns**:

| DNA Component | Inherited Form |
|--------------|---------------|
| 3-Phase Structure | Research (Steps 1-4) → Planning (Steps 5-8) → Implementation (Steps 9-12) |
| SOT Pattern | `.claude/state.yaml` — single writer (Orchestrator) |
| 4-Layer QA | L0 Anti-Skip → L1 Verification (validate_*.py) → L1.5 pACS → L2 Adversarial Review (@reviewer) |
| P1 Hallucination Prevention | Deterministic Python scripts: `validate_story_bible.py`, `validate_chapter.py`, `validate_consistency.py`, `compute_voice_fingerprint.py`, `validate_blueprint.py`, `validate_source_tracing.py`, `validate_voice_match.py`, `validate_pacs_floor.py` |
| P2 Expert Delegation | `@interviewer`, `@story-architect`, `@chapter-writer`, `@voice-calibrator`, `@reviewer`, `@translator` |
| Safety Hooks | `block_destructive_commands.py`, `validate_schema_on_write.py` |
| Adversarial Review | `@reviewer` (prose quality + cross-chapter facts, unified 7-dimension evaluation) |
| Decision Log | `autopilot-logs/` — every auto-approved decision recorded |
| Context Preservation | Parent system handles snapshot/restore |
| English-First + Translation | All work in English → `@translator` produces Korean `.ko.md` pair at every step |

**Domain-Specific Gene Expression**:
The **P2 Expert Delegation** and **Adversarial Review** genes are strongly expressed. Each stage of book production requires specialized expertise (interviewing, narrative architecture, prose writing, voice calibration, review). The Generator-Critic pattern operates at two levels: chapter-level (writer vs. reviewer) and manuscript-level (all chapters vs. @reviewer + @reviewer-deep).

**Voice & Style Data Flow** (critical for quality — all numeric, Python-computed):
```
Step 2-3: Interviews (raw text)
    ↓
Step 4 Pre-processing: compute_voice_fingerprint.py
    → outputs/voice_fingerprint.json (12 quantitative parameters)
    ↓
Step 5: @story-architect reads voice_fingerprint.json
    → Populates story_bible.voice_guide with Python-computed metrics
    ↓
Step 8: User selects style → style_blender.py --apply
    → Blends: skill_params × ratio + observed_params × (1-ratio)
    → Updates story_bible.voice_guide with blended metrics
    → Writes _blend_metadata.computed_by = "style_blender.py"
    ↓
Step 9a: assemble_chapter_context.py
    → Loads: voice_guide (blended) + style_selection + blueprint
    → U-shaped positioning: voice/style at START, instructions at END
    ↓
Step 9b: @chapter-writer follows blended numeric targets
Step 9c: @voice-calibrator verifies against targets
Step 9d: validate_voice_match.py (VM1-VM6) deterministic check
```

---

## Research

### 1. Interview Session Planning
- **Agent**: Orchestrator
- **Technology**: sub-agent
- **Quality Rationale**: Single unified plan ensures coherent interview strategy
- **Verification**:
  - [ ] Life period map covers birth to present
  - [ ] At least 5 interview themes identified
  - [ ] Session schedule produced with 1 session per major life period
  - [ ] Minimum 3 sessions planned (never fewer)
- **Task**: Create interview plan covering all major life periods. Identify key themes, people, and events to explore. Determine session count and ordering. Plan minimum 3 sessions.
- **Output**: `outputs/interviews/interview_plan.md`
- **Translation**: `@translator`

### 2. Conduct Interview Sessions (Repeating)
- **Agent**: `@interviewer`
- **Technology**: sub-agent (sequential — conversational continuity requires single interviewer)
- **Quality Rationale**: Rapport-building across sessions is impossible with parallel interviewers
- **Verification**:
  - [ ] Each session produces valid JSON per `schemas/interview_transcript.schema.json`
  - [ ] At least 3 segments per session with full transcript text
  - [ ] key_quotes, people_mentioned, emotional_markers extracted
  - [ ] Schema validation passes: `python3 scripts/schema_validator.py --schema schemas/interview_transcript.schema.json --data {output}`
  - [ ] Minimum 3 total sessions completed before advancing
  - [ ] Interview coverage validated: `python3 scripts/validate_interview_coverage.py --project-dir .`
- **Task**: Conduct structured interview sessions. For each session: guide subject through one life period or theme, extract sensory details and emotional truths, capture direct quotes, identify people and places. **After EVERY session**: show session summary + coverage map to user, ask 3 questions before continuing.
- **Interaction Protocol** (mandatory):
  ```
  After each session:
    1. Display: session summary (themes covered, key quotes, people mentioned)
    2. Display: coverage map (which life periods are covered, which have gaps)
    3. Ask user:
       Q1: "Are there areas from this session you'd like to explore deeper?"
       Q2: "What topic or time period should the next session focus on?"
       Q3: "Are you ready to conclude interviews, or should we continue?"
    4. NEVER auto-advance to Step 3 without explicit user confirmation
  ```
- **Output**: `outputs/interviews/INT-{NNN}.json` (one per session)
- **Post-processing**: `python3 scripts/schema_validator.py --schema schemas/interview_transcript.schema.json --data outputs/interviews/INT-{NNN}.json`
- **Translation**: `@translator` (per session)

### 3. (human) Interview Review
- **Action**: Review interview transcripts for completeness. Check coverage map. Identify gaps or topics needing deeper exploration. Approve transcript set or request additional sessions.
- **Pre-display**: Coverage map + material assessment (`python3 scripts/assess_material.py --project-dir .`)
- **Options**:
  1. Approve — proceed to story blueprint co-creation (Step 4)
  2. Request additional sessions — return to Step 2 with specific topics
  3. Edit transcripts — correct factual errors in raw data
- **Translation**: `@translator`

### 4. (human) Story Blueprint Co-Creation
- **Agent**: Orchestrator (facilitates) + `@story-architect` (generates candidates)
- **Technology**: sub-agent (sequential — each candidate builds on user feedback from previous)
- **Quality Rationale**: Co-creation requires single coherent dialogue thread; user's vision must be captured in unified document
- **Pre-processing**:
  - `python3 scripts/compute_voice_fingerprint.py --project-dir .` (deterministic voice metrics from interviews)
  - `python3 scripts/assess_material.py --project-dir .` (material richness per life stage)
- **Verification**:
  - [ ] Blueprint passes schema validation: `python3 scripts/schema_validator.py --schema schemas/story_blueprint.schema.json --data outputs/story-blueprint/story_blueprint.json`
  - [ ] Blueprint passes quality gate: `python3 scripts/validate_blueprint.py --project-dir .`
  - [ ] All BP1-BP7 checks pass (structure, kickpoints ≥ 3, core_message ≥ 30 chars, emphasis/exclusion no overlap, controlling metaphor verified in interviews ≥ 2 mentions, target_audience defined, emotional_arc complete)
  - [ ] User explicitly approved the blueprint
- **Task**: Co-create the narrative blueprint with the subject. This is NOT a review gate — it is a creative collaboration session.
  ```
  Phase A: Insight Presentation (auto)
    @story-architect analyzes interviews → proposes 3 candidate structures:
      Structure A: Chronological (birth → present)
      Structure B: Thematic (family / career / faith clusters)
      Structure C: Kickpoint-driven (3-5 turning points as anchors)
    Each structure includes:
      - 12 chapter title drafts
      - 3-5 identified kickpoints (life turning points)
      - 2 controlling metaphor candidates
      - Emotional arc visualization (한-흥-정 cycle)
      - Material Strength Map (rich vs sparse interview areas)

  Phase B: User Consultation (human — core interaction)
    Q1: "Which structure resonates most? Or do you have a different vision?"
    Q2: "What are the 3 most important turning points in your life?"
    Q3: "What is the single message you want readers to take away?"
    Q4: "Is there anything you want to exclude or especially emphasize?"
    Record all responses in story_blueprint.json

  Phase C: Blueprint Confirmation (human-approve)
    Display final blueprint with user's choices incorporated
    User: [Approve] / [Request changes] / [Redesign from scratch]
  ```
- **Output**: `outputs/story-blueprint/story_blueprint.json`
- **Post-processing**: `python3 scripts/validate_blueprint.py --project-dir .`
- **Translation**: `@translator`

---

## Planning

### 5. Story Bible Construction
- **Pre-processing**: Load all interview transcripts from `outputs/interviews/` + story blueprint from `outputs/story-blueprint/story_blueprint.json` + voice fingerprint from `outputs/voice_fingerprint.json`
- **Agent**: `@story-architect`
- **Technology**: sub-agent (narrative architecture requires holistic single-architect vision)
- **Quality Rationale**: Thematic coherence requires one architect seeing the full picture; splitting would weaken cross-theme connections
- **Verification**:
  - [ ] Story bible passes schema validation: `python3 scripts/schema_validator.py --schema schemas/story_bible.schema.json --data outputs/story-bible/story_bible.json`
  - [ ] Quality gate passes: `python3 scripts/validate_story_bible.py --story-bible outputs/story-bible/story_bible.json`
  - [ ] All SB1-SB10 checks pass (entity cross-ref, timeline order, character appearances, theme coverage, chapter completeness, fact registry, voice guide)
  - [ ] At least 3 characters, 5 timeline events, 3 themes, 3 chapters planned
  - [ ] Every chapter plan entry has source interviews cited
  - [ ] voice_guide populated with quantified metrics from compute_voice_fingerprint.py output (NOT AI estimates)
  - [ ] Blueprint constraints honored: structure_type, kickpoints, emphasis_areas, exclusion_areas
  - [ ] Source tracing validated: `python3 scripts/validate_source_tracing.py --artifact outputs/story-bible/story_bible.json --project-dir .`
- **Task**: Synthesize all interviews into a comprehensive story bible, **constrained by the user-approved story blueprint**. Build: character registry with canonical names, chronological timeline, place registry, theme analysis, chapter plan, voice guide (using Python-computed metrics as baseline), and fact registry. The blueprint's kickpoints, core_message, emphasis_areas, and exclusion_areas are binding constraints.
- **Output**: `outputs/story-bible/story_bible.json`
- **Post-processing**: `python3 scripts/validate_story_bible.py --story-bible outputs/story-bible/story_bible.json --project-dir .`
- **Translation**: `@translator`

### 6. Story Bible Review
- **Agent**: `@reviewer`
- **Technology**: sub-agent (full bible must be read by single reviewer to catch cross-references)
- **Quality Rationale**: One reviewer catches all cross-reference inconsistencies; splitting risks missed contradictions between sections
- **Verification**:
  - [ ] Review verdict produced per `schemas/review_verdict.schema.json`
  - [ ] Pre-mortem section completed
  - [ ] At least 1 issue identified (anti-rubber-stamp)
  - [ ] Independent pACS scored before seeing generator's score
  - [ ] Timeline contradictions flagged (if any)
  - [ ] Character arc completeness assessed
  - [ ] Blueprint compliance verified (story bible honors all blueprint constraints)
  - [ ] pACS floor check: `python3 scripts/validate_pacs_floor.py --step 6 --project-dir .`
- **Task**: Adversarial review of story bible. Check factual accuracy against interviews, timeline coherence, character completeness, theme coverage, voice guide specificity. Verify that blueprint constraints (kickpoints, emphasis_areas, exclusion_areas) are honored.
- **Output**: `review-logs/RV-story-bible.json`
- **Translation**: `@translator`

### 7. (human) Story Bible Approval
- **Action**: Review story bible and reviewer feedback. Approve chapter plan, voice guide, and narrative structure. Approve or modify before style selection and writing begins.
- **Pre-display**: Story bible summary + reviewer feedback (critical/warning/suggestion counts) + pACS scores
- **Options**:
  1. Approve — proceed to writing style selection (Step 8)
  2. Revise story bible — return to Step 5 with specific corrections
  3. Restructure chapters — modify chapter plan ordering or scope
  4. Revise blueprint — return to Step 4 to change narrative structure
- **Translation**: `@translator`

### 8. (human) Writing Style Selection & Calibration
- **Agent**: Orchestrator (facilitates) + `@chapter-writer` (produces calibration samples)
- **Technology**: sub-agent (sequential — each sample must learn from previous for quality improvement)
- **Quality Rationale**: Calibration samples must be sequentially refined; parallel generation produces similar-quality results without iterative improvement
- **Pre-processing**:
  - Load voice fingerprint: `outputs/voice_fingerprint.json` (Python-computed from interviews)
  - Load story bible voice_guide: `outputs/story-bible/story_bible.json`
  - Load available style skills from `.claude/skills/writing-styles/`
- **Verification**:
  - [ ] Style selection validates: `python3 scripts/validate_style_selection.py --project-dir .`
  - [ ] All SS1-SS5 checks pass (style chosen from valid set, blending_ratio 0.0-1.0, 3 calibration samples exist with ≥ 400 words each, voice_guide updated in story_bible)
  - [ ] Blended voice_guide metrics are mathematically correct: `python3 scripts/style_blender.py --verify --project-dir .`
  - [ ] User explicitly approved the final style
- **Task**: Guide the user through writing style selection and voice calibration.
  ```
  Phase A: Style Gallery (auto)
    Display 10 style skill cards with:
      - Author name + core technique
      - Key voice parameters (sentence length, dialogue ratio, etc.)
      - Suitable autobiography types
      - 2 golden exemplar sentences
    Display "Top 3 Recommended" based on voice fingerprint similarity:
      "Your interview voice shows [metrics]. Style X matches at [N]% similarity."
    Display "Custom Blend" option (mix 2-3 styles)

  Phase B: User Selection (human)
    Q1: "Which style appeals to you? (number, name, or 'custom')"
    Q2: "Adjust blending ratio? (default: 30% style / 70% your voice)"
    Q3: "Any specific style elements to emphasize or avoid?"

  Phase C: Calibration Samples (auto → human)
    @chapter-writer produces Chapter 1 opening (~500 words) in 3 versions:
      Version A: Style-heavy (50% style / 50% voice)
      Version B: Balanced blend (30% style / 70% voice) — default
      Version C: Voice-heavy (10% style / 90% voice)
    User selects preferred version → blending ratio confirmed

  Phase D: Voice Guide Finalization (auto)
    style_blender.py computes final blended parameters (pure arithmetic)
    Update story_bible.voice_guide with blended metrics
    Display final voice_guide to user for confirmation
  ```
- **Output**: `outputs/style-selection/style_selection.json` + 3 calibration samples
- **Post-processing**: `python3 scripts/style_blender.py --apply --project-dir .` + `python3 scripts/validate_style_selection.py --project-dir .`
- **Translation**: `@translator` (calibration samples only — user needs to see Korean versions)

---

## Implementation

### 9. Chapter Writing Loop (per chapter)

For each chapter N in the chapter plan (executed sequentially by default):

#### Technology Selection (quality-driven)

```
IF total_chapters ≤ 6:
  → Sub-agent (sequential): Single @chapter-writer writes all chapters
  → Rationale: Under 500KB context, one writer maintains natural voice consistency

IF total_chapters > 6:
  → Agent-team: 2-3 @chapter-writers split by life-period clusters
  → Rationale: Over 500KB context causes attention fatigue; splitting preserves quality
  → Shared: story_bible + voice_guide (identical for all writers)
  → Isolated: interview segments (each writer gets only their cluster's interviews)
  → SOT Safety: Team Lead (Orchestrator) only writes state.yaml
```

#### Agent Team Parallelization (when total_chapters > 6)

```
Orchestrator (Team Lead)
├── Phase A: Parallel chapter drafting (Agent Team)
│   ├── @chapter-writer: Ch.1-4 (early life)
│   ├── @chapter-writer: Ch.5-8 (middle life)
│   └── @chapter-writer: Ch.9-12 (later life)
├── Phase B: Voice Calibration (sequential — cross-chapter consistency)
│   └── @voice-calibrator: each chapter against blended voice_guide
└── Phase C: Chapter Quality Gate (parallel review)
    ├── @reviewer: Ch.1-4
    ├── @reviewer: Ch.5-8
    └── @reviewer: Ch.9-12
```

**active_team SOT update** (Team Lead only):
```yaml
active_team:
  name: "chapter-writing-team"
  status: "partial"
  tasks_completed: ["ch01", "ch02"]
  tasks_pending: ["ch03", "ch04", ...]
  completed_summaries: {ch01: {words: 4200, voice_score: 0.85}, ...}
```

**Sequential mode (default)**: Execute 9a-9d for chapters 1 through N in order.

#### 9a. Context Assembly
- **Pre-processing**: `python3 scripts/assemble_chapter_context.py --chapter {N} --project-dir .`
- **Agent**: Orchestrator
- **Verification**:
  - [ ] Context package produced at `outputs/chapters/ch{NN}_context.json`
  - [ ] Token budget calculated and within limits
  - [ ] Relevant characters, events, places filtered from story bible
  - [ ] Interview segments loaded for this chapter's source interviews
  - [ ] Previous chapter closing paragraphs included (if N > 1)
  - [ ] Blended voice_guide parameters included explicitly
- **Task**: Assemble focused context for the chapter writer. Filter story bible to relevant entities, load pertinent interview segments, extract continuity context from previous chapters. Include blended voice_guide with explicit numeric targets.
- **Output**: `outputs/chapters/ch{NN}_context.json`

#### 9b. Chapter Drafting
- **Agent**: `@chapter-writer`
- **Verification**:
  - [ ] Prose file produced: `outputs/chapters/ch{NN}_draft_v{V}.md`
  - [ ] Metadata file produced: `outputs/chapters/ch{NN}_draft_v{V}.meta.json`
  - [ ] Word count within +/- 15% of target
  - [ ] At least 2 sections/scenes
  - [ ] At least 1 interview source cited
  - [ ] Schema validation passes on metadata
  - [ ] Source tracing validated: `python3 scripts/validate_source_tracing.py --artifact outputs/chapters/ch{NN}_draft_v{V}.meta.json --project-dir .`
  - [ ] Voice match validated: `python3 scripts/validate_voice_match.py --chapter {N} --project-dir .`
- **Task**: Write the chapter as literary prose in English. Follow blended voice_guide, use interview quotes, show-don't-tell, maintain continuity with previous chapters. Apply selected writing style at the confirmed blending ratio.
- **Output**: `outputs/chapters/ch{NN}_draft_v{V}.md` + `.meta.json`
- **Translation**: `@translator` (per chapter, after quality gate PASS)

#### 9c. Voice Calibration
- **Agent**: `@voice-calibrator`
- **Technology**: sub-agent (sequential — previous chapter metrics inform next chapter baseline)
- **Verification**:
  - [ ] Voice metrics computed: sentence length, dialogue ratio, passive voice %, show:tell ratio
  - [ ] Forbidden word check completed
  - [ ] All metrics within acceptable thresholds (blended voice_guide ± tolerance)
  - [ ] Python cross-verification: `python3 scripts/validate_voice_match.py --chapter {N} --project-dir .`
- **Task**: Analyze chapter prose against blended voice_guide metrics. Produce quantitative deviation report. Flag metrics outside tolerance range.
- **Output**: Voice calibration report (included in chapter metadata update)

#### 9d. Chapter Quality Gate
- **Pre-processing**: `python3 scripts/validate_chapter.py --chapter {N} --project-dir .`
- **Agent**: `@reviewer`
- **Verification**:
  - [ ] Chapter validation passes all CH1-CH10 checks
  - [ ] Reviewer produces verdict per `schemas/review_verdict.schema.json`
  - [ ] Pre-mortem completed
  - [ ] Voice consistency scored
  - [ ] Source fidelity verified (claims checked against interviews)
  - [ ] pACS floor check: `python3 scripts/validate_pacs_floor.py --step 9 --chapter {N} --project-dir .`
  - [ ] If FAIL: revision cycle (return to 9b with feedback, max 3 rounds; Chapter 1 gets 5 rounds)
- **Task**: Adversarial review of chapter draft. Check prose quality, voice consistency, factual accuracy, emotional authenticity, structural completeness.
- **Output**: `review-logs/RV-ch{NN}-round{R}.json`
- **Post-processing**: If PASS, update state.yaml chapter status to "approved". If FAIL, loop to 9b.

### 10. Cross-Chapter Consistency Check
- **Pre-processing**: `python3 scripts/validate_consistency.py --project-dir .`
- **Agent**: `@reviewer` (continuity dimension) + `@reviewer-deep` (anti-homogenization)
- **Technology**: agent-team (two independent reviewers catch different issues — adversarial independence)
- **Quality Rationale**: Two independent adversarial reviewers prevent groupthink; each catches issues the other misses
- **Verification**:
  - [ ] All CC1-CC8 checks executed across all approved chapters
  - [ ] Name consistency verified (canonical names only)
  - [ ] Timeline consistency verified (chronological order)
  - [ ] Character appearance ordering verified
  - [ ] Place consistency verified
  - [ ] Fact registry compliance verified
  - [ ] Consistency report produced
- **Task**: Full cross-chapter consistency audit. Check every name, date, place, character appearance, and verifiable fact against the story bible.
- **Output**: `review-logs/consistency-report.json`
- **Post-processing**: If critical issues found, identify affected chapters and return to 9b for targeted revisions.
- **Translation**: `@translator`

#### Agent Team Dimensional Review (quality maximization)

Full manuscript (~500KB) reviewed by a single agent causes attention degradation. Dimensional split ensures each reviewer focuses on specific verification dimensions:

```
Orchestrator (Team Lead)
├── @reviewer: Name/character consistency (CC1-CC3)
├── @reviewer: Timeline/place consistency (CC4-CC6)
├── @reviewer-deep: Repeated narratives / anti-homogenization (CC7-CC8)
└── Orchestrator: Merge results → consistency-report.json
```

**SOT Safety**: Each reviewer writes only `review-logs/RV-consistency-{dimension}.json`. Orchestrator merges and updates SOT.

### 11. (human) Manuscript Review
- **Action**: Review complete manuscript. Read consistency report. Approve final manuscript or request targeted revisions.
- **Pre-display**: All chapter titles + word counts + status + consistency check results + pACS history
- **Options**:
  1. Approve — proceed to book build
  2. Revise specific chapters — return to Step 9 for identified chapters
  3. Major restructure — return to Step 5 to revise story bible
  4. Revise blueprint — return to Step 4 to change narrative structure
- **Translation**: `@translator`

### 12. Book Build
- **Pre-processing**: Ensure all chapters are in "approved" or "final" status
- **Agent**: Orchestrator
- **Technology**: sub-agent
- **Verification**:
  - [ ] Combined manuscript markdown produced (English)
  - [ ] Combined manuscript markdown produced (Korean — from translated chapters)
  - [ ] PDF builds successfully via XeLaTeX + memoir template (EN + KO)
  - [ ] EPUB builds successfully with custom CSS (EN + KO)
  - [ ] Table of contents generated
  - [ ] Front matter (title page, dedication, preface) included
  - [ ] Back matter (acknowledgments, about the author) included
  - [ ] Build manifest produced with word counts and file paths
- **Task**: Run the Pandoc build pipeline to produce final book files in both English and Korean.
- **Output**: `outputs/builds/book_latest.pdf`, `outputs/builds/book_latest.epub`, `outputs/builds/book_latest.ko.pdf`, `outputs/builds/book_latest.ko.epub`
- **Post-processing**: `python3 scripts/build_book.py --project-dir . --format all --languages en,ko`

---

## Agent Registry

| Agent | Role | Model | Tools | SOT Access |
|-------|------|-------|-------|------------|
| Orchestrator | Workflow coordinator, state manager | opus | All | Read/Write state.yaml |
| `@interviewer` | AI-guided interview conductor | opus | Read, Glob, Grep | Read only |
| `@story-architect` | Story bible constructor (constrained by blueprint) | opus | Read, Glob, Grep, Bash | Write story_bible.json |
| `@chapter-writer` | Prose author (with style blending) | opus | Read, Glob, Grep, Bash | Read only |
| `@voice-calibrator` | Voice metrics analyzer | sonnet | Read, Glob, Grep, Bash | Read only |
| `@reviewer` | Adversarial quality reviewer + cross-chapter consistency (7-dimension, CoVe) | opus | Read, Write, Edit, Glob, Grep, Bash | Read only |
| `@reviewer-deep` | Anti-homogenization deep scan (Step 10 only) | opus | Read, Glob, Grep | Read only |
| `@translator` | English→Korean translation with glossary consistency (7-step protocol) | opus | Read, Write, Glob, Grep | Read only |

## Validation Scripts (P1 Hallucination Prevention)

| Script | Purpose | Trigger | Checks |
|--------|---------|---------|--------|
| `schema_validator.py` | JSON Schema compliance for all artifacts | After every JSON write | Schema match |
| `validate_story_bible.py` | Story bible quality gate | After Step 5 | SB1-SB10 |
| `validate_chapter.py` | Chapter quality gate | After Step 9b | CH1-CH10 |
| `validate_consistency.py` | Cross-chapter consistency | After Step 10 | CC1-CC8 |
| `compute_voice_fingerprint.py` | Deterministic voice metrics from interviews | Before Step 4 | H2 metrics (sentence length, dialogue ratio, etc.) |
| `validate_blueprint.py` | Blueprint structure + coverage | After Step 4 | BP1-BP7 |
| `validate_interview_coverage.py` | Interview completeness | After Step 2 | IC1-IC5 |
| `validate_source_tracing.py` | [INFERRED] tag + source verification | After Step 5, 9b | ST1-ST6 |
| `validate_voice_match.py` | Chapter vs voice_guide metrics | After Step 9b, 9c | VM1-VM6 |
| `validate_pacs_floor.py` | pACS self-assessment inflation check | After Step 6, 9d | Floor computation |
| `style_blender.py` | Style parameter blending (pure arithmetic) | After Step 8 | SS blending |
| `validate_style_selection.py` | Style selection integrity | After Step 8 | SS1-SS5 |
| `assess_material.py` | Interview richness scoring | Before Step 4 | Depth scores |
| `init_project.py` | Deterministic project initialization + symlink management | `/start` Step 4-2 | Project ID, dirs, symlinks |
| `validate_project_init.py` | Project isolation integrity | `/start` Step 4-3b | PI1-PI8 |

## Validation Enforcement Matrix (P1 — Mandatory)

Every step completion MUST trigger its validation chain. Orchestrator MUST NOT advance `current_step` until ALL validations PASS.

| Step | Validation Chain (execute in order) | Blocks |
|------|-------------------------------------|--------|
| 2 | `validate_interview_coverage.py --project-dir .` (IC1-IC5) | Step 3 |
| 4 | `validate_blueprint.py --project-dir .` (BP1-BP7) | Step 5 |
| 5 | `validate_story_bible.py` (SB1-SB10) → `validate_pacs.py --step 5 --check-l0` → `validate_source_tracing.py` (ST1-ST6) | Step 6 |
| 6 | `validate_review.py --step 6 --check-pacs-arithmetic` (R1-R5 + T9) | Step 7 |
| 8 | `validate_style_selection.py` (SS1-SS5) → `style_blender.py --verify` | Step 9 |
| 9b | `validate_voice_match.py --chapter N` (VM1-VM6) → `validate_source_tracing.py` (ST1-ST6) | Step 9c |
| 9d | `validate_review.py --step 9 --check-pacs-arithmetic` → `validate_pacs_floor.py --step 9 --chapter N` | Next chapter or Step 10 |
| 9-translation | `validate_translation.py --step 9 --check-sequence --check-pacs` (T1-T9 + RV1) | SOT update |
| 10 | `validate_consistency.py` (CC1-CC8) → `validate_review.py --step 10 --check-pacs-arithmetic` | Step 11 |
| N-translation | `validate_translation.py --step N --check-sequence --check-pacs` (T1-T9 + RV1) | SOT outputs.step-N-ko |

**NEVER DO**: Advance `current_step` without running the validation chain. If any CRITICAL check fails, the step MUST be re-executed.

## Hook Configuration

Active hooks registered in `.claude/settings.json`:

| Hook Event | Script | Purpose |
|-----------|--------|---------|
| Setup (init) | `setup_init.py` | Infrastructure health + SOT write safety |
| Setup (maintenance) | `setup_maintenance.py` | Periodic health check + doc-code sync |
| PreToolUse (Bash) | `block_destructive_commands.py` | Block dangerous/network/system commands (exit 2) |
| PreToolUse (Edit\|Write) | `block_test_file_edit.py` | TDD Guard — protect test files |
| PreToolUse (Edit\|Write) | `predictive_debug_guard.py` | Error-history-based risk warning |
| PreToolUse (Write) | `validate_schema_on_write.py` | Enforce JSON Schema on autobiography artifacts |
| SessionStart (clear\|compact\|resume) | `context_guard.py --mode=restore` | RLM context restoration |
| PostToolUse (9 tools) | `context_guard.py --mode=post-tool` | Work log tracking |
| PostToolUse (Bash\|Read) | `output_secret_filter.py` | Secret detection (25+ patterns, 2-pass) |
| PostToolUse (Edit\|Write) | `security_sensitive_file_guard.py` | Security-sensitive file warning |
| Stop | `context_guard.py --mode=stop` | Incremental snapshot + Knowledge Archive |
| PreCompact | `context_guard.py --mode=pre-compact` | Pre-compression snapshot |
| SessionEnd (clear) | `save_context.py` | Full snapshot save |

Autobiography-specific hooks (in `autobiography-generator/.claude/hooks/scripts/`, available but not yet activated):

| Script | Purpose | Activation Status |
|--------|---------|-------------------|
| `update_state_on_write.py` | Auto-update state.yaml on artifact write | Available |
| `track_chapter_progress.py` | Log chapter progress metrics | Available |
| `checkpoint_state.py` | State checkpoint on stop | Superseded by `context_guard.py` |
