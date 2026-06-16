"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Interactive API docs are then at http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, auth, profiles
from app.core.config import settings

app = FastAPI(
    title="StudySync AI",
    version="0.1.0",
    description="AI-powered student accountability platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(ai.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
