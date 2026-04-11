#!/usr/bin/env python3
"""Tests for validate_gates.py — Q1-Q11 technical quality gates."""

import json
import os
import sys
import tempfile
import unittest

# Add parent dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_gates import (
    check_q2, check_q3, check_q4, check_q5, check_q6,
    get_project_files, read_files_by_ext,
)


class TestQ2HtmlValidity(unittest.TestCase):
    """Q2: HTML validity — no render-blocking errors."""

    def test_valid_html_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><head><title>Test</title></head><body><p>Hello</p></body></html>")
            result = check_q2(td)
            self.assertTrue(result["pass"])

    def test_empty_project_fails(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_q2(td)
            self.assertFalse(result["pass"])

    def test_html_with_korean_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><body><h1>수련회 앱</h1></body></html>")
            result = check_q2(td)
            self.assertTrue(result["pass"])


class TestQ3ExternalDeps(unittest.TestCase):
    """Q3: External deps — 0 external scripts."""

    def test_no_external_scripts_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write('<html><body><script src="app.js"></script></body></html>')
            result = check_q3(td)
            self.assertTrue(result["pass"])

    def test_external_script_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write('<html><body><script src="https://cdn.example.com/lib.js"></script></body></html>')
            result = check_q3(td)
            self.assertFalse(result["pass"])

    def test_cdn_font_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write('<html><head><link href="https://fonts.googleapis.com/css" rel="stylesheet"></head></html>')
            result = check_q3(td)
            self.assertTrue(result["pass"])


class TestQ4BundleSize(unittest.TestCase):
    """Q4: Bundle size ≤ 500KB."""

    def test_small_project_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html><body>Small</body></html>")
            result = check_q4(td)
            self.assertTrue(result["pass"])
            self.assertLess(result["value"], 512000)

    def test_large_project_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "big.js"), "w") as f:
                f.write("x" * 600000)
            result = check_q4(td)
            self.assertFalse(result["pass"])

    def test_node_modules_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            nm = os.path.join(td, "node_modules", "pkg")
            os.makedirs(nm)
            with open(os.path.join(nm, "big.js"), "w") as f:
                f.write("x" * 600000)
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html></html>")
            result = check_q4(td)
            self.assertTrue(result["pass"])


class TestQ5KoreanRendering(unittest.TestCase):
    """Q5: Korean rendering — no broken text, Korean present."""

    def test_korean_text_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><body><h1>안녕하세요</h1></body></html>")
            result = check_q5(td)
            self.assertTrue(result["pass"])

    def test_replacement_char_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><body><h1>\uFFFD broken</h1></body></html>")
            result = check_q5(td)
            self.assertFalse(result["pass"])

    def test_no_korean_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
                f.write("<html><body><h1>English only</h1></body></html>")
            result = check_q5(td)
            self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
