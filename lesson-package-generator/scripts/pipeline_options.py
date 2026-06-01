"""Runtime options for orchestrator — supplementary flags and human gates."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunSupplementary:
    teaching: bool = False
    praise: bool = False
    promo: bool = False

    def any_enabled(self) -> bool:
        return self.teaching or self.praise or self.promo


@dataclass
class PipelineOptions:
    """Control non-interactive vs human-gated execution."""

    run_supplementary: RunSupplementary = field(default_factory=RunSupplementary)
    skip_human_gates: bool = False
    auto_approve: bool = False

    def gates_bypassed(self) -> bool:
        return self.skip_human_gates or self.auto_approve
