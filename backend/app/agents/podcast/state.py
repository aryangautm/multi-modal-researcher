from typing import Optional

from typing_extensions import TypedDict


class PodcastStateInput(TypedDict):
    """State for the research and podcast generation workflow"""

    # Input fields
    topic: str
    research_text: Optional[str]
    video_text: Optional[str]


class PodcastStateOutput(TypedDict):
    """State for the research and podcast generation workflow"""

    # Final outputs
    podcast_script: Optional[str]
    podcast_audio_bytes: Optional[bytes]


class PodcastState(TypedDict):
    """State for the research and podcast generation workflow"""

    # Input fields
    topic: str
    research_text: Optional[str]
    video_text: Optional[str]

    # Final outputs
    podcast_script: Optional[str]
    podcast_audio_bytes: Optional[bytes]
