from pydantic import BaseModel


class CreatePodcastRequest(BaseModel):
    session_id: str
