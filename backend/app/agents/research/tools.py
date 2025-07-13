from app.core.llm import genai_client
from app.prompts.research import report_base
from langchain_core.prompts import PromptTemplate


def create_research_report(
    topic, research_text, video_text, search_sources_text, video_url, configuration=None
):
    """Create a comprehensive research report by synthesizing search and video content"""

    # Use default values if no configuration provided
    if configuration is None:
        from core.config import Configuration

        configuration = Configuration()

    # Step 1: Create synthesis using Gemini
    synthesis_prompt = PromptTemplate.from_template(report_base).invoke(
        {
            "topic": topic,
            "research_text": research_text,
            "video_text": video_text,
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
        f"# Research Report: {topic}",
        "## Executive Summary",
        synthesis_text,
    ]

    if video_url:
        report_sections.append(f"## Video Source\n- **URL**: {video_url}")

    report_sections.append(f"## Additional Sources\n{search_sources_text}")
    # Add footer
    report_sections.append(
        "---\n*Report generated using multi-modal AI research combining web search and video analysis*"
    )
    report = "\n\n".join(report_sections)

    return report
