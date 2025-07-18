import asyncio
import logging
import os
import sys
import uuid
from typing import Literal

from app.core.config import settings
from fpdf import FPDF

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from io import BytesIO

import boto3
from app.utils.logging import handler
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, handlers=[handler])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def upload_to_s3(
    file_bytes: bytes,
    bucket: str,
    object_name: str,
    job_id: uuid.UUID,
    worker: Literal["ResearchWorker", "PodcastWorker"] = "ResearchWorker",
) -> bool:
    logging.info(
        f"S3 Uploader: Uploading {object_name}",
        extra={"job_id": str(job_id), "worker": "ResearchWorker"},
    )
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_INTERNAL_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        await asyncio.to_thread(
            s3_client.upload_fileobj, BytesIO(file_bytes), bucket, object_name
        )
        logging.info(
            "S3 Uploader: Upload successful",
            extra={"job_id": str(job_id), "worker": worker},
        )
        return True
    except Exception as e:
        logging.error(
            f"S3 Uploader: Failed to upload to S3: {e}",
            extra={"job_id": str(job_id), "worker": worker},
        )
        raise  # Re-raise the exception to trigger tenacity's retry mechanism


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
