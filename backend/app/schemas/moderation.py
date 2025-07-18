from typing import List, Literal, Optional

from pydantic import BaseModel, Field

UNSAFE_CATEGORIES = Literal[
    "HATE_SPEECH",
    "HARASSMENT",
    "SEXUALLY_EXPLICIT",
    "DANGEROUS",
    "CIVIC_INTEGRITY",
    "UNSAFE_CONTENT",
    "GARBAGE_JUNK",
    "PROMPT_INJECTION",
]


class ModerationResponse(BaseModel):
    validation_result: Literal["passed", "failed"] = Field(
        ...,
        description="Indicates whether the content passed moderation checks.",
    )
    failure_reason: Optional[List[UNSAFE_CATEGORIES]] = Field(
        None,
        description=f"""List of categories that the content failed moderation checks against.
        HATE_SPEECH: Content that is rude, disrespectful, or profane.
        HARASSMENT: Negative or harmful comments targeting identity and/or protected attributes.
        SEXUALLY_EXPLICIT: Contains references to sexual acts or other lewd content.
        DANGEROUS: Promotes, facilitates, or encourages harmful acts.
        CIVIC_INTEGRITY: Election-related queries.
        GARBAGE_JUNK: Random letters or nonsensical content.
        PROMPT_INJECTION: Attempts to trick the LLM into revealing internal instructions or system prompts
        """,
    )


class RelevanceCheckResponse(BaseModel):
    validation_result: Literal["passed", "failed"] = Field(
        ...,
        description="""Indicates whether the topic and video are relevant to each other.
        passed: The topic is relevant to the video. Video does not contain harmful content.
        failed: The topic is not relevant to the video or the video contains harmful content.
        """,
    )
