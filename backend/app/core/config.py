import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@dataclass(kw_only=True)
class Configuration:
    """Configuration for the deep research agent."""

    # Model settings
    search_model: str = "gemini-2.5-flash"  # Web search supported model
    synthesis_model: str = "gemini-2.5-flash"  # Citations supported model
    video_model: str = "gemini-2.5-flash"  # Citations supported model
    tts_model: str = "gemini-2.5-flash-preview-tts"

    # Temperature settings for different use cases
    search_temperature: float = 0.0  # Factual search queries
    synthesis_temperature: float = 0.3  # Balanced synthesis
    podcast_script_temperature: float = 0.4  # Creative dialogue

    # TTS Configuration
    mike_voice: str = "Kore"
    sarah_voice: str = "Puck"
    tts_channels: int = 1
    tts_rate: int = 24000
    tts_sample_width: int = 2

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    GEMINI_API_KEY: str
    # Database settings
    DATABASE_URL: str

    # Firebase settings
    FIREBASE_CREDENTIALS_FILENAME: str

    # Property to get the absolute path to the Firebase credentials file
    @property
    def FIREBASE_CREDENTIALS_PATH(self) -> Path:
        return PROJECT_ROOT / self.FIREBASE_CREDENTIALS_FILENAME

    # AWS Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_S3_BUCKET_NAME: str
    AWS_REGION: str
    AWS_S3_INTERNAL_ENDPOINT: str
    AWS_S3_PUBLIC_URL: str

    # Kafka settings for communication
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_RESEARCH_TOPIC: str = "research.requests"
    KAFKA_PODCAST_TOPIC: str = "podcast.requests"

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
