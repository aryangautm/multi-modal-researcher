from typing import Literal, Optional

from typing_extensions import TypedDict


class ResearchStateInput(TypedDict):
    """State for the research and podcast generation workflow"""

    # Input fields
    topic: str
    video_url: Optional[str]


class ResearchStateOutput(TypedDict):
    """State for the research and podcast generation workflow"""

    # Final outputs
    report: Optional[str]
    research_text: Optional[str]
    video_text: Optional[str]

    validation_result: Literal["passed", "failed"]
    failure_reason: Optional[str]


class ResearchState(TypedDict):
    """State for the research and podcast generation workflow"""

    # Input fields
    topic: str
    video_url: Optional[str]

    # Intermediate results
    search_sources_text: Optional[str]

    # Final outputs
    report: Optional[str]
    research_text: Optional[str]
    video_text: Optional[str]

    # Validation results
    validation_result: Literal["passed", "failed"]
    failure_reason: Optional[str]
