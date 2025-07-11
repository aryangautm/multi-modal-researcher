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


# Full schema for the job, representing the model in the database
class ResearchJobInDB(BaseModel):
    id: uuid.UUID
    user_id: str
    status: str
    research_topic: str

    class Config:
        from_attributes = True


# WebSocket updates
class JobStatusUpdate(BaseModel):
    jobId: uuid.UUID = Field(..., alias="id")
    status: str
    summary: Optional[str] = None
    reportUrl: Optional[str] = Field(None, alias="report_url")
    podcastUrl: Optional[str] = Field(None, alias="podcast_url")

    class Config:
        from_attributes = True  # Allows creating from a SQLAlchemy model
        populate_by_name = True  # Allows using both field names and aliases
