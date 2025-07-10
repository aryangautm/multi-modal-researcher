import sys
import os
import asyncio
import uuid
import logging
import json
from io import BytesIO

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.database import db as database  # Corrected import
from app.models.session import ResearchJob, JobStatus

# from app.agent.research.graph import create_compiled_graph # TODO: UNCOMMENT THIS


# LOGGING & CONCURRENCY SETUP
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "job_id": getattr(record, "job_id", "N/A"),
        }
        return json.dumps(log_record)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Limit the number of concurrent AI jobs to prevent resource exhaustion
MAX_CONCURRENT_JOBS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


async def run_ai_research(
    topic: str, video_url: str | None, job_id: uuid.UUID
) -> tuple[str, bytes]:
    # TODO: Integrate your LangGraph agent
    # research_graph = create_compiled_graph()
    # result = await research_graph.ainvoke({"topic": topic, "video_url": video_url})
    # summary = result.get("summary")
    # pdf_bytes = result.get("report_bytes")

    # Placeholder logic:
    logging.info(f"AI Agent: Starting research", extra={"job_id": str(job_id)})
    await asyncio.sleep(10)
    summary = f"This is a comprehensive summary about {topic}."
    pdf_bytes = f"PDF Report\n\nTopic: {topic}".encode("utf-8")
    logging.info(f"AI Agent: Research complete", extra={"job_id": str(job_id)})
    return summary, pdf_bytes


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def upload_to_s3(
    file_bytes: bytes, bucket: str, object_name: str, job_id: uuid.UUID
) -> bool:
    logging.info(f"S3 Uploader: Uploading {object_name}", extra={"job_id": str(job_id)})
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        await asyncio.to_thread(
            s3_client.upload_fileobj, BytesIO(file_bytes), bucket, object_name
        )
        logging.info("S3 Uploader: Upload successful", extra={"job_id": str(job_id)})
        return True
    except Exception as e:
        logging.error(
            f"S3 Uploader: Failed to upload to S3: {e}", extra={"job_id": str(job_id)}
        )
        raise  # Re-raise the exception to trigger tenacity's retry mechanism


async def process_job(job_id: uuid.UUID):
    """
    Processes a single research job with concurrency limiting and idempotency.
    """
    async with semaphore:
        db: Session = database.SessionLocal
        try:
            # 1. IDEMPOTENCY CHECK: Fetch the job and check its status
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if not job:
                logging.error(
                    f"Job not found in database. Skipping.",
                    extra={"job_id": str(job_id)},
                )
                return

            if job.status != JobStatus.PENDING:
                logging.warning(
                    f"Job is not in PENDING state (is {job.status}). Skipping reprocessing.",
                    extra={"job_id": str(job_id)},
                )
                return

            # 2. STATUS UPDATE: Mark as PROCESSING
            logging.info(
                f"Picked up. Status -> PROCESSING", extra={"job_id": str(job_id)}
            )
            job.status = JobStatus.PROCESSING
            db.commit()

            # 3. AI WORKFLOW
            summary, pdf_bytes = await run_ai_research(
                job.research_topic, job.source_video_url, job.id
            )

            # 4. S3 UPLOAD
            s3_object_key = f"reports/{job.user_id}/{job.id}.pdf"
            await upload_to_s3(
                pdf_bytes, settings.AWS_S3_BUCKET_NAME, s3_object_key, job.id
            )

            # 5. FINALIZE JOB
            logging.info(
                f"Finalizing. Status -> COMPLETED", extra={"job_id": str(job_id)}
            )
            job.status = JobStatus.COMPLETED
            job.summary = summary
            job.report_url = s3_object_key
            db.commit()

        except Exception as e:
            logging.error(
                f"An error occurred during processing: {e}",
                extra={"job_id": str(job_id)},
            )
            if "job" in locals() and job:
                job.status = JobStatus.FAILED
                db.commit()
                logging.info(f"Status -> FAILED", extra={"job_id": str(job_id)})
        finally:
            db.close()
            logging.info(f"Processing finished.", extra={"job_id": str(job_id)})


# KAFKA CONSUMER MAIN LOOP
async def main():
    """The main function that runs the Kafka consumer in a robust loop."""
    while True:
        try:
            consumer = AIOKafkaConsumer(
                settings.KAFKA_RESEARCH_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="research_worker_group",
                auto_offset_reset="earliest",
            )
            await consumer.start()
            logging.info(
                "Research worker started successfully. Waiting for messages..."
            )

            async for msg in consumer:
                try:
                    job_id_str = msg.value.decode("utf-8")
                    job_id = uuid.UUID(job_id_str)
                    logging.info(f"Received message", extra={"job_id": str(job_id)})
                    asyncio.create_task(process_job(job_id))
                except Exception as e:
                    logging.error(
                        f"Error processing message value: {msg.value}. Error: {e}",
                        extra={"job_id": "unknown"},
                    )

        except Exception as e:
            logging.error(
                f"Kafka consumer connection failed: {e}. Retrying in 10 seconds..."
            )
            await asyncio.sleep(10)
        finally:
            if "consumer" in locals():
                await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
