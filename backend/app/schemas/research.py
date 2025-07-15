import uuid
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


# Schema for the data we expect when a user CREATES a research job
class ResearchJobCreate(BaseModel):
    researchTopic: str
    sourceVideoUrl: Optional[HttpUrl] = None


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

    class Config:
        from_attributes = True  # Allows creating from a SQLAlchemy model
        populate_by_name = True  # Allows using both field names and aliases


class PresignedUrlResponse(BaseModel):
    url: HttpUrl
