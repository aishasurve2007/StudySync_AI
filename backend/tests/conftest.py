"""
Shared test fixtures.

Each test gets a FRESH in-memory SQLite database (function-scoped), so tests
are fully isolated — one test can never leave data that breaks another. We
swap the real Postgres connection for this test DB using FastAPI's
`dependency_overrides`, which is the intended way to inject test doubles
without touching application code.
"""
# Force a hermetic test environment BEFORE any app module is imported.
# This guarantees the suite never connects to a real database (no psycopg2
# needed) and never reads the developer's .env — tests must be reproducible.
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 -- registers all models on Base.metadata
from app.core.database import Base, get_db
from app.main import app

# A canonical valid profile payload tests can copy and tweak.
VALID_PROFILE = {
    "course": "Computer Science",
    "year": 2,
    "subjects": ["Machine Learning", "Statistics"],
    "learning_style": "practice",
    "preferred_study_time": "evening",
    "study_environment": "quiet",
    "study_intensity": "intensive",
    "current_goal": "Prepare ML interview",
    "daily_goal_hours": 3,
    "motivation_type": "achievement",
    "experience_level": "intermediate",
}


@pytest.fixture()
def client():
    # StaticPool keeps a single shared connection, so every session in this
    # test sees the same in-memory database.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def auth_client(client):
    """A `client` already registered and carrying a valid bearer token."""
    resp = client.post(
        "/auth/register",
        json={
            "email": "tester@example.com",
            "password": "supersecret1",
            "name": "Tester",
            "timezone": "Asia/Kolkata",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
