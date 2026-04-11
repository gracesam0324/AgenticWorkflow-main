# Quality Gates — L0 through L2 Specifications

## Overview

Quality enforcement uses a 4-layer system inherited from the AgenticWorkflow genome. Each layer serves a distinct purpose, and they execute in sequence — a step must pass all applicable layers before advancing.

```
L0 (Anti-Skip Guard)
  → L1 (Verification Gate — Python deterministic)
    → L1.5 (pACS Self-Rating — agent introspection)
      → L2 (Calibration — @autobiography-reviewer adversarial evaluation)
```

---

## L0: Anti-Skip Guard

### Purpose
Prevent agents from skipping validation steps entirely. Structural enforcement — not a quality check itself, but a guarantee that quality checks actually run.

### Mechanism

Schema validation hooks fire on every JSON write:
- `PreToolUse(Write|Edit)` → `validate_schema_on_write.py`
- Rejects writes to `outputs/` that do not conform to their schema
- Cannot be bypassed by agents — hook runs at the infrastructure level

### What L0 Enforces

| Artifact | Schema | Rejection Condition |
|----------|--------|-------------------|
| Interview transcript | `schemas/interview_transcript.schema.json` | Missing required fields, invalid types |
| Story bible | `schemas/story_bible.schema.json` | Missing components, broken references |
| Chapter metadata | `schemas/chapter_metadata.schema.json` | Missing fields, invalid version |
| Review verdict | `schemas/review_verdict.schema.json` | Missing dimensions, no verdict |
| Consistency report | `schemas/consistency_report.schema.json` | Missing check categories |

### Anti-Skip Properties
- Fires automatically (no agent cooperation needed)
- Returns exit code 2 (hard block) — the write is rejected
- Agent must fix the artifact and re-attempt the write
- Logged in `review-logs/l0-rejections.jsonl`

---

## L1: Verification Gate (Python Deterministic)

### Purpose
Run all checks that can be deterministically computed by Python. These checks are objective, reproducible, and cannot hallucinate.

### Primary Script

```bash
.venv/bin/python3 scripts/quality_gate_check.py --step {step_id} [--chapter {N}]
```

**Exit codes:**
- 0 = all checks pass
- 1 = one or more checks fail (diagnostic on stderr)

### Check Registry by Step

#### Build Phase
| Check ID | Description |
|----------|-------------|
| `check_schemas_valid` | All JSON schemas are syntactically valid |
| `check_scripts_syntax` | All Python scripts compile without errors |
| `check_tests_pass` | Full test suite passes |

#### Research Phase
| Check ID | Description |
|----------|-------------|
| `check_interview_schema` | Transcript conforms to schema |

#### Story Bible
| Check ID | Description |
|----------|-------------|
| `check_story_bible_schema` | Bible conforms to schema |
| `check_story_bible_completeness` | SB1-SB10 checks pass |

#### Chapter (Step 7c/7d — runs BEFORE @autobiography-reviewer)
| Check ID | Description |
|----------|-------------|
| `check_chapter_schema` | Metadata conforms to schema |
| `check_chapter_word_count` | Within +/- 15% of target |
| `check_chapter_forbidden_words` | No forbidden vocabulary |
| `check_chapter_sentence_length` | Distribution within thresholds |
| `check_chapter_inferred_ratio` | `[INFERRED]` tags within cap |
| `check_chapter_voice_metrics` | Quantitative voice metrics |
| `check_chapter_byeonyeokche` | 번역체 patterns 5-9 (regex) |
| `check_chapter_metaphor` | Controlling metaphor presence |
| `check_chapter_emotional_balance` | Emotional balance scoring |

#### Cross-Chapter
| Check ID | Description |
|----------|-------------|
| `check_consistency_names` | Name consistency (CC-01) |
| `check_consistency_timeline` | Timeline consistency (CC-02) |
| `check_consistency_places` | Place consistency (CC-03) |
| `check_consistency_characters` | Character appearance ordering (CC-04) |

### Constraint: No LLM Calls

L1 scripts MUST NEVER:
- Invoke an LLM
- Spawn a subagent
- Make any non-deterministic call
- Use random sampling

If a check requires judgment, it belongs at L1.5 or L2, not L1.

---

## L1.5: pACS Self-Rating

### Purpose
Agent self-assessment on three dimensions. Provides early warning of quality issues before the adversarial reviewer sees the output.

### Dimensions

| Dimension | Code | What It Measures |
|-----------|------|-----------------|
| Factual Accuracy | F | Are all claims grounded in source material? |
| Completeness | C | Are all required elements present? |
| Literary Quality | L | Does the output meet the literary standard? |

### Scoring

Each dimension: 0-100 (integer)
- Combined score: weighted average (F: 40%, C: 30%, L: 30%)
- Minimum threshold: **60** per dimension
- Human checkpoint threshold: **70** combined (BLOCKING for translations)

### When pACS Runs
- After every agent produces output (built into agent instructions)
- Before output is submitted to Orchestrator
- Score recorded in `state.yaml.workflow.pacs`

### pACS Below Threshold

| Score | Action |
|-------|--------|
| >= 70 | Proceed to next layer |
| 60-69 | Proceed with WARNING logged; reviewer notified of weak areas |
| < 60 on any dimension | Agent must self-revise before submitting |
| < 60 after self-revision | Escalate to Orchestrator for routing decision |

### SOT Tracking

```yaml
workflow:
  pacs:
    current_step_score: 72
    dimensions:
      F: 80
      C: 65
      L: 70
    weak_dimension: "C"
    history:
      step-4: { F: 85, C: 78, L: 72 }
      step-7b-ch01: { F: 90, C: 82, L: 68 }
```

---

## L2: Calibration (@autobiography-reviewer Adversarial Evaluation)

### Purpose
LLM-based qualitative evaluation that catches everything Python and self-assessment cannot. The adversarial reviewer acts as an independent critic.

### When L2 Runs
- After L1 passes for chapter-producing steps (7d → 7e)
- Story Bible review (Step 4.5, before H2)
- Cross-chapter continuity check (Step 8)

### L2 Does NOT Run For
- Build phase steps (L1 sufficient)
- Interview production (L1 schema check sufficient)
- Material assessment (Python-only scoring)
- Export/build (L1 artifact check sufficient)

### Reviewer Scope Boundary

The reviewer handles ONLY what Python cannot:

**Reviewer's exclusive domain:**
1. 번역체 patterns 1-4 (qualitative)
2. 여운 ending quality
3. 기승전결 structure quality
4. 침묵 as narrative
5. 의미 발견 moments
6. Voice authenticity
7. Narrative thread resolution (CC-07)
8. 한-흥-정 transition quality
9. CoVe: claim verification against Story Bible
10. Overall literary quality judgment

**NOT the reviewer's domain** (Python handles):
- Word count, schema compliance, forbidden words
- Sentence length statistics
- `[INFERRED]` ratio
- Name/timeline/place consistency (CC-01 to CC-04)
- Voice statistics (quantitative)
- 번역체 patterns 5-9 (regex)

### Verdict Format

```
APPROVE — chapter advances to next step
REVISE  — chapter returns to 7b with specific feedback
```

### Anti-Rubber-Stamp Rule
- Every review MUST identify at least 1 issue (even if minor/suggestion)
- 0-issue reviews are structurally invalid
- Any dimension score below 40/100 forces REVISE regardless of total

### L2 at Step 8 (Deep Review)

At Step 8, two reviewers operate (in parallel if Agent Teams available):
- `@autobiography-reviewer`: consistency + literary quality across all chapters
- `@reviewer-deep`: anti-homogenization, pattern detection, structural variety

---

## Gate Interaction Flow

Complete flow for a chapter (Step 7):

```
7b: @chapter-writer produces draft
    ↓
7c: @voice-calibrator measures metrics
    ↓
L0: Schema hook validates chapter metadata JSON write
    ↓
L1: quality_gate_check.py --step 7c --chapter N
    ↓ FAIL → return to 7b (no reviewer involved)
    ↓ PASS
L1.5: @chapter-writer's pACS self-rating checked
    ↓ < 60 → self-revision → re-check
    ↓ >= 60
L2: @autobiography-reviewer 7-dimension evaluation
    ↓ REVISE → return to 7b with feedback (max 3 rounds)
    ↓ APPROVE
SOT updated: chapter status = "approved"
    ↓
Next chapter (or Step 8 if last chapter)
```

---

## Cost Awareness

Quality gates have cost implications:
- L0: Zero cost (hook infrastructure)
- L1: Minimal cost (Python script execution)
- L1.5: Built into agent turns (no additional cost)
- L2: Significant cost (full LLM evaluation per chapter)

The Python gate at L1 BEFORE L2 is a deliberate cost optimization — structurally deficient chapters are caught early without spending L2 budget.
