import asyncio
import json
import logging
import uuid

from aiokafka import AIOKafkaConsumer
from app.core.auth import get_current_user_ws
from app.core.config import settings
from app.core.database import db as database
from app.models.session import JobStatus, ResearchJob
from app.schemas.research import JobStatusUpdate
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self, websocket: WebSocket, job_id: uuid.UUID):
        self.websocket = websocket
        self.job_id = job_id
        self.consumer: AIOKafkaConsumer | None = None
        self.consumer_task: asyncio.Task | None = None
        self.client_handler_task: asyncio.Task | None = None

    async def connect(self):
        """Accepts the connection and sends the initial job state."""
        await self.websocket.accept()
        logger.info(
            f"WebSocket accepted.",
            extra={"job_id": str(self.job_id)},
        )

        self.consumer_task = asyncio.create_task(self._kafka_consumer_task())
        self.client_handler_task = asyncio.create_task(self._client_handler_task())

    async def disconnect(self):
        """Cleanly cancels and awaits all running tasks for this connection."""
        tasks = [self.consumer_task, self.client_handler_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
        await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)
        logger.info(
            "Connection tasks have been cleaned up.", extra={"job_id": str(self.job_id)}
        )

    async def _kafka_consumer_task(self):
        """Listens to a job-specific Kafka topic and forwards messages to the client."""
        db = database.SessionLocal()
        try:
            self.consumer = AIOKafkaConsumer(
                f"job.updates.{self.job_id}",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"ws-group-{uuid.uuid4()}",  # Ephemeral group ID is correct
                auto_offset_reset="latest",
            )
            await self.consumer.start()
            logger.info(
                "Kafka consumer started for live updates.",
                extra={"job_id": str(self.job_id)},
            )
            job = db.query(ResearchJob).filter(ResearchJob.id == self.job_id).first()
            logger.info(
                f"Sending initial state.",
                extra={"job_id": str(self.job_id)},
            )

            # SEND INITIAL JOB STATE
            initial_payload = JobStatusUpdate.model_validate(job).model_dump_json(
                by_alias=True
            )
            await self.websocket.send_json(json.loads(initial_payload))

            async for msg in self.consumer:
                try:
                    payload = json.loads(msg.value.decode("utf-8"))
                    await self.websocket.send_json(payload)

                    status = payload.get("status")
                    if status in [
                        JobStatus.COMPLETED.value,
                        JobStatus.FAILED.value,
                        JobStatus.PODCAST_COMPLETED.value,
                    ]:
                        logger.info(
                            f"Job reached terminal state '{status}'. Closing Kafka consumer task.",
                            extra={"job_id": str(self.job_id)},
                        )
                        break
                except json.JSONDecodeError:
                    logger.error(
                        "Failed to decode Kafka message JSON.",
                        extra={"job_id": str(self.job_id)},
                    )
        except asyncio.CancelledError:
            logger.info(
                "Kafka consumer task was cancelled.", extra={"job_id": str(self.job_id)}
            )
        except Exception as e:
            logger.error(
                f"Kafka consumer task failed: {e}", extra={"job_id": str(self.job_id)}
            )
        finally:
            if self.consumer:
                await self.consumer.stop()
            logger.info("Kafka consumer stopped.", extra={"job_id": str(self.job_id)})

    async def _client_handler_task(self):
        """Detects client disconnects. A ping can be added if needed."""
        try:
            while True:
                data = await self.websocket.receive_text()
                logger.info(
                    f"Received message from client: {data}",
                    extra={"job_id": str(self.job_id)},
                )
        except WebSocketDisconnect:
            logger.info("Client disconnected.", extra={"job_id": str(self.job_id)})
        except asyncio.CancelledError:
            logger.info(
                "Client handler was cancelled.", extra={"job_id": str(self.job_id)}
            )


def get_websocket_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    job_id: uuid.UUID,
    db: Session = Depends(get_websocket_db),
    user: dict = Depends(get_current_user_ws),
):
    # 1. Authentication
    if user is None:
        logger.warning(
            "WebSocket connection attempt with invalid or missing authentication token."
        )
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token"
        )
        return

    # 2. Authorization & Initial State Fetch
    job = (
        db.query(ResearchJob)
        .filter(ResearchJob.id == job_id, ResearchJob.user_id == user["uid"])
        .first()
    )
    if not job:
        logger.warning(
            f"Job {job_id} not found or unauthorized for user {user['uid']}.",
            extra={"job_id": str(job_id)},
        )
        await websocket.close(
            code=status.WS_1003_UNSUPPORTED_DATA, reason="Job not found or unauthorized"
        )
        return

    if job.status not in [
        JobStatus.PENDING,
        JobStatus.PROCESSING,
        JobStatus.PODCAST_PENDING,
    ]:
        logger.warning(
            f"Job {job_id} is not in a state that supports WebSocket updates: {job.status}",
            extra={"job_id": str(job_id)},
        )
        await websocket.close(
            code=status.WS_1003_UNSUPPORTED_DATA,
            reason="Job is not in a state that supports WebSocket updates",
        )
        return

    # 3. Connection Handling
    manager = ConnectionManager(websocket, job_id)
    try:
        await manager.connect()
        if manager.client_handler_task:
            await manager.client_handler_task
    except Exception as e:
        logger.error(
            f"Unexpected error in WebSocket manager for job {job_id}: {e}",
            exc_info=True,
        )
    finally:
        await manager.disconnect()
        logger.info(f"WebSocket connection for job {job_id} fully closed.")
