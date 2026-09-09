def test_register_sets_session_cookie_and_returns_csrf_token(client):
    resp = client.post(
        "/api/auth/register", json={"email": "new@example.com", "password": "correct-horse"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["csrf_token"]
    assert "session_id" in resp.cookies


def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dup@example.com", "password": "correct-horse"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_wrong_password_rejected(client):
    client.post("/api/auth/register", json={"email": "u@example.com", "password": "correct-horse"})
    resp = client.post("/api/auth/login", json={"email": "u@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_session_requires_cookie(client):
    resp = client.get("/api/auth/session")
    assert resp.status_code == 401


def test_logout_without_csrf_header_rejected(registered_client):
    resp = registered_client.post("/api/auth/logout", headers={"X-CSRF-Token": ""})
    assert resp.status_code == 403


def test_logout_revokes_session(registered_client):
    resp = registered_client.post("/api/auth/logout")
    assert resp.status_code == 204
    resp = registered_client.get("/api/auth/session")
    assert resp.status_code == 401


def test_account_deletion_revokes_session(registered_client):
    registered_client.post(
        "/api/bullets", json={"section": "skill", "raw_text": "Python"}
    )
    registered_client.post(
        "/api/job-descriptions", json={"raw_text": "Senior Python engineer, 5+ years"}
    )

    resp = registered_client.delete("/api/auth/account")
    assert resp.status_code == 204
    resp = registered_client.get("/api/auth/session")
    assert resp.status_code == 401

    from app.models import Bullet, JobDescription, SourceFact
    from tests.conftest import TestSessionLocal

    with TestSessionLocal() as db:
        assert db.query(Bullet).count() == 0
        assert db.query(SourceFact).count() == 0
        assert db.query(JobDescription).count() == 0
