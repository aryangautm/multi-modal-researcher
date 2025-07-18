from app.core.config import Configuration
from app.core.llm import genai_client
from app.prompts.moderation import moderation_base
from app.schemas.moderation import ModerationResponse, RelevanceCheckResponse
from app.utils.helpers import extract_text_and_sources
from google.genai import types
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from .state import ResearchState
from .tools import create_research_report, fetch_video_metadata


def guardrail_node(state: ResearchState, config: RunnableConfig) -> dict:
    """
    First node in the graph. Performs deep validation on the inputs.
    Returns a dictionary indicating whether to proceed or fail.
    """
    configuration = Configuration.from_runnable_config(config)
    topic = state["topic"]
    video_url = state.get("video_url")

    # 1. Harmful Content Check using a Moderation API
    moderation_prompt = PromptTemplate.from_template(moderation_base).invoke(
        {
            "topic": topic,
        }
    )

    response = genai_client.models.generate_content(
        model=configuration.moderation_model,
        contents=moderation_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ModerationResponse,
            "temperature": 0.0,
        },
    )

    moderation_result: ModerationResponse = response.parsed
    if moderation_result.validation_result == "failed":
        return {
            "validation_result": "failed",
            "failure_reason": moderation_result.failure_reason,
        }
    if video_url:
        try:
            video_data = fetch_video_metadata(video_url)

            # Video Length Check
            if video_data["duration"] > 6400:
                return {
                    "validation_result": "failed",
                    "failure_reason": "Video is too long (max 2 hour).",
                }

            # Relevance/Mismatch Check
            response = genai_client.models.generate_content(
                model=configuration.moderation_model,
                contents=f"""
                Check if the topic '{topic}' is relevant and related to the video metadata given below:
                Title: {video_data['title']}
                Description: {video_data['description']}

                If the topic and video are not related at all, return validation_result as "failed".
                If they are related, return validation_result as "passed".
                """,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RelevanceCheckResponse,
                    "temperature": 0.0,
                },
            )
            relevance_result: RelevanceCheckResponse = response.parsed
            if relevance_result.validation_result == "failed":
                return {
                    "validation_result": "failed",
                    "failure_reason": "The provided topic and YouTube video do not seem to be related.",
                }
        except Exception as e:
            return {
                "validation_result": "failed",
                "failure_reason": f"Could not process video URL",
            }

    return {"validation_result": "passed", "failure_reason": None}


def research_node(state: ResearchState, config: RunnableConfig) -> dict:
    """Node that performs web search research on the topic"""
    configuration = Configuration.from_runnable_config(config)
    topic = state["topic"]

    search_response = genai_client.models.generate_content(
        model=configuration.search_model,
        contents=f"Research this topic and give me an overview: {topic}",
        config={
            "tools": [{"google_search": {}}],
            "temperature": configuration.search_temperature,
        },
    )

    research_text, search_sources_text = extract_text_and_sources(search_response)

    return {"research_text": research_text, "search_sources_text": search_sources_text}


def analyze_video_node(state: ResearchState, config: RunnableConfig) -> dict:
    """Node that analyzes video content if video URL is provided"""
    configuration = Configuration.from_runnable_config(config)
    video_url = state.get("video_url")
    topic = state["topic"]

    if not video_url:
        return {"video_text": "No video provided for analysis."}

    video_response = genai_client.models.generate_content(
        model=configuration.video_model,
        contents=types.Content(
            parts=[
                types.Part(file_data=types.FileData(file_uri=video_url)),
                types.Part(
                    text=f"Based on the video content, give me an overview of this topic: {topic}"
                ),
            ]
        ),
    )

    video_text, _ = extract_text_and_sources(video_response)

    return {"video_text": video_text}


def create_report_node(state: ResearchState, config: RunnableConfig) -> dict:
    """Node that creates a comprehensive research report"""
    configuration = Configuration.from_runnable_config(config)
    topic = state["topic"]
    research_text = state.get("research_text", "")
    video_text = state.get("video_text", "")
    search_sources_text = state.get("search_sources_text", "")
    video_url = state.get("video_url", "")

    report = create_research_report(
        topic, research_text, video_text, search_sources_text, video_url, configuration
    )

    return {"report": report}


def should_analyze_video(state: ResearchState) -> str:
    """Conditional edge to determine if video analysis should be performed"""
    if state.get("video_url"):
        return "analyze_video"
    else:
        return "create_report"


def guardrail_check(state: ResearchState) -> str:
    """Determines the next step based on validation result."""
    if state.get("validation_result") == "failed":
        return "failed"
    return "passed"
