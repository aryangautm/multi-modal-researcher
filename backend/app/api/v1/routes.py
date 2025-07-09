from fastapi import APIRouter

from .endpoints import research

api_router = APIRouter()

api_router.include_router(research.router, prefix="/v1", tags=["Research"])
