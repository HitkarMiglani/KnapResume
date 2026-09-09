import uuid

from app.models import Bullet, ResumeImport, SourceFact


def test_import_resume_success_pdf(registered_client, monkeypatch):
    # Mock extract_text to return deterministic resume content
    resume_content = """
    Work Experience
    - Software Engineer at Acme Corp

    Technical Skills
    • Python, FastAPI, Docker
    """
    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text",
        lambda content, filename: resume_content,
    )

    pdf_data = b"dummy pdf data"
    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", pdf_data, "application/pdf")},
    )

    assert resp.status_code == 201
    body = resp.json()

    assert body["filename"] == "resume.pdf"
    assert body["file_type"] == "pdf"
    assert body["status"] == "completed"
    assert "id" in body
    assert "bullets" in body

    bullets = body["bullets"]
    assert len(bullets) == 2

    # Check first bullet matching 'Software Engineer at Acme Corp' under experience
    exp_bullet = next(b for b in bullets if b["section"] == "experience")
    assert exp_bullet["raw_text"] == "Software Engineer at Acme Corp"
    assert exp_bullet["normalized_text"] == "Software Engineer at Acme Corp"

    # Check second bullet matching 'Python, FastAPI, Docker' under skill
    skill_bullet = next(b for b in bullets if b["section"] == "skill")
    assert skill_bullet["raw_text"] == "Python, FastAPI, Docker"
    assert skill_bullet["normalized_text"] == "Python, FastAPI, Docker"


def test_import_resume_success_docx(registered_client, monkeypatch):
    # Mock extract_text to return deterministic resume content
    resume_content = """
    Technical Skills
    • Rust, Assembly
    """
    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text",
        lambda content, filename: resume_content,
    )

    docx_data = b"dummy docx data"
    resp = registered_client.post(
        "/api/profile/import",
        files={
            "file": (
                "resume.docx",
                docx_data,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "resume.docx"
    assert body["file_type"] == "docx"
    assert body["status"] == "completed"
    assert len(body["bullets"]) == 1
    assert body["bullets"][0]["normalized_text"] == "Rust, Assembly"


def test_import_resume_unauthorized(client):
    pdf_data = b"dummy pdf data"
    resp = client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", pdf_data, "application/pdf")},
    )
    assert resp.status_code == 401


def test_import_resume_missing_csrf(client):
    # Register but do not send CSRF token header
    client.post(
        "/api/auth/register",
        json={"email": "nocsrf@example.com", "password": "correct-horse"},
    )
    pdf_data = b"dummy pdf data"
    resp = client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", pdf_data, "application/pdf")},
    )
    assert resp.status_code == 403


def test_import_resume_too_large(registered_client):
    # Create content larger than 5MB
    large_data = b"A" * (5 * 1024 * 1024 + 1)
    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", large_data, "application/pdf")},
    )
    assert resp.status_code == 413
    assert "exceeds" in resp.json()["detail"]


def test_import_resume_invalid_format(registered_client):
    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("resume.txt", b"plain text", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Invalid file format" in resp.json()["detail"]


def test_import_resume_normalization_failures_safely_ignored(
    registered_client, monkeypatch
):
    # One bullet has valid text, the second bullet is empty/multiline which fails normalization
    # Specifically, a multiline string in a fact will raise NormalizationError
    resume_content = f"""
    Work Experience
    - Valid Bullet Text
    - {"A" * 501}
    """
    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text",
        lambda content, filename: resume_content,
    )

    pdf_data = b"dummy pdf data"
    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", pdf_data, "application/pdf")},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "completed"

    # Only one valid bullet should be inserted, the invalid one is ignored
    bullets = body["bullets"]
    assert len(bullets) == 1
    assert bullets[0]["normalized_text"] == "Valid Bullet Text"


def test_import_resume_general_exception_failed_status(registered_client, monkeypatch):
    # Trigger exception in extract_text to simulate general error
    def mock_extract_fails(content, filename):
        raise ValueError("Simulated parsing failure")

    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text", mock_extract_fails
    )

    pdf_data = b"dummy pdf data"
    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", pdf_data, "application/pdf")},
    )

    assert resp.status_code == 422
    assert "Resume processing failed" in resp.json()["detail"]

    # Verify that a ResumeImport record exists with 'failed' status,
    # and no SourceFact or Bullet records were committed for it.
    db = next(app_db_session())
    try:
        imports = db.query(ResumeImport).all()
        assert len(imports) == 1
        assert imports[0].status == "failed"

        facts = db.query(SourceFact).all()
        assert len(facts) == 0

        bullets = db.query(Bullet).all()
        assert len(bullets) == 0
    finally:
        db.close()


def test_list_resume_imports(registered_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text",
        lambda content, filename: "Technical Skills\n• Python",
    )

    # Make two imports
    r1 = registered_client.post(
        "/api/profile/import",
        files={"file": ("first.pdf", b"pdf1", "application/pdf")},
    )
    assert r1.status_code == 201

    r2 = registered_client.post(
        "/api/profile/import",
        files={"file": ("second.pdf", b"pdf2", "application/pdf")},
    )
    assert r2.status_code == 201

    # Fetch them
    resp = registered_client.get("/api/profile/imports")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body) == 2
    # Sorted by creation date DESC, so the second one should be first
    assert body[0]["filename"] == "second.pdf"
    assert body[1]["filename"] == "first.pdf"


def test_delete_resume_import_cascade(registered_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text",
        lambda content, filename: "Technical Skills\n• Web Development",
    )

    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("resume.pdf", b"pdf1", "application/pdf")},
    )
    assert resp.status_code == 201
    import_id = resp.json()["id"]

    # Verify records exist in DB
    db = next(app_db_session())
    try:
        assert db.query(ResumeImport).count() == 1
        assert db.query(SourceFact).count() == 1
        assert db.query(Bullet).count() == 1
    finally:
        db.close()

    # Delete the resume import
    del_resp = registered_client.delete(f"/api/profile/imports/{import_id}")
    assert del_resp.status_code == 204

    # Verify everything is cascaded and deleted perfectly
    db = next(app_db_session())
    try:
        assert db.query(ResumeImport).count() == 0
        assert db.query(SourceFact).count() == 0
        assert db.query(Bullet).count() == 0
    finally:
        db.close()


def test_delete_resume_import_not_found(registered_client):
    random_uuid = uuid.uuid4()
    resp = registered_client.delete(f"/api/profile/imports/{random_uuid}")
    assert resp.status_code == 404


def test_delete_resume_import_ownership(registered_client, client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.profile_imports.extract_text",
        lambda content, filename: "Technical Skills\n• Python",
    )

    # User 1 makes an import
    resp = registered_client.post(
        "/api/profile/import",
        files={"file": ("user1.pdf", b"pdf", "application/pdf")},
    )
    assert resp.status_code == 201
    import_id = resp.json()["id"]

    # User 2 logs in and tries to delete User 1's import
    user2 = client.post(
        "/api/auth/register",
        json={"email": "user2@example.com", "password": "correct-horse"},
    )
    user2_csrf = user2.json()["csrf_token"]
    client.headers.update({"X-CSRF-Token": user2_csrf})

    del_resp = client.delete(f"/api/profile/imports/{import_id}")
    assert del_resp.status_code == 404


def app_db_session():
    # Helper to get clean db session for test assertions
    from app.database import get_db
    return get_db()
