# Code Review Checklist — AI Autobiography Pipeline

Use this checklist when reviewing PRs to the autobiography-generator.
Check each item. Mark N/A if the category does not apply to this PR.

---

## A. Agent Prompt Changes

Changes to `.md` files in `.claude/agents/` or prompt templates.

### A1. Frontmatter Integrity
- [ ] YAML frontmatter parses without errors
- [ ] `version` field bumped correctly (see Prompt Versioning Convention)
- [ ] `changelog` has a new entry with `version`, `date`, `author`, `type`, `changes`, `rationale`
- [ ] `input_schema` and `output_schema` still match actual agent behavior
- [ ] `known_limitations` updated if new limitations discovered
- [ ] `dependencies` updated if new agent/file dependencies added

### A2. Prompt Content Quality
- [ ] One instruction per line (diff-friendly)
- [ ] No contradictory instructions (search for "always" vs "never" on same topic)
- [ ] Examples are in fenced code blocks, not inline
- [ ] NEVER DO section updated if new anti-patterns discovered
- [ ] No leaked implementation details (paths, API keys, internal tool names)

### A3. Contract Compatibility
- [ ] Output schema changes are backward-compatible (MINOR) or marked BREAKING (MAJOR)
- [ ] All downstream agents that consume this agent's output identified
- [ ] If MAJOR version: migration notes present in changelog
- [ ] If MAJOR version: downstream agent tests updated

### A4. Behavioral Regression Check
- [ ] Sample run with updated prompt produces expected output
- [ ] pACS score on sample run is >= previous version's score
- [ ] No regressions in factual accuracy, completeness, or logical coherence
- [ ] Edge cases tested (empty input, minimal input, maximum-length input)

---

## B. Python Script Changes

Changes to `.py` files in `scripts/` or `tests/`.

### B1. Type Safety
- [ ] All functions have type annotations (enforced by mypy strict mode)
- [ ] No `Any` types without explicit justification comment
- [ ] Pydantic models used for all structured data (no raw dicts crossing boundaries)
- [ ] `load_yaml()` / `save_yaml()` used instead of raw yaml.safe_load/dump

### B2. Error Handling
- [ ] All file I/O wrapped in try/except with descriptive error messages
- [ ] Validation errors include the field name AND the invalid value
- [ ] No bare `except:` or `except Exception:` without re-raise or logging
- [ ] Path operations use `pathlib.Path`, not string concatenation

### B3. Code Standards
- [ ] `ruff check` passes with zero warnings
- [ ] `ruff format --check` passes (auto-formatted)
- [ ] `mypy --strict` passes with zero errors
- [ ] No commented-out code (enforced by ERA rule in ruff)
- [ ] Google-style docstrings on all public functions

### B4. Testing
- [ ] New code has corresponding tests in `tests/`
- [ ] Tests use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.schema`, etc.)
- [ ] No test accesses the network or external APIs
- [ ] Test fixtures create data in memory, no file I/O for unit tests
- [ ] Coverage does not decrease (minimum 80%, enforced in pyproject.toml)

### B5. AI Pipeline Specific
- [ ] No hardcoded file paths (use config or arguments)
- [ ] Schema changes in `scripts/schemas.py` have matching test updates
- [ ] State file transitions validated (no skipping steps)
- [ ] Interview ref patterns validated (INT-### format)

---

## C. Schema Changes

Changes to `scripts/schemas.py` or `schemas/*.json`.

### C1. Backward Compatibility
- [ ] New fields have default values (existing data still loads)
- [ ] Removed fields are deprecated first (add `deprecated=True` for one version)
- [ ] Enum values only ADDED, never removed (unless MAJOR version)
- [ ] Validation error messages are human-readable (include field name + expected value)

### C2. Cross-Schema Consistency
- [ ] Character names in EventEntry.characters_involved match CharacterEntry.name
- [ ] Interview ref patterns (INT-###) are consistent across all schemas
- [ ] Emotional tone enums are the same in StoryBibleEntry and ChapterDraft
- [ ] Date/time formats consistent (ISO 8601 for machines, human-readable noted)

### C3. Validation Coverage
- [ ] Every new field has at least one positive and one negative test case
- [ ] Cross-field validators have tests (e.g., start_year <= end_year)
- [ ] Edge cases tested: empty lists, max-length strings, boundary values
- [ ] `model_validate()` error output is actionable (user can fix without reading code)

---

## D. State File Changes

Changes to pipeline state management or `StepRecord`/`StateFile` schemas.

### D1. Transition Safety
- [ ] Steps cannot go backward (completed -> in-progress)
- [ ] Failed steps require error_message
- [ ] Skip logic documented (why was the step skipped?)
- [ ] `advance_to()` validates prerequisites before advancing

### D2. SOT Integrity
- [ ] Only one writer (Orchestrator) modifies the state file
- [ ] No concurrent writes possible in the pipeline design
- [ ] `last_modified` updated on every write
- [ ] State file can be reconstructed from step records (no orphaned state)

### D3. Recovery
- [ ] Pipeline can resume from any completed step
- [ ] Failed step retry does not corrupt previous step outputs
- [ ] State file is valid YAML after interruption (atomic write or temp-file swap)
- [ ] Error log entries include timestamp and step context

---

## Quick Reference: Review Priorities

When time is limited, check in this order:

1. **Contract breaks** (A3, C1) -- Will this break other agents?
2. **Type safety** (B1) -- Does mypy pass?
3. **Test coverage** (B4, C3) -- Are changes tested?
4. **State transitions** (D1) -- Can the pipeline corrupt itself?
5. **Prompt quality** (A2) -- Is the prompt clear and unambiguous?

---

## PR Description Template

```markdown
## What Changed
- [one line per change]

## Why
- [link to issue, failed review, or pACS regression]

## Category
- [ ] Agent prompt change
- [ ] Python script change
- [ ] Schema change
- [ ] State file change

## Checklist
- [ ] I ran `ruff check && ruff format --check && mypy --strict scripts/`
- [ ] I ran `pytest` and all tests pass
- [ ] I updated the changelog in affected agent .md files
- [ ] I checked backward compatibility for schema changes

## Test Evidence
[paste pytest output or pACS score comparison]
```
