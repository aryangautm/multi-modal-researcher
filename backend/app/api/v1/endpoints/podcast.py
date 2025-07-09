from fastapi import APIRouter, Depends
from schemas.podcast import CreatePodcastRequest

router = APIRouter()


@router.post("/create", summary="Create a new podcast")
async def create_podcast(request: CreatePodcastRequest):
    return {
        "message": "Podcast creation initiated",
    }
