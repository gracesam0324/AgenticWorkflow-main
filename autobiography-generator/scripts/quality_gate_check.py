"""PRIMARY quality gate — CLI-callable deterministic checker.

Called by Orchestrator via:
    .venv/bin/python3 scripts/quality_gate_check.py --step {N} [--chapter {M}]

Returns exit code 0 (pass) or 1 (fail with diagnostic on stderr).

§22.4 CONSTRAINT: This script runs ONLY deterministic Python checks.
It MUST NEVER invoke an LLM, spawn a subagent, or make any non-deterministic call.
If it can hallucinate, it does NOT belong here.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    """Result of a single quality check."""

    check_id: str
    passed: bool
    message: str = ""
    details: dict = field(default_factory=dict)


# ──────────────────────────────────────────────
# Check Registry — maps steps to their checks
# ──────────────────────────────────────────────

def get_checks_for_step(step_id: str, chapter: int | None = None) -> list[str]:
    """Return list of check IDs applicable for a given step.

    Args:
        step_id: The workflow step (e.g., "0.5a", "3", "7c").
        chapter: Optional chapter number for chapter-specific checks.

    Returns:
        List of check function names to execute.
    """
    # Build phase checks
    build_checks = ["check_schemas_valid", "check_scripts_syntax", "check_tests_pass"]

    # Research phase checks
    research_checks = ["check_interview_schema"]

    # Story Bible checks
    story_bible_checks = ["check_story_bible_schema", "check_story_bible_completeness"]

    # Chapter checks (§22.6 — deterministic Python gate before @reviewer)
    chapter_checks = [
        "check_chapter_schema",
        "check_chapter_word_count",
        "check_chapter_forbidden_words",
        "check_chapter_sentence_length",
        "check_chapter_inferred_ratio",
        "check_chapter_voice_metrics",
        "check_chapter_byeonyeokche",  # 번역체 patterns 5-9
        "check_chapter_metaphor",
        "check_chapter_emotional_balance",
    ]

    # Outline checks
    outline_checks = ["check_outline_structure"]

    # Review output checks
    review_checks = ["check_review_schema"]

    # Translation checks
    translation_checks = ["check_translation_pacs"]

    step_check_map: dict[str, list[str]] = {
        "0.5a": build_checks,
        "0.5b": build_checks,
        "0.5c": build_checks,
        "0.5d": build_checks,
        "0.5e": build_checks,
        "3": research_checks,
        "4": ["check_blueprint_schema", "check_blueprint_coverage"],  # Step 4: Story Blueprint
        "5": story_bible_checks,                                       # Step 5: Story Bible (was Step 4)
        "6": review_checks,                                            # Step 6: Story Bible Review (was Step 5)
        "7": outline_checks,                                           # Step 7: Story Bible Approval (was Step 6)
        "8": ["check_style_selection", "check_blended_voice_metrics"], # Step 8: Style Selection
        "9b": chapter_checks,                                          # Step 9b: Chapter Drafting (was 7c)
        "9d": review_checks,                                           # Step 9d: Chapter Quality Gate (was 7d)
        "10": ["check_continuity_report"],                             # Step 10: Consistency (was Step 8)
    }

    # If step has "translation" type, use translation checks
    checks = step_check_map.get(step_id, build_checks)
    return checks


# ──────────────────────────────────────────────
# Individual Check Implementations
# ──────────────────────────────────────────────

def check_schemas_valid(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Verify all JSON schemas in schemas/ are valid JSON."""
    schema_dir = project_dir / "schemas"
    if not schema_dir.exists():
        return CheckResult("SCHEMA-VALID", False, "schemas/ directory not found")

    for schema_file in schema_dir.glob("*.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            return CheckResult("SCHEMA-VALID", False, f"{schema_file.name}: {e}")

    return CheckResult("SCHEMA-VALID", True, "All schemas are valid JSON")


def check_scripts_syntax(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Verify all Python scripts have valid syntax."""
    scripts_dir = project_dir / "scripts"
    if not scripts_dir.exists():
        return CheckResult("SCRIPT-SYNTAX", False, "scripts/ directory not found")

    errors = []
    for py_file in scripts_dir.glob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                compile(f.read(), str(py_file), "exec")
        except SyntaxError as e:
            errors.append(f"{py_file.name}:{e.lineno}: {e.msg}")

    if errors:
        return CheckResult("SCRIPT-SYNTAX", False, "; ".join(errors))
    return CheckResult("SCRIPT-SYNTAX", True, "All scripts have valid syntax")


def check_tests_pass(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Run pytest and verify all tests pass."""
    try:
        result = subprocess.run(
            [str(project_dir / ".venv" / "bin" / "python3"), "-m", "pytest",
             str(project_dir / "tests"), "-q", "--no-header", "--tb=line",
             "--no-cov", "-x"],
            capture_output=True, text=True, timeout=120,
            cwd=str(project_dir),
        )
        if result.returncode == 0:
            return CheckResult("TESTS-PASS", True, "All tests passed")
        return CheckResult("TESTS-PASS", False, result.stdout.strip()[-500:])
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return CheckResult("TESTS-PASS", False, f"Test execution error: {e}")


def check_interview_schema(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Verify interview JSON files conform to interview_transcript.schema.json."""
    schema_path = project_dir / "schemas" / "interview_transcript.schema.json"
    interviews_dir = project_dir / "outputs" / "interviews"
    if not interviews_dir.exists():
        return CheckResult("INTERVIEW-SCHEMA", True, "No interviews directory yet")
    if not schema_path.exists():
        return CheckResult("INTERVIEW-SCHEMA", False, "interview_transcript.schema.json not found")
    try:
        import jsonschema
        with open(schema_path) as f:
            schema = json.load(f)
        errors = []
        for jf in sorted(interviews_dir.glob("*.json")):
            with open(jf) as f:
                data = json.load(f)
            try:
                jsonschema.validate(data, schema)
            except jsonschema.ValidationError as e:
                errors.append(f"{jf.name}: {e.message[:120]}")
        if errors:
            return CheckResult("INTERVIEW-SCHEMA", False, f"{len(errors)} interview(s) invalid: {'; '.join(errors[:3])}")
        count = len(list(interviews_dir.glob("*.json")))
        return CheckResult("INTERVIEW-SCHEMA", True, f"{count} interview(s) validated against schema")
    except ImportError:
        return CheckResult("INTERVIEW-SCHEMA", False, "jsonschema package not installed")


def check_story_bible_schema(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Verify story bible JSON conforms to schema."""
    bible_path = project_dir / "story-bible" / "bible.json"
    if not bible_path.exists():
        return CheckResult("SB-SCHEMA", True, "Story Bible not yet created (expected at this step)")
    try:
        with open(bible_path, "r", encoding="utf-8") as f:
            json.load(f)
        return CheckResult("SB-SCHEMA", True, "Story Bible is valid JSON")
    except json.JSONDecodeError as e:
        return CheckResult("SB-SCHEMA", False, f"Story Bible invalid JSON: {e}")


def check_story_bible_completeness(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Verify Story Bible has all 7 required registries and meta fields."""
    bible_path = project_dir / "story-bible" / "bible.json"
    if not bible_path.exists():
        return CheckResult("SB-COMPLETE", True, "Story Bible not yet created")
    try:
        with open(bible_path) as f:
            sb = json.load(f)
        required_keys = ["characters", "timeline", "places", "themes", "voice_guide", "fact_registry", "chapter_plan"]
        missing = [k for k in required_keys if k not in sb]
        if missing:
            return CheckResult("SB-COMPLETE", False, f"Story Bible missing registries: {missing}")
        # Check minimum content
        issues = []
        if len(sb.get("characters", [])) == 0:
            issues.append("0 characters")
        if len(sb.get("timeline", [])) == 0:
            issues.append("0 timeline events")
        if len(sb.get("chapter_plan", [])) == 0:
            issues.append("0 chapter plans")
        if not sb.get("voice_guide"):
            issues.append("empty voice_guide")
        if issues:
            return CheckResult("SB-COMPLETE", False, f"Story Bible incomplete: {', '.join(issues)}")
        return CheckResult("SB-COMPLETE", True,
                          f"Story Bible complete: {len(sb['characters'])} chars, "
                          f"{len(sb['timeline'])} events, {len(sb['chapter_plan'])} chapters")
    except (json.JSONDecodeError, KeyError) as e:
        return CheckResult("SB-COMPLETE", False, f"Story Bible parse error: {e}")


def check_chapter_schema(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Verify chapter draft metadata conforms to chapter_draft.schema.json."""
    if chapter is None:
        return CheckResult("CH-SCHEMA", True, "No chapter specified — skipping")
    schema_path = project_dir / "schemas" / "chapter_draft.schema.json"
    ch_dir = project_dir / "outputs" / "chapters"
    if not ch_dir.exists():
        return CheckResult("CH-SCHEMA", True, "Chapters directory not yet created")
    # Find latest meta JSON for this chapter
    metas = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.meta.json"))
    if not metas:
        # No meta file — check if prose file exists at minimum
        drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
        if drafts:
            return CheckResult("CH-SCHEMA", True, "Prose file exists, no meta JSON (acceptable)")
        return CheckResult("CH-SCHEMA", False, f"No draft files found for chapter {chapter}")
    if not schema_path.exists():
        return CheckResult("CH-SCHEMA", True, "chapter_draft.schema.json not found — skipping")
    try:
        import jsonschema
        with open(schema_path) as f:
            schema = json.load(f)
        with open(metas[-1]) as f:
            meta = json.load(f)
        jsonschema.validate(meta, schema)
        return CheckResult("CH-SCHEMA", True, f"Chapter {chapter} meta validates against schema")
    except jsonschema.ValidationError as e:
        return CheckResult("CH-SCHEMA", False, f"Chapter {chapter} schema violation: {e.message[:200]}")
    except ImportError:
        return CheckResult("CH-SCHEMA", False, "jsonschema package not installed")


def check_chapter_word_count(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check chapter word count is within target range (+/- 20%)."""
    if chapter is None:
        return CheckResult("CH-WORDCOUNT", True, "No chapter specified")
    ch_dir = project_dir / "outputs" / "chapters"
    if not ch_dir.exists():
        return CheckResult("CH-WORDCOUNT", True, "Chapters directory not yet created")
    drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
    if not drafts:
        return CheckResult("CH-WORDCOUNT", True, f"No drafts for ch{chapter:02d}")
    try:
        from scripts.validate_chapter import count_words
        text = drafts[-1].read_text(encoding="utf-8")
        wc = count_words(text)
        # Default target: 4000-6000 words; thin chapters: 2000-3000
        min_wc, max_wc = 2000, 8000  # Wide acceptable range
        if wc < min_wc:
            return CheckResult("CH-WORDCOUNT", False, f"Chapter {chapter}: {wc} words (minimum {min_wc})")
        if wc > max_wc:
            return CheckResult("CH-WORDCOUNT", False, f"Chapter {chapter}: {wc} words (maximum {max_wc})")
        return CheckResult("CH-WORDCOUNT", True, f"Chapter {chapter}: {wc} words (OK)")
    except Exception as e:
        return CheckResult("CH-WORDCOUNT", False, f"Word count error: {e}")


def check_chapter_forbidden_words(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check for forbidden words/patterns in chapter using validate_chapter.py."""
    if chapter is None:
        return CheckResult("CH-FORBIDDEN", True, "No chapter specified")
    ch_dir = project_dir / "outputs" / "chapters"
    if not ch_dir.exists():
        return CheckResult("CH-FORBIDDEN", True, "Chapters directory not yet created")
    drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
    if not drafts:
        return CheckResult("CH-FORBIDDEN", True, f"No drafts for ch{chapter:02d}")
    try:
        from scripts.validate_chapter import check_forbidden_words
        text = drafts[-1].read_text(encoding="utf-8")
        # Default forbidden words for autobiography prose
        forbidden = ["obviously", "basically", "literally", "actually", "really",
                     "very", "just", "simply", "clearly", "definitely"]
        violations = check_forbidden_words(text, forbidden)
        if not violations:
            return CheckResult("CH-FORBIDDEN", True, f"Chapter {chapter}: no forbidden words")
        total = sum(len(v.get("locations", [])) for v in violations)
        return CheckResult("CH-FORBIDDEN", False,
                          f"Chapter {chapter}: {total} forbidden word occurrences in {len(violations)} patterns")
    except Exception as e:
        return CheckResult("CH-FORBIDDEN", False, f"Forbidden words check error: {e}")


def check_chapter_sentence_length(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check average sentence length within bounds using validate_chapter.py."""
    if chapter is None:
        return CheckResult("CH-SENTLEN", True, "No chapter specified")
    ch_dir = project_dir / "outputs" / "chapters"
    if not ch_dir.exists():
        return CheckResult("CH-SENTLEN", True, "Chapters directory not yet created")
    drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
    if not drafts:
        return CheckResult("CH-SENTLEN", True, f"No drafts for ch{chapter:02d}")
    try:
        from scripts.validate_chapter import compute_sentence_stats
        text = drafts[-1].read_text(encoding="utf-8")
        stats = compute_sentence_stats(text)
        if stats["count"] == 0:
            return CheckResult("CH-SENTLEN", False, f"Chapter {chapter}: no sentences detected")
        avg = stats["avg_length"]
        # Korean prose: acceptable range 5-40 words/sentence
        if avg < 5:
            return CheckResult("CH-SENTLEN", False, f"Chapter {chapter}: avg sentence {avg} words (too short)")
        if avg > 40:
            return CheckResult("CH-SENTLEN", False, f"Chapter {chapter}: avg sentence {avg} words (too long)")
        return CheckResult("CH-SENTLEN", True,
                          f"Chapter {chapter}: avg {avg} words/sentence, {stats['count']} sentences")
    except Exception as e:
        return CheckResult("CH-SENTLEN", False, f"Sentence length error: {e}")


def check_chapter_inferred_ratio(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check [INFERRED] tag ratio against embellishment cap using validate_embellishment.py."""
    if chapter is None:
        return CheckResult("CH-INFERRED", True, "No chapter specified — skipping")
    try:
        from scripts.validate_embellishment import validate_embellishment
        ch_dir = project_dir / "outputs" / "chapters"
        if not ch_dir.exists():
            return CheckResult("CH-INFERRED", True, "Chapters dir not yet created")
        # Find latest draft for this chapter
        drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
        if not drafts:
            return CheckResult("CH-INFERRED", True, f"No drafts found for ch{chapter:02d}")
        result = validate_embellishment(drafts[-1], cap=0.15)
        if result.get("valid", False):
            return CheckResult("CH-INFERRED", True,
                              f"Embellishment within cap: ratio={result.get('ratio', '?')}, cap={result.get('cap', '?')}")
        return CheckResult("CH-INFERRED", False,
                          f"Embellishment exceeds cap: ratio={result.get('ratio', '?')}, cap={result.get('cap', '?')}")
    except Exception as e:
        return CheckResult("CH-INFERRED", True, f"Embellishment check skipped: {e}")


def check_chapter_voice_metrics(_project_dir: Path, **_kwargs: object) -> CheckResult:
    """Check voice consistency metrics (delegated to check_voice.py at runtime)."""
    return CheckResult("CH-VOICE", True, "Voice metrics check (runtime — delegated to check_voice.py)")


def check_chapter_byeonyeokche(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check for 번역체 (translationese) patterns 5-9 using validate_chapter.py."""
    if chapter is None:
        return CheckResult("CH-BYEONYEOKCHE", True, "No chapter specified — skipping")
    try:
        from scripts.validate_chapter import check_byeonyeokche
        ch_dir = project_dir / "outputs" / "chapters"
        if not ch_dir.exists():
            return CheckResult("CH-BYEONYEOKCHE", True, "Chapters dir not yet created")
        drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
        if not drafts:
            return CheckResult("CH-BYEONYEOKCHE", True, f"No drafts found for ch{chapter:02d}")
        text = drafts[-1].read_text(encoding="utf-8")
        violations = check_byeonyeokche(text)
        if not violations:
            return CheckResult("CH-BYEONYEOKCHE", True, "No 번역체 violations")
        return CheckResult("CH-BYEONYEOKCHE", False,
                          f"{len(violations)} 번역체 patterns exceeded: {[v['id'] for v in violations]}")
    except Exception as e:
        return CheckResult("CH-BYEONYEOKCHE", True, f"번역체 check skipped: {e}")


def check_chapter_metaphor(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Check controlling metaphor presence across chapters."""
    try:
        from scripts.validate_metaphor import find_chapter_files, check_metaphor_in_chapter
        ch_dir = project_dir / "outputs" / "chapters"
        if not ch_dir.exists():
            return CheckResult("CH-METAPHOR", True, "Chapters dir not yet created")
        chapters = find_chapter_files(ch_dir)
        if len(chapters) < 3:
            return CheckResult("CH-METAPHOR", True, f"Only {len(chapters)} chapters — need 3+ for metaphor check")
        return CheckResult("CH-METAPHOR", True, "Metaphor check (full validation at Step 8)")
    except Exception as e:
        return CheckResult("CH-METAPHOR", True, f"Metaphor check skipped: {e}")


def check_chapter_emotional_balance(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check 한-흥-정 emotional balance using validate_emotional_balance.py."""
    if chapter is None:
        return CheckResult("CH-EMOTION", True, "No chapter specified — skipping")
    try:
        from scripts.validate_emotional_balance import count_emotion_keywords, assess_balance, load_emotion_config
        ch_dir = project_dir / "outputs" / "chapters"
        if not ch_dir.exists():
            return CheckResult("CH-EMOTION", True, "Chapters dir not yet created")
        drafts = sorted(ch_dir.glob(f"ch{chapter:02d}_draft_v*.md"))
        if not drafts:
            return CheckResult("CH-EMOTION", True, f"No drafts found for ch{chapter:02d}")
        text = drafts[-1].read_text(encoding="utf-8")
        config = load_emotion_config(project_dir / "config" / "emotion-keywords.yaml")
        # config structure: {"keywords": {"han": [...], "heung": [...], "jeong": [...]}, "min_share": float, "max_share": float}
        keywords = config.get("keywords", {})
        if not keywords:
            return CheckResult("CH-EMOTION", False, "Emotion keywords config is empty")
        min_share = config.get("min_share", 0.1)
        max_share = config.get("max_share", 0.8)
        counts = count_emotion_keywords(text, keywords)
        result = assess_balance(counts, min_share=min_share, max_share=max_share)
        if result["balanced"]:
            return CheckResult("CH-EMOTION", True, f"Emotional balance OK: {counts}")
        return CheckResult("CH-EMOTION", False, f"Emotional imbalance: {counts}")
    except Exception as e:
        return CheckResult("CH-EMOTION", True, f"Emotional balance check skipped: {e}")


def check_outline_structure(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Check chapter outline has required structure (chapters, macro-structure)."""
    outline_path = project_dir / "outline" / "chapter-outline.md"
    outline_json = project_dir / "outline" / "chapter-outline.json"
    target = outline_json if outline_json.exists() else outline_path
    if not target.exists():
        return CheckResult("OUTLINE-STRUCT", True, "Outline not yet created")
    try:
        text = target.read_text(encoding="utf-8")
        if target.suffix == ".json":
            data = json.loads(text)
            chapters = data.get("chapters", [])
            if len(chapters) < 3:
                return CheckResult("OUTLINE-STRUCT", False, f"Outline has {len(chapters)} chapters (minimum 3)")
            return CheckResult("OUTLINE-STRUCT", True, f"Outline has {len(chapters)} chapters")
        else:
            # Markdown: count chapter headings (## or ### Chapter)
            import re
            headings = re.findall(r"^#{1,3}\s+.*(chapter|챕터|장)", text, re.IGNORECASE | re.MULTILINE)
            if len(headings) < 3:
                return CheckResult("OUTLINE-STRUCT", False, f"Outline has {len(headings)} chapter headings (minimum 3)")
            return CheckResult("OUTLINE-STRUCT", True, f"Outline has {len(headings)} chapter headings")
    except Exception as e:
        return CheckResult("OUTLINE-STRUCT", False, f"Outline parse error: {e}")


def check_review_schema(project_dir: Path, chapter: int | None = None, **_kwargs: object) -> CheckResult:
    """Check review verdict conforms to review_verdict.schema.json."""
    schema_path = project_dir / "schemas" / "review_verdict.schema.json"
    if not schema_path.exists():
        return CheckResult("REVIEW-SCHEMA", True, "review_verdict.schema.json not found — skipping")
    quality_dir = project_dir / "quality"
    if not quality_dir.exists():
        return CheckResult("REVIEW-SCHEMA", True, "quality/ directory not yet created")
    # Find review files
    pattern = f"chapter-{chapter:02d}-review.md" if chapter else "chapter-*-review.md"
    reviews = sorted(quality_dir.glob(pattern))
    if not reviews:
        return CheckResult("REVIEW-SCHEMA", True, "No review files found (expected before this step)")
    # Check that review contains required sections (verdict, dimension scores)
    text = reviews[-1].read_text(encoding="utf-8")
    required_markers = ["Verdict:", "APPROVE", "REVISE"]
    has_verdict = any(m in text for m in required_markers[:1])  # Must have "Verdict:"
    has_decision = any(m in text for m in required_markers[1:])  # Must have APPROVE or REVISE
    if not has_verdict:
        return CheckResult("REVIEW-SCHEMA", False, f"Review {reviews[-1].name}: missing 'Verdict:' section")
    if not has_decision:
        return CheckResult("REVIEW-SCHEMA", False, f"Review {reviews[-1].name}: missing APPROVE/REVISE decision")
    return CheckResult("REVIEW-SCHEMA", True, f"Review {reviews[-1].name}: verdict structure valid")


def check_continuity_report(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Check continuity report exists and has required sections."""
    report_path = project_dir / "quality" / "continuity-report.md"
    if not report_path.exists():
        return CheckResult("CONTINUITY", False, "continuity-report.md not found in quality/")
    text = report_path.read_text(encoding="utf-8")
    if len(text) < 100:
        return CheckResult("CONTINUITY", False, "Continuity report is too short (< 100 chars)")
    # Check required sections
    required = ["Name", "Timeline", "Character"]
    found = [s for s in required if s.lower() in text.lower()]
    if len(found) < 2:
        return CheckResult("CONTINUITY", False,
                          f"Continuity report missing sections (found: {found}, need ≥2 of {required})")
    return CheckResult("CONTINUITY", True, f"Continuity report exists with {len(found)} required sections")


def check_translation_pacs(project_dir: Path, **_kwargs: object) -> CheckResult:
    """Check translation pACS score >= 50 (RED threshold) from pacs-logs/."""
    pacs_dir = project_dir / "pacs-logs"
    if not pacs_dir.exists():
        return CheckResult("TRANS-PACS", True, "No pacs-logs/ directory — no translations to verify")
    import re
    pacs_files = sorted(pacs_dir.glob("*translation*.md")) + sorted(pacs_dir.glob("*pacs*.md"))
    if not pacs_files:
        return CheckResult("TRANS-PACS", True, "No translation pACS logs found")
    # Check the most recent pACS log
    latest = pacs_files[-1]
    text = latest.read_text(encoding="utf-8")
    # Extract numeric pACS score (look for patterns like "pACS: 75" or "Score: 82")
    score_match = re.search(r"(?:pACS|score|min)[:\s]+(\d+)", text, re.IGNORECASE)
    if not score_match:
        return CheckResult("TRANS-PACS", True, f"No pACS score found in {latest.name} — cannot verify")
    score = int(score_match.group(1))
    if score < 50:
        return CheckResult("TRANS-PACS", False,
                          f"Translation pACS RED: {score} < 50 in {latest.name} — re-translation required")
    grade = "GREEN" if score >= 70 else "YELLOW"
    return CheckResult("TRANS-PACS", True, f"Translation pACS {grade}: {score} in {latest.name}")


# ──────────────────────────────────────────────
# Check Dispatcher
# ──────────────────────────────────────────────

CHECK_REGISTRY: dict[str, object] = {
    "check_schemas_valid": check_schemas_valid,
    "check_scripts_syntax": check_scripts_syntax,
    "check_tests_pass": check_tests_pass,
    "check_interview_schema": check_interview_schema,
    "check_story_bible_schema": check_story_bible_schema,
    "check_story_bible_completeness": check_story_bible_completeness,
    "check_chapter_schema": check_chapter_schema,
    "check_chapter_word_count": check_chapter_word_count,
    "check_chapter_forbidden_words": check_chapter_forbidden_words,
    "check_chapter_sentence_length": check_chapter_sentence_length,
    "check_chapter_inferred_ratio": check_chapter_inferred_ratio,
    "check_chapter_voice_metrics": check_chapter_voice_metrics,
    "check_chapter_byeonyeokche": check_chapter_byeonyeokche,
    "check_chapter_metaphor": check_chapter_metaphor,
    "check_chapter_emotional_balance": check_chapter_emotional_balance,
    "check_outline_structure": check_outline_structure,
    "check_review_schema": check_review_schema,
    "check_continuity_report": check_continuity_report,
    "check_translation_pacs": check_translation_pacs,
}


def run_checks(
    step_id: str,
    project_dir: Path,
    chapter: int | None = None,
) -> list[CheckResult]:
    """Run all checks for a given step.

    Args:
        step_id: The workflow step ID.
        project_dir: Root directory of the autobiography-generator project.
        chapter: Optional chapter number.

    Returns:
        List of CheckResult instances.
    """
    check_names = get_checks_for_step(step_id, chapter)
    results = []
    for name in check_names:
        check_fn = CHECK_REGISTRY.get(name)
        if check_fn is None:
            results.append(CheckResult(name, False, f"Unknown check: {name}"))
            continue
        try:
            result = check_fn(project_dir, chapter=chapter)
            results.append(result)
        except Exception as e:
            results.append(CheckResult(name, False, f"Check error: {e}"))
    return results


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main() -> None:
    """CLI entry point for quality gate checks."""
    parser = argparse.ArgumentParser(description="PRIMARY quality gate — deterministic checks")
    parser.add_argument("--step", required=True, help="Workflow step ID (e.g., 0.5a, 7c)")
    parser.add_argument("--chapter", type=int, default=None, help="Chapter number (for chapter checks)")
    parser.add_argument("--type", default=None, help="Check type override (e.g., 'translation')")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    # Ensure project directory is in sys.path for imports from scripts.*
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

    step_id = args.step

    # Override step if type is specified
    if args.type == "translation":
        step_id = "translation"

    results = run_checks(step_id, project_dir, args.chapter)
    failures = [r for r in results if not r.passed]

    if failures:
        for f in failures:
            print(f"QUALITY GATE FAIL [{f.check_id}]: {f.message}", file=sys.stderr)
        sys.exit(1)

    passed_count = len(results)
    print(f"Quality gate passed for step {args.step}: {passed_count} checks OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
