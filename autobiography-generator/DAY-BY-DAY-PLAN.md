# Day-by-Day Coding Plan: AI Autobiography Generator

5 days from zero to working autobiography. Every step is a command you type.

---

## Day 1: Scaffold + First Agent Output (4-6 hours)

### Hour 1: Project Setup

```bash
# Step 1: Run the scaffold
cd autobiography-generator
bash scripts/setup.sh

# Step 2: Install dependencies
pip install textstat pyyaml
npm install -g promptfoo

# Step 3: Install prompt versioning hook
cd ..
ln -sf ../../autobiography-generator/.git-hooks/pre-commit-prompt-version .git/hooks/pre-commit
cd autobiography-generator

# Step 4: Verify everything exists
ls -la agents/prompts/
cat state.yaml
python3 scripts/check.py test-data/golden-outputs/chapter-1-golden.md
```

Expected: check.py runs against the golden output, shows all passes.

### Hour 2: First chapter-writer run

```bash
# Step 5: Run the dev loop for the first time
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json

# Step 6: Check the output quality
python3 scripts/check.py outputs/drafts/chapter-writer-*.md \
  --source test-data/micro-interviews/INT-001-childhood.json

# Step 7: Read the output manually — this is critical
# Open the output file and read it word by word.
# Ask yourself: Does this sound like Park Jimin? Or does it sound like ChatGPT?
```

### Hour 3: First prompt iteration

```bash
# Step 8: Edit the chapter-writer prompt based on what you read
#   Common first-iteration fixes:
#   - Add "Do NOT use passive voice" if output is too formal
#   - Add "Start with a specific sensory detail, not a summary" if opening is weak
#   - Increase example quotes if the voice is too generic
$EDITOR agents/prompts/chapter-writer.md

# Step 9: Re-run and compare
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json --compare

# Step 10: Compare against the golden output
python3 scripts/compare.py test-data/golden-outputs/chapter-1-golden.md outputs/drafts/chapter-writer-*.md --no-llm
```

### Hour 4: Voice profiler agent

```bash
# Step 11: Run the voice profiler to generate a data-driven voice profile
bash scripts/dev.sh voice-profiler test-data/micro-interviews/INT-001-childhood.json

# Step 12: Review the generated voice profile
# Copy the good parts into agents/voice-profile.yaml
cat outputs/drafts/voice-profiler-*.md

# Step 13: Re-run chapter-writer with the improved voice profile
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json --compare
```

### Hour 5-6: Iterate until word count + voice pass

```bash
# The iteration loop:
# 1. Edit prompt
$EDITOR agents/prompts/chapter-writer.md
# 2. Run
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json --compare
# 3. Check
python3 scripts/check.py outputs/drafts/chapter-writer-$(ls -t outputs/drafts/chapter-writer-*.md | head -1 | xargs basename)
# 4. Compare against golden
python3 scripts/compare.py test-data/golden-outputs/chapter-1-golden.md $(ls -t outputs/drafts/chapter-writer-*.md | head -1) --no-llm
# 5. Repeat until satisfied

# End of Day 1: Commit your prompt versions
cd ..
git add autobiography-generator/agents/prompts/ autobiography-generator/agents/voice-profile.yaml
git add autobiography-generator/test-data/ autobiography-generator/scripts/
git commit -m "day 1: chapter-writer v1, voice profile, test data"
cd autobiography-generator
```

**Day 1 Exit Criteria:**
- [ ] chapter-writer produces 3500-5000 words
- [ ] Output starts with a scene, not exposition
- [ ] At least 2 of 3 key quotes appear in the output
- [ ] Voice profile exists and is being used
- [ ] check.py passes on the output

---

## Day 2: Evaluation Pipeline + Second Agent (4-6 hours)

### Hour 1: promptfoo setup

```bash
# Step 1: Run the full eval suite
cd eval/promptfoo
promptfoo eval

# Step 2: View the HTML report
promptfoo view
# Opens browser — examine each test case result

# Step 3: Note which tests fail
# Common failures on first run:
#   - voice_drift_guard: output sounds too generic
#   - no_hallucination: agent invented details not in source
#   - word_count_restrained: agent writes too much from minimal source
```

### Hour 2: Fix failing eval cases

```bash
# Step 4: Edit the prompt to fix failures
cd ../../
$EDITOR agents/prompts/chapter-writer.md

# Common fixes:
# - For hallucination: Add "NEVER invent quotes, names, or events not in the source"
# - For word count: Add "If source material is sparse, write a shorter chapter (1000-3000 words)"
# - For voice drift: Add 3-5 specific example phrases from the voice profile

# Step 5: Re-run eval
cd eval/promptfoo
promptfoo eval
promptfoo view

# Step 6: Iterate until 4/5 tests pass
```

### Hour 3: Chapter reviewer agent

```bash
cd ../../

# Step 7: Generate a chapter for the reviewer to review
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json

# Step 8: Run the reviewer against the chapter output
LATEST=$(ls -t outputs/drafts/chapter-writer-*.md | head -1)
bash scripts/dev.sh chapter-reviewer "$LATEST"

# Step 9: Read the review output
cat outputs/drafts/chapter-reviewer-*.md

# Step 10: Does the reviewer catch real issues?
# If the reviewer is too lenient:
$EDITOR agents/prompts/chapter-reviewer.md
# Add: "Be adversarial. Score harshly. A 7/10 means 'publishable with minor edits'."
# Add: "Flag ANY sentence that could not be traced to a specific transcript segment."
```

### Hour 4: Interviewer agent (synthetic data generation)

```bash
# Step 11: Create a subject profile for generating new interviews
cat > test-data/subject-profile.yaml << 'EOF'
subject_name: "Park Jimin"
birth_year: 1990
current_age: 36
nationality: "South Korean"
current_city: "Seoul"
occupation: "Novelist"
background: |
  Born in Busan. Father ran a fishing supply shop.
  Mother was a piano teacher. Older brother Jihoon.
  Studied creative writing at Yonsei University.
  Published two novels. Currently working on third.
life_periods_to_cover:
  - label: "Childhood in Busan"
    years: "1990-2002"
    status: "interviewed"
  - label: "High school"
    years: "2003-2007"
    status: "needs-interview"
  - label: "University in Seoul"
    years: "2008-2012"
    status: "interviewed"
  - label: "First job and first novel"
    years: "2013-2017"
    status: "needs-interview"
  - label: "The quiet years"
    years: "2018-2020"
    status: "needs-interview"
  - label: "Breakthrough and recognition"
    years: "2021-2026"
    status: "needs-interview"
EOF

# Step 12: Generate a new interview transcript
bash scripts/dev.sh interviewer test-data/subject-profile.yaml

# Step 13: Validate the generated interview against the schema
python3 -c "
import json, sys
with open('schemas/interview_transcript.schema.json') as f:
    schema = json.load(f)
latest = sorted([f for f in __import__('os').listdir('outputs/drafts') if f.startswith('interviewer-')])[-1]
with open(f'outputs/drafts/{latest}') as f:
    content = f.read()
# Try to find JSON in the output
import re
match = re.search(r'\{[\s\S]*\}', content)
if match:
    data = json.loads(match.group())
    print(f'Valid JSON with {len(data.get(\"segments\", []))} segments')
    print(f'Subject: {data.get(\"meta\", {}).get(\"subject_name\", \"unknown\")}')
else:
    print('ERROR: No JSON found in output')
    sys.exit(1)
"
```

### Hour 5-6: Wire up the review loop

```bash
# Step 14: Create a mini-pipeline script
cat > scripts/pipeline-one-chapter.sh << 'PIPE'
#!/usr/bin/env bash
# Pipeline: Generate one chapter, review it, run quality checks
set -euo pipefail

INTERVIEW_FILE="${1:?Usage: pipeline-one-chapter.sh <interview-file>}"
CHAPTER_NUM="${2:-1}"

echo "=== Pipeline: Chapter ${CHAPTER_NUM} ==="

# Generate chapter
echo "[1/3] Generating chapter..."
bash scripts/dev.sh chapter-writer "$INTERVIEW_FILE"
CHAPTER=$(ls -t outputs/drafts/chapter-writer-*.md | head -1)
echo "  -> ${CHAPTER}"

# Review chapter
echo "[2/3] Reviewing chapter..."
bash scripts/dev.sh chapter-reviewer "$CHAPTER"
REVIEW=$(ls -t outputs/drafts/chapter-reviewer-*.md | head -1)
echo "  -> ${REVIEW}"

# Quality check
echo "[3/3] Quality check..."
python3 scripts/check.py "$CHAPTER" --source "$INTERVIEW_FILE"

echo ""
echo "=== Pipeline Complete ==="
echo "Chapter: $CHAPTER"
echo "Review:  $REVIEW"
PIPE
chmod +x scripts/pipeline-one-chapter.sh

# Step 15: Test the pipeline
bash scripts/pipeline-one-chapter.sh test-data/micro-interviews/INT-001-childhood.json

# End of Day 2: Commit
cd ..
git add autobiography-generator/
git commit -m "day 2: eval pipeline, reviewer agent, interview generator, mini-pipeline"
cd autobiography-generator
```

**Day 2 Exit Criteria:**
- [ ] promptfoo runs 5 test cases, at least 4 pass
- [ ] chapter-reviewer produces actionable feedback
- [ ] interviewer generates schema-valid transcripts
- [ ] pipeline-one-chapter.sh runs end-to-end
- [ ] Prompt versions are tracked in git

---

## Day 3: Full Pipeline + Multi-Chapter (4-6 hours)

### Hour 1-2: Generate remaining interviews

```bash
# Step 1: Generate interviews for uncovered life periods
# Edit the interviewer prompt for each period
for period in "high-school" "first-job" "quiet-years" "breakthrough"; do
    echo "Generating interview for: $period"
    # Create period-specific input
    cat > /tmp/interview-request.yaml << PERIOD_EOF
subject_name: "Park Jimin"
target_period: "$period"
previous_sessions:
  - INT-001: "Childhood in Busan — family, school, father's shop"
  - INT-002: "University in Seoul — culture shock, major change"
PERIOD_EOF

    bash scripts/dev.sh interviewer /tmp/interview-request.yaml

    # Save to test-data with proper naming
    LATEST=$(ls -t outputs/drafts/interviewer-*.md | head -1)
    # Extract JSON and save
    python3 -c "
import re, json
with open('$LATEST') as f:
    content = f.read()
match = re.search(r'\{[\s\S]*\}', content)
if match:
    data = json.loads(match.group())
    sid = data.get('meta', {}).get('session_id', 'INT-XXX')
    with open(f'test-data/micro-interviews/{sid}-${period}.json', 'w') as out:
        json.dump(data, out, indent=2)
    print(f'Saved: test-data/micro-interviews/{sid}-${period}.json')
"
done

# Step 2: Verify all interviews
ls -la test-data/micro-interviews/
```

### Hour 3-4: Generate all chapters

```bash
# Step 3: Create the full chapter generation script
cat > scripts/generate-all-chapters.sh << 'ALLCHAP'
#!/usr/bin/env bash
set -euo pipefail

echo "=== Generating All Chapters ==="

INTERVIEWS=(test-data/micro-interviews/INT-*.json)
CHAPTER_NUM=1

for interview in "${INTERVIEWS[@]}"; do
    if [ ! -f "$interview" ]; then continue; fi

    echo ""
    echo "--- Chapter ${CHAPTER_NUM}: $(basename "$interview") ---"

    # Get previous chapter ending for continuity
    PREV_ENDING=""
    if [ $CHAPTER_NUM -gt 1 ]; then
        PREV_CHAPTER=$(ls -t outputs/chapters/chapter-$(printf "%02d" $((CHAPTER_NUM-1)))-*.md 2>/dev/null | head -1)
        if [ -n "$PREV_CHAPTER" ]; then
            PREV_ENDING=$(tail -5 "$PREV_CHAPTER")
        fi
    fi

    # Generate
    bash scripts/dev.sh chapter-writer "$interview"
    LATEST=$(ls -t outputs/drafts/chapter-writer-*.md | head -1)

    # Save to chapters directory with proper naming
    cp "$LATEST" "outputs/chapters/chapter-$(printf "%02d" $CHAPTER_NUM)-draft.md"

    # Quality check
    python3 scripts/check.py "$LATEST" --source "$interview" 2>&1 | tail -5

    CHAPTER_NUM=$((CHAPTER_NUM + 1))
done

echo ""
echo "=== All Chapters Generated ==="
echo "Total: $((CHAPTER_NUM - 1)) chapters"

# Cross-chapter quality check
echo ""
echo "=== Cross-Chapter Quality Check ==="
python3 scripts/check.py outputs/chapters/
ALLCHAP
chmod +x scripts/generate-all-chapters.sh

# Step 4: Run it
bash scripts/generate-all-chapters.sh
```

### Hour 5-6: Cross-chapter consistency check

```bash
# Step 5: Run the full quality suite across all chapters
python3 scripts/check.py outputs/chapters/ --source test-data/micro-interviews/INT-001-childhood.json

# Step 6: Check name consistency manually
python3 -c "
import os, re
from collections import Counter

names = Counter()
for f in sorted(os.listdir('outputs/chapters')):
    if not f.endswith('.md'): continue
    with open(f'outputs/chapters/{f}') as fh:
        text = fh.read()
    # Find all capitalized name-like tokens
    found = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
    for name in found:
        names[name] += 1

print('=== Name Frequency Across All Chapters ===')
for name, count in names.most_common(30):
    print(f'  {count:3d}x  {name}')
"

# Step 7: Compare chapter 1 draft vs golden
python3 scripts/compare.py \
    test-data/golden-outputs/chapter-1-golden.md \
    outputs/chapters/chapter-01-draft.md \
    --source test-data/micro-interviews/INT-001-childhood.json \
    --output outputs/comparisons/ch01-vs-golden.md

# End of Day 3: Commit
cd ..
git add autobiography-generator/
git commit -m "day 3: full pipeline, all chapters generated, cross-chapter checks"
cd autobiography-generator
```

**Day 3 Exit Criteria:**
- [ ] 4+ interview transcripts generated
- [ ] 4+ chapter drafts generated
- [ ] Cross-chapter name consistency check passes
- [ ] Timeline chronology check passes across chapters
- [ ] At least one LLM-as-judge comparison completed

---

## Day 4: Revision Cycle + Quality Hardening (4-6 hours)

### Hour 1-2: Targeted revision based on review feedback

```bash
# Step 1: Run the reviewer on each chapter, collect all issues
for chapter in outputs/chapters/chapter-*-draft.md; do
    echo "=== Reviewing: $(basename "$chapter") ==="
    bash scripts/dev.sh chapter-reviewer "$chapter"
done

# Step 2: Create a revision prompt that takes review + original + transcript
cat > agents/prompts/chapter-reviser.md << 'REVISE'
---
name: chapter-reviser
version: 1.0.0
temperature: 0.6
max_tokens: 8000
---

# Role
You are a literary editor revising an autobiography chapter based on review feedback.

# Instructions
Given the original chapter, the review notes, and source transcripts, produce a revised chapter.

## Input Variables
- `{{original_chapter}}`: The chapter text to revise
- `{{review_feedback}}`: The structured review with scores and specific issues
- `{{source_transcripts}}`: Original interview transcripts
- `{{voice_profile}}`: The voice profile to maintain

## Rules
1. Address every item in the review's `must_fix` list
2. Attempt to address `nice_to_have` items without sacrificing quality
3. Do NOT change parts that scored 8+ unless they conflict with fixes
4. Maintain the same voice throughout — do not "fix" the voice out of the text
5. If the review says a quote is ungrounded, REMOVE it — do not try to rephrase
6. Keep the chapter within 3500-5000 words
7. Preserve the scene opening and chapter-ending hook

Output the complete revised chapter in markdown.
REVISE

# Step 3: Run revision on chapter 1
CHAPTER_1=$(ls outputs/chapters/chapter-01-draft.md)
REVIEW_1=$(ls -t outputs/drafts/chapter-reviewer-*.md | head -1)

# Combine chapter + review into a single input for the reviser
cat > /tmp/revision-input.md << REVINPUT
# Original Chapter
$(cat "$CHAPTER_1")

---

# Review Feedback
$(cat "$REVIEW_1")
REVINPUT

bash scripts/dev.sh chapter-reviser /tmp/revision-input.md

# Step 4: Compare original vs revised
REVISED=$(ls -t outputs/drafts/chapter-reviser-*.md | head -1)
python3 scripts/compare.py "$CHAPTER_1" "$REVISED" \
    --source test-data/micro-interviews/INT-001-childhood.json \
    --output outputs/comparisons/ch01-revision-report.md
```

### Hour 3-4: promptfoo regression sweep

```bash
# Step 5: Run the full eval with the revised prompt
cd eval/promptfoo
promptfoo eval
promptfoo view

# Step 6: Save the eval results for tracking
cp output/eval-results.json "output/eval-results-day4-$(date +%H%M).json"

# Step 7: If any test regressed, investigate
# Common regressions:
#   - Fixing hallucination makes voice too cautious
#   - Fixing word count breaks narrative flow
# Solution: add explicit carve-outs in the prompt

cd ../../
```

### Hour 5-6: Automated revision loop

```bash
# Step 8: Create the full revision pipeline
cat > scripts/revise-all-chapters.sh << 'REVALL'
#!/usr/bin/env bash
set -euo pipefail

echo "=== Revision Pipeline ==="

for chapter in outputs/chapters/chapter-*-draft.md; do
    CHNUM=$(echo "$chapter" | grep -oP '\d+')
    echo ""
    echo "--- Revising Chapter ${CHNUM} ---"

    # Find corresponding interview
    INTERVIEW=$(ls test-data/micro-interviews/INT-*.json | sed -n "${CHNUM}p" 2>/dev/null || echo "")

    # Review
    bash scripts/dev.sh chapter-reviewer "$chapter"
    REVIEW=$(ls -t outputs/drafts/chapter-reviewer-*.md | head -1)

    # Combine for revision
    cat > /tmp/revision-input.md << REVIN
# Original Chapter
$(cat "$chapter")

---

# Review Feedback
$(cat "$REVIEW")
REVIN

    # Revise
    bash scripts/dev.sh chapter-reviser /tmp/revision-input.md

    REVISED=$(ls -t outputs/drafts/chapter-reviser-*.md | head -1)

    # Save revised version
    cp "$REVISED" "outputs/chapters/chapter-${CHNUM}-revised.md"

    # Quality check on revised
    python3 scripts/check.py "outputs/chapters/chapter-${CHNUM}-revised.md" \
        ${INTERVIEW:+--source "$INTERVIEW"} 2>&1 | grep -E '\[PASS\]|\[FAIL\]'

    echo "  Saved: outputs/chapters/chapter-${CHNUM}-revised.md"
done

echo ""
echo "=== Final Cross-Chapter Check ==="
python3 scripts/check.py outputs/chapters/ --json > outputs/eval-reports/revision-quality.json
python3 scripts/check.py outputs/chapters/
REVALL
chmod +x scripts/revise-all-chapters.sh

# Step 9: Run it
bash scripts/revise-all-chapters.sh

# End of Day 4: Commit
cd ..
git add autobiography-generator/
git commit -m "day 4: revision pipeline, chapter-reviser agent, quality hardening"
cd autobiography-generator
```

**Day 4 Exit Criteria:**
- [ ] chapter-reviser agent produces measurably better chapters
- [ ] LLM-as-judge scores improve from draft to revision
- [ ] promptfoo regression sweep shows no new failures
- [ ] All revised chapters pass check.py
- [ ] Cross-chapter consistency maintained after revision

---

## Day 5: Assembly + Final Quality Gate (4-6 hours)

### Hour 1-2: Assemble the full book

```bash
# Step 1: Create the assembly script
cat > scripts/assemble-book.sh << 'ASSEMBLE'
#!/usr/bin/env bash
set -euo pipefail

OUTPUT="outputs/chapters/FULL-AUTOBIOGRAPHY.md"
echo "=== Assembling Full Autobiography ==="

# Use revised versions if available, otherwise drafts
cat > "$OUTPUT" << 'HEADER'
---
title: "Untitled Autobiography"
author: "Park Jimin"
generated: "2026-03-17"
chapters: 0
total_words: 0
---

HEADER

CHAPTER_COUNT=0
TOTAL_WORDS=0

for revised in outputs/chapters/chapter-*-revised.md; do
    if [ ! -f "$revised" ]; then
        # Fall back to draft
        CHNUM=$(echo "$revised" | grep -oP '\d+')
        draft="outputs/chapters/chapter-${CHNUM}-draft.md"
        if [ ! -f "$draft" ]; then continue; fi
        revised="$draft"
    fi

    echo "" >> "$OUTPUT"
    echo "---" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    cat "$revised" >> "$OUTPUT"

    WORDS=$(wc -w < "$revised" | tr -d ' ')
    TOTAL_WORDS=$((TOTAL_WORDS + WORDS))
    CHAPTER_COUNT=$((CHAPTER_COUNT + 1))

    echo "  Chapter ${CHAPTER_COUNT}: ${WORDS} words ($(basename "$revised"))"
done

# Update header
sed -i.bak "s/chapters: 0/chapters: ${CHAPTER_COUNT}/" "$OUTPUT"
sed -i.bak "s/total_words: 0/total_words: ${TOTAL_WORDS}/" "$OUTPUT"
rm -f "${OUTPUT}.bak"

echo ""
echo "=== Assembly Complete ==="
echo "File:     ${OUTPUT}"
echo "Chapters: ${CHAPTER_COUNT}"
echo "Words:    ${TOTAL_WORDS}"
echo ""

# Final quality check
python3 scripts/check.py "$OUTPUT"
ASSEMBLE
chmod +x scripts/assemble-book.sh

# Step 2: Assemble
bash scripts/assemble-book.sh
```

### Hour 3-4: Final quality gate

```bash
# Step 3: Full evaluation sweep
cd eval/promptfoo
promptfoo eval -o output/final-eval.json
promptfoo view

# Step 4: Final quality check on assembled book
cd ../../
python3 scripts/check.py outputs/chapters/FULL-AUTOBIOGRAPHY.md

# Step 5: Run compare on best chapter vs golden
python3 scripts/compare.py \
    test-data/golden-outputs/chapter-1-golden.md \
    outputs/chapters/chapter-01-revised.md \
    --source test-data/micro-interviews/INT-001-childhood.json \
    --output outputs/comparisons/final-vs-golden.md

# Step 6: Generate final quality report
python3 -c "
import os, json, glob

print('=== FINAL QUALITY REPORT ===')
print()

# Collect all metrics files
metrics_files = sorted(glob.glob('outputs/drafts/*.metrics.json'))
if metrics_files:
    print('Generation History:')
    for mf in metrics_files[-10:]:
        with open(mf) as f:
            m = json.load(f)
        print(f'  {m[\"timestamp\"]} | {m[\"agent\"]} v{m[\"prompt_version\"]} | '
              f'{m[\"metrics\"][\"word_count\"]} words | {m[\"generation_time_seconds\"]}s')

# Count files
chapters = glob.glob('outputs/chapters/chapter-*-revised.md')
drafts = glob.glob('outputs/chapters/chapter-*-draft.md')
interviews = glob.glob('test-data/micro-interviews/INT-*.json')

print()
print(f'Interviews:      {len(interviews)}')
print(f'Draft chapters:  {len(drafts)}')
print(f'Revised chapters:{len(chapters)}')

# Total word count
total = 0
for ch in chapters or drafts:
    with open(ch) as f:
        total += len(f.read().split())
print(f'Total words:     {total}')
print()
print('=== END REPORT ===')
"
```

### Hour 5-6: Update state.yaml and document

```bash
# Step 7: Update state.yaml with final status
python3 -c "
import yaml, glob, os
from datetime import date

state = yaml.safe_load(open('state.yaml'))

# Update state
interviews = glob.glob('test-data/micro-interviews/INT-*.json')
chapters = glob.glob('outputs/chapters/chapter-*-revised.md') or glob.glob('outputs/chapters/chapter-*-draft.md')

state['meta']['subject_name'] = 'Park Jimin'
state['meta']['project_start_date'] = '2026-03-17'
state['meta']['current_phase'] = 'revision'

state['interviews']['total_collected'] = len(interviews)
state['interviews']['sessions'] = [
    {'session_id': os.path.basename(f).split('-')[0] + '-' + os.path.basename(f).split('-')[1],
     'file': f, 'status': 'processed'}
    for f in sorted(interviews)
]

state['drafts']['current_round'] = 1
state['drafts']['chapters_drafted'] = len(glob.glob('outputs/chapters/chapter-*-draft.md'))
state['drafts']['chapters_revised'] = len(glob.glob('outputs/chapters/chapter-*-revised.md'))

state['structure']['chapters'] = [
    {'number': i+1, 'title': '', 'status': 'revised' if os.path.exists(f'outputs/chapters/chapter-{i+1:02d}-revised.md') else 'drafted'}
    for i in range(len(chapters))
]

state['quality']['last_eval_date'] = str(date.today())

with open('state.yaml', 'w') as f:
    yaml.dump(state, f, default_flow_style=False, allow_unicode=True)

print('state.yaml updated')
"

# Step 8: Final commit
cd ..
git add autobiography-generator/
git commit -m "day 5: assembled book, final quality gate, state updated"
cd autobiography-generator
```

**Day 5 Exit Criteria:**
- [ ] Full autobiography assembled in one file
- [ ] Final promptfoo eval: 5/5 test cases pass
- [ ] check.py passes on assembled book
- [ ] LLM-as-judge comparison shows improvement over golden baseline
- [ ] state.yaml reflects current project status
- [ ] All prompt versions tracked in git

---

## Quick Reference: Daily Commands

```bash
# The commands you'll type most often:

# Edit a prompt
$EDITOR agents/prompts/chapter-writer.md

# Test the prompt
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json

# Compare with previous
bash scripts/dev.sh chapter-writer test-data/micro-interviews/INT-001-childhood.json --compare

# Quality check
python3 scripts/check.py outputs/drafts/chapter-writer-LATEST.md --source test-data/micro-interviews/INT-001-childhood.json

# Full eval
cd eval/promptfoo && promptfoo eval && promptfoo view && cd ../../

# Compare two versions
python3 scripts/compare.py outputs/drafts/v1.md outputs/drafts/v2.md

# Generate + review + check (one command)
bash scripts/pipeline-one-chapter.sh test-data/micro-interviews/INT-001-childhood.json
```

## Prompt Iteration Checklist

When a chapter output is not good enough, check these in order:

1. **Voice wrong?** -> Edit voice-profile.yaml, add more sample phrases
2. **Too generic?** -> Add "Do NOT use passive voice" and specific anti-patterns
3. **Hallucinating?** -> Add "Every claim must trace to a transcript segment ID"
4. **Wrong length?** -> Adjust word count targets and add length-aware instructions
5. **Weak opening?** -> Add "First paragraph must be a specific scene with sensory detail"
6. **No quotes?** -> Add "Weave in at least 3 direct quotes from key_quotes"
7. **Timeline jumbled?** -> Add "Maintain chronological order within each chapter"
8. **Chapter disconnect?** -> Add previous_chapter_ending context and bridge instruction
