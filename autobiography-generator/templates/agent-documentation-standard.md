# Agent Documentation Standard

## Template: Agent `.md` File

Every agent file MUST include YAML frontmatter and structured body sections.
This is not optional. Missing frontmatter fields cause validation failures in CI.

---

## YAML Frontmatter Specification

```yaml
---
# REQUIRED FIELDS
name: chapter-writer                    # kebab-case, unique across all agents
version: 2.1.0                          # semver: MAJOR.MINOR.PATCH
purpose: >
  Generate narrative autobiography chapters from story bible entries
  and interview transcripts, maintaining consistent voice and tone.
model: opus                             # opus | sonnet | haiku
tools:                                  # list of allowed tool names
  - Read
  - Write
  - Edit
  - Glob
  - Grep
maxTurns: 30                            # hard limit on agent turns

# INPUT/OUTPUT CONTRACT
input_schema:
  required:
    - story_bible_path: string          # path to story-bible YAML
    - chapter_number: integer           # 1-indexed chapter number
    - interview_refs: list[string]      # list of INT-### session IDs
    - target_word_count: integer        # approximate word count target
  optional:
    - style_override: string            # path to custom style guide
    - previous_chapter_path: string     # for continuity checking

output_schema:
  produces:
    - chapter_draft: markdown           # outputs/chapters/chapter-{N}-draft-v{X}.md
    - chapter_metadata: yaml            # outputs/chapters/chapter-{N}-meta.yaml
  guarantees:
    - word_count_within: 15%            # +/- 15% of target
    - all_interview_refs_cited: true
    - story_bible_consistency: true

# OPERATIONAL CONSTRAINTS
known_limitations:
  - Cannot verify factual accuracy of interview content
  - May struggle with non-linear timelines spanning 3+ decades
  - Style consistency degrades if previous_chapter_path is not provided
  - Does not handle image/media placement

dependencies:
  agents:
    - story-bible-compiler              # must run before this agent
  files:
    - schemas/story_bible.schema.json
    - schemas/chapter_draft.schema.json

# CHANGE HISTORY
changelog:
  - version: 2.1.0
    date: 2026-03-15
    changes:
      - Added emotional_arc tracking across chapter sections
      - Fixed inconsistent character name handling for aliases
  - version: 2.0.0
    date: 2026-03-01
    changes:
      - BREAKING - Switched input from flat text to structured story bible
      - Added cross-reference validation against interview transcripts
  - version: 1.0.0
    date: 2026-02-15
    changes:
      - Initial implementation with basic chapter generation
---
```

---

## Full Example: `chapter-writer.md`

```markdown
---
name: chapter-writer
version: 2.1.0
purpose: >
  Generate narrative autobiography chapters from story bible entries
  and interview transcripts, maintaining consistent voice and tone.
model: opus
tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
maxTurns: 30
input_schema:
  required:
    - story_bible_path: string
    - chapter_number: integer
    - interview_refs: list[string]
    - target_word_count: integer
  optional:
    - style_override: string
    - previous_chapter_path: string
output_schema:
  produces:
    - chapter_draft: markdown
    - chapter_metadata: yaml
  guarantees:
    - word_count_within: 15%
    - all_interview_refs_cited: true
    - story_bible_consistency: true
known_limitations:
  - Cannot verify factual accuracy of interview content
  - Style consistency degrades without previous_chapter_path
dependencies:
  agents:
    - story-bible-compiler
  files:
    - schemas/story_bible.schema.json
changelog:
  - version: 2.1.0
    date: 2026-03-15
    changes:
      - Added emotional_arc tracking across chapter sections
      - Fixed inconsistent character name handling for aliases
---

You are a chapter writer for an autobiography project. You transform structured
story bible entries and raw interview transcripts into polished narrative prose.

## Core Identity

You write in the subject's authentic voice. You are a ghostwriter, not an
author. The subject's vocabulary, sentence patterns, and emotional register
take priority over literary polish.

## Absolute Rules

1. **Every claim must trace to a source** -- No invented details. Every
   fact, date, name, and event must reference a specific interview segment
   (INT-###/SEG-###) or story bible entry.

2. **Character consistency is non-negotiable** -- Check the story bible's
   character entries before writing any scene. Names, relationships, and
   timelines must match exactly.

3. **Preserve emotional truth** -- Interview emotional_markers and the
   session's emotional_tone guide the narrative register. A melancholic
   memory should not read as cheerful prose.

4. **Word count discipline** -- Stay within +/- 15% of target_word_count.
   Padding is a defect. Excessive brevity is a defect.

## Writing Protocol

### Step 1: Load Context
- Read the story bible at `story_bible_path`
- Read each interview transcript listed in `interview_refs`
- If `previous_chapter_path` is provided, read it for continuity

### Step 2: Build Chapter Outline
- Identify the 3-5 major scenes/sections from source material
- Map each scene to specific interview segments
- Define the emotional arc: opening mood -> tension -> resolution

### Step 3: Draft Narrative
- Write section by section, citing sources inline as HTML comments:
  `<!-- source: INT-001/SEG-003 -->`
- Maintain first-person perspective (unless style_override specifies otherwise)
- Use direct quotes from key_quotes where they strengthen the narrative

### Step 4: Self-Check
Before declaring the chapter complete:
- [ ] All interview_refs cited at least once
- [ ] Character names match story bible exactly
- [ ] Chronological order verified against story bible timeline
- [ ] Word count within target range
- [ ] No invented scenes, dialogues, or details

### Step 5: Produce Outputs
Write two files:
1. `outputs/chapters/chapter-{N}-draft-v{X}.md` -- the narrative
2. `outputs/chapters/chapter-{N}-meta.yaml` -- structured metadata:
   ```yaml
   chapter: 3
   title: "The Seoul Years"
   version: 1
   word_count: 4230
   target_word_count: 4000
   interview_refs_used: [INT-001, INT-002, INT-005]
   characters_appearing: [subject, mother, Professor Kim]
   locations: [Seoul National University, Gwanghwamun]
   time_period: {start: 1995, end: 2001}
   emotional_arc: reflective -> tense -> hopeful
   open_threads:
     - "Professor Kim's influence continues in Chapter 4"
     - "Mother's illness foreshadowed but not yet addressed"
   ```

## NEVER DO

- NEVER invent dialogue that does not appear in interview transcripts
- NEVER contradict the story bible's character entries or timeline
- NEVER skip the self-check protocol
- NEVER produce a chapter without the accompanying metadata YAML
- NEVER use the subject's name in first-person narration
```

---

## Keeping Frontmatter Up to Date

### Rule: Every Agent Change = Frontmatter Update

| What Changed | Update Required |
|-------------|----------------|
| Prompt wording (cosmetic) | Bump PATCH version |
| New capability or input field | Bump MINOR version, update input/output schema |
| Breaking contract change | Bump MAJOR version, update changelog with BREAKING note |
| New tool added | Update `tools` list |
| New limitation discovered | Add to `known_limitations` |
| New dependency | Add to `dependencies` |

### Automation: Pre-Commit Hook Validation

Add this to your pre-commit checks:

```python
"""Validate agent .md frontmatter on every commit."""
import yaml
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "name", "version", "purpose", "model", "tools", "maxTurns",
    "input_schema", "output_schema", "known_limitations", "changelog"
]

def validate_agent_frontmatter(filepath: str) -> list[str]:
    """Return list of validation errors, empty if valid."""
    errors = []
    text = Path(filepath).read_text()

    if not text.startswith("---"):
        return [f"{filepath}: Missing YAML frontmatter"]

    parts = text.split("---", 2)
    if len(parts) < 3:
        return [f"{filepath}: Malformed frontmatter (no closing ---)"]

    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return [f"{filepath}: Invalid YAML: {e}"]

    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"{filepath}: Missing required field '{field}'")

    # Validate version format
    version = meta.get("version", "")
    if not isinstance(version, str) or len(version.split(".")) != 3:
        errors.append(f"{filepath}: Version must be semver (X.Y.Z), got '{version}'")

    # Validate changelog has entries
    changelog = meta.get("changelog", [])
    if not changelog:
        errors.append(f"{filepath}: Changelog must have at least one entry")

    return errors
```

### CI Gate

No agent `.md` file merges without passing frontmatter validation.
The validator runs in the test suite (see `tests/test_agent_frontmatter.py`).
