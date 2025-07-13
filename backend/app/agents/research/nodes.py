from app.core.config import Configuration
from app.core.llm import genai_client
from app.utils.helpers import extract_text_and_sources
from google.genai import types
from langchain_core.runnables import RunnableConfig

from .state import ResearchState
from .tools import create_research_report


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
        # TODO: Validate video URL format and relevance
        return "analyze_video"
    else:
        return "create_report"
