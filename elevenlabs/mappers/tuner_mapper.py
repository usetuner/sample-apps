from datetime import datetime
from typing import Any

from mappers.elevenlabs_mapper import map_elevenlabs_to_tuner_transcript
from schemas.v1.elevenlabs_conversation import GetConversationWithRecordingUrl
from schemas.v1.call import CreateCallRequest
from schemas.v1.transcript import PublicTranscriptSegment


def _coerce_unix_ms(value: int | float | None) -> int | None:
    if value is None:
        return None
    if value < 10**10:
        return int(value * 1000)
    return int(value)


def transform_conversation_to_tuner_format(
    conversation: GetConversationWithRecordingUrl,
) -> CreateCallRequest:
    """Transform ElevenLabs conversation data to Tuner API format."""
    # Extract conversation ID
    conversation_id = conversation.conversation_id

    transcript_text: str | None = None
    transcript_with_tool_calls: list[PublicTranscriptSegment] = []
    call_status = conversation.status
    call_successful: bool | None = None
    disconnection_reason: str | None = None
    caller_phone: str | None = None
    call_cost: float | None = 0.0
    call_analysis: dict[str, Any] | None = None
    general_meta_data_raw: dict[str, Any] | None = None
    duration_ms: int | None = None
    start_timestamp: int | None = None
    end_timestamp: int | None = None
    call_type = "voice"

    
    metadata = conversation.metadata
    start_timestamp = _coerce_unix_ms(metadata.start_time_unix_secs)
    duration_ms = int(metadata.call_duration_secs * 1000)
    if start_timestamp is not None:
        end_timestamp = start_timestamp + duration_ms
    if conversation.transcript:
        transcript_with_tool_calls = map_elevenlabs_to_tuner_transcript(
            conversation.transcript
        )
    call_analysis = (
        conversation.analysis.model_dump(mode="json", exclude_none=True)
        if conversation.analysis is not None
        else None
    )
    if metadata.phone_call:
        caller_phone = metadata.phone_call.external_number
        call_type = "phone_call"
    disconnection_reason = metadata.termination_reason
    
    if metadata.charging is not None:
        call_cost += metadata.charging.llm_price

    if metadata.call_duration_secs is not None:
        call_cost += (metadata.call_duration_secs / 60) * 0.1  # Example: $0.10 per minute of call time
        
    general_meta_data_raw = metadata.model_dump(mode="json", exclude_none=True)


    if transcript_text and not transcript_with_tool_calls:
        transcript_with_tool_calls = [
            PublicTranscriptSegment(
                role="agent",
                text=transcript_text,
                start_ms=0,
                end_ms=duration_ms or 1000,
                metadata={},
            )
        ]

    # Ensure at least one segment exists (required by API)
    if not transcript_with_tool_calls:
        transcript_with_tool_calls = [
            PublicTranscriptSegment(
                role="agent",
                text="No transcript available",
                start_ms=0,
                end_ms=duration_ms or 1000,
                metadata={},
            )
        ]

    recording_url = conversation.recording_url

    return CreateCallRequest(
        call_id=conversation_id,
        call_type=call_type,
        transcript_with_tool_calls=transcript_with_tool_calls,
        start_timestamp=start_timestamp or int(datetime.now().timestamp() * 1000),
        end_timestamp=end_timestamp
        or (start_timestamp or int(datetime.now().timestamp() * 1000))
        + (duration_ms or 60000),
        recording_url=recording_url,
        transcript=transcript_text,
        duration_ms=duration_ms,
        call_status=call_status,
        caller_phone_number=caller_phone,
        call_successful=call_successful,
        in_voicemail=None,
        disconnection_reason=disconnection_reason,
        call_analysis=call_analysis,
        call_cost=call_cost * 100,  # Convert to cents
        general_meta_data_raw=general_meta_data_raw,
    )
