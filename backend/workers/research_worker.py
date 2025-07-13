import asyncio
import logging
import os
import sys
import uuid
from io import BytesIO

from fpdf import FPDF

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.agents.research.graph import create_compiled_graph
from app.core.config import settings
from app.core.database import db as database
from app.core.messaging import publish_status_update
from app.models.session import JobStatus, ResearchJob
from app.utils.logging import handler
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, handlers=[handler])

# Limit the number of concurrent AI jobs to prevent resource exhaustion
MAX_CONCURRENT_JOBS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


def create_pdf_from_text(text: str, job_id: str) -> bytes:
    """
    Generates a valid PDF file in memory from a string of text,
    using the modern fpdf2 API and suppressing verbose logging.

    Args:
        text: The report text from the AI agent.
        job_id: The ID of the job for logging context.

    Returns:
        The raw bytes of the generated PDF file.
    """
    try:
        logging.getLogger("fpdf").setLevel(logging.WARNING)

        pdf = FPDF()
        pdf.add_page()

        pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf")
        pdf.set_font("DejaVu", size=12)

        pdf.multi_cell(0, 10, text=text, align="L")

        return pdf.output()

    except Exception as e:
        logging.error(
            f"Error generating PDF: {e}",
            extra={"job_id": job_id, "worker": "ResearchWorker"},
        )
        raise


async def run_ai_research(
    topic: str, video_url: str | None, job_id: uuid.UUID
) -> tuple[str, str, bytes]:
    logging.info(
        f"AI Agent: Starting research",
        extra={"job_id": str(job_id), "worker": "ResearchWorker"},
    )
    try:
        async with AsyncPostgresSaver.from_conn_string(
            database.DATABASE_URL
        ) as checkpointer:
            research_graph = create_compiled_graph(checkpointer)
            result = await research_graph.ainvoke(
                {"topic": topic, "video_url": video_url},
                config={"thread_id": str(job_id)},
            )
    except Exception as e:
        logging.error(
            f"AI Agent: Error during research: {e}",
            extra={"job_id": str(job_id), "worker": "ResearchWorker"},
        )
        raise
    research_text = result.get("research_text")
    video_text = result.get("video_text")
    report = result.get("report")

    # conver the report to bytes
    pdf_bytes = create_pdf_from_text(report, job_id=str(job_id))
    logging.info(
        f"AI Agent: Research complete",
        extra={"job_id": str(job_id), "worker": "ResearchWorker"},
    )
    return research_text, video_text, pdf_bytes


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def upload_to_s3(
    file_bytes: bytes, bucket: str, object_name: str, job_id: uuid.UUID
) -> bool:
    logging.info(
        f"S3 Uploader: Uploading {object_name}",
        extra={"job_id": str(job_id), "worker": "ResearchWorker"},
    )
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
        logging.info(
            "S3 Uploader: Upload successful",
            extra={"job_id": str(job_id), "worker": "ResearchWorker"},
        )
        return True
    except Exception as e:
        logging.error(
            f"S3 Uploader: Failed to upload to S3: {e}",
            extra={"job_id": str(job_id), "worker": "ResearchWorker"},
        )
        raise  # Re-raise the exception to trigger tenacity's retry mechanism


async def process_job(job_id: uuid.UUID, producer: AIOKafkaProducer):
    """
    Processes a single research job with concurrency limiting and idempotency.
    """
    async with semaphore:
        db: Session = database.SessionLocal()
        try:
            # 1. IDEMPOTENCY CHECK: Fetch the job and check its status
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if not job:
                logging.error(
                    f"Job not found in database. Skipping.",
                    extra={"job_id": str(job_id), "worker": "ResearchWorker"},
                )
                return

            if job.status != JobStatus.PENDING:
                logging.warning(
                    f"Job is not in PENDING state (is {job.status}). Skipping reprocessing.",
                    extra={"job_id": str(job_id), "worker": "ResearchWorker"},
                )
                return

            # 2. STATUS UPDATE: Mark as PROCESSING
            logging.info(
                f"Picked up. Status -> PROCESSING",
                extra={"job_id": str(job_id), "worker": "ResearchWorker"},
            )
            job.status = JobStatus.PROCESSING
            db.commit()
            db.refresh(job)  # Refresh to get the updated timestamp if you have one
            await publish_status_update(job, producer)

            # 3. AI WORKFLOW
            research_text, video_text, pdf_bytes = await run_ai_research(
                job.research_topic, job.source_video_url, job.id
            )

            # 4. S3 UPLOAD
            s3_object_key = f"reports/{job.user_id}/{job.id}.pdf"
            await upload_to_s3(
                pdf_bytes, settings.AWS_S3_BUCKET_NAME, s3_object_key, job.id
            )

            # 5. FINALIZE JOB and PUBLISH UPDATE
            logging.info(
                f"Finalizing. Status -> COMPLETED",
                extra={"job_id": str(job_id), "worker": "ResearchWorker"},
            )
            job.status = JobStatus.COMPLETED
            job.research_text = research_text
            job.video_text = video_text
            job.report_url = s3_object_key
            db.commit()
            db.refresh(job)
            await publish_status_update(job, producer)

        except Exception as e:
            logging.error(
                f"An error occurred during research processing: {e}",
                extra={"job_id": str(job_id), "worker": "ResearchWorker"},
            )
            if "job" in locals() and job:
                db.rollback()
                job.status = JobStatus.FAILED
                db.commit()
                db.refresh(job)
                await publish_status_update(job, producer)
                logging.info(f"Status -> FAILED", extra={"job_id": str(job_id)})
        finally:
            db.close()
            logging.info(
                f"Research Processing finished.",
                extra={"job_id": str(job_id), "worker": "ResearchWorker"},
            )


# KAFKA CONSUMER MAIN LOOP
async def main():
    """The main function that runs the Kafka consumer in a robust loop."""
    producer = None
    while True:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )
            await producer.start()

            consumer = AIOKafkaConsumer(
                settings.KAFKA_RESEARCH_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="research_worker_group",
                auto_offset_reset="earliest",
            )
            await consumer.start()
            logging.info(
                "Research worker started successfully. Waiting for messages...",
                extra={"worker": "ResearchWorker"},
            )

            async for msg in consumer:
                try:
                    job_id_str = msg.value.decode("utf-8")
                    job_id = uuid.UUID(job_id_str)
                    logging.info(f"Received message", extra={"job_id": str(job_id)})
                    asyncio.create_task(process_job(job_id, producer))
                except Exception as e:
                    logging.error(
                        f"Error processing message value: {msg.value}. Error: {e}",
                        extra={"job_id": "unknown", "worker": "ResearchWorker"},
                    )

        except Exception as e:
            logging.error(
                f"Kafka consumer connection failed: {e}. Retrying in 10 seconds...",
                extra={"worker": "ResearchWorker"},
            )
            await asyncio.sleep(10)
        finally:
            if producer:
                await producer.stop()
            if "consumer" in locals():
                await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
