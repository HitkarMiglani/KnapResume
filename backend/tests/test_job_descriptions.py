def test_create_job_description_requires_csrf(client):
    client.post("/api/auth/register", json={"email": "x@example.com", "password": "correct-horse"})
    resp = client.post("/api/job-descriptions", json={"raw_text": "We need a Python developer"})
    assert resp.status_code == 403


def test_create_job_description_persists_and_returns_parsed_fields(registered_client):
    resp = registered_client.post(
        "/api/job-descriptions",
        json={"raw_text": "Senior Python engineer with Docker and React experience needed"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "python" in body["skills"]
    assert "docker" in body["skills"]
    assert "react" in body["skills"]
    assert body["seniority"] == "senior"
    assert isinstance(body["keywords"], list)
    assert body["raw_text"] == "Senior Python engineer with Docker and React experience needed"


def test_list_job_descriptions_is_owner_scoped(registered_client, client):
    registered_client.post("/api/job-descriptions", json={"raw_text": "Python developer role"})

    other = client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "correct-horse"}
    )
    other_csrf = other.json()["csrf_token"]
    client.headers.update({"X-CSRF-Token": other_csrf})
    other_list = client.get("/api/job-descriptions")
    assert other_list.json() == []


def test_get_job_description_404_for_missing(registered_client):
    resp = registered_client.get("/api/job-descriptions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_get_job_description_404_for_other_owner(registered_client, client):
    created = registered_client.post(
        "/api/job-descriptions", json={"raw_text": "Python developer role"}
    ).json()

    other = client.post(
        "/api/auth/register", json={"email": "other2@example.com", "password": "correct-horse"}
    )
    other_csrf = other.json()["csrf_token"]
    client.headers.update({"X-CSRF-Token": other_csrf})
    resp = client.get(f"/api/job-descriptions/{created['id']}")
    assert resp.status_code == 404


def test_delete_job_description_requires_csrf(registered_client):
    created = registered_client.post(
        "/api/job-descriptions", json={"raw_text": "Python developer role"}
    ).json()
    resp = registered_client.delete(
        f"/api/job-descriptions/{created['id']}", headers={"X-CSRF-Token": ""}
    )
    assert resp.status_code == 403


def test_delete_job_description_removes_the_row(registered_client):
    created = registered_client.post(
        "/api/job-descriptions", json={"raw_text": "Python developer role"}
    ).json()

    resp = registered_client.delete(f"/api/job-descriptions/{created['id']}")
    assert resp.status_code == 204

    listed = registered_client.get("/api/job-descriptions")
    assert listed.json() == []


def test_completeness_endpoint_returns_per_section_and_overall_scores(registered_client):
    registered_client.post("/api/bullets", json={"section": "skill", "raw_text": "Python"})

    resp = registered_client.get("/api/profile/completeness")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"experience", "project", "education", "skill", "overall"}
    assert body["skill"] > 0.0
