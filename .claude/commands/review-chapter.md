---
description: "Manually trigger review for chapter N"
---

# /review-chapter — Manually Trigger Chapter Review

Manually trigger the full review pipeline for a specific chapter.

## Usage

```
/review-chapter {chapter_number}
```

Example: `/review-chapter 3` — reviews chapter 3.

## Execute These Steps

### Step 1: Parse Arguments

Extract the chapter number from the command arguments.

- **If no argument provided**: Ask the user: "Which chapter number should I review? (1-based integer)"
- **If argument provided**: Store as `N` (integer).

### Step 2: Read Pipeline State

Use the **Read tool** on `.claude/state.yaml`.

Extract:
- `workflow.chapters.ch-{N}.status` — current chapter status
- `workflow.chapters.ch-{N}.draft_version` — current draft version `V`
- `workflow.chapters.ch-{N}.review_count` — number of reviews so far

### Step 3: Validate Chapter Exists

Use the **Glob tool** to check for these files:
- `outputs/chapters/ch{NN}_draft_v{V}.md` (where NN is zero-padded chapter number)
- `outputs/chapters/ch{NN}_draft_v{V}.meta.json`

- **If either file is missing**: Report to user: "Chapter {N} draft v{V} not found. The chapter must be drafted before review. Expected files: `outputs/chapters/ch{NN}_draft_v{V}.md` and `.meta.json`." **STOP here.**
- **If both exist**: Continue.

### Step 4: Run Python Quality Gate (L1)

Use the **Bash tool** to run the L1 automated quality gate:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/quality_gate_check.py --step 7c --chapter {N}
```

- **If L1 FAILS**:
  1. Display the full diagnostic output to the user.
  2. List which specific checks failed.
  3. Suggest fixes for each failure.
  4. Report: "L1 quality gate failed. The chapter must pass L1 before L2 (reviewer) can run. Fix the issues above and re-run `/review-chapter {N}`."
  5. **STOP here — do NOT spawn @reviewer.**

- **If L1 PASSES**: Continue to Step 5.

### Step 5: Spawn @reviewer (L2)

Use the **Skill tool** or **SendMessage tool** to spawn the `@reviewer` subagent with:
- Chapter file path: `outputs/chapters/ch{NN}_draft_v{V}.md`
- Chapter metadata path: `outputs/chapters/ch{NN}_draft_v{V}.meta.json`
- Story Bible reference: `outputs/story-bible/story_bible.json`
- Source interviews for this chapter (use Glob tool on `outputs/interviews/INT-*.json` and filter by chapter mapping in story bible)
- Previous review feedback if this is a revision cycle (check `outputs/reviews/ch{NN}_review_*.json`)

Wait for @reviewer to complete and return a verdict.

### Step 6: Process Verdict and Update SOT

Use the **Edit tool** on `.claude/state.yaml` based on the verdict:

- **If APPROVE**:
  ```yaml
  workflow:
    chapters:
      ch-{N}:
        status: "approved"
        review_count: {R}
  ```

- **If REVISE**:
  1. Check revision count: current `review_count` vs limit (3 for most chapters, 5 for ch-1).
  2. If at or above limit: Report "Maximum revision limit reached for chapter {N}. Escalating to human review." Update status to `"human_review_required"`. **STOP.**
  3. Otherwise, update:
  ```yaml
  workflow:
    chapters:
      ch-{N}:
        status: "revision"
        review_count: {R+1}
  ```

### Step 7: Display Review Report

Output the following directly to the user:

```
Chapter {N} Review Results
==========================
L1 (Python Gate): PASS
L2 (Reviewer):    {APPROVE | REVISE}

Dimension Scores:
  Emotional Resonance (20%): {score}
  Voice Consistency (20%):   {score}
  Prose Quality (15%):       {score}
  Factual Accuracy (15%):    {score}
  Narrative Arc (15%):       {score}
  Source Traceability (10%): {score}
  Continuity (5%):           {score}
  ────────────────────────
  Weighted Total:            {total}

Review Round: {R} / {max}
Verdict:      {APPROVE | REVISE}
{if REVISE: "Feedback: {specific revision feedback from @reviewer}"}
{if REVISE: "Next: Fix issues and re-run /review-chapter {N}"}
{if APPROVE: "Next: Proceed to next chapter or /export if all approved"}
```

## Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| chapter_number | Yes | The chapter number to review (1-based integer) |

## Error Handling

| Error | Tool to Use | Action |
|-------|-------------|--------|
| Chapter not yet drafted | Glob tool | Report missing files, suggest writing the chapter first |
| L1 fails | Bash tool output | Display full diagnostic, do NOT invoke @reviewer |
| @reviewer fails | SendMessage retry | Retry once; if still fails, display L1 results only with note "L2 unavailable" |
| Max revisions reached | Edit tool on state.yaml | Set status to `human_review_required`, escalate to human |
| state.yaml missing | Read tool on backup | Restore from `.claude/state.yaml.bak` |

## Constraints

- L1 MUST pass before L2 runs — never skip L1
- Review dimension scores come from @reviewer, not from L1
- Revision limits: 3 general, 5 for chapter 1 (calibration chapter)
- This command writes to state.yaml ONLY after the review completes (never mid-review)
