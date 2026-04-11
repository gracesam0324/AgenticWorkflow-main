"""Tests for StateFile schema and pipeline step transitions.

Covers:
- Valid state file construction
- Step sequencing (no gaps, no out-of-order)
- Transition validation (advance_to logic)
- Failed step requires error message
- Step boundary enforcement
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.schemas import StateFile, StepRecord, StepStatus


# ──────────────────────────────────────────────
# StepRecord Tests
# ──────────────────────────────────────────────


class TestStepRecord:
    """Tests for individual step records."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_step_record(self, valid_step_record_data: dict[str, Any]) -> None:
        step = StepRecord.model_validate(valid_step_record_data)
        assert step.step_number == 1
        assert step.status == StepStatus.COMPLETED

    @pytest.mark.unit
    @pytest.mark.schema
    def test_step_pending_no_timestamps(self) -> None:
        step = StepRecord.model_validate({
            "step_number": 1,
            "name": "Interview Ingestion",
            "status": "pending",
        })
        assert step.started_at is None
        assert step.completed_at is None

    @pytest.mark.unit
    @pytest.mark.schema
    def test_step_completed_without_started_rejected(self) -> None:
        with pytest.raises(ValidationError, match="completed_at but no started_at"):
            StepRecord.model_validate({
                "step_number": 1,
                "name": "Interview Ingestion",
                "status": "completed",
                "completed_at": "2026-03-15T09:15:00",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_step_completed_before_started_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cannot be before started_at"):
            StepRecord.model_validate({
                "step_number": 1,
                "name": "Interview Ingestion",
                "status": "completed",
                "started_at": "2026-03-15T10:00:00",
                "completed_at": "2026-03-15T09:00:00",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_failed_step_without_error_message_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must have an error_message"):
            StepRecord.model_validate({
                "step_number": 1,
                "name": "Interview Ingestion",
                "status": "failed",
                "started_at": "2026-03-15T09:00:00",
                "error_message": "",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_failed_step_with_error_message_accepted(self) -> None:
        step = StepRecord.model_validate({
            "step_number": 1,
            "name": "Interview Ingestion",
            "status": "failed",
            "started_at": "2026-03-15T09:00:00",
            "error_message": "Transcript file not found: INT-001.json",
        })
        assert step.status == StepStatus.FAILED
        assert "not found" in step.error_message

    @pytest.mark.unit
    @pytest.mark.schema
    def test_step_pacs_score_boundaries(self) -> None:
        """pACS score must be 0-100."""
        step = StepRecord.model_validate({
            "step_number": 1,
            "name": "Test",
            "pacs_score": 0,
        })
        assert step.pacs_score == 0

        step = StepRecord.model_validate({
            "step_number": 1,
            "name": "Test",
            "pacs_score": 100,
        })
        assert step.pacs_score == 100

        with pytest.raises(ValidationError):
            StepRecord.model_validate({
                "step_number": 1,
                "name": "Test",
                "pacs_score": 101,
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_step_retry_count_max(self) -> None:
        step = StepRecord.model_validate({
            "step_number": 1,
            "name": "Test",
            "retry_count": 3,
        })
        assert step.retry_count == 3

        with pytest.raises(ValidationError):
            StepRecord.model_validate({
                "step_number": 1,
                "name": "Test",
                "retry_count": 4,
            })


# ──────────────────────────────────────────────
# StateFile Tests
# ──────────────────────────────────────────────


class TestStateFile:
    """Tests for the pipeline state file."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_state_file(self, valid_state_file_data: dict[str, Any]) -> None:
        state = StateFile.model_validate(valid_state_file_data)
        assert state.project_name == "park-jihoon-autobiography"
        assert state.total_steps == 3
        assert len(state.steps) == 3

    @pytest.mark.unit
    @pytest.mark.schema
    def test_current_step_exceeds_total_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_state_file_data)
        data["current_step"] = 5
        with pytest.raises(ValidationError, match="exceeds total_steps"):
            StateFile.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_steps_count_mismatch_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_state_file_data)
        data["total_steps"] = 5  # But only 3 steps in list
        with pytest.raises(ValidationError, match="steps list has 3 entries"):
            StateFile.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_steps_not_sequential_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_state_file_data)
        data["steps"][1]["step_number"] = 5  # Gap: 1, 5, 3
        with pytest.raises(ValidationError, match="expected 2"):
            StateFile.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_invalid_workflow_version_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_state_file_data)
        data["workflow_version"] = "latest"
        with pytest.raises(ValidationError):
            StateFile.model_validate(data)


# ──────────────────────────────────────────────
# State Transition Tests (advance_to)
# ──────────────────────────────────────────────


class TestStateTransitions:
    """Tests for pipeline step advancement logic."""

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_to_step_2_from_completed_step_1(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        state = StateFile.model_validate(valid_state_file_data)
        state.advance_to(2)
        assert state.current_step == 2
        assert state.steps[1].status == StepStatus.IN_PROGRESS
        assert state.steps[1].started_at is not None

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_to_step_1_always_allowed(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        """Step 1 has no prerequisites."""
        data = copy.deepcopy(valid_state_file_data)
        # Reset all steps to pending
        for step in data["steps"]:
            step["status"] = "pending"
            step["started_at"] = None
            step["completed_at"] = None
        data["current_step"] = 0
        data["status"] = "pending"
        state = StateFile.model_validate(data)
        state.advance_to(1)
        assert state.current_step == 1

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_to_step_3_without_step_2_completed_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        """Cannot skip to step 3 when step 2 is still in-progress."""
        state = StateFile.model_validate(valid_state_file_data)
        with pytest.raises(ValueError, match="previous step.*is in-progress"):
            state.advance_to(3)

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_past_total_steps_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        state = StateFile.model_validate(valid_state_file_data)
        with pytest.raises(ValueError, match="out of range"):
            state.advance_to(4)

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_to_zero_rejected(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        state = StateFile.model_validate(valid_state_file_data)
        with pytest.raises(ValueError, match="out of range"):
            state.advance_to(0)

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_after_skipped_step_allowed(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        """Skipped steps count as completed for advancement purposes."""
        data = copy.deepcopy(valid_state_file_data)
        data["steps"][1]["status"] = "skipped"
        state = StateFile.model_validate(data)
        state.advance_to(3)
        assert state.current_step == 3

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_advance_updates_last_modified(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        state = StateFile.model_validate(valid_state_file_data)
        old_modified = state.last_modified
        state.advance_to(2)
        assert state.last_modified >= old_modified

    @pytest.mark.unit
    @pytest.mark.pipeline
    def test_full_pipeline_progression(
        self, valid_state_file_data: dict[str, Any]
    ) -> None:
        """Simulate a complete pipeline run: step 1 done, advance 2, complete 2, advance 3."""
        import datetime

        data = copy.deepcopy(valid_state_file_data)
        state = StateFile.model_validate(data)

        # Step 1 is already completed. Advance to step 2.
        state.advance_to(2)
        assert state.steps[1].status == StepStatus.IN_PROGRESS

        # Complete step 2
        state.steps[1].status = StepStatus.COMPLETED
        state.steps[1].completed_at = datetime.datetime.now()
        state.steps[1].pacs_score = 90

        # Advance to step 3
        state.advance_to(3)
        assert state.current_step == 3
        assert state.steps[2].status == StepStatus.IN_PROGRESS
