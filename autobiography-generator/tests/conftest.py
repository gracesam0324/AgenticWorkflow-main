"""Shared fixtures for all autobiography-generator tests.

Fixtures create data IN MEMORY -- no file I/O for unit tests.
Integration tests that need files use tmp_path (built-in pytest fixture).
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest
import yaml


# ──────────────────────────────────────────────
# Raw data factories (dicts, not models)
# These return plain dicts so tests can mutate them
# to create invalid states for negative testing.
# ──────────────────────────────────────────────


@pytest.fixture
def valid_character_data() -> dict[str, Any]:
    """Minimal valid character entry."""
    return {
        "name": "Kim Minjun",
        "aliases": ["MJ", "Professor Kim"],
        "relationship": "mentor",
        "first_appearance_session": "INT-001",
        "description": "University professor who guided the subject's career",
        "years_active": [1995, 1996, 1997, 1998],
    }


@pytest.fixture
def valid_location_data() -> dict[str, Any]:
    """Minimal valid location entry."""
    return {
        "name": "Seoul National University",
        "city": "Seoul",
        "country": "South Korea",
        "years_relevant": [1995, 1996, 1997, 1998],
        "significance": "Where the subject studied computer science",
    }


@pytest.fixture
def valid_event_data() -> dict[str, Any]:
    """Minimal valid event entry."""
    return {
        "description": "Graduated from Seoul National University with honors",
        "date_approximate": "Spring 1998",
        "significance": "milestone",
        "interview_refs": ["INT-001", "INT-003"],
        "characters_involved": ["Kim Minjun"],
    }


@pytest.fixture
def valid_story_bible_data(
    valid_character_data: dict[str, Any],
    valid_location_data: dict[str, Any],
    valid_event_data: dict[str, Any],
) -> dict[str, Any]:
    """Complete valid story bible."""
    return {
        "version": "1.0.0",
        "subject_name": "Park Jihoon",
        "characters": [valid_character_data],
        "locations": [valid_location_data],
        "events": [valid_event_data],
        "timeline_start_year": 1975,
        "timeline_end_year": 2025,
        "last_updated": "2026-03-15",
        "source_sessions": ["INT-001", "INT-002", "INT-003"],
    }


@pytest.fixture
def valid_chapter_section_data() -> dict[str, Any]:
    """Minimal valid chapter section."""
    return {
        "heading": "The First Day",
        "content": "I remember walking through the gates of Seoul National University for the first time.",
        "interview_refs": ["INT-001/SEG-001", "INT-001/SEG-002"],
        "emotional_tone": "reflective",
    }


@pytest.fixture
def valid_chapter_draft_data(
    valid_chapter_section_data: dict[str, Any],
) -> dict[str, Any]:
    """Complete valid chapter draft."""
    return {
        "chapter_number": 1,
        "title": "The Seoul Years",
        "version": 1,
        "status": "first-draft",
        "word_count": 4200,
        "target_word_count": 4000,
        "sections": [valid_chapter_section_data],
        "interview_refs_used": ["INT-001", "INT-002"],
        "characters_appearing": ["Park Jihoon", "Kim Minjun"],
        "locations": ["Seoul National University"],
        "time_period": {"start": 1995, "end": 1998},
        "emotional_arc": "reflective -> tense -> hopeful",
        "open_threads": ["Professor Kim's influence continues in Chapter 2"],
        "created_at": "2026-03-15T10:30:00",
        "story_bible_version": "1.0.0",
    }


@pytest.fixture
def valid_step_record_data() -> dict[str, Any]:
    """Minimal valid step record."""
    return {
        "step_number": 1,
        "name": "Interview Ingestion",
        "status": "completed",
        "agent": "transcript-parser",
        "started_at": "2026-03-15T09:00:00",
        "completed_at": "2026-03-15T09:15:00",
        "output_files": ["outputs/interviews/INT-001.json"],
        "pacs_score": 85,
        "error_message": "",
        "retry_count": 0,
    }


@pytest.fixture
def valid_state_file_data() -> dict[str, Any]:
    """Complete valid state file with 3 steps."""
    return {
        "project_name": "park-jihoon-autobiography",
        "workflow_version": "1.0.0",
        "current_step": 1,
        "total_steps": 3,
        "status": "in-progress",
        "steps": [
            {
                "step_number": 1,
                "name": "Interview Ingestion",
                "status": "completed",
                "agent": "transcript-parser",
                "started_at": "2026-03-15T09:00:00",
                "completed_at": "2026-03-15T09:15:00",
                "output_files": ["outputs/interviews/INT-001.json"],
                "pacs_score": 85,
                "error_message": "",
                "retry_count": 0,
            },
            {
                "step_number": 2,
                "name": "Story Bible Compilation",
                "status": "in-progress",
                "agent": "story-bible-compiler",
                "started_at": "2026-03-15T09:16:00",
                "completed_at": None,
                "output_files": [],
                "pacs_score": None,
                "error_message": "",
                "retry_count": 0,
            },
            {
                "step_number": 3,
                "name": "Chapter Writing",
                "status": "pending",
                "agent": "",
                "started_at": None,
                "completed_at": None,
                "output_files": [],
                "pacs_score": None,
                "error_message": "",
                "retry_count": 0,
            },
        ],
        "story_bible_path": "outputs/story-bible/bible-v1.yaml",
        "output_dir": "outputs/",
        "created_at": "2026-03-15T08:00:00",
        "last_modified": "2026-03-15T09:16:00",
        "error_log": [],
    }


# ──────────────────────────────────────────────
# File-based fixtures (for integration tests)
# ──────────────────────────────────────────────


@pytest.fixture
def story_bible_yaml_file(
    tmp_path: Any,
    valid_story_bible_data: dict[str, Any],
) -> Any:
    """Write a valid story bible YAML to a temp file. Returns path."""
    filepath = tmp_path / "story-bible.yaml"
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(valid_story_bible_data, f, default_flow_style=False, allow_unicode=True)
    return filepath


@pytest.fixture
def state_file_yaml(
    tmp_path: Any,
    valid_state_file_data: dict[str, Any],
) -> Any:
    """Write a valid state file YAML to a temp file. Returns path."""
    filepath = tmp_path / "state.yaml"
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(valid_state_file_data, f, default_flow_style=False, allow_unicode=True)
    return filepath


@pytest.fixture
def empty_yaml_file(tmp_path: Any) -> Any:
    """Write an empty YAML file. Returns path."""
    filepath = tmp_path / "empty.yaml"
    filepath.write_text("")
    return filepath


@pytest.fixture
def invalid_yaml_file(tmp_path: Any) -> Any:
    """Write invalid YAML to a temp file. Returns path."""
    filepath = tmp_path / "invalid.yaml"
    filepath.write_text("{ this is not: valid: yaml: [")
    return filepath


# ──────────────────────────────────────────────
# v2.0 Orchestration Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def valid_orchestration_data() -> dict[str, Any]:
    """Minimal valid orchestration section for state.yaml v2.0."""
    return {
        "version": "2.0",
        "current_phase": "build",
        "current_substep": None,
        "teams": {
            "build_team": {"status": "not_started", "teammates": [], "fallback_activated": False},
            "review_deep": {"status": "not_started", "teammates": [], "fallback_activated": False},
        },
        "tasks": {"total": 0, "completed": 0, "failed": 0, "blocked": 0, "items": {}},
        "fallback": {"activations": [], "current_tier": 2},
        "rlm": {
            "last_snapshot": "",
            "knowledge_archive_path": "",
            "session_count": 0,
            "recovery_points": [],
        },
        "translation": {
            "status": "active",
            "glossary_path": "translations/glossary.yaml",
            "glossary_terms_count": 34,
            "total_translations": 0,
            "completed_translations": 0,
            "pacs_history": {},
            "pending_translations": [],
            "pairs": {},
        },
        "error_log": [],
    }


@pytest.fixture
def valid_state_v2_data(valid_orchestration_data: dict[str, Any]) -> dict[str, Any]:
    """Complete valid state.yaml v2.0 with workflow + orchestration."""
    return {
        "workflow": {
            "name": "AI Autobiography Generator",
            "current_step": 1,
            "status": "not_started",
            "parent_genome": {
                "source": "AgenticWorkflow",
                "version": "2026-03-17",
                "inherited_dna": [
                    "absolute-criteria", "sot-pattern", "3-phase-structure",
                    "4-layer-qa", "safety-hooks", "adversarial-review",
                    "decision-log", "context-preservation",
                ],
            },
            "book_config": {
                "subject_name": "Test Subject",
                "total_chapters": 12,
                "target_word_count": 50000,
                "narrative_voice": "first-person-past",
                "language": "ko",
            },
            "outputs": {},
            "chapters": {},
            "interviews": {
                "total_sessions": 8,
                "completed_sessions": 0,
                "status": "not_started",
                "sessions": [],
            },
            "story_bible": {
                "path": "story-bible/bible.json",
                "status": "not_started",
                "validation": {"passed": False, "checks": []},
            },
            "pending_human_action": {"step": None, "options": []},
            "pacs": {
                "current_step_score": 0,
                "dimensions": {"F": 0, "C": 0, "L": 0},
                "weak_dimension": None,
                "history": {},
            },
            "verification": {"last_verified_step": 0, "retries": {}},
            "build": {
                "last_build_date": None,
                "pdf_path": None,
                "epub_path": None,
                "build_status": "not_started",
            },
            "autopilot": {
                "enabled": False,
                "decision_log_dir": "autopilot-logs/",
                "auto_approved_steps": [],
            },
        },
        "orchestration": valid_orchestration_data,
    }


@pytest.fixture
def state_v2_yaml_file(
    tmp_path: Any,
    valid_state_v2_data: dict[str, Any],
) -> Any:
    """Write a valid v2.0 state file to a temp file. Returns path."""
    filepath = tmp_path / ".claude" / "state.yaml"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(valid_state_v2_data, f, default_flow_style=False, allow_unicode=True)
    return filepath


@pytest.fixture
def project_dir_with_state(tmp_path: Any, valid_state_v2_data: dict[str, Any]) -> Any:
    """Create a temporary project directory with state.yaml v2.0. Returns project root."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    state_path = claude_dir / "state.yaml"
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(valid_state_v2_data, f, default_flow_style=False, allow_unicode=True)

    # Create minimal directory structure
    (tmp_path / "schemas").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()

    return tmp_path


@pytest.fixture
def sample_korean_chapter_text() -> str:
    """Sample Korean chapter text for validator testing."""
    return """어머니는 항상 이른 새벽에 일어나셨다. 아버지가 출근하시기 전에 밥상을 차려야 했으니까.
그때는 몰랐지만, 그 새벽 부엌의 불빛이 우리 가족의 등대 같은 것이었다.

서울역에서 기차를 타고 고향으로 향할 때면, 창밖으로 스쳐가는 풍경이 어린 시절의 기억과 겹쳤다.
논 사이로 난 좁은 길, 여름이면 미꾸라지를 잡던 개울, 할머니 댁 뒤편의 대나무 숲.

"엄마, 나 서울 가서도 잘 할 수 있을까?"
어머니는 대답 대신 내 손을 꼭 잡으셨다. 그 손의 온기가 아직도 기억난다.

[INFERRED] 기차역은 아마 1970년대 후반의 전형적인 시골 간이역이었을 것이다.
"""


@pytest.fixture
def emotion_keywords_config(tmp_path: Any) -> Any:
    """Create a minimal emotion-keywords.yaml for testing. Returns path."""
    config = {
        "han": {"keywords": ["그리움", "아픔", "슬픔", "눈물"], "weight": 1.0},
        "heung": {"keywords": ["기쁨", "웃음", "즐거움", "신나"], "weight": 1.0},
        "jeong": {"keywords": ["정", "사랑", "따뜻", "다정"], "weight": 1.0},
    }
    filepath = tmp_path / "emotion-keywords.yaml"
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    return filepath
