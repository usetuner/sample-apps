"""Map Eleven Labs transcript format to Tuner PublicTranscriptSegment format."""

import json
import typing
from typing import Any, Sequence

from elevenlabs.types.conversation_history_transcript_common_model_output import (
    ConversationHistoryTranscriptCommonModelOutput,
)
from elevenlabs.types.conversation_history_transcript_common_model_output_tool_results_item import (
    ConversationHistoryTranscriptCommonModelOutputToolResultsItem,
)
from elevenlabs.types.conversation_history_transcript_tool_call_common_model_output import (
    ConversationHistoryTranscriptToolCallCommonModelOutput,
)
from schemas.v1.transcript import PublicTranscriptSegment, PublicTranscriptTool


def _normalize_role(role: str | None) -> str:
    if role == "assistant":
        return "agent"
    if role in {"user", "agent"}:
        return role
    return "agent"


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_none=True)
    return value


def map_elevenlabs_to_tuner_transcript(
    elevenlabs_transcript: Sequence[ConversationHistoryTranscriptCommonModelOutput],
) -> list[PublicTranscriptSegment]:
    """
    Convert Eleven Labs conversation transcript to Tuner transcript_with_tool_calls format.

    Mapping logic:
    - Regular user/agent messages -> user/agent segments with timing
    - Tool calls within agent turns -> separate agent_function segments
    - Tool results -> separate agent_result segments
    - time_in_call_secs (seconds) -> start_ms/end_ms (milliseconds)
    - Eleven Labs metadata stored in metadata field

    Args:
        elevenlabs_transcript: List of Eleven Labs conversation turns

    Returns:
        List of Tuner PublicTranscriptSegment dictionaries
    """
    tuner_segments: list[PublicTranscriptSegment] = []

    for i, turn in enumerate(elevenlabs_transcript):
        role = _normalize_role(turn.role)
        message = turn.message
        time_in_call_secs = turn.time_in_call_secs
        tool_calls = turn.tool_calls or []
        tool_results = turn.tool_results or []

        # Use actual timing data from ElevenLabs, no estimation
        if time_in_call_secs is None:
            continue  # Skip segments without timing data
        
        # Get elapsed_time from the first metric entry, regardless of key name
        if turn.conversation_turn_metrics:
            elapsed_time = next(iter(turn.conversation_turn_metrics.metrics.values())).elapsed_time
        else:
            elapsed_time = 0
        start_ms = int(time_in_call_secs * 1000) + (elapsed_time * 1000)

        # Use next turn's time for end_ms if available, otherwise no end_ms
        end_ms = None
        if i + 1 < len(elevenlabs_transcript):
            next_time_secs = getattr(
                elevenlabs_transcript[i + 1], "time_in_call_secs", None
            )
            if next_time_secs is not None:
                end_ms = int(next_time_secs * 1000)

        # Build metadata from Eleven Labs-specific fields
        metadata = {}
        
        # Include relevant Eleven Labs fields
        if turn.interrupted is not None:
            metadata["interrupted"] = turn.interrupted
        if turn.agent_metadata:
            metadata["agent_metadata"] = _to_jsonable(turn.agent_metadata)
        if turn.conversation_turn_metrics:
            metadata["conversation_turn_metrics"] = _to_jsonable(turn.conversation_turn_metrics)
        if turn.source_medium:
            metadata["source_medium"] = turn.source_medium
        if turn.rag_retrieval_info:
            metadata["rag_retrieval_info"] = _to_jsonable(turn.rag_retrieval_info)
        if turn.llm_usage:
            metadata["llm_usage"] = _to_jsonable(turn.llm_usage)
        if turn.original_message:
            metadata["original_message"] = turn.original_message
        if turn.feedback:
            metadata["feedback"] = _to_jsonable(turn.feedback)

        # 1. Create main user/agent message segment
        if message:
            segment = PublicTranscriptSegment(
                role=role,
                text=message,
                start_ms=start_ms,
                end_ms=end_ms,
                metadata=metadata,
            )
            tuner_segments.append(segment)

        # 2. Create agent_function segments for tool calls
        for tool_call in tool_calls:
            tool_call = typing.cast(ConversationHistoryTranscriptToolCallCommonModelOutput, tool_call)
            # Parse params_as_json if it's a string
            params = tool_call.params_as_json
            if params:
                try:
                    params = json.loads(params)
                except json.JSONDecodeError:
                    params = {"raw": params}

            tool_segment = PublicTranscriptSegment(
                role="agent_function",
                start_ms=start_ms,
                end_ms=start_ms,
                tool=PublicTranscriptTool(
                    name=tool_call.tool_name,
                    request_id=tool_call.request_id,
                    params=params,
                ),
            )
            
            # Add tool-specific metadata
            tool_metadata = {}
            if tool_call.type:
                tool_metadata["type"] = tool_call.type
            if tool_call.tool_has_been_called is not None:
                tool_metadata["tool_has_been_called"] = tool_call.tool_has_been_called
            if tool_call.tool_details:
                tool_metadata["tool_details"] = _to_jsonable(tool_call.tool_details)
            
            if tool_metadata:
                tool_segment.metadata = tool_metadata
                
            tuner_segments.append(tool_segment)

        # 3. Create agent_result segments for tool results
        for tool_result in tool_results:
            tool_result = typing.cast(ConversationHistoryTranscriptCommonModelOutputToolResultsItem, tool_result)
            # Build result structure
            result_data = {}
            result_value = getattr(tool_result, "result_value", None)
            if result_value is not None:
                result_data["value"] = result_value
            result_payload = getattr(tool_result, "result", None)
            if result_payload is not None:
                result_data["payload"] = _to_jsonable(result_payload)

            result_segment = PublicTranscriptSegment(
                role="agent_result",
                start_ms=start_ms,
                end_ms=start_ms,
                tool=PublicTranscriptTool(
                    name=getattr(tool_result, "tool_name", None),
                    request_id=getattr(tool_result, "request_id", None),
                    result=result_data if result_data else None,
                    is_error=getattr(tool_result, "is_error", None),
                ),
            )
            
            # Add error message if present
            if getattr(tool_result, "is_error", None) and getattr(tool_result, "raw_error_message", None):
                if result_segment.tool is not None:
                    result_segment.tool.error = getattr(tool_result, "raw_error_message")
            
            # Add result-specific metadata
            result_metadata = {}
            if getattr(tool_result, "type", None):
                result_metadata["type"] = getattr(tool_result, "type")
            if getattr(tool_result, "tool_latency_secs", None) is not None:
                result_metadata["tool_latency_secs"] = getattr(tool_result, "tool_latency_secs")
            if getattr(tool_result, "error_type", None):
                result_metadata["error_type"] = getattr(tool_result, "error_type")
            if getattr(tool_result, "dynamic_variable_updates", None):
                result_metadata["dynamic_variable_updates"] = _to_jsonable(
                    getattr(tool_result, "dynamic_variable_updates")
                )
            
            if result_metadata:
                result_segment.metadata = result_metadata
                
            tuner_segments.append(result_segment)

    return tuner_segments


# For detailed field mapping reference and usage examples, see ELEVENLABS_MAPPING.md
