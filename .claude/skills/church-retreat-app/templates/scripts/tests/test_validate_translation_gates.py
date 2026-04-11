#!/usr/bin/env python3
"""Tests for validate_translation_gates.py — T1-T3."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_translation_gates import check_t1, check_t2, check_t3


class TestT1TranslationFiles(unittest.TestCase):
    """T1: .ko files exist for all phase reports."""

    def test_all_ko_files_pass(self):
        with tempfile.TemporaryDirectory() as td:
            reports = os.path.join(td, "reports")
            os.makedirs(reports)
            for i in range(1, 4):
                with open(os.path.join(reports, f"phase{i}-report.md"), "w") as f:
                    f.write(f"Phase {i} report")
                with open(os.path.join(reports, f"phase{i}-report.ko.md"), "w") as f:
                    f.write(f"Phase {i} 보고서")
            result = check_t1(td)
            self.assertTrue(result["pass"])

    def test_missing_ko_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            reports = os.path.join(td, "reports")
            os.makedirs(reports)
            with open(os.path.join(reports, "phase1-report.md"), "w") as f:
                f.write("Phase 1")
            # No .ko file
            result = check_t1(td)
            self.assertFalse(result["pass"])

    def test_no_reports_dir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_t1(td)
            self.assertFalse(result["pass"])


class TestT2PacsScores(unittest.TestCase):
    """T2: pACS >= 70 for each translation."""

    def test_high_scores_pass(self):
        with tempfile.TemporaryDirectory() as td:
            pacs_dir = os.path.join(td, "pacs-logs")
            os.makedirs(pacs_dir)
            with open(os.path.join(pacs_dir, "phase1-translation-pacs.md"), "w") as f:
                f.write("Translation quality:\npACS = 85\n")
            result = check_t2(td)
            self.assertTrue(result["pass"])

    def test_low_score_fails(self):
        with tempfile.TemporaryDirectory() as td:
            pacs_dir = os.path.join(td, "pacs-logs")
            os.makedirs(pacs_dir)
            with open(os.path.join(pacs_dir, "phase1-translation-pacs.md"), "w") as f:
                f.write("pACS = 45\n")
            result = check_t2(td)
            self.assertFalse(result["pass"])

    def test_no_pacs_dir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_t2(td)
            self.assertFalse(result["pass"])


class TestT3GlossaryConsistency(unittest.TestCase):
    """T3: Glossary terms consistently translated."""

    def test_no_glossary_passes(self):
        """No glossary = skip (pass)."""
        with tempfile.TemporaryDirectory() as td:
            result = check_t3(td)
            self.assertTrue(result["pass"])

    def test_consistent_translation_passes(self):
        with tempfile.TemporaryDirectory() as td:
            trans_dir = os.path.join(td, "translations")
            os.makedirs(trans_dir)
            with open(os.path.join(trans_dir, "glossary.yaml"), "w", encoding="utf-8") as f:
                f.write("orchestrator: 오케스트레이터\n")
            reports = os.path.join(td, "reports")
            os.makedirs(reports)
            with open(os.path.join(reports, "phase1-report.ko.md"), "w", encoding="utf-8") as f:
                f.write("오케스트레이터가 Phase 1을 관리합니다.")
            result = check_t3(td)
            self.assertTrue(result["pass"])


if __name__ == "__main__":
    unittest.main()
