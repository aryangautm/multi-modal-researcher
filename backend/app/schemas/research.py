import uuid
from typing import Optional

from pydantic import BaseModel, HttpUrl


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
