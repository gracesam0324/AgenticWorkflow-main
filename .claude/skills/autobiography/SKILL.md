---
name: autobiography
description: "AI autobiography generation — transforms life stories into publication-ready books through AI-guided interviews, narrative architecture, multi-agent writing, adversarial review, and automated PDF/EPUB publishing."
---

# Autobiography Generator — Executable Orchestration

## When to Use

Activate when the user requests:
- "Write my autobiography", "Help me write a memoir"
- "Turn my life story into a book", "Create a biography"
- Any request to generate a book from interviews or life stories

---

## Entry Protocol — EXECUTE THESE STEPS IN ORDER

When this skill is invoked, you ARE the Orchestrator. Follow these steps exactly:

### Step 1: Read SOT and determine current state

```
Read the file .claude/state.yaml
```

Extract these values:
- `workflow.current_step` — which step we are on
- `workflow.status` — not_started / in_progress / completed / failed
- `orchestration.current_phase` — build / research / planning / implementation
- `orchestration.current_substep` — for chapter loop resume (7a/7b/7c/7d/7e/7f)

### Step 2: Route to the correct phase

Based on the state read above:

**If `workflow.status` == "not_started"**:
→ Begin at Step 0. Set `workflow.status` to "in_progress" in state.yaml.

**If `workflow.status` == "completed"**:
→ Display completion message with cost summary from `workflow.api_cost`. Stop.

**If `workflow.status` == "in_progress"**:
→ Resume from `workflow.current_step`. Read the phase reference file for details:
  - Steps 0 to 0.7 → Read `references/build-phase.md`, execute Build Phase
  - Steps 1 to 3.5 → Read `references/research-phase.md`, execute Research Phase
  - Steps 4 to 6.5 → Read `references/planning-phase.md`, execute Planning Phase
  - Steps 7 to 11 → Read `references/implementation-phase.md`, execute Implementation Phase

### Step 3: Execute the current step

For EVERY step, follow this universal execution pattern:

```
1. SPAWN the designated agent (see Agent Table below) with a detailed prompt
   - Include file paths to read (Story Bible, interviews, previous chapters)
   - Include the specific step requirements from workflow.md
   - Include quality criteria the output must meet

2. VERIFY output with Python quality gate:
   .venv/bin/python3 scripts/quality_gate_check.py --step {step_id} [--chapter {N}]

3. If gate FAILS:
   - Import and use the FallbackController:
     .venv/bin/python3 -c "
     from scripts.fallback_controller import FallbackController
     fc = FallbackController()
     action = fc.handle_failure('{step_id}', '{agent_name}', '{error_message}')
     print(f'Tier: {action.tier}, Action: {action.action}')
     print(f'Feedback: {action.feedback}')
     "
   - Follow the FallbackAction: retry with feedback, degrade tier, or escalate to human

4. If gate PASSES:
   - For English-First outputs: spawn @translator for .ko.md pair
   - Update state.yaml: set current_step to next step, update outputs
   - Git checkpoint if appropriate

5. If this step has a Human Checkpoint (H1-H7):
   - Ensure any BLOCKING translations are complete
   - Present the guided questions to the user (in Korean)
   - Wait for user response
   - Route based on choice: Approve → advance, Revise → loop back
```

---

## Agent Table — Who to Spawn for Each Step

| Step(s) | Agent | subagent_type | Key Context to Include in Prompt |
|---------|-------|---------------|----------------------------------|
| 0-0.7 | (Orchestrator direct) | — | Environment setup, no agent needed |
| 1 | (Orchestrator direct) | — | Initialize interview directory |
| 2.x | @interviewer | `interviewer` | Life stage questions, session state, previous session summary |
| 3 | (Orchestrator runs script) | — | `scripts/assess_material.py --interviews-dir interviews/` |
| 3.5 | Human Checkpoint H1 | — | Present material assessment (Korean translation) |
| 4 | @story-architect | `story-architect` | Filtered transcripts, interview summaries |
| 4.5 | Human Checkpoint H2 | — | Present Story Bible (Korean translation) |
| 5a | @chapter-writer | `chapter-writer` | Voice calibration mode, golden exemplars |
| 5b | @chapter-writer | `chapter-writer` | Selected voice register, literary mode |
| 5.5 | Human Checkpoint H3 | — | Present voice samples |
| 6 | @story-architect | `story-architect` | Story Bible, voice profile, macro-structure |
| 6.5 | Human Checkpoint H4 | — | Present outline (Korean translation) |
| 7a | (Orchestrator runs script) | — | `scripts/assemble_chapter_context.py --chapter {N}` |
| 7b | @chapter-writer | `chapter-writer` | Chapter context package (from 7a output) |
| 7c | (Orchestrator runs script) | — | `quality_gate_check.py --step 7c --chapter {N}` |
| 7d | @autobiography-reviewer | `autobiography-reviewer` | Chapter + analytical companion + Story Bible |
| 7e | Human Checkpoint H5 | — | Present chapter (Korean-native prose) |
| 7f | (Orchestrator runs script) | — | `scripts/check_voice.py --compare` (every 3 chapters) |
| 8 | @autobiography-reviewer + @reviewer-deep | `reviewer`, `reviewer-deep` | Full manuscript, consistency ledger |
| 8.5 | Human Checkpoint H6 | — | Present continuity report (Korean translation) |
| 9 | (Orchestrator runs script) | — | `scripts/build_book.py` |
| 9.5 | Human Checkpoint H7 | — | Present PDF/EPUB |
| 10 | (Orchestrator direct) | — | Generate PUBLISHING.md |
| 11 | (Orchestrator direct) | — | Cost report from state.yaml.api_cost |

---

## Chapter Writing Loop — Steps 7a through 7f (SEQUENTIAL per chapter)

For each chapter N from 1 to total_chapters:

```
1. CONTEXT ASSEMBLY (7a):
   Run: .venv/bin/python3 scripts/assemble_chapter_context.py --chapter {N}
   Output: temp/chapter-{NN}-context.md

2. CHAPTER DRAFTING (7b):
   Spawn @chapter-writer with prompt:
   - "Write chapter {N} for the autobiography."
   - "REASONING LANGUAGE: English. OUTPUT LANGUAGE: Korean-native."
   - "Context file: temp/chapter-{NN}-context.md"
   - "Apply all Appendix A directives. Apply 4-layer Self-Refine."
   - "OUTPUT 1: outputs/chapters/ch{NN}_draft_v{V}.md"
   - "OUTPUT 2: quality/chapter-{NN}-analysis-en.md"
   Update state.yaml: chapters.ch-{N}.substep = "7b", status = "drafted"

3. PYTHON QUALITY GATE (7c):
   Run: .venv/bin/python3 scripts/quality_gate_check.py --step 7c --chapter {N}
   If FAILS: retry 7b with gate feedback (max 3 retries, ch1: 5)
   If PASSES: proceed to 7d

4. REVIEWER EVALUATION (7d):
   Spawn @autobiography-reviewer with prompt:
   - "Evaluate chapter {N} on 7 dimensions."
   - "Read quality/chapter-{NN}-analysis-en.md first."
   - "Read outputs/chapters/ch{NN}_draft_v{V}.md for Korean prose."
   - "Verdict: APPROVE or REVISE with specific feedback."
   - "Output: quality/chapter-{NN}-review.md"
   If REVISE: return to 7b with reviewer feedback (max 3 rounds, ch1: 5)
   If APPROVE: proceed to 7e

5. HUMAN APPROVAL (7e):
   Present chapter to user (Korean-native prose, no translation needed).
   If Approve: mark chapter as approved in state.yaml
   If Revise: return to 7b

6. VOICE DRIFT CHECK (7f — every 3 chapters):
   Run: .venv/bin/python3 scripts/check_voice.py --compare --chapters 1-{N}
   If voice_score < 0.60: return to Step 5a for voice re-profiling
```

---

## Human Checkpoint Protocol (H1-H7)

| ID | Step | What to Present | Options |
|----|------|-----------------|---------|
| H1 | 3.5 | Material assessment (Korean) | Approve / Supplement (→ more interviews) / Proceed with gaps |
| H2 | 4.5 | Story Bible (Korean translation) | Approve / Revise |
| H3 | 5.5 | Voice calibration samples | Select voice register A/B/C, literary mode X/Y |
| H4 | 6.5 | Chapter outline (Korean translation) | Approve / Modify |
| H5 | 7e | Chapter prose (Korean-native) | Approve / Minor revision / Major revision / Voice recalibration |
| H6 | 8.5 | Continuity report (Korean translation) | Approve / Fix specific issues |
| H7 | 9.5 | PDF/EPUB manuscript | Approve for publication / Request changes |

For each checkpoint:
1. Ensure BLOCKING translations are complete (H1, H2, H4, H6 need Korean)
2. Present guided questions to user in Korean
3. Use AskUserQuestion to wait for response
4. Route based on choice, update state.yaml

---

## Fallback Protocol

When any agent fails or quality gate fails repeatedly:

```
1. Try retry with feedback (same tier, max 3 attempts)
2. If still failing: degrade tier
   - Tier 1 (Agent Team) → Tier 2 (Sequential Subagent)
   - Tier 2 (Subagent) → Tier 3 (Orchestrator direct execution)
   - Tier 3 (Direct) → Tier 4 (Human escalation with diagnostic)
3. Log all fallback events in state.yaml.orchestration.fallback
```

Use FallbackController for automated tier management:
```bash
.venv/bin/python3 -c "
from scripts.fallback_controller import FallbackController
fc = FallbackController()
action = fc.handle_failure('STEP', 'AGENT', 'ERROR')
print(action.tier, action.action, action.feedback)
"
```

---

## SOT Update Protocol

After every step completion, update state.yaml atomically:

```bash
.venv/bin/python3 -c "
from scripts.sot_lib import update_state_yaml
update_state_yaml('workflow', current_step=NEXT_STEP)
update_state_yaml('orchestration', current_phase='PHASE', current_substep=None)
"
```

---

## Quality Gate Integration

Quality enforcement is Orchestrator-explicit — call gates directly after every agent output:

```bash
.venv/bin/python3 scripts/quality_gate_check.py --step {step_id} [--chapter {N}]
```

| Layer | Name | Mechanism |
|-------|------|-----------|
| L0 | Anti-Skip Guard | Schema hooks prevent invalid writes |
| L1 | Verification Gate | Python deterministic checks (quality_gate_check.py) |
| L1.5 | pACS Self-Rating | Agent self-assessment |
| L2 | Calibration | @autobiography-reviewer adversarial evaluation |

---

## English-First Execution

| Context | Language |
|---------|----------|
| Agent prompts and reasoning | English |
| Chapter prose output | **Korean-Native** (not translated) |
| Interview transcripts | Korean |
| Human checkpoint displays | Korean |
| SOT, logs, metadata | English |

After English-First outputs: spawn @translator for .ko.md pair.
Translation pACS >= 70 required for human checkpoints (BLOCKING).

---

## Reference Files

| File | When to Read |
|------|-------------|
| `references/build-phase.md` | Steps 0-0.7: Build phase details |
| `references/research-phase.md` | Steps 1-3.5: Interview protocol |
| `references/planning-phase.md` | Steps 4-6.5: Story Bible, calibration, outline |
| `references/implementation-phase.md` | Steps 7-11: Chapter loop, export |
| `references/fallback-paths.md` | When agent fails or quality gate fails |
| `references/quality-gates.md` | Quality gate specifications |

## Commands

| Command | Purpose |
|---------|---------|
| `/interview` | Start or resume an interview session |
| `/review-chapter` | Manually trigger review for a specific chapter |
| `/build-verify` | Run full build verification |
| `/export` | Trigger manuscript export (PDF + EPUB) |
| `/status` | Display pipeline dashboard |
| `/fallback` | Manually trigger fallback for stuck step |
