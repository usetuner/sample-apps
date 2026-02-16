"""ElevenLabs response models extended for internal use."""

from pydantic import Field
from elevenlabs import GetConversationResponseModel


class GetConversationWithRecordingUrl(GetConversationResponseModel):
    """ElevenLabs conversation response with optional recording URL."""

    recording_url: str | None = Field(
        None,
        description="Public recording URL when resolved from the ElevenLabs API.",
    )
