from core.config import Configuration
from core.llm import genai_client
from google.genai import types
from langchain_core.runnables import RunnableConfig
from schemas.research import ResearchState
from utils.helpers import display_gemini_response

from .tools import create_research_report


def search_research_node(state: ResearchState, config: RunnableConfig) -> dict:
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

    search_text, search_sources_text = display_gemini_response(search_response)

    return {"search_text": search_text, "search_sources_text": search_sources_text}


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

    video_text, _ = display_gemini_response(video_response)

    return {"video_text": video_text}


def create_report_node(state: ResearchState, config: RunnableConfig) -> dict:
    """Node that creates a comprehensive research report"""
    configuration = Configuration.from_runnable_config(config)
    topic = state["topic"]
    search_text = state.get("search_text", "")
    video_text = state.get("video_text", "")
    search_sources_text = state.get("search_sources_text", "")
    video_url = state.get("video_url", "")

    report, synthesis_text = create_research_report(
        topic, search_text, video_text, search_sources_text, video_url, configuration
    )

    return {"report": report, "synthesis_text": synthesis_text}


def should_analyze_video(state: ResearchState) -> str:
    """Conditional edge to determine if video analysis should be performed"""
    if state.get("video_url"):
        # TODO: Validate video URL format and relevance
        return "analyze_video"
    else:
        return "create_report"
