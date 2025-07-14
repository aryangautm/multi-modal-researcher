import logging
from contextlib import asynccontextmanager

from app.api.v1.routes import api_router
from app.core.auth import get_current_user, initialize_firebase_app
from app.core.config import settings
from app.core.messaging import initialize_kafka_producer, shutdown_kafka_producer
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    initialize_firebase_app()
    await initialize_kafka_producer()
    yield
    print("Application shutting down...")
    await shutdown_kafka_producer()


app = FastAPI(title="Multi-Modal AI Researcher API", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api")


@app.exception_handler(404)
async def not_found(req: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Not Found"})


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # No content response


# --- Test Endpoint ---
@app.get("/users/me", tags=["Users"])
async def read_current_user(current_user: dict = Depends(get_current_user)):
    """
    A protected endpoint that returns the authenticated user's Firebase UID.
    """
    # The `current_user` variable is the decoded token dictionary.
    return {"uid": current_user["uid"], "email": current_user.get("email")}
