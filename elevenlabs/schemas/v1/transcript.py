"""Public API transcript schemas: unified segment format with timing validation.

These models define the request contract for the create-call public API so that
all voice-agent providers send a consistent, timestamped transcript. Validation
ensures user/agent segments include at least one timing source for voice metrics.
"""

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _ceil_ms(value: int | float) -> int:
    """Accept ms as int or float; return int (ceiling) for consistent storage."""
    if isinstance(value, int):
        return value
    return math.ceil(value)


# Roles that require timing for voice metrics (user/agent speech).
_ROLES_REQUIRING_TIMING: frozenset[str] = frozenset({"user", "agent"})

# Allowed values for segment role (documented in create-call API description).
PublicTranscriptRole = Literal[
    "node_transition",
    "user",
    "agent",
    "agent_function",
    "agent_result",
]


class PublicTranscriptWord(BaseModel):
    """Word-level timing; preferred when available for accurate metrics."""

    word: str = Field(..., description="The word text")
    start_ms: int = Field(
        ...,
        description="Start time relative to call start (ms); accepts int or float, stored as int (ceiling)",
    )
    end_ms: int = Field(
        ...,
        description="End time relative to call start (ms); accepts int or float, stored as int (ceiling)",
    )
    confidence: float | None = Field(None, description="Optional confidence score")

    @model_validator(mode="before")
    @classmethod
    def _ceil_word_timing(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for key in ("start_ms", "end_ms"):
            v = data.get(key)
            if v is not None and isinstance(v, float):
                data = {**data, key: _ceil_ms(v)}
        return data


class PublicTranscriptNode(BaseModel):
    """Workflow node transition; only for role='node_transition'."""

    from_node: str = Field(..., alias="from", description="Source node id")
    to: str = Field(..., description="Target node id")
    reason: str | None = Field(None, description="Transition reason (e.g. 'workflow route')")

    model_config = ConfigDict(populate_by_name=True)


class PublicTranscriptTool(BaseModel):
    """Tool call info; for role='agent_function' (params set) and 'agent_result' (result set)."""

    name: str | None = Field(None, description="Tool name")
    request_id: str | None = Field(None, description="Request id")
    params: dict[str, Any] | None = Field(None, description="Tool input parameters (JSON).")
    result: dict[str, Any] | None = Field(None, description="Tool output payload (JSON).")
    is_error: bool | None = Field(
        None, description="Whether the tool execution resulted in an error."
    )
    error: str | None = Field(None, description="Error message returned by the tool.")


class PublicTranscriptSegment(BaseModel):
    """Single transcript segment: unified shape for all providers.

    For role in ('user', 'agent') at least one timing source is required:
    - words (non-empty with start_ms/end_ms), or
    - start_ms + end_ms, or
    - start_ms + duration_ms (end_ms is then derived).
    """

    role: PublicTranscriptRole = Field(
        ...,
        description="Defines the type of segment in the call timeline. Allowed: node_transition, user, agent, agent_function, agent_result",
    )
    text: str | None = Field(
        None,
        description="Utterance text for user or agent messages.",
    )
    words: list[PublicTranscriptWord] | None = Field(
        None,
        description="Word-level timing data (recommended when available).",
    )
    start_ms: int | None = Field(
        None,
        description="Segment start time relative to call start (ms); accepts int or float, stored as int (ceiling).",
    )
    end_ms: int | None = Field(
        None,
        description="Segment end time relative to call start (ms); accepts int or float, stored as int (ceiling).",
    )
    duration_ms: int | None = Field(
        None,
        description="Utterance duration (ms); accepts int or float, stored as int (ceiling). Should equal end_ms - start_ms if both set.",
    )
    node: PublicTranscriptNode | None = Field(
        None,
        description="Workflow transition details (used for node_transition).",
    )
    tool: PublicTranscriptTool | None = Field(
        None,
        description="Tool invocation or result details (used for agent_function and agent_result).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific or extra fields",
    )

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _ceil_segment_timing(cls, data: Any) -> Any:
        """Accept int or float for ms fields; coerce to int (ceiling) for storage."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for key in ("start_ms", "end_ms", "duration_ms"):
            v = out.get(key)
            if v is not None and isinstance(v, float):
                out[key] = _ceil_ms(v)
        return out

    @model_validator(mode="after")
    def _require_timing_for_speech_roles(self) -> "PublicTranscriptSegment":
        """Ensure user/agent segments have at least one valid timing source."""
        if self.role not in _ROLES_REQUIRING_TIMING:
            return self

        has_words_timing = bool(self.words and len(self.words) > 0)
        has_utterance_timing = self.start_ms is not None and self.end_ms is not None
        has_start_and_duration = self.start_ms is not None and self.duration_ms is not None

        if has_words_timing or has_utterance_timing or has_start_and_duration:
            return self

        raise ValueError(
            f"Segment with role='{self.role}' must include timing: "
            "non-empty 'words' with start_ms/end_ms, or 'start_ms' and 'end_ms', "
            "or 'start_ms' and 'duration_ms'"
        )

    @model_validator(mode="after")
    def _derive_end_ms_from_duration(self) -> "PublicTranscriptSegment":
        """Set end_ms from start_ms + duration_ms when only those two are provided."""
        if self.start_ms is not None and self.duration_ms is not None and self.end_ms is None:
            return self.model_copy(
                update={"end_ms": self.start_ms + self.duration_ms},
                deep=False,
            )
        return self
