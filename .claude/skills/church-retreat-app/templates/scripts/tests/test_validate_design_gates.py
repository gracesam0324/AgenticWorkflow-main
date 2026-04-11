#!/usr/bin/env python3
"""Tests for validate_design_gates.py — D1-D9 design quality gates."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_design_gates import check_d1, check_d2, check_d3, check_d4, check_d8


class TestD1CardUI(unittest.TestCase):
    """D1: border-radius ≥ 12px + box-shadow."""

    def test_valid_card_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".card { border-radius: 16px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }")
            result = check_d1(td)
            self.assertTrue(result["pass"])

    def test_small_radius_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".card { border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }")
            result = check_d1(td)
            self.assertFalse(result["pass"])

    def test_no_shadow_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".card { border-radius: 16px; }")
            result = check_d1(td)
            self.assertFalse(result["pass"])


class TestD2Animation(unittest.TestCase):
    """D2: ≥ 2 transitions ≥ 150ms + page transition."""

    def test_valid_animations_pass(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write("""
                .btn { transition: transform 150ms ease; }
                .card { transition: opacity 250ms ease; }
                @keyframes slideIn { from { opacity: 0; } to { opacity: 1; } }
                """)
            result = check_d2(td)
            self.assertTrue(result["pass"])

    def test_too_fast_transitions_fail(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write("""
                .btn { transition: transform 50ms; }
                .card { transition: opacity 100ms; }
                @keyframes slideIn { from { opacity: 0; } to { opacity: 1; } }
                """)
            result = check_d2(td)
            self.assertFalse(result["pass"])

    def test_no_keyframes_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".btn { transition: transform 200ms; } .card { transition: opacity 200ms; }")
            result = check_d2(td)
            self.assertFalse(result["pass"])


class TestD3DarkMode(unittest.TestCase):
    """D3: prefers-color-scheme: dark media query."""

    def test_dark_mode_present_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write("@media (prefers-color-scheme: dark) { body { background: #111; } }")
            result = check_d3(td)
            self.assertTrue(result["pass"])

    def test_no_dark_mode_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write("body { background: white; }")
            result = check_d3(td)
            self.assertFalse(result["pass"])


class TestD4ColorConsistency(unittest.TestCase):
    """D4: CSS variables only, 0 hardcoded colors outside :root."""

    def test_css_vars_only_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(":root { --primary: #4F46E5; } .btn { color: var(--primary); }")
            result = check_d4(td)
            self.assertTrue(result["pass"])

    def test_hardcoded_color_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(":root { --primary: #4F46E5; } .btn { color: #ff0000; }")
            result = check_d4(td)
            self.assertFalse(result["pass"])


class TestD8LoadingUX(unittest.TestCase):
    """D8: Skeleton UI or spinner present."""

    def test_skeleton_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div class="skeleton skeleton-text"></div>')
            result = check_d8(td)
            self.assertTrue(result["pass"])

    def test_spinner_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "style.css"), "w") as f:
                f.write(".spinner { width: 32px; }")
            result = check_d8(td)
            self.assertTrue(result["pass"])

    def test_no_loading_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<div>No loading</div>")
            result = check_d8(td)
            self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
