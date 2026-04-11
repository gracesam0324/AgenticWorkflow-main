#!/usr/bin/env python3
"""Tests for validate_integration.py — T-3.11 cross-reference checks."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_integration import check_html_css, check_js_html, check_manifest


class TestHtmlCssIntegration(unittest.TestCase):
    """HTML classes ↔ CSS selectors."""

    def test_matching_classes_pass(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div class="card active"></div>')
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".card { padding: 16px; } .active { display: block; }")
            result = check_html_css(td)
            self.assertTrue(result["pass"])

    def test_orphaned_class_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div class="card my-custom-orphan"></div>')
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".card { padding: 16px; }")
            result = check_html_css(td)
            self.assertFalse(result["pass"])
            self.assertIn("my-custom-orphan", result["value"]["orphaned"])

    def test_common_classes_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div class="active hidden"></div>')
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write("/* no definitions */")
            result = check_html_css(td)
            # 'active' and 'hidden' are in the common exclusion list
            self.assertTrue(result["pass"])


class TestJsHtmlIntegration(unittest.TestCase):
    """JS DOM refs ↔ HTML IDs."""

    def test_matching_ids_pass(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div id="score-display"></div>')
            with open(os.path.join(td, "app.js"), "w") as f:
                f.write('document.getElementById("score-display")')
            result = check_js_html(td)
            self.assertTrue(result["pass"])

    def test_dangling_ref_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div id="existing"></div>')
            with open(os.path.join(td, "app.js"), "w") as f:
                f.write('document.getElementById("nonexistent")')
            result = check_js_html(td)
            self.assertFalse(result["pass"])
            self.assertIn("nonexistent", result["value"]["dangling"])


class TestManifest(unittest.TestCase):
    """Manifest start_url check."""

    def test_valid_manifest_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "manifest.json"), "w") as f:
                json.dump({"name": "Test", "start_url": "/"}, f)
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html></html>")
            result = check_manifest(td)
            self.assertTrue(result["pass"])

    def test_no_manifest_ok(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_manifest(td)
            self.assertTrue(result["pass"])  # Non-PWA is OK

    def test_missing_index_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "manifest.json"), "w") as f:
                json.dump({"name": "Test", "start_url": "/"}, f)
            # No index.html
            result = check_manifest(td)
            self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
