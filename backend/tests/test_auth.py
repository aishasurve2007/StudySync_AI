"""Auth endpoint tests (spec §1)."""


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_returns_token_and_user(client):
    r = client.post(
        "/auth/register",
        json={"email": "a@x.com", "password": "supersecret1", "name": "A", "timezone": "Asia/Kolkata"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "a@x.com"
    assert body["user"]["timezone"] == "Asia/Kolkata"
    # password / hash must never appear in the response
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_rejects_short_password(client):
    r = client.post("/auth/register", json={"email": "a@x.com", "password": "short", "name": "A"})
    assert r.status_code == 422  # pydantic validation


def test_duplicate_email_rejected(client):
    payload = {"email": "dup@x.com", "password": "supersecret1", "name": "A"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_login_success_and_failure(client):
    client.post("/auth/register", json={"email": "a@x.com", "password": "supersecret1", "name": "A"})
    assert client.post("/auth/login", json={"email": "a@x.com", "password": "supersecret1"}).status_code == 200
    assert client.post("/auth/login", json={"email": "a@x.com", "password": "wrong"}).status_code == 401
    assert client.post("/auth/login", json={"email": "nobody@x.com", "password": "supersecret1"}).status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_token(auth_client):
    r = auth_client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "tester@example.com"


def test_invalid_token_rejected(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
