import asyncio
import logging
import os
import sys
import uuid
from typing import Literal

from app.core.config import settings
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from weasyprint import CSS, HTML

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


def create_pdf_from_text(markdown_text: str, job_id: str) -> bytes:
    """
    Creates a high-fidelity PDF file from a Markdown string using WeasyPrint.

    Args:
        markdown_text: The string containing the Markdown content.
        job_id: The ID of the job for logging purposes.
    Returns:
        The PDF content as a bytes object.
    """
    try:
        # This function will be called by markdown-it when it finds a code block
        def highlight_code(code, name, attrs):
            try:
                lexer = get_lexer_by_name(name)
            except:
                lexer = get_lexer_by_name("text")
            formatter = HtmlFormatter()
            return highlight(code, lexer, formatter)

        md = (
            MarkdownIt(
                "commonmark",
                options_update={
                    "breaks": True,
                    "html": True,
                    "highlight": highlight_code,
                },
            )
            .enable("strikethrough")
            .enable("table")
        )

        html_content = md.render(markdown_text)

        formatter = HtmlFormatter(style="default")
        syntax_highlight_css = formatter.get_style_defs(".highlight")

        custom_css = f"""
            @page {{
                size: A4;
                margin: 1cm;
            }}
            body {{
                font-family: 'DejaVu Sans', sans-serif;
                font-size: 12px;
            }}
            h1, h2, h3, h4, h5, h6 {{
                font-family: 'DejaVu Sans', sans-serif;
            }}
            code, pre {{
                font-family: 'DejaVu Sans Mono', monospace;
                font-size: 11px;
            }}
            .highlight pre {{
                border-radius: 4px;
                padding: 10px;
                overflow: auto;
            }}
            {syntax_highlight_css}
        """

        html = HTML(string=html_content)
        css = CSS(string=custom_css)

        # The write_pdf method returns the PDF as bytes
        return html.write_pdf(stylesheets=[css])

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(
            f"Error generating PDF: {e}",
            extra={"job_id": job_id, "worker": "ResearchWorker"},
        )
        raise
