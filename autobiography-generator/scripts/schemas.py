"""Pydantic v2 schemas for the AI Autobiography Generator pipeline.

Every data structure that crosses an agent boundary or gets persisted to disk
has a schema here. Load with `Model.model_validate(data)` or use the
convenience functions `load_yaml()` / `save_yaml()` at the bottom.

Usage:
    from scripts.schemas import StoryBibleEntry, ChapterDraft, StateFile
    entry = StoryBibleEntry.model_validate(yaml.safe_load(open("story.yaml")))
"""

from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ──────────────────────────────────────────────
# Enums — shared across schemas
# ──────────────────────────────────────────────

class EntryKind(str, Enum):
    """Kind of story bible entry."""

    CHARACTER = "character"
    LOCATION = "location"
    EVENT = "event"


class EventSignificance(str, Enum):
    """How significant an event is to the narrative."""

    TURNING_POINT = "turning-point"
    MILESTONE = "milestone"
    BACKGROUND = "background"
    ANECDOTE = "anecdote"


class EmotionalTone(str, Enum):
    """Dominant emotional tone for a scene or chapter."""

    REFLECTIVE = "reflective"
    JOYFUL = "joyful"
    MELANCHOLIC = "melancholic"
    NEUTRAL = "neutral"
    INTENSE = "intense"
    HUMOROUS = "humorous"
    BITTERSWEET = "bittersweet"


class ChapterStatus(str, Enum):
    """Lifecycle status of a chapter draft."""

    OUTLINE = "outline"
    FIRST_DRAFT = "first-draft"
    REVISED = "revised"
    REVIEWED = "reviewed"
    FINAL = "final"


class StepStatus(str, Enum):
    """Status of a pipeline step."""

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ──────────────────────────────────────────────
# Story Bible Schemas
# ──────────────────────────────────────────────

class CharacterEntry(BaseModel):
    """A person appearing in the autobiography."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, description="Full name as used in the narrative")
    aliases: list[str] = Field(default_factory=list, description="Nicknames, maiden names, etc.")
    relationship: str = Field(min_length=1, description="Relationship to the subject")
    first_appearance_session: str | None = Field(
        default=None,
        pattern=r"^INT-\d{3}$",
        description="Interview session where this person first appears",
    )
    description: str = Field(
        default="",
        description="Physical appearance, personality traits, role in subject's life",
    )
    years_active: list[int] = Field(
        default_factory=list,
        description="Years when this person was relevant to the narrative",
    )

    @field_validator("name")
    @classmethod
    def name_not_whitespace(cls, v: str) -> str:
        """Reject names that are only whitespace."""
        if not v.strip():
            msg = "Character name cannot be blank or whitespace-only"
            raise ValueError(msg)
        return v.strip()


class LocationEntry(BaseModel):
    """A place appearing in the autobiography."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    city: str = Field(default="")
    country: str = Field(default="")
    years_relevant: list[int] = Field(default_factory=list)
    significance: str = Field(
        default="",
        description="Why this place matters to the subject's story",
    )


class EventEntry(BaseModel):
    """A notable event in the autobiography timeline."""

    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=5)
    date_approximate: str = Field(
        default="",
        description="Human-readable date, e.g. 'Summer 1998' or '2003-09-15'",
    )
    significance: EventSignificance = Field(default=EventSignificance.BACKGROUND)
    interview_refs: list[str] = Field(
        default_factory=list,
        description="INT-### sessions that mention this event",
    )
    characters_involved: list[str] = Field(
        default_factory=list,
        description="Names of characters involved (must match CharacterEntry.name)",
    )


class StoryBibleEntry(BaseModel):
    """Top-level story bible container.

    A story bible is the single source of truth for all characters,
    locations, and events in the autobiography. It is built from
    interview transcripts and maintained across the pipeline.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    version: str = Field(pattern=r"^\d+\.\d+\.\d+$", description="Semver version")
    subject_name: str = Field(min_length=1)
    characters: list[CharacterEntry] = Field(default_factory=list)
    locations: list[LocationEntry] = Field(default_factory=list)
    events: list[EventEntry] = Field(default_factory=list)
    timeline_start_year: int = Field(ge=1900, le=2100)
    timeline_end_year: int = Field(ge=1900, le=2100)
    last_updated: datetime.date = Field(default_factory=datetime.date.today)
    source_sessions: list[str] = Field(
        default_factory=list,
        description="List of INT-### sessions incorporated into this bible",
    )

    @model_validator(mode="after")
    def timeline_order(self) -> StoryBibleEntry:
        """Ensure start year is not after end year."""
        if self.timeline_start_year > self.timeline_end_year:
            msg = (
                f"timeline_start_year ({self.timeline_start_year}) must be "
                f"<= timeline_end_year ({self.timeline_end_year})"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def character_names_unique(self) -> StoryBibleEntry:
        """Ensure no duplicate character names."""
        names = [c.name for c in self.characters]
        dupes = [n for n in names if names.count(n) > 1]
        if dupes:
            msg = f"Duplicate character names: {set(dupes)}"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def event_characters_exist(self) -> StoryBibleEntry:
        """Ensure every character referenced in events exists in characters list."""
        known_names = {c.name for c in self.characters}
        known_aliases = {alias for c in self.characters for alias in c.aliases}
        all_known = known_names | known_aliases
        for event in self.events:
            for char_name in event.characters_involved:
                if char_name not in all_known:
                    msg = (
                        f"Event '{event.description}' references character "
                        f"'{char_name}' not found in characters list"
                    )
                    raise ValueError(msg)
        return self


# ──────────────────────────────────────────────
# Chapter Draft Schema
# ──────────────────────────────────────────────

class ChapterSection(BaseModel):
    """One section within a chapter draft."""

    heading: str = Field(min_length=1)
    content: str = Field(min_length=1)
    interview_refs: list[str] = Field(
        default_factory=list,
        description="INT-###/SEG-### references used in this section",
    )
    emotional_tone: EmotionalTone = Field(default=EmotionalTone.NEUTRAL)


class ChapterDraft(BaseModel):
    """A chapter draft with full metadata.

    This is the output of the chapter-writer agent. Every chapter
    must have traceable sources and measurable quality metrics.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    chapter_number: int = Field(ge=1, le=100)
    title: str = Field(min_length=1, max_length=200)
    version: int = Field(ge=1, description="Draft version, starts at 1")
    status: ChapterStatus = Field(default=ChapterStatus.FIRST_DRAFT)
    word_count: int = Field(ge=0)
    target_word_count: int = Field(ge=100)
    sections: list[ChapterSection] = Field(min_length=1)
    interview_refs_used: list[str] = Field(
        min_length=1,
        description="All INT-### sessions referenced in this chapter",
    )
    characters_appearing: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    time_period: dict[str, int] = Field(
        description="{'start': YYYY, 'end': YYYY}",
    )
    emotional_arc: str = Field(
        default="",
        description="e.g. 'reflective -> tense -> hopeful'",
    )
    open_threads: list[str] = Field(
        default_factory=list,
        description="Narrative threads to be continued in later chapters",
    )
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    story_bible_version: str = Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Version of story bible used during generation",
    )

    @model_validator(mode="after")
    def word_count_within_range(self) -> ChapterDraft:
        """Warn if word count is more than 20% off target."""
        if self.target_word_count > 0:
            deviation = abs(self.word_count - self.target_word_count) / self.target_word_count
            if deviation > 0.20:
                msg = (
                    f"Word count {self.word_count} deviates {deviation:.0%} from "
                    f"target {self.target_word_count} (max allowed: 20%)"
                )
                raise ValueError(msg)
        return self

    @field_validator("time_period")
    @classmethod
    def time_period_valid(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate time_period has start and end keys with valid years."""
        if "start" not in v or "end" not in v:
            msg = "time_period must have 'start' and 'end' keys"
            raise ValueError(msg)
        if v["start"] > v["end"]:
            msg = f"time_period start ({v['start']}) must be <= end ({v['end']})"
            raise ValueError(msg)
        return v

    @field_validator("interview_refs_used")
    @classmethod
    def interview_refs_format(cls, v: list[str]) -> list[str]:
        """Validate all interview refs match INT-### pattern."""
        import re

        pattern = re.compile(r"^INT-\d{3}$")
        for ref in v:
            if not pattern.match(ref):
                msg = f"Invalid interview ref '{ref}', must match INT-### pattern"
                raise ValueError(msg)
        return v


# ──────────────────────────────────────────────
# State File Schema (Pipeline State)
# ──────────────────────────────────────────────

class StepRecord(BaseModel):
    """Record of a single pipeline step execution."""

    step_number: int = Field(ge=1)
    name: str = Field(min_length=1)
    status: StepStatus = Field(default=StepStatus.PENDING)
    agent: str = Field(default="", description="Agent name that executed this step")
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    output_files: list[str] = Field(default_factory=list)
    pacs_score: int | None = Field(default=None, ge=0, le=100)
    error_message: str = Field(default="")
    retry_count: int = Field(default=0, ge=0, le=3)

    @model_validator(mode="after")
    def completed_requires_start(self) -> StepRecord:
        """A step cannot complete before it starts."""
        if self.completed_at and not self.started_at:
            msg = "Step has completed_at but no started_at"
            raise ValueError(msg)
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            msg = "completed_at cannot be before started_at"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def failed_requires_error(self) -> StepRecord:
        """A failed step must have an error message."""
        if self.status == StepStatus.FAILED and not self.error_message:
            msg = "Failed steps must have an error_message"
            raise ValueError(msg)
        return self


class StateFile(BaseModel):
    """Pipeline state file -- the SOT for pipeline progress.

    Only the Orchestrator writes to this file. All other agents
    read it to understand where the pipeline currently is.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    project_name: str = Field(min_length=1)
    workflow_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    current_step: int = Field(ge=0, description="0 = not started, 1+ = active step")
    total_steps: int = Field(ge=1)
    status: StepStatus = Field(default=StepStatus.PENDING)
    steps: list[StepRecord] = Field(min_length=1)
    story_bible_path: str = Field(default="")
    output_dir: str = Field(default="outputs/")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_modified: datetime.datetime = Field(default_factory=datetime.datetime.now)
    error_log: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def current_step_in_range(self) -> StateFile:
        """Current step must not exceed total steps."""
        if self.current_step > self.total_steps:
            msg = (
                f"current_step ({self.current_step}) exceeds "
                f"total_steps ({self.total_steps})"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def steps_count_matches(self) -> StateFile:
        """Number of step records must match total_steps."""
        if len(self.steps) != self.total_steps:
            msg = (
                f"steps list has {len(self.steps)} entries but "
                f"total_steps is {self.total_steps}"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def steps_sequential(self) -> StateFile:
        """Step numbers must be sequential starting from 1."""
        for i, step in enumerate(self.steps, start=1):
            if step.step_number != i:
                msg = f"Step at index {i - 1} has step_number {step.step_number}, expected {i}"
                raise ValueError(msg)
        return self

    def advance_to(self, step_number: int) -> None:
        """Move pipeline to a specific step (validates transitions)."""
        if step_number < 1 or step_number > self.total_steps:
            msg = f"Step {step_number} out of range [1, {self.total_steps}]"
            raise ValueError(msg)
        if step_number > 1:
            prev = self.steps[step_number - 2]
            if prev.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED):
                msg = (
                    f"Cannot advance to step {step_number}: "
                    f"previous step '{prev.name}' is {prev.status.value}"
                )
                raise ValueError(msg)
        self.current_step = step_number
        self.steps[step_number - 1].status = StepStatus.IN_PROGRESS
        self.steps[step_number - 1].started_at = datetime.datetime.now()
        self.status = StepStatus.IN_PROGRESS
        self.last_modified = datetime.datetime.now()


# ──────────────────────────────────────────────
# State File v2.0 Schema (Orchestration Layer)
# Additive-only: preserves all v1.0 fields
# ──────────────────────────────────────────────


class FallbackActivation(BaseModel):
    """Record of a single fallback tier degradation event."""

    step: str = Field(description="Step where fallback was triggered")
    from_tier: int = Field(ge=1, le=4)
    to_tier: int = Field(ge=1, le=4)
    reason: str = Field(default="")
    timestamp: str = Field(default="")


class RLMRecoveryPoint(BaseModel):
    """RLM recovery checkpoint for session resume."""

    step: str = Field(description="Workflow step at checkpoint")
    substep: str | None = Field(default=None, description="Sub-step for chapter loop resume")
    snapshot_path: str = Field(default="")
    timestamp: str = Field(default="")


class TranslationPacsRecord(BaseModel):
    """Translation quality score record."""

    Ft: int = Field(default=0, ge=0, le=100, description="Fidelity score")
    Ct: int = Field(default=0, ge=0, le=100, description="Completeness score")
    Nt: int = Field(default=0, ge=0, le=100, description="Naturalness score")
    min_score: int = Field(default=0, ge=0, le=100, description="Minimum of Ft, Ct, Nt")
    grade: str = Field(default="", description="GREEN/YELLOW/RED")


class OrchestrationSection(BaseModel):
    """v2.0 orchestration layer — additive section in state.yaml."""

    model_config = ConfigDict(str_strip_whitespace=True)

    version: str = Field(default="2.0")
    current_phase: str = Field(
        default="build",
        description="build | research | planning | implementation | export | complete",
    )
    current_substep: str | None = Field(
        default=None,
        description="7a|7b|7c|7d|7e|7f for chapter loop resume",
    )
    teams: dict[str, Any] = Field(default_factory=dict)
    tasks: dict[str, Any] = Field(default_factory=lambda: {
        "total": 0, "completed": 0, "failed": 0, "blocked": 0, "items": {},
    })
    fallback: dict[str, Any] = Field(default_factory=lambda: {
        "activations": [], "current_tier": 2,
    })
    rlm: dict[str, Any] = Field(default_factory=lambda: {
        "last_snapshot": "", "knowledge_archive_path": "",
        "session_count": 0, "recovery_points": [],
    })
    translation: dict[str, Any] = Field(default_factory=lambda: {
        "status": "active", "glossary_path": "translations/glossary.yaml",
        "glossary_terms_count": 34, "total_translations": 0,
        "completed_translations": 0, "pacs_history": {},
        "pending_translations": [], "pairs": {},
    })
    error_log: list[dict[str, Any]] = Field(default_factory=list)


class StateFileV2(BaseModel):
    """Pipeline state file v2.0 — the SOT for orchestrated pipeline.

    Extends v1.0 with an additive orchestration section.
    All v1.0 fields are preserved byte-for-byte.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    workflow: dict[str, Any] = Field(description="v1.0 workflow section — preserved as-is")
    orchestration: OrchestrationSection = Field(
        default_factory=OrchestrationSection,
        description="v2.0 additive orchestration layer",
    )

    @model_validator(mode="after")
    def workflow_has_required_keys(self) -> StateFileV2:
        """Verify v1.0 workflow section has required keys."""
        required = {"name", "current_step", "status", "parent_genome", "outputs", "book_config"}
        missing = required - set(self.workflow.keys())
        if missing:
            msg = f"workflow section missing required keys: {missing}"
            raise ValueError(msg)
        return self


# ──────────────────────────────────────────────
# I/O Helpers
# ──────────────────────────────────────────────

def load_yaml(path: str | Path, model: type[BaseModel]) -> BaseModel:
    """Load a YAML file and validate against a Pydantic model.

    Args:
        path: Path to the YAML file.
        model: Pydantic model class to validate against.

    Returns:
        Validated model instance.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
        pydantic.ValidationError: If the data does not match the schema.
    """
    filepath = Path(path)
    if not filepath.exists():
        msg = f"File not found: {filepath}"
        raise FileNotFoundError(msg)

    with filepath.open("r", encoding="utf-8") as f:
        data: Any = yaml.safe_load(f)

    if data is None:
        msg = f"File is empty: {filepath}"
        raise ValueError(msg)

    return model.model_validate(data)


def save_yaml(path: str | Path, model_instance: BaseModel) -> Path:
    """Save a Pydantic model instance to a YAML file.

    Args:
        path: Path to write the YAML file.
        model_instance: Validated Pydantic model instance.

    Returns:
        Path to the written file.
    """
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data = model_instance.model_dump(mode="json")

    with filepath.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return filepath
