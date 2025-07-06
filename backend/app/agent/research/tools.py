from core.llm import genai_client
from langchain_core.prompts import PromptTemplate
from prompts.research_report import report_base


def create_research_report(
    topic, search_text, video_text, search_sources_text, video_url, configuration=None
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
            "search_text": search_text,
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
    report = f"""# Research Report: {topic}

            ## Executive Summary

            {synthesis_text}

            ## Video Source
            - **URL**: {video_url}

            ## Additional Sources
            {search_sources_text}

            ---
            *Report generated using multi-modal AI research combining web search and video analysis*
            """

    return report, synthesis_text
