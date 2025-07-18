import re
import uuid
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# Schema for the data we expect when a user CREATES a research job
class ResearchJobCreate(BaseModel):
    researchTopic: str = Field(..., min_length=10, max_length=300)
    sourceVideoUrl: Optional[HttpUrl] = None

    @field_validator("sourceVideoUrl", mode="before")
    @classmethod
    def validate_youtube_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validates that the provided URL is a standard YouTube watch or share link.
        """
        if v is None or v == "":
            return None

        # This regex is a bit more robust to handle various YouTube URL formats
        youtube_regex = (
            r"(https?://)?(www\.)?"
            "(youtube|youtu|youtube-nocookie)\.(com|be)/"
            "(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
        )

        if not re.match(youtube_regex, v):
            raise ValueError("Invalid URL: Please provide a valid YouTube video link.")

        return v


# Schema for the immediate response after a job is successfully created
class ResearchJobResponse(BaseModel):
    jobId: uuid.UUID

    class Config:
        from_attributes = True  # Pydantic v2 alias for orm_mode


# WebSocket updates
class JobStatusUpdate(BaseModel):
    id: uuid.UUID = Field(..., alias="id")
    status: str
    research_text: Optional[str] = Field(None, alias="summary")
    research_topic: str = Field(None, alias="topic")
    source_video_url: Optional[HttpUrl] = Field(None, alias="sourceVideoUrl")
    failure_reason: Optional[str] = Field(None, alias="failureReason")

    class Config:
        from_attributes = True  # Allows creating from a SQLAlchemy model
        populate_by_name = True  # Allows using both field names and aliases


class PresignedUrlResponse(BaseModel):
    url: HttpUrl
