import logging
import uuid

import boto3
from aiokafka import AIOKafkaProducer
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import db as database
from app.core.messaging import get_kafka_producer
from app.models.session import JobStatus, ResearchJob
from app.schemas.research import (
    PresignedUrlResponse,
    ResearchJobCreate,
    ResearchJobResponse,
)
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/research",
    response_model=ResearchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate a new research job",
)
async def create_research_job(
    research_request: ResearchJobCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer),
):
    """
    Endpoint to create and queue a new research job.

    - **research_request**: Contains the topic and optional video URL.
    - **Returns**: A response with the unique ID of the created job.
    """
    # 1. Get the authenticated user's unique ID from the verified token
    user_id = current_user["uid"]

    # 2. Create the SQLAlchemy model instance for the database
    db_job = ResearchJob(
        user_id=user_id,
        research_topic=research_request.researchTopic,
        source_video_url=(
            str(research_request.sourceVideoUrl)
            if research_request.sourceVideoUrl
            else None
        ),
        # Status defaults to PENDING
    )

    # 3. Add to the session and commit to the database
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # 4. Publish a message to Kafka to trigger the worker
    #    The message is the job_id, which the worker will use to fetch details from the DB.
    job_id_bytes = str(db_job.id).encode("utf-8")
    await kafka_producer.send_and_wait(
        topic=settings.KAFKA_RESEARCH_TOPIC,
        value=job_id_bytes,
        key=user_id.encode("utf-8"),  # Using user_id as key can help with partitioning
    )

    return {"jobId": db_job.id}


@router.get(
    "/research/{job_id}/report",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a secure, temporary URL to download a research report",
)
async def get_report_download_url(
    job_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generates a pre-signed URL for downloading a completed research report.

    - This endpoint is protected and requires authentication.
    - It verifies that the user requesting the report is the one who created the job.
    - It checks that the report has actually been generated.
    """
    user_id = current_user["uid"]

    # 1. Query DB & Authorize: Fetch the job only if the user_id matches.
    job = (
        db.query(ResearchJob)
        .filter(ResearchJob.id == job_id, ResearchJob.user_id == user_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or you do not have permission to access it.",
        )

    # 2. Check Job Status
    if job.status != JobStatus.COMPLETED or not job.report_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report is not yet available for this job.",
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
            Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": job.report_url},
            ExpiresIn=300,  # URL is valid for 5 minutes
        )

        return {"url": presigned_url}

    except ClientError as e:
        # Log the error for debugging
        logging.error(f"Could not generate pre-signed URL for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate download link.",
        )
