from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    elevenlabs_api_key: str | None
    elevenlabs_agent_id: str | None
    tuner_api_key: str | None
    tuner_api_url: str
    start_time: int
    end_time: int


def load_config() -> Config:
    """Load configuration from environment variables."""
    load_dotenv()

    # Parse time window parameters (in hours, default to last 24 hours)
    hours_back = int(os.getenv("TIME_WINDOW_HOURS", "24"))
    start_time = datetime.now() - timedelta(hours=hours_back)

    # Allow custom start/end time as Unix timestamps
    custom_start = os.getenv("START_TIME_UNIX")
    custom_end = os.getenv("END_TIME_UNIX")

    return Config(
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
        elevenlabs_agent_id=os.getenv("ELEVENLABS_AGENT_ID"),
        tuner_api_key=os.getenv("TUNER_API_KEY"),
        tuner_api_url=os.getenv(
            "TUNER_API_URL", "https://api.usetuner.ai/api/v1/public/call"
        ),
        start_time=int(custom_start) if custom_start else int(start_time.timestamp()),
        end_time=int(custom_end) if custom_end else int(datetime.now().timestamp()),
    )
