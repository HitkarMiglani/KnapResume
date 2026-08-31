def test_create_bullet_normalizes_and_persists(registered_client):
    resp = registered_client.post(
        "/api/bullets", json={"section": "project", "raw_text": "- Built a thing  "}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["normalized_text"] == "Built a thing"
    assert body["raw_text"] == "- Built a thing  "
    assert body["section"] == "project"


def test_create_bullet_rejects_invalid_section(registered_client):
    resp = registered_client.post(
        "/api/bullets", json={"section": "hobbies", "raw_text": "Something"}
    )
    assert resp.status_code == 422


def test_create_bullet_requires_csrf(client):
    client.post("/api/auth/register", json={"email": "x@example.com", "password": "correct-horse"})
    resp = client.post("/api/bullets", json={"section": "skill", "raw_text": "Python"})
    assert resp.status_code == 403


def test_list_bullets_is_owner_scoped(registered_client, client):
    registered_client.post("/api/bullets", json={"section": "skill", "raw_text": "Python"})

    other = client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "correct-horse"}
    )
    other_csrf = other.json()["csrf_token"]
    client.headers.update({"X-CSRF-Token": other_csrf})
    other_list = client.get("/api/bullets")
    assert other_list.json() == []


def test_delete_bullet_removes_source_fact(registered_client):
    created = registered_client.post(
        "/api/bullets", json={"section": "skill", "raw_text": "Python"}
    ).json()

    resp = registered_client.delete(f"/api/bullets/{created['id']}")
    assert resp.status_code == 204

    listed = registered_client.get("/api/bullets")
    assert listed.json() == []


def test_delete_missing_bullet_is_404(registered_client):
    resp = registered_client.delete("/api/bullets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
