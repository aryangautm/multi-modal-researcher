from typing import Optional

from typing_extensions import TypedDict


class PodcastStateInput(TypedDict):
    """State for the research and podcast generation workflow"""

    # Input fields
    topic: str
    video_url: Optional[str]


class PodcastStateOutput(TypedDict):
    """State for the research and podcast generation workflow"""

    # Final outputs
    podcast_script: Optional[str]
    podcast_filename: Optional[str]


class PodcastState(TypedDict):
    """State for the research and podcast generation workflow"""

    # Input fields
    topic: str

    # Intermediate results
    search_text: Optional[str]
    search_sources_text: Optional[str]
    video_text: Optional[str]

    # Final outputs
    podcast_script: Optional[str]
    podcast_filename: Optional[str]
