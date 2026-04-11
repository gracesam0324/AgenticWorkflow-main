#!/usr/bin/env python3
"""Comprehensive tests for _church_app_lib shared library.

Tests all public functions against the corrected API:
- parse_tool_input_from_string() returns tool_input dict (not full stdin)
- ALLOWED_SOT_WRITERS is a list (not dict)
- OWNERSHIP_MAP is {agent_name: [patterns]} (not {pattern: role})
- CONTENT_MATRIX uses 9 app types (quiz, score, schedule, ...)
- classify_modification() returns tuple ("A"/"B"/"C"/"?", type)
- detect_completion_signal() uses Korean patterns
- calculate_bundle_size() returns (kb, count, over_target, over_hard)
- validate_translation_pair() returns (valid, errors) tuple
"""

import json
import os
import sys
import tempfile
import unittest

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _church_app_lib as lib


# =============================================================================
# parse_tool_input (C-1 fix: returns tool_input dict)
# =============================================================================
class TestParseToolInput(unittest.TestCase):
    def test_valid_stdin_format(self):
        """parse_tool_input_from_string extracts tool_input from Claude Code format."""
        data = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/test.js"}})
        result = lib.parse_tool_input_from_string(data)
        self.assertEqual(result["file_path"], "/test.js")

    def test_missing_tool_input(self):
        """Returns empty dict if tool_input key is missing."""
        data = json.dumps({"tool_name": "Write"})
        result = lib.parse_tool_input_from_string(data)
        self.assertEqual(result, {})

    def test_invalid_json(self):
        result = lib.parse_tool_input_from_string("not json")
        self.assertEqual(result, {})

    def test_empty_string(self):
        result = lib.parse_tool_input_from_string("")
        self.assertEqual(result, {})

    def test_nested_tool_input(self):
        data = json.dumps({"tool_name": "Edit", "tool_input": {
            "file_path": "/app.js", "old_string": "a", "new_string": "b"
        }})
        result = lib.parse_tool_input_from_string(data)
        self.assertEqual(result["file_path"], "/app.js")
        self.assertEqual(result["old_string"], "a")


# =============================================================================
# SOT management (C-2 fix: ALLOWED_SOT_WRITERS is a list)
# =============================================================================
class TestSOTManagement(unittest.TestCase):
    def test_sot_files_list(self):
        self.assertIn("app-state.json", lib.SOT_FILES)
        self.assertEqual(len(lib.SOT_FILES), 1)  # Only app-state.json

    def test_allowed_writers_is_list(self):
        self.assertIsInstance(lib.ALLOWED_SOT_WRITERS, list)
        self.assertIn("church-app-orchestrator", lib.ALLOWED_SOT_WRITERS)
        self.assertNotIn("unknown", lib.ALLOWED_SOT_WRITERS)

    def test_read_sot_missing(self):
        result = lib.read_sot("/nonexistent/path")
        self.assertEqual(result, {})

    def test_read_sot_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sot_path = os.path.join(tmpdir, "app-state.json")
            with open(sot_path, "w") as f:
                json.dump({"intent": {"app_type": "quiz"}}, f)
            result = lib.read_sot(tmpdir)
            self.assertEqual(result["intent"]["app_type"], "quiz")

    def test_get_sot_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sot_path = os.path.join(tmpdir, "app-state.json")
            with open(sot_path, "w") as f:
                json.dump({"status": {"current_phase": 3}}, f)
            val = lib.get_sot_field("status.current_phase", tmpdir)
            self.assertEqual(val, 3)

    def test_get_sot_field_missing(self):
        val = lib.get_sot_field("nonexistent.field", "/nonexistent")
        self.assertIsNone(val)


# =============================================================================
# File ownership (C-3 fix: {agent_name: [patterns]})
# =============================================================================
class TestFileOwnership(unittest.TestCase):
    def test_ownership_map_structure(self):
        """OWNERSHIP_MAP keys are agent names, values are pattern lists."""
        for agent_name, patterns in lib.OWNERSHIP_MAP.items():
            self.assertIsInstance(agent_name, str)
            self.assertIsInstance(patterns, list)
        self.assertIn("code-generator", lib.OWNERSHIP_MAP)
        self.assertIn("design-system", lib.OWNERSHIP_MAP)
        self.assertIn("tdd-guard", lib.OWNERSHIP_MAP)

    def test_code_generator_owns_server(self):
        owner = lib.get_file_owner("server.js")
        self.assertEqual(owner, "code-generator")

    def test_design_system_owns_css(self):
        owner = lib.get_file_owner("styles.css")
        self.assertEqual(owner, "design-system")

    def test_tdd_guard_owns_tests(self):
        owner = lib.get_file_owner("tests/test_server.js")
        self.assertEqual(owner, "tdd-guard")

    def test_translator_owns_ko_files(self):
        owner = lib.get_file_owner("reports/phase1.ko.md")
        self.assertEqual(owner, "app-translator")

    def test_unowned_file(self):
        owner = lib.get_file_owner("README.md")
        self.assertIsNone(owner)

    def test_ownership_check_allowed(self):
        ok, _ = lib.check_file_ownership("server.js", "code-generator")
        self.assertTrue(ok)

    def test_ownership_check_blocked(self):
        ok, owner = lib.check_file_ownership("styles.css", "code-generator")
        self.assertFalse(ok)
        self.assertEqual(owner, "design-system")

    def test_sot_orchestrator_allowed(self):
        ok, _ = lib.check_file_ownership("app-state.json", "church-app-orchestrator")
        self.assertTrue(ok)

    def test_sot_non_orchestrator_blocked(self):
        ok, _ = lib.check_file_ownership("app-state.json", "code-generator")
        self.assertFalse(ok)

    def test_unknown_agent_not_allowed_for_owned_files(self):
        """C-2/H-5 fix: 'unknown' agent should NOT be allowed for owned files."""
        ok, _ = lib.check_file_ownership("server.js", "unknown")
        self.assertFalse(ok)

    def test_unowned_file_anyone_allowed(self):
        ok, _ = lib.check_file_ownership("README.md", "anyone")
        self.assertTrue(ok)


# =============================================================================
# Modification classifier (Korean patterns)
# =============================================================================
class TestClassifyModification(unittest.TestCase):
    def test_style_color(self):
        code, label = lib.classify_modification("색상 좀 바꿔줘")
        self.assertEqual(code, "A")
        self.assertEqual(label, "style")

    def test_style_dark_mode(self):
        code, _ = lib.classify_modification("다크모드로 해줘")
        self.assertEqual(code, "A")

    def test_feature_add(self):
        code, _ = lib.classify_modification("타이머 기능 추가해줘")
        self.assertEqual(code, "B")

    def test_rollback(self):
        code, _ = lib.classify_modification("아까 상태로 돌려줘")
        self.assertEqual(code, "C")

    def test_uncertain(self):
        code, _ = lib.classify_modification("음... 잘 모르겠어")
        self.assertEqual(code, "?")

    def test_empty(self):
        code, _ = lib.classify_modification("")
        self.assertEqual(code, "?")


# =============================================================================
# Completion signal (Korean patterns)
# =============================================================================
class TestDetectCompletionSignal(unittest.TestCase):
    def test_positive(self):
        self.assertTrue(lib.detect_completion_signal("좋아요!"))
        self.assertTrue(lib.detect_completion_signal("배포해줘"))
        self.assertTrue(lib.detect_completion_signal("완성!"))

    def test_negation(self):
        self.assertFalse(lib.detect_completion_signal("괜찮은데 버튼이..."))
        self.assertFalse(lib.detect_completion_signal("좋아요 근데 하나만"))

    def test_no_signal(self):
        self.assertFalse(lib.detect_completion_signal("그래서 뭘 해야 해?"))
        self.assertFalse(lib.detect_completion_signal(""))


# =============================================================================
# Bundle size (returns 4-tuple)
# =============================================================================
class TestBundleSize(unittest.TestCase):
    def test_returns_tuple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.txt"), "w") as f:
                f.write("x" * 1024)
            result = lib.calculate_bundle_size(tmpdir)
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 4)
            total_kb, file_count, over_target, over_hard = result
            self.assertGreater(total_kb, 0)
            self.assertEqual(file_count, 1)
            self.assertFalse(over_target)
            self.assertFalse(over_hard)

    def test_excludes_node_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nm = os.path.join(tmpdir, "node_modules")
            os.makedirs(nm)
            with open(os.path.join(nm, "big.js"), "w") as f:
                f.write("x" * 1000000)
            with open(os.path.join(tmpdir, "app.js"), "w") as f:
                f.write("x" * 100)
            _, count, _, _ = lib.calculate_bundle_size(tmpdir)
            self.assertEqual(count, 1)


# =============================================================================
# Content Matrix (C-4 fix: 9 app types)
# =============================================================================
class TestContentMatrix(unittest.TestCase):
    def test_nine_app_types(self):
        expected = {"quiz", "score", "schedule", "lyrics", "stamps", "qt", "prayer", "photo", "combined"}
        self.assertEqual(set(lib.CONTENT_MATRIX.keys()), expected)

    def test_quiz_requires_fields(self):
        quiz = lib.CONTENT_MATRIX["quiz"]
        required = set(quiz["required_fields"].keys())
        self.assertIn("intent.team_count", required)
        self.assertIn("content.quiz_questions", required)

    def test_validate_quiz_complete(self):
        sot = {
            "intent": {"app_type": "quiz", "team_count": 4,
                       "team_names": ["1조", "2조", "3조", "4조"],
                       "design_palette": "A"},
            "content": {"quiz_questions": [{"q": "Q1"}]},
        }
        complete, missing, app_type = lib.validate_content_collection(sot)
        self.assertTrue(complete)
        self.assertEqual(app_type, "quiz")

    def test_validate_quiz_missing(self):
        sot = {"intent": {"app_type": "quiz", "team_count": 0, "team_names": []}}
        complete, missing, _ = lib.validate_content_collection(sot)
        self.assertFalse(complete)
        self.assertIn("intent.team_count", missing)

    def test_validate_no_sot(self):
        complete, missing, _ = lib.validate_content_collection(None)
        self.assertFalse(complete)

    def test_validate_unknown_type(self):
        sot = {"intent": {"app_type": "nonexistent"}}
        complete, _, app_type = lib.validate_content_collection(sot)
        self.assertFalse(complete)


# =============================================================================
# Hardcoded color detection (M-5 fix: per-match not per-line)
# =============================================================================
class TestHardcodedColors(unittest.TestCase):
    def test_detects_hardcoded_hex(self):
        css = "body { color: #FF0000; }"
        violations = lib.detect_hardcoded_colors(css)
        self.assertTrue(len(violations) > 0)

    def test_allows_var_declarations(self):
        css = ":root { --primary: #4F46E5; }\nbody { color: var(--primary); }"
        violations = lib.detect_hardcoded_colors(css)
        self.assertEqual(len(violations), 0)

    def test_skips_comments(self):
        css = "// color: #fff;\n/* color: #000; */"
        violations = lib.detect_hardcoded_colors(css)
        self.assertEqual(len(violations), 0)


# =============================================================================
# Translation validation (H-4 fix: loads glossary)
# =============================================================================
class TestTranslationValidation(unittest.TestCase):
    def test_valid_pair(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            en = os.path.join(tmpdir, "report.md")
            ko = os.path.join(tmpdir, "report.ko.md")
            with open(en, "w", encoding="utf-8") as f:
                f.write("# Title\n\nContent.\n\n## Section\n\nMore.\n")
            with open(ko, "w", encoding="utf-8") as f:
                f.write("# 제목\n\n내용.\n\n## 섹션\n\n추가.\n")
            valid, errors = lib.validate_translation_pair(en, ko)
            self.assertTrue(valid)

    def test_section_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            en = os.path.join(tmpdir, "report.md")
            ko = os.path.join(tmpdir, "report.ko.md")
            with open(en, "w") as f:
                f.write("# A\n\n## B\n\n## C\n")
            with open(ko, "w") as f:
                f.write("# 가\n\n내용\n")
            valid, errors = lib.validate_translation_pair(en, ko)
            self.assertFalse(valid)
            self.assertTrue(any("Section count" in e for e in errors))

    def test_missing_file(self):
        valid, errors = lib.validate_translation_pair("/nonexistent.md", "/ko.md")
        self.assertFalse(valid)


# =============================================================================
# SOT Snapshot
# =============================================================================
class TestSotSnapshot(unittest.TestCase):
    def test_creates_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sot = os.path.join(tmpdir, "app-state.json")
            with open(sot, "w") as f:
                json.dump({"status": {"current_phase": 1}}, f)
            path = lib.create_sot_snapshot(project_dir=tmpdir, max_keep=3)
            self.assertIsNotNone(path)
            self.assertTrue(os.path.exists(path))

    def test_no_sot_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = lib.create_sot_snapshot(project_dir=tmpdir)
            self.assertIsNone(path)


if __name__ == "__main__":
    unittest.main()
