import uuid
from enum import Enum as PyEnum

from app.core.database import db
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class JobStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PODCAST_PENDING = "PODCAST_PENDING"
    PODCAST_COMPLETED = "PODCAST_COMPLETED"
    PODCAST_FAILED = "PODCAST_FAILED"


class ResearchJob(db.Base):
    __tablename__ = "research_jobs"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # Firebase UID is a string

    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)

    research_topic = Column(Text, nullable=False)
    source_video_url = Column(String, nullable=True)

    research_text = Column(Text, nullable=True)
    video_text = Column(Text, nullable=True)

    podcast_script = Column(Text, nullable=True)

    report_url = Column(String, nullable=True)  # This will be the S3 object key
    podcast_url = Column(String, nullable=True)  # This will be the S3 object key

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    failure_reason = Column(Text, nullable=True)
