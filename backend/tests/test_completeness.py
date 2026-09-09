def test_empty_profile_gives_zero_scores(registered_client):
    resp = registered_client.get("/api/profile/completeness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["experience"] == 0.0
    assert body["project"] == 0.0
    assert body["education"] == 0.0
    assert body["skill"] == 0.0
    assert body["overall"] == 0.0


def test_adding_facts_raises_that_sections_score(registered_client):
    registered_client.post("/api/bullets", json={"section": "skill", "raw_text": "Python"})

    resp = registered_client.get("/api/profile/completeness")
    body = resp.json()
    assert body["skill"] == 0.2
    assert body["experience"] == 0.0


def test_scores_are_bounded_within_zero_and_one(registered_client):
    for i in range(10):
        registered_client.post(
            "/api/bullets", json={"section": "education", "raw_text": f"Fact {i}"}
        )

    resp = registered_client.get("/api/profile/completeness")
    body = resp.json()
    assert body["education"] == 1.0
    assert 0.0 <= body["overall"] <= 1.0


def test_overall_score_is_average_of_section_scores(registered_client):
    registered_client.post("/api/bullets", json={"section": "skill", "raw_text": "Python"})
    registered_client.post("/api/bullets", json={"section": "education", "raw_text": "Degree"})

    resp = registered_client.get("/api/profile/completeness")
    body = resp.json()
    expected_overall = (
        body["experience"] + body["project"] + body["education"] + body["skill"]
    ) / 4
    assert body["overall"] == expected_overall
