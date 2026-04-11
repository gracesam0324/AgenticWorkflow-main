# Implementation Phase — Chapter Writing, Review, and Export

## Overview

The Implementation phase (Steps 7 through 11) is where the book is written, reviewed, and published. The central mechanism is the chapter writing loop (Step 7), which iterates through each chapter with drafting, calibration, quality gates, and revision cycles.

## Step Map

| Step | Name | Agent | Output |
|------|------|-------|--------|
| 7 | Chapter Writing Loop | Multiple | `outputs/chapters/ch{NN}_draft_v{V}.md` |
| 8 | Continuity Check | `@autobiography-reviewer` + `@reviewer-deep` | `review-logs/consistency-report.json` |
| 8.5 | H6: Manuscript Review | Human | Decision: approve / revise / restructure |
| 9 | Book Build + Export | Orchestrator | `outputs/builds/book_latest.pdf`, `.epub` |
| 9.5 | H7: Final Approval | Human | Decision: approve / revise |
| 10 | Publishing Guide | Orchestrator | `outputs/publishing-guide.md` |
| 11 | Cost Report | Orchestrator | `outputs/cost-report.md` |

---

## Step 7: Chapter Writing Loop

For each chapter N in the chapter plan (executed sequentially):

### 7a: Context Assembly

**Agent**: Orchestrator

```bash
.venv/bin/python3 scripts/assemble_chapter_context.py --chapter {N} --project-dir .
```

Produces `outputs/chapters/ch{NN}_context.json` containing:
- Filtered story bible entities (characters, events, places relevant to this chapter)
- Relevant interview segments from source interviews
- Previous chapter closing paragraphs (if N > 1)
- Token budget calculation
- Voice guide and literary directives
- Controlling metaphor threading instructions

**Verification checklist:**
- Context package produced
- Token budget within limits
- Relevant entities filtered correctly
- Source interviews loaded
- Previous chapter bridge included (N > 1)

### 7b: Chapter Drafting

**Agent**: `@chapter-writer`

**Input**: Context package from 7a + voice guide + literary directives

**Output**:
- `outputs/chapters/ch{NN}_draft_v{V}.md` — prose file
- `outputs/chapters/ch{NN}_draft_v{V}.meta.json` — metadata file

**Verification checklist:**
- Prose file produced
- Metadata file produced
- Word count within +/- 15% of target
- At least 2 sections/scenes
- At least 1 interview source cited
- Schema validation passes on metadata

**Korean-Native Writing**: Chapter prose is written DIRECTLY in Korean, not translated from English. The chapter-writer operates in Korean-native mode following Appendix A literary directives.

### 7c: Voice Calibration

**Agent**: `@voice-calibrator`

Analyzes chapter prose against voice guide metrics:
- Sentence length distribution
- Dialogue ratio
- Passive voice percentage
- Show:tell ratio
- Forbidden word check

**Output**: Voice calibration report (included in chapter metadata update)

### 7d: Python Quality Gate (MUST pass before @autobiography-reviewer)

**Critical**: This deterministic gate runs BEFORE the `@autobiography-reviewer` receives the chapter. This is the boundary between Python-deterministic and LLM-qualitative checks.

```bash
.venv/bin/python3 scripts/quality_gate_check.py --step 7c --chapter {N}
```

**Deterministic checks performed:**
- CH1-CH10 chapter validation
- Word count compliance
- Forbidden word detection
- Sentence length statistics
- `[INFERRED]` tag ratio
- Voice metrics quantitative thresholds
- 번역체 patterns 5-9 (regex-detectable)
- Metaphor validation
- Emotional balance scoring

If this gate FAILS, the chapter returns to 7b immediately WITHOUT going to `@autobiography-reviewer`. This saves review budget and prevents the reviewer from evaluating structurally deficient drafts.

### 7e: Adversarial Review

**Agent**: `@autobiography-reviewer`

**Scope boundary**: The reviewer handles ONLY qualitative literary judgment that requires LLM evaluation. All deterministic checks have already passed in 7d.

**7-dimension evaluation:**

| Dimension | Weight | Assessment |
|-----------|--------|-----------|
| Emotional Resonance | 20% | 한-흥-정 transitions, embodied emotion, 여운 endings |
| Voice Consistency | 20% | Subject authenticity, honorific shifts, golden exemplar presence |
| Prose Quality | 15% | 번역체-free (qualitative), 침묵, surprise sentences |
| Factual Accuracy | 15% | CoVe verification, source traceability |
| Narrative Arc | 15% | 기승전결, 이중 의식 ratio, 의미 발견 |
| Source Traceability | 10% | Interview references verifiable |
| Continuity | 5% | Thread tracking, cross-chapter narrative consistency |

**Verdict**: APPROVE or REVISE

**Output**: `review-logs/RV-ch{NN}-round{R}.json`

### 7f: Revision Loop

If `@autobiography-reviewer` issues a REVISE verdict:

1. Feedback from review is attached to the context package
2. Chapter returns to 7b with specific revision instructions
3. Draft version increments (v1 -> v2 -> v3)
4. Process repeats: 7b -> 7c -> 7d -> 7e

**Revision limits:**
- General chapters: max 3 revision rounds
- Chapter 1: max 5 revision rounds (voice calibration anchor)
- `voice_score < 0.60`: triggers voice re-profiling (return to Step 5a)

**After max revisions**: Escalate to human review (Tier 4)

### SOT Tracking per Chapter

```yaml
workflow:
  chapters:
    ch-{N}:
      status: "drafting" | "in_review" | "revision" | "approved"
      draft_version: {V}
      word_count: {W}
      review_rounds: {R}
      voice_score: {S}
      pacs_score: {P}
orchestration:
  current_substep: "7b" | "7c" | "7d" | "7e" | "7f"
```

---

## Step 8: Cross-Chapter Continuity Check

### Pre-processing

```bash
.venv/bin/python3 scripts/validate_consistency.py --project-dir .
```

### Agent Teams (if available)

Two agents run in parallel:

| Agent | Focus |
|-------|-------|
| `@autobiography-reviewer` | CC1-CC8 consistency: names, dates, places, characters, facts |
| `@reviewer-deep` | Anti-homogenization: opening/closing patterns, metaphor tracking, structural variety |

### Sequential Fallback

If Agent Teams unavailable, `@autobiography-reviewer` runs first (consistency), then `@reviewer-deep` runs second (anti-homogenization).

### Checks Performed

**Consistency (CC1-CC8):**
- CC1: Name consistency against story bible
- CC2: Date and timeline chronology
- CC3: Place consistency
- CC4: Character appearance ordering
- CC5: Object and detail consistency
- CC6: Fact registry compliance
- CC7: Narrative thread tracking (LLM-only)
- CC8: Source fidelity (quotes match interviews)

**Anti-Homogenization:**
- No repeated anecdotes (> 70% semantic overlap)
- Opening pattern variety across chapters
- Closing pattern variety across chapters
- Controlling metaphor presence and evolution
- Golden exemplar integration
- Chapter rhythm variation

### Output
- `review-logs/consistency-report.json`

### Critical Issue Handling
If critical consistency issues found: identify affected chapters and queue targeted revisions (return to 7b for specific chapters).

---

## Step 8.5: H6 Checkpoint — Manuscript Review

### Pre-Checkpoint
1. All chapters in "approved" status
2. Consistency report generated
3. Anti-homogenization report generated
4. Total word count and chapter count summarized
5. Korean translation of reports available

### User Options

| Choice | Action |
|--------|--------|
| **Approve** | Advance to Step 9 (Export) |
| **Revise specific chapters** | Return to Step 7 for identified chapters only |
| **Major restructure** | Return to Step 4 to revise story bible |

---

## Step 9: Book Build + Export

### Pre-processing
Verify all chapters are in "approved" or "final" status.

### Build Pipeline

```bash
.venv/bin/python3 scripts/build_book.py --project-dir . --format all
```

### Outputs

| Format | File | Details |
|--------|------|---------|
| PDF (screen) | `outputs/builds/book_latest.pdf` | XeLaTeX + memoir, A5 screen optimized |
| PDF (print) | `outputs/builds/book_print.pdf` | 6x9 KDP/IngramSpark ready (optional) |
| EPUB | `outputs/builds/book_latest.epub` | EPUB3 with custom CSS |
| Manuscript | `outputs/builds/manuscript.md` | Combined markdown |

### Build Includes
- Title page, dedication, preface (front matter)
- Table of contents (auto-generated)
- All chapters in sequence
- Acknowledgments, about the author (back matter)
- Build manifest with word counts and file paths

---

## Step 9.5: H7 Checkpoint — Final Approval

### User Options

| Choice | Action |
|--------|--------|
| **Approve** | Advance to Step 10 (Publishing Guide) |
| **Request changes** | Return to specific chapters or formatting |

---

## Step 10: Publishing Guide

Orchestrator generates a publishing guide with:
- Self-publishing options (Amazon KDP, IngramSpark)
- Traditional publishing query letter template
- ISBN procurement guidance
- Cover design recommendations

### Output
- `outputs/publishing-guide.md`

---

## Step 11: Cost Report

Orchestrator generates a final cost report from `state.yaml.api_cost`:

| Phase | Cost |
|-------|------|
| Interview | `by_phase.interview` |
| Story Bible | `by_phase.story_bible` |
| Calibration | `by_phase.calibration` |
| Drafting | `by_phase.drafting` |
| Review | `by_phase.review` |
| **Total** | `total_spent` |

### Output
- `outputs/cost-report.md`

---

## Quality Gates

| Check | Script | When |
|-------|--------|------|
| Chapter deterministic (CH1-CH10) | `validate_chapter.py` + `quality_gate_check.py` | After 7b, before 7e |
| Cross-chapter consistency (CC1-CC8) | `validate_consistency.py` | After Step 8 |
| Build artifact integrity | `build_book.py --validate` | After Step 9 |

## Failure Handling

| Failure | Fallback |
|---------|----------|
| `@chapter-writer` fails | Retry (Tier 2); Orchestrator writes minimal draft (Tier 3) |
| Python gate loops (3 fails) | Escalate to human with diagnostic |
| `@autobiography-reviewer` unavailable | Quality gate only (reduced review); flag for human |
| Build fails (missing pandoc) | Produce markdown-only manuscript |
| Export fails (XeLaTeX error) | EPUB-only output; log error for human |
