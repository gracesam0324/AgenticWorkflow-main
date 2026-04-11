#!/usr/bin/env python3
"""Tests for compute_pacs_data.py — pACS objective data extraction."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from compute_pacs_data import compute_c_data, read_sot


class TestComputeCData(unittest.TestCase):
    """C_data: Feature Completeness."""

    def test_all_features_implemented(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {"intent": {"app_type": "schedule", "features": []}}
            with open(os.path.join(td, "app-state.json"), "w") as f:
                json.dump(sot, f)
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write('<div class="schedule_page">Schedule here</div>')
            with open(os.path.join(td, "app.js"), "w") as f:
                f.write("// schedule page logic")
            result = compute_c_data(td)
            self.assertGreater(result["coverage_rate"], 0)

    def test_empty_features_passes(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {"intent": {"app_type": "combined", "features": []}}
            with open(os.path.join(td, "app-state.json"), "w") as f:
                json.dump(sot, f)
            result = compute_c_data(td)
            self.assertEqual(result["coverage_rate"], 1.0)

    def test_missing_features_detected(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {"intent": {"app_type": "quiz", "features": []}}
            with open(os.path.join(td, "app-state.json"), "w") as f:
                json.dump(sot, f)
            # Empty project — no features implemented
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html></html>")
            with open(os.path.join(td, "app.js"), "w") as f:
                f.write("// empty")
            result = compute_c_data(td)
            self.assertGreater(len(result["unimplemented"]), 0)


class TestReadSot(unittest.TestCase):
    """SOT reading utility."""

    def test_valid_sot(self):
        with tempfile.TemporaryDirectory() as td:
            sot = {"intent": {"app_type": "quiz"}}
            with open(os.path.join(td, "app-state.json"), "w") as f:
                json.dump(sot, f)
            result = read_sot(td)
            self.assertEqual(result["intent"]["app_type"], "quiz")

    def test_missing_sot_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            result = read_sot(td)
            self.assertEqual(result, {})

    def test_invalid_json_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "app-state.json"), "w") as f:
                f.write("not json {{{")
            result = read_sot(td)
            self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
