import logging
import uuid

import boto3
from aiokafka import AIOKafkaProducer
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import db as database
from app.core.messaging import get_kafka_producer
from app.models.session import JobStatus, ResearchJob
from app.schemas.research import PresignedUrlResponse
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()
from aiokafka import AIOKafkaProducer
from app.core.messaging import get_kafka_producer, publish_status_update


# INITIATE PODCAST GENERATION
@router.post(
    "/research-jobs/{job_id}/podcast",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate podcast generation for a completed research job",
)
async def create_podcast_from_research(
    job_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer),
):
    """
    Triggers the asynchronous generation of a podcast based on a completed research report.
    """
    user_id = current_user["uid"]

    # 1. Fetch and Authorize
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found."
        )
    if job.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized."
        )

    # 2. State Check: Ensure the job is in the correct state to start a podcast
    if job.status not in [JobStatus.COMPLETED, JobStatus.PODCAST_FAILED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot generate podcast. Job status is '{job.status}', must be 'COMPLETED'.",
        )

    # 3. Update Status and Commit
    job.status = JobStatus.PODCAST_PENDING
    db.commit()
    db.refresh(job)

    # 4. Publish to Kafka to trigger the podcast worker
    job_id_bytes = str(job.id).encode("utf-8")
    await kafka_producer.send_and_wait(
        topic=settings.KAFKA_PODCAST_TOPIC,
        value=job_id_bytes,
        key=user_id.encode("utf-8"),
    )

    # 5. Publish immediate feedback to the WebSocket client
    await publish_status_update(job, kafka_producer)

    return {"message": "Podcast generation has been queued."}


# SECURELY DOWNLOAD PODCAST
@router.get(
    "/research-jobs/{job_id}/podcast",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a secure download URL for a generated podcast",
)
async def get_podcast_download_url(
    job_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Provides a temporary, secure, pre-signed URL to download a generated podcast audio file.
    """
    user_id = current_user["uid"]

    # 1. Fetch and Authorize
    job = (
        db.query(ResearchJob)
        .filter(ResearchJob.id == job_id, ResearchJob.user_id == user_id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found."
        )

    # 2. State Check
    if job.status != JobStatus.PODCAST_COMPLETED or not job.podcast_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast is not available. It may be processing or has failed.",
        )

    # 3. Generate Pre-signed URL
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": job.podcast_url},
            ExpiresIn=300,  # URL is valid for 5 minutes
        )
        return PresignedUrlResponse(url=presigned_url)
    except ClientError as e:
        print(
            f"ERROR: Could not generate pre-signed URL for {job.podcast_url}. Error: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate download link.",
        )
