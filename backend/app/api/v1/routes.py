from fastapi import APIRouter

from .endpoints import research, websockets

api_router = APIRouter()

api_router.include_router(research.router, prefix="/v1", tags=["Research"])
api_router.include_router(websockets.router, prefix="/v1", tags=["WebSockets"])
