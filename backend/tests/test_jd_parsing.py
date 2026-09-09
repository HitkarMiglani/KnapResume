import json
from io import BytesIO

import pytest

from app.config import settings
from app.jd_parsing import AIParsingError, parse_job_description


def test_known_skill_terms_are_detected():
    skills, _keywords, _seniority = parse_job_description(
        "We need someone skilled in Python, React, and Docker."
    )
    assert skills == ["python", "docker", "react"] or set(skills) == {"python", "docker", "react"}


def test_unknown_noise_text_produces_minimal_results():
    skills, keywords, seniority = parse_job_description("asdf qwer zxcv!!! 123")
    assert skills == []
    assert seniority is None
    # noise words are still tokenized as keywords since they aren't stopwords
    assert all(len(word) >= 3 for word in keywords)


def test_seniority_title_term_is_detected():
    _skills, _keywords, seniority = parse_job_description("Looking for a Senior Engineer")
    assert seniority == "senior"


def test_seniority_years_of_experience_is_detected():
    _skills, _keywords, seniority = parse_job_description("Requires 5+ years of experience")
    assert seniority == "mid"


def test_seniority_years_of_experience_senior_threshold():
    _skills, _keywords, seniority = parse_job_description("Requires 8+ years of experience")
    assert seniority == "senior"


def test_seniority_years_of_experience_junior_threshold():
    _skills, _keywords, seniority = parse_job_description("Requires 2 years of experience")
    assert seniority == "junior"


def test_no_seniority_signal_returns_none():
    _skills, _keywords, seniority = parse_job_description("We build great software for customers")
    assert seniority is None


def test_keywords_are_deduplicated_stopword_filtered_and_ordered():
    _skills, keywords, _seniority = parse_job_description(
        "The team needs the team to ship features and features"
    )
    assert keywords == ["needs", "ship", "features"]


def test_configured_ai_provider_parses_structured_response(monkeypatch):
    response = {"choices": [{"message": {"content": json.dumps({
        "skills": ["Python", "python", "FastAPI"],
        "keywords": ["distributed systems", "backend"],
        "seniority": "senior",
    })}}]}

    class FakeResponse(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    monkeypatch.setattr(settings, "ai_api_key", "test-key")
    monkeypatch.setattr("app.jd_parsing.urlopen", lambda *_args, **_kwargs: FakeResponse(
        json.dumps(response).encode()
    ))

    skills, keywords, seniority = parse_job_description("Senior backend role")

    assert skills == ["python", "fastapi"]
    assert keywords == ["distributed systems", "backend"]
    assert seniority == "senior"


def test_configured_ai_provider_errors_are_not_hidden(monkeypatch):
    monkeypatch.setattr(settings, "ai_api_key", "test-key")
    monkeypatch.setattr(
        "app.jd_parsing.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()),
    )

    with pytest.raises(AIParsingError):
        parse_job_description("Python role")
