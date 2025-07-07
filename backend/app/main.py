from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from app.api.v1.routes import api_router as v1_router


app = FastAPI(title="ScholarAI Backend")


# Middleware can be added here
# e.g., app.add_middleware(...)


# Include search routes
app.include_router(v1_router, prefix="/api/v1")


@app.exception_handler(404)
async def not_found(req: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Not Found"})


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # No content response
