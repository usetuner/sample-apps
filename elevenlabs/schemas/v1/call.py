"""Call log schemas for API responses."""

from typing import Any

from pydantic import BaseModel, Field

from schemas.v1.transcript import PublicTranscriptSegment

class CreateCallRequest(BaseModel):
    """Request schema for public call creation."""

    call_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Unique call identifier from your provider (used for idempotency).",
    )
    call_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Call channel/type from your provider (e.g., 'phone_call', 'web_call').",
    )
    # agent_id: str = Field(..., description="Agent ID shown in the Agent Settings page")
    transcript_with_tool_calls: list[PublicTranscriptSegment] = Field(
        ...,
        min_length=1,
        description='Unified call timeline. Each item represents either a user message, agent message, node transition, or a tool event. Include timing either as word-level ("words") or segment-level ("start_ms + end_ms" or "duration_ms")',
    )
    start_timestamp: int = Field(
        ..., description=" Call start time as Unix epoch. Accepts either seconds or milliseconds."
    )
    end_timestamp: int = Field(
        ...,
        description="Call end time as Unix epoch. Accepts either seconds or milliseconds. Must be greater than or equal to start_timestamp.",
    )
    recording_url: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Publicly reachable recording URL (audio file or provider recording link).",
    )

    transcript: str | None = Field(
        None,
        description="Diarized plain-text transcript (fallback for display/search). If omitted, we derive it from transcript_with_tool_calls when possible.",
    )

    duration_ms: int | None = Field(
        None,
        description="Call duration in milliseconds. If omitted, we compute it from start_timestamp and end_timestamp.",
    )
    call_status: str | None = Field(
        None,
        max_length=100,
        description="Provider call status at ingest time. Preferred values: 'call_ended'.",
    )
    disconnection_reason: str | None = Field(
        None, max_length=100, description="Why the call ended (e.g. user_hangup, agent_hangup)."
    )
    caller_phone_number: str | None = Field(
        None,
        max_length=50,
        description="Caller phone number in E.164 format when available (e.g., '+14155550123').",
    )
    call_successful: bool | None = Field(None, description="Whether the call was successful")
    user_sentiment: str | None = Field(
        None,
        max_length=50,
        description="User sentiment label. Must be one of [positive, neutral, negative, unknown]",
    )
    in_voicemail: bool | None = Field(None, description="Whether the call reached voicemail")
    collected_dynamic_variables: dict[str, Any] | None = Field(
        None, description="Dynamic variables collected during the call (free-form JSON)"
    )
    call_cost: float | None = Field(
        None, description="Total call cost in USD as a decimal amount (e.g., 1.25 for $1.25)."
    )
    call_analysis: dict[str, Any] | None = Field(
        None, description="Provider-native analysis payload (free-form JSON; stored as-is)"
    )
    # llm_token_usage: dict[str, Any] | None = Field(None, description="LLM token usage")
    general_meta_data_raw: dict[str, Any] | None = Field(
        None, description="Use to store any extra metadata payload as a JSON object"
    )
    recording_multi_channel_url: str | None = Field(
        None,
        max_length=1024,
        description="Multi-channel recording URL (separate speaker channels), if available.",
    )


class CreateCallResponse(BaseModel):
    """Response schema for public call creation."""

    id: int = Field(..., description="Internal Tuner call ID")
    provider_call_id: str = Field(
        ..., description="Echo of the provider call ID you sent (call_id)."
    )
    is_new: bool = Field(
        ..., description="Whether the call was newly created (false means it already existed)"
    )