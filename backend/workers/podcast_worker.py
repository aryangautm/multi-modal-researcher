import asyncio
import logging
import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.agents.podcast.graph import create_compiled_graph
from app.core.config import settings
from app.core.database import db as database
from app.core.messaging import publish_status_update
from app.models.session import JobStatus, ResearchJob
from app.utils.logging import handler
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.orm import Session

from .utils import upload_to_s3

logging.basicConfig(level=logging.INFO, handlers=[handler])

MAX_CONCURRENT_JOBS = 3  # Podcast generation might be more CPU intensive
semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


async def run_ai_podcast_generation(
    research_text: str, video_text: str, topic: str, job_id: uuid.UUID
) -> tuple[bytes, str]:
    """AI podcast generation process."""
    logging.info(
        f"AI Agent: Starting podcast generation", extra={"job_id": str(job_id)}
    )
    try:
        async with AsyncPostgresSaver.from_conn_string(
            database.DATABASE_URL
        ) as checkpointer:
            podcast_graph = create_compiled_graph(checkpointer)
            result = await podcast_graph.ainvoke(
                {
                    "research_text": research_text,
                    "video_text": video_text,
                    "topic": topic,
                },
                config={"thread_id": str(job_id)},
            )
    except Exception as e:
        logging.error(
            f"AI Agent: Error during podcast generation: {e}",
            extra={"job_id": str(job_id)},
        )
        raise
    audio_bytes = result.get("podcast_audio_bytes")
    podcast_script = result.get("podcast_script")

    logging.info(
        f"AI Agent: Podcast generation complete", extra={"job_id": str(job_id)}
    )
    return audio_bytes, podcast_script


async def process_podcast_job(job_id: uuid.UUID, producer: AIOKafkaProducer):
    async with semaphore:
        db: Session = database.SessionLocal()
        try:
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if not job:
                return
            if job.status != JobStatus.PODCAST_PENDING:
                logging.warning(
                    f"Job not in PODCAST_PENDING state (is {job.status}). Skipping.",
                    extra={"job_id": str(job_id)},
                )
                return

            logging.info(
                f"Picked up for podcast generation.", extra={"job_id": str(job_id)}
            )
            audio_bytes, podcast_script = await run_ai_podcast_generation(
                job.research_text, job.video_text, job.research_topic, job.id
            )

            s3_object_key = f"podcasts/{job.user_id}/{job.id}.mp3"
            await upload_to_s3(
                audio_bytes,
                settings.AWS_S3_BUCKET_NAME,
                s3_object_key,
                job.id,
                worker="PodcastWorker",
            )

            logging.info(
                f"Finalizing. Status -> PODCAST_COMPLETED",
                extra={"job_id": str(job_id)},
            )
            job.status = JobStatus.PODCAST_COMPLETED
            job.podcast_url = s3_object_key
            job.podcast_script = podcast_script
            db.commit()
            db.refresh(job)
            await publish_status_update(job, producer)  # Notify WebSocket clients

        except Exception as e:
            logging.error(
                f"An error occurred during podcast processing: {e}",
                extra={"job_id": str(job_id)},
            )
            if "job" in locals() and job:
                db.rollback()
                job.status = JobStatus.PODCAST_FAILED
                db.commit()
                db.refresh(job)
                await publish_status_update(job, producer)
                logging.info(f"Status -> PODCAST_FAILED", extra={"job_id": str(job_id)})
        finally:
            db.close()
            logging.info(f"Podcast processing finished.", extra={"job_id": str(job_id)})


async def main():
    while True:
        producer = None
        consumer = None
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )
            await producer.start()
            consumer = AIOKafkaConsumer(
                settings.KAFKA_PODCAST_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="podcast_worker_group",
            )
            await consumer.start()
            logging.info("Podcast worker started. Waiting for messages...")

            async for msg in consumer:
                job_id = uuid.UUID(msg.value.decode("utf-8"))
                logging.info(f"Received message", extra={"job_id": str(job_id)})
                asyncio.create_task(process_podcast_job(job_id, producer))

        except Exception as e:
            logging.error(
                f"Kafka consumer connection failed: {e}. Retrying in 10 seconds..."
            )
            await asyncio.sleep(10)
        finally:
            if producer:
                await producer.stop()
            if consumer:
                await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
