from aiokafka import AIOKafkaProducer
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.messaging import get_kafka_producer
from app.models.session import ResearchJob
from app.schemas.research import ResearchJobCreate, ResearchJobResponse
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/research",
    response_model=ResearchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate a new research job",
)
async def create_research_job(
    research_request: ResearchJobCreate,
    db: Session = Depends(get_db),
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
