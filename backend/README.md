# StudySync AI — Backend

AI-powered student accountability platform. FastAPI · PostgreSQL · JWT.

> **Done: chunks 1–2** — Foundation + Auth, Student Profile + deterministic `goal_tags`.
> Tested with pytest (22 passing). Next: AI engine → matching → tasks/focus → analytics → frontend → Phase 2 (rooms + coach).

## Project structure

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py      # typed settings from env (single source of truth)
│   │   ├── database.py    # engine, session factory, get_db dependency
│   │   └── security.py    # bcrypt hashing + JWT issue/verify
│   ├── models/            # SQLAlchemy ORM models (write models / source of truth)
│   │   ├── enums.py       # shared domain enums + matching orderings
│   │   ├── user.py
│   │   └── student_profile.py
│   ├── schemas/           # Pydantic request/response contracts
│   │   ├── auth.py
│   │   └── profile.py
│   ├── services/
│   │   └── goal_tags.py   # deterministic, AI-independent tag extraction
│   ├── api/
│   │   ├── deps.py        # get_current_user (protected-route dependency)
│   │   ├── auth.py        # /auth/register, /auth/login, /auth/me
│   │   └── profiles.py    # /profiles  (create / update / me)
│   └── main.py            # app entrypoint + CORS + router wiring
├── tests/                 # pytest suite (isolated in-memory DB per test)
│   ├── conftest.py        # fixtures: test DB + auth helpers
│   ├── test_goal_tags.py  # unit tests for the tag extractor
│   ├── test_auth.py
│   └── test_profiles.py
├── alembic/               # database migrations (0001 users, 0002 profiles)
├── requirements.txt
├── requirements-dev.txt   # adds pytest, httpx
└── .env.example
```

## Run it locally

```bash
pip install -r requirements.txt
cp .env.example .env                                  # set DATABASE_URL + JWT_SECRET
python -c "import secrets; print(secrets.token_hex(32))"   # -> JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload
```

Interactive docs: **http://localhost:8000/docs**

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite runs against a throwaway in-memory SQLite database (no Postgres or
network needed), with a fresh DB per test for full isolation. Run it after
every change — it re-checks auth, profiles, and tag extraction so a new
feature can't silently break an old one.

## Endpoints so far

| Method | Path             | Auth | Purpose                              |
|--------|------------------|------|--------------------------------------|
| POST   | `/auth/register` | no   | Create account, returns a JWT        |
| POST   | `/auth/login`    | no   | Verify credentials, returns a JWT    |
| GET    | `/auth/me`       | yes  | Current user                         |
| POST   | `/profiles`      | yes  | Create study profile (runs goal_tags)|
| PUT    | `/profiles`      | yes  | Update study profile (re-runs tags)  |
| GET    | `/profiles/me`   | yes  | Current user's study profile         |
| GET    | `/health`        | no   | Liveness check                       |

## Design decisions (be ready to explain these)

- **Stateless JWT auth** — signed token carries the user id; no server session
  store, so any instance can verify it. Scales horizontally.
- **Schemas separate from ORM models** — schema = public contract, ORM = storage.
  Stops `password_hash` leaking; `goal_tags` is output-only (client can't set it).
- **bcrypt directly, not passlib** — passlib is unmaintained and breaks on
  current bcrypt; inputs truncated to bcrypt's 72-byte limit explicitly.
- **`goal_tags` is deterministic, not AI** — `extract_goal_tags()` runs on every
  profile write. Matching (§4) therefore works even if the AI provider is down.
- **Array columns** — Postgres `text[]` in prod (GIN-indexable for the matching
  candidate pre-filter), JSON on SQLite for tests, via `.with_variant()`.
- **`timezone` at signup** — streaks/active-days are bucketed by calendar day in
  the user's timezone, not server time (used in analytics).
