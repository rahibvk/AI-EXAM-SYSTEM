from dotenv import load_dotenv
import os

load_dotenv()

# Startup Check
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings

app = FastAPI(title="AI Exam System API")

# Set up CORS
# Allow all for dev
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to AI Exam System API"}
