# Prompt Versioning Convention

## Semantic Versioning for Prompts

Prompts follow **semver** (MAJOR.MINOR.PATCH) with AI-specific semantics:

| Component | Meaning | When to Bump | Example |
|-----------|---------|-------------|---------|
| **MAJOR** | Breaking behavior change | Output format changes, new required inputs, role redefinition | `1.0.0` -> `2.0.0` |
| **MINOR** | Backward-compatible enhancement | New capability, improved instructions, added examples | `1.0.0` -> `1.1.0` |
| **PATCH** | Non-behavioral fix | Typo fix, clarification, whitespace cleanup | `1.0.0` -> `1.0.1` |

### Decision Tree

```
Did the output CONTRACT change (schema, format, required fields)?
  YES -> MAJOR bump
  NO  -> Did you add new CAPABILITIES or INSTRUCTIONS?
           YES -> MINOR bump
           NO  -> PATCH bump
```

---

## Diff-Friendly Prompt Structure

Prompts MUST be structured so `git diff` produces readable, reviewable output.

### Rule 1: One Instruction Per Line

BAD (diff shows entire paragraph changed):
```markdown
You are a chapter writer. Write chapters from story bible entries. Use first person. Keep word count within 15% of target. Cite all sources.
```

GOOD (diff shows exactly which instruction changed):
```markdown
You are a chapter writer.
Write chapters from story bible entries.
Use first person.
Keep word count within 15% of target.
Cite all sources.
```

### Rule 2: Numbered Rules for Stable Anchors

BAD (inserting a rule shifts all subsequent rules in diff):
```markdown
## Rules
- Always cite sources
- Use first person
- Check character names
```

GOOD (numbered rules are stable anchors):
```markdown
## Rules
1. Always cite sources.
2. Use first person.
3. Check character names.
```

### Rule 3: Examples in Fenced Blocks

BAD (example text mixes with instructions):
```markdown
For dates, use formats like "Summer 1998" or "early 2003" rather than exact dates unless the subject specifies them.
```

GOOD (example separated from instruction):
```markdown
For dates, use approximate phrasing unless the subject specifies an exact date.

Example:
```
GOOD: "Summer 1998", "early 2003"
BAD:  "June 15, 1998" (unless subject said this)
```
```

---

## Changelog Format in Prompt Files

Every prompt file includes a changelog section in YAML frontmatter.
This is the ONLY place to track prompt evolution.

### Format

```yaml
changelog:
  - version: 1.2.0
    date: 2026-03-15
    author: orchestrator
    type: minor
    changes:
      - "Added emotional arc tracking instruction in Step 2"
      - "New example for handling non-linear timelines"
    rationale: >
      Chapters 3-5 showed flat emotional progression. Added explicit
      arc instruction to guide tone transitions within sections.
    test_results: >
      Re-ran chapter 4 with v1.2.0. Emotional arc score improved
      from 62 to 78 (pACS F dimension).

  - version: 1.1.1
    date: 2026-03-10
    author: reviewer
    type: patch
    changes:
      - "Fixed ambiguous wording in Rule 3 about quote attribution"
    rationale: >
      Chapter 2 review found misattributed quote. Root cause was
      ambiguous instruction text.

  - version: 1.1.0
    date: 2026-03-05
    author: orchestrator
    type: minor
    changes:
      - "Added self-check protocol in Step 4"
      - "Added open_threads field to output metadata"
    rationale: >
      Chapters were missing continuity threads. Self-check ensures
      the writer tracks open narrative lines.
```

### Required Fields Per Entry

| Field | Required | Description |
|-------|----------|-------------|
| `version` | YES | New semver version |
| `date` | YES | ISO date of change |
| `author` | YES | Who made the change (orchestrator, reviewer, user) |
| `type` | YES | major, minor, or patch |
| `changes` | YES | List of specific changes (imperative mood) |
| `rationale` | YES | WHY this change was made (link to specific failure) |
| `test_results` | NO | Before/after metrics if available |

---

## Migration Notes

When a MAJOR version bump changes prompt behavior, include migration notes.

### Format

```yaml
migration:
  from_version: 1.x
  to_version: 2.0.0
  breaking_changes:
    - description: "Output format changed from flat markdown to structured YAML + markdown pair"
      action_required: "Update all downstream agents that consume chapter output"
      affected_agents: [editor, continuity-checker, reviewer]

    - description: "input_schema now requires story_bible_path instead of raw text"
      action_required: "Ensure story-bible-compiler runs before chapter-writer"
      affected_agents: [orchestrator]

  rollback_plan: >
    If v2.0.0 produces lower quality output, revert to v1.3.2 tag.
    Downstream agents will need to be reverted to their pre-v2.0.0
    versions as well. See DECISION-LOG.md ADR-XXX for rollback steps.
```

---

## Concrete Example: Version History of a Real Prompt

### `chapter-writer.md` Version Timeline

```
v1.0.0  2026-02-15  Initial implementation
  - Basic "write a chapter" instruction
  - No source citation requirement
  - No self-check protocol

v1.1.0  2026-02-20  Add source citation requirement
  - Added Rule 1: "Every claim must trace to a source"
  - Added inline comment format: <!-- source: INT-001/SEG-003 -->
  - Rationale: Chapters contained invented details

v1.1.1  2026-02-22  Fix citation format ambiguity
  - Clarified that citations go AFTER the sentence, not before
  - Rationale: Agent was placing citations mid-sentence

v1.2.0  2026-03-01  Add character consistency check
  - Added Rule 2: Character name cross-reference against story bible
  - Added aliases support in character lookup
  - Rationale: Chapter 2 used "Dr. Kim" and "Professor Kim" inconsistently

v1.3.0  2026-03-05  Add self-check protocol
  - Added Step 4: Self-Check with 5-item checklist
  - Added open_threads to metadata output
  - Rationale: Missing continuity threads between chapters

v2.0.0  2026-03-10  BREAKING: Structured input/output
  - Input changed from raw text to story_bible_path reference
  - Output now produces both .md and .yaml files
  - Migration: All downstream agents updated to consume new format
  - Rationale: Flat text input caused inconsistent parsing

v2.1.0  2026-03-15  Add emotional arc tracking
  - New emotional_arc field in output metadata
  - Step 2 now requires explicit arc planning
  - Rationale: pACS scores showed flat emotional progression
```

### Filename Convention

Prompt files do NOT include version numbers in their filename.
Version is tracked ONLY in the frontmatter.

```
GOOD: chapter-writer.md          (version in frontmatter: 2.1.0)
BAD:  chapter-writer-v2.1.0.md   (version in filename creates file sprawl)
```

Git tags mark releases: `prompt/chapter-writer/v2.1.0`
Git log shows the full history: `git log --follow -- .claude/agents/chapter-writer.md`
