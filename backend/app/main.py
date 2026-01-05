"""
Main Application Entry Point

Purpose:
    Initializes the FastAPI application, configures middleware (CORS, Error Handling),
    and includes the main API router.

Features:
    - **Startup Checks**: Verifies `OPENAI_API_KEY` presence.
    - **CORS Config**: Currently permissive ("*") for ease of development.
    - **Global Exception Handler**: Catches 500 errors and returns debug info (useful for dev).
    - **Routing**: Mounts all API endpoints under `/api/v1`.
"""
from dotenv import load_dotenv
import os

load_dotenv()

# Startup Check: Verify dependencies before loading the full app
key = os.getenv("OPENAI_API_KEY")
if not key:
    print("\n" + "="*50)
    print("WARNING: OPENAI_API_KEY is NOT set in .env")
    print("AI features will run in MOCK mode.")
    print("="*50 + "\n")
elif key.startswith("sk-place"):
    print("\n" + "="*50)
    print("WARNING: OPENAI_API_KEY is set to PLACEHOLDER.")
    print("Please update .env with your real key.")
    print("="*50 + "\n")
else:
    print(f"INFO: OPENAI_API_KEY loaded successfully (starts with {key[:4]}...)")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings

app = FastAPI(title="AI Exam System API")

# Set up CORS (Cross-Origin Resource Sharing)
# Allow all origins ("*") for development flexibility.
# In production, this should be restricted to the frontend domain.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """
    Global catch-all exception middleware.
    Prints stack trace to console and returns a generic 500 JSON response.
    Preventing the server from crashing silently.
    """
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "debug_error": str(e)},
        )

# Register Routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Welcome to AI Exam System API"}

# Force reload triggers
