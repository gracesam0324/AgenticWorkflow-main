#!/usr/bin/env python3
"""Tests for validate_content_insertion.py — SOT content ↔ HTML matching."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_content_insertion import check_content, extract_content_items, normalize_text


class TestContentInsertion(unittest.TestCase):
    """SOT content appears in HTML."""

    def test_all_content_present_passes(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {
                "intent": {"app_type": "quiz", "team_names": ["사랑", "믿음"]},
                "content": {
                    "quiz_questions": [
                        {"question": "노아의 방주", "answer": "한 쌍", "options": ["한 쌍", "두 쌍"]}
                    ]
                }
            }
            with open(os.path.join(td, "app-state.json"), "w", encoding="utf-8") as f:
                json.dump(sot, f, ensure_ascii=False)
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><body><h2>사랑</h2><h2>믿음</h2><p>노아의 방주</p><p>한 쌍</p></body></html>")
            result = check_content(td)
            self.assertTrue(result["pass"])
            self.assertGreaterEqual(result["match_rate"], 0.95)

    def test_missing_content_fails(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {
                "intent": {"app_type": "quiz", "team_names": ["사랑", "믿음", "소망"]},
                "content": {
                    "quiz_questions": [
                        {"question": "Q1 text", "answer": "A1"},
                        {"question": "Q2 text", "answer": "A2"},
                        {"question": "Q3 text", "answer": "A3"},
                    ]
                }
            }
            with open(os.path.join(td, "app-state.json"), "w", encoding="utf-8") as f:
                json.dump(sot, f, ensure_ascii=False)
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><body><p>사랑</p><p>Q1 text</p></body></html>")
            result = check_content(td)
            self.assertFalse(result["pass"])
            self.assertGreater(len(result["missing"]), 0)

    def test_no_sot_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html></html>")
            result = check_content(td)
            self.assertFalse(result["pass"])

    def test_empty_content_passes(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {"intent": {"app_type": "schedule"}, "content": {}}
            with open(os.path.join(td, "app-state.json"), "w") as f:
                json.dump(sot, f)
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html></html>")
            result = check_content(td)
            self.assertTrue(result["pass"])


class TestNormalizeText(unittest.TestCase):
    """Text normalization for comparison."""

    def test_whitespace_normalized(self):
        self.assertEqual(normalize_text("  hello   world  "), "hello world")

    def test_non_string_converted(self):
        self.assertEqual(normalize_text(42), "42")


if __name__ == "__main__":
    unittest.main()
