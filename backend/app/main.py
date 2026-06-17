"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Interactive API docs are then at http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, auth, coach, dashboard, focus, matching, productivity, profiles, rooms, tasks
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
app.include_router(matching.router)
app.include_router(tasks.router)
app.include_router(focus.router)
app.include_router(productivity.router)
app.include_router(dashboard.router)
app.include_router(coach.router)
app.include_router(rooms.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Real-time (Phase 2) ---
# `app` stays a pure FastAPI app (used by tests and all HTTP routes).
# `socket_app` wraps it with the Socket.IO server for WebSocket support.
# Run the full app (HTTP + WebSockets) with:  uvicorn app.main:socket_app
import socketio  # noqa: E402
from app.realtime.socket import sio  # noqa: E402

socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="socket.io")
