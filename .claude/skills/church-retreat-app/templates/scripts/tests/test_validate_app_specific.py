#!/usr/bin/env python3
"""Tests for validate_app_specific.py — app-type-specific gates."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_app_specific import (
    check_quiz_ws_routing, check_score_admin_screen,
    check_lyrics_sync, check_static_app,
)


class TestQuizWsRouting(unittest.TestCase):
    """Quiz: WebSocket message type routing."""

    def test_routing_with_types_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "server.js"), "w") as f:
                f.write("""
                if (data.type === 'buzzer') { handleBuzzer(data); }
                if (data.type === 'answer') { handleAnswer(data); }
                if (data.type === 'reset') { handleReset(data); }
                """)
            result = check_quiz_ws_routing(td)
            self.assertTrue(result["ws_routing"]["pass"])

    def test_no_routing_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "server.js"), "w") as f:
                f.write("console.log('no routing');")
            result = check_quiz_ws_routing(td)
            self.assertFalse(result["ws_routing"]["pass"])

    def test_single_type_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "server.js"), "w") as f:
                f.write("if (data.type === 'buzzer') { handle(); }")
            result = check_quiz_ws_routing(td)
            self.assertFalse(result["ws_routing"]["pass"])


class TestScoreAdminScreen(unittest.TestCase):
    """Score: admin update + broadcast to screen."""

    def test_score_flow_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "server.js"), "w") as f:
                f.write("""
                function updateScore(team, points) {
                    scores[team] += points;
                    clients.forEach(client => client.send(JSON.stringify(scores)));
                }
                """)
            result = check_score_admin_screen(td)
            self.assertTrue(result["admin_to_screen"]["pass"])

    def test_no_broadcast_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "server.js"), "w") as f:
                f.write("function updateScore(team, points) { scores[team] += points; }")
            result = check_score_admin_screen(td)
            self.assertFalse(result["admin_to_screen"]["pass"])


class TestLyricsSync(unittest.TestCase):
    """Lyrics: sync mechanism."""

    def test_sync_present_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "server.js"), "w") as f:
                f.write("""
                let currentSong = 0;
                function changeSong(idx) {
                    currentSong = idx;
                    clients.forEach(c => c.send(JSON.stringify({song: currentSong})));
                }
                """)
            result = check_lyrics_sync(td)
            self.assertTrue(result["lyrics_sync"]["pass"])


class TestStaticApp(unittest.TestCase):
    """Static apps (schedule, QT, etc.)."""

    def test_html_content_passes(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "index.html"), "w") as f:
                f.write("<html><body>" + "x" * 200 + "</body></html>")
            result = check_static_app(td)
            self.assertTrue(result["static_content"]["pass"])

    def test_empty_project_fails(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_static_app(td)
            self.assertFalse(result["static_content"]["pass"])


if __name__ == "__main__":
    unittest.main()
