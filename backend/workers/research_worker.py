import asyncio
import uuid
from io import BytesIO

import boto3
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import db as database
from app.models.session import ResearchJob, JobStatus


async def run_ai_research(topic: str, video_url: str | None) -> tuple[str, bytes]:
    """
    Runs the AI research process for a given topic and optional video URL.

    Args:
        topic: The research topic.
        video_url: The optional video URL.

    Returns:
        A tuple containing (summary_string, pdf_file_bytes).
    """
    print(f"AI Agent: Starting research on '{topic}'...")
    if video_url:
        print(f"AI Agent: Analyzing video at {video_url}...")

    await asyncio.sleep(
        10
    )  # TODO: Replace with actual AI processing logic (./app/agents/ implementation)

    summary = f"This is a comprehensive summary about {topic}. The research indicates significant findings."

    # PDF generation
    pdf_content = f"PDF Report\n\nTopic: {topic}\n\nThis is the full report content."
    pdf_bytes = pdf_content.encode("utf-8")

    print("AI Agent: Research and report generation complete.")
    return summary, pdf_bytes


async def upload_to_s3(file_bytes: bytes, bucket: str, object_name: str) -> bool:
    """
    Uploads a file-like object to an S3 bucket asynchronously.

    Args:
        file_bytes: The bytes of the file to upload.
        bucket: The target S3 bucket.
        object_name: The desired key (path) for the object in S3.

    Returns:
        True if upload was successful, False otherwise.
    """
    print(f"S3 Uploader: Uploading {object_name} to bucket {bucket}...")
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        # Boto3 operations are blocking, so running them in a thread pool
        # to not block the asyncio event loop.
        await asyncio.to_thread(
            s3_client.upload_fileobj, BytesIO(file_bytes), bucket, object_name
        )
        print("S3 Uploader: Upload successful.")
        return True
    except Exception as e:
        print(f"S3 Uploader: ERROR - Failed to upload to S3: {e}")
        return False


async def process_job(job_id: uuid.UUID):
    """
    Processes a single research job from start to finish.
    """
    db: Session = database.SessionLocal
    try:
        # Fetch the job from the database
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            print(f"ERROR: Job {job_id} not found in database. Skipping.")
            return

        # CRITICAL: Update status to PROCESSING immediately
        print(f"[{job.id}] Picked up. Status -> PROCESSING")
        job.status = JobStatus.PROCESSING
        db.commit()

        summary, pdf_bytes = await run_ai_research(
            job.research_topic, job.source_video_url
        )

        # Upload the resulting PDF to S3
        s3_object_key = f"reports/{job.user_id}/{job.id}.pdf"
        upload_success = await upload_to_s3(
            pdf_bytes, settings.AWS_S3_BUCKET_NAME, s3_object_key
        )

        if not upload_success:
            raise Exception("Failed to upload report to S3.")

        print(f"[{job.id}] Finalizing. Status -> COMPLETED")
        job.status = JobStatus.COMPLETED
        job.summary = summary
        job.report_url = s3_object_key
        db.commit()

    except Exception as e:
        print(f"[{job_id}] An error occurred during processing: {e}")
        if "job" in locals() and job:
            job.status = JobStatus.FAILED
            db.commit()
            print(f"[{job_id}] Status -> FAILED")
    finally:
        db.close()
        print(f"[{job_id}] Processing finished.")


async def main():
    """
    The main function that sets up and runs the Kafka consumer.
    """
    consumer = AIOKafkaConsumer(
        settings.KAFKA_RESEARCH_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="research_worker_group",  # Use a group_id for consumer groups
        auto_offset_reset="earliest",  # Start reading at the earliest message if no offset is stored
    )

    await consumer.start()
    print("Research worker started. Waiting for messages...")
    try:
        # This loop will run forever, processing messages as they arrive
        async for msg in consumer:
            job_id_str = msg.value.decode("utf-8")
            print(f"\nReceived message: Job ID {job_id_str}")
            try:
                job_id = uuid.UUID(job_id_str)
                # Process each job concurrently without blocking the consumer loop
                asyncio.create_task(process_job(job_id))
            except ValueError:
                print(f"ERROR: Received invalid UUID in message: {job_id_str}")
    finally:
        await consumer.stop()
        print("Research worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
