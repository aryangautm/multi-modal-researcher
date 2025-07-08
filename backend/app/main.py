from contextlib import asynccontextmanager

from app.api.v1.routes import api_router as v1_router
from app.core.auth import get_current_user, initialize_firebase_app
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase_app()
    yield


app = FastAPI(title="Multi-Modal AI Researcher API", lifespan=lifespan)


# Middleware can be added here
# e.g., app.add_middleware(...)


app.include_router(v1_router, prefix="/api/v1")


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
