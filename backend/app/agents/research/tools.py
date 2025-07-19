import logging

import isodate
from app.core.config import settings
from app.core.llm import genai_client
from app.prompts.research import report_base
from googleapiclient.discovery import build
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


def create_research_report(
    topic, research_text, video_text, search_sources_text, video_url, configuration=None
):
    """Create a comprehensive research report by synthesizing search and video content"""

    # Use default values if no configuration provided
    if configuration is None:
        from core.config import Configuration

        configuration = Configuration()

    # Step 1: Create synthesis using Gemini
    sources = [f"SEARCH RESULTS\n{research_text}"]
    if video_text:
        sources.append(f"VIDEO CONTENT\n{video_text}")
    synthesis_prompt = PromptTemplate.from_template(report_base).invoke(
        {
            "topic": topic,
            "sources": "\n\n".join(sources),
        }
    )

    synthesis_response = genai_client.models.generate_content(
        model=configuration.synthesis_model,
        contents=synthesis_prompt,
        config={
            "temperature": configuration.synthesis_temperature,
        },
    )

    synthesis_text = synthesis_response.candidates[0].content.parts[0].text

    # Step 2: Create markdown report
    report_sections = [
        f"<h2 style='text-align: center;'><strong>{topic.title()}</strong></h1>",
        research_text,
        "### Executive Summary",
        synthesis_text,
    ]

    if video_url:
        report_sections.append(f"### Video Source\n- **URL**: {video_url}")

    report_sections.append(f"### References\n{search_sources_text}")
    # Add footer
    report_sections.append("---\n*Report generated using Scholar AI*")
    report = "\n\n".join(report_sections)

    return report, synthesis_text


def fetch_video_metadata(video_url: str) -> dict:
    """
    Fetches video title, description, and duration using the YouTube Data API v3.
    Args:
        url (str): The YouTube video URL.
    Returns:
        dict: A dictionary with title, description, and duration, or None on error.
    """
    try:
        video_id = video_url.split("v=")[1]
        youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_DATA_API_KEY)

        # Make the API request
        request = youtube.videos().list(
            part="snippet,contentDetails",  # Parts of the video resource to retrieve
            id=video_id,
        )
        response = request.execute()

        if not response.get("items"):
            print("Video not found.")
            return None

        video_item = response["items"][0]

        # --- Extract Information ---
        title = video_item["snippet"]["title"]
        description = video_item["snippet"]["description"]

        # Duration comes in ISO 8601 format (e.g., 'PT1H2M12S')
        iso_duration = video_item["contentDetails"]["duration"]
        duration_timedelta = isodate.parse_duration(iso_duration)
        duration_seconds = int(duration_timedelta.total_seconds())

        video_details = {
            "title": title,
            "description": description,
            "duration": duration_seconds,
        }

        return video_details

    except Exception as e:
        logger.error(f"Error fetching video metadata from url: {e}")
        raise
