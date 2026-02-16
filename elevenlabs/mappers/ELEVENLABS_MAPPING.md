# Eleven Labs to Tuner Transcript Mapping

## Field Mapping Reference

### Eleven Labs → Tuner PublicTranscriptSegment

#### 1. Regular messages (user/agent):
- `role` (user/agent) → `role` (user/agent)
- `message` → `text`
- `time_in_call_secs * 1000` → `start_ms`
- next turn's `time_in_call_secs * 1000` → `end_ms`

#### 2. Tool calls (creates separate agent_function segments):
- `tool_calls[].tool_name` → `tool.name`
- `tool_calls[].request_id` → `tool.request_id`
- `tool_calls[].params_as_json` → `tool.params` (JSON parsed)
- `tool_calls[].type` → `metadata.type`

#### 3. Tool results (creates separate agent_result segments):
- `tool_results[].tool_name` → `tool.name`
- `tool_results[].request_id` → `tool.request_id`
- `tool_results[].result_value` → `tool.result.value`
- `tool_results[].is_error` → `tool.is_error`
- `tool_results[].raw_error_message` → `tool.error`
- `tool_results[].tool_latency_secs` → `metadata.tool_latency_secs`

#### 4. Preserved in metadata field:
- interrupted, agent_metadata, conversation_turn_metrics, source_medium,
  rag_retrieval_info, llm_usage, original_message, feedback

#### 5. Ignored fields (no Tuner equivalent):
- multivoice_message, llm_override

## Example usage

```python
from elevenlabs_mapper import map_elevenlabs_to_tuner_transcript
from schemas.v1.call import CreateCallRequest

elevenlabs_data = [...]  # Your Eleven Labs transcript
tuner_transcript = map_elevenlabs_to_tuner_transcript(elevenlabs_data)

# Use in CreateCallRequest
request = CreateCallRequest(
    call_id="elevenlabs_call_123",
    call_type="phone_call",
    transcript_with_tool_calls=tuner_transcript,
    start_timestamp=1234567890,
    end_timestamp=1234567950,
    recording_url="https://example.com/recording.mp3"
)
```
