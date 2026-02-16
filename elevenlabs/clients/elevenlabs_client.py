from datetime import datetime
import logging
from typing import List, Optional

import requests
from elevenlabs.client import ElevenLabs

from schemas.v1.elevenlabs_conversation import GetConversationWithRecordingUrl


# TODO: Eleven labs deprecated this endpoint, Need to download the recording on publicly available server and return the URL to Tuner
def get_recording_url(api_key: str, conversation_id: str) -> str:
    """Fetch recording URL from ElevenLabs API or return fallback."""

    try:
        response = requests.get(
            f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}/audio",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            }
        )
        if response.status_code == 200:
            return response.url
    except Exception:
        logging.warning(f"Failed to fetch recording URL for conversation {conversation_id}")
        pass
    
    # Fallback if API call fails
    return " "


def get_conversation_transcript_and_recording(
    api_key: str,
    conversation_id: str,
) -> Optional[GetConversationWithRecordingUrl]:
    """Retrieve full conversation details including transcript using the GET endpoint."""
    try:
        client = ElevenLabs(api_key=api_key)
        conversation = client.conversational_ai.conversations.get(conversation_id)
        recording_url = get_recording_url(api_key, conversation_id)
        return GetConversationWithRecordingUrl(
            **conversation.model_dump(mode="python"),
            recording_url=recording_url,
        )
    except Exception as e:
        print(
            "  Warning: Failed to get transcript for conversation "
            f"{conversation_id}: {str(e)}"
        )
        return None


def get_elevenlabs_conversations(
    api_key: str,
    agent_id: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
) -> List[GetConversationWithRecordingUrl]:
    """Retrieve conversations from ElevenLabs for a specific agent within a time window."""
    time_window_msg = ""
    if start_time and end_time:
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        time_window_msg = (
            f" (from {start_dt.strftime('%Y-%m-%d %H:%M:%S')} "
            f"to {end_dt.strftime('%Y-%m-%d %H:%M:%S')})"
        )

    print(f"Fetching conversations for agent: {agent_id}{time_window_msg}")

    try:
        client = ElevenLabs(api_key=api_key)

        # List conversations for the agent with native time filtering
        all_conversations = []
        cursor = None

        while True:
            response = client.conversational_ai.conversations.list(
                agent_id=agent_id,
                call_start_after_unix=start_time,
                call_start_before_unix=end_time,
                cursor=cursor,
                page_size=100,  # Maximum page size
            )

            all_conversations.extend(response.conversations)

            # Check if there are more pages
            if not response.has_more:
                break

            cursor = response.next_cursor

        print(f"Retrieved {len(all_conversations)} conversations")

        # Fetch full transcript data for each conversation
        if all_conversations:
            print("Fetching full transcript data for each conversation...")
            enriched_conversations = []
            for idx, conv in enumerate(all_conversations, 1):
                conv_id = conv.conversation_id
                full_conv = get_conversation_transcript_and_recording(api_key, conv_id)
                if not full_conv:
                    continue

                enriched_conversations.append(full_conv)
                print(
                    f"  [{idx}/{len(all_conversations)}] "
                    f"Fetched transcript for conversation: {conv_id}"
                )

            return enriched_conversations

        return []

    except Exception as e:
        print(f"Error retrieving ElevenLabs conversations: {str(e)}")
        raise
