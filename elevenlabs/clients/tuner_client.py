from typing import List

import requests

from schemas.v1.elevenlabs_conversation import GetConversationWithRecordingUrl
from mappers.tuner_mapper import transform_conversation_to_tuner_format


def push_to_tuner(
    api_key: str,
    api_url: str,
    calls: List[GetConversationWithRecordingUrl],
    workspace_id: str,
    agent_remote_identifier: str,
) -> None:
    """Push call data to Tuner API."""
    print(f"Pushing {len(calls)} calls to Tuner...")

    headers = {
        "X-API-Key": f"{api_key}",
        "Content-Type": "application/json",
    }

    # Add required query parameters
    query_params = {
        "workspace_id": workspace_id,
        "agent_remote_identifier": agent_remote_identifier,
    }

    success_count = 0
    error_count = 0

    for idx, call in enumerate(calls, 1):
        try:
            # Transform ElevenLabs conversation data to Tuner format
            call_request = transform_conversation_to_tuner_format(call)
            payload = call_request.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )

            response = requests.post(
                api_url, json=payload, headers=headers, params=query_params
            )

            if response.status_code in [200, 201]:
                success_count += 1
                print(
                    f"  [{idx}/{len(calls)}] Successfully pushed call ID: "
                    f"{call_request.call_id}"
                )
            else:
                error_count += 1
                print(
                    f"  [{idx}/{len(calls)}] Failed to push call: "
                    f"{response.status_code} - {response.text}"
                )

        except Exception as e:
            error_count += 1
            print(f"  [{idx}/{len(calls)}] Error pushing call: {str(e)}")

    print(f"\nSummary: {success_count} successful, {error_count} failed")
