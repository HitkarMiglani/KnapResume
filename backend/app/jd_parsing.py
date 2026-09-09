import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings

# Small curated set of common tech/professional skills matched verbatim (case-insensitive).
CURATED_SKILLS = (
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "rust",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "react",
    "vue",
    "angular",
    "node.js",
    "django",
    "flask",
    "fastapi",
    "spring",
    "git",
    "linux",
    "ci/cd",
    "rest",
    "graphql",
    "html",
    "css",
    "terraform",
    "ansible",
    "machine learning",
    "data analysis",
    "agile",
    "scrum",
    "leadership",
    "communication",
)

SENIORITY_TERMS = ("principal", "staff", "senior", "lead", "junior", "intern")

_YEARS_PATTERN = re.compile(r"(\d{1,2})\s*\+?\s*years?", re.IGNORECASE)
_WORD_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z\-]{2,}")

STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "are",
        "with",
        "you",
        "our",
        "have",
        "will",
        "this",
        "that",
        "your",
        "role",
        "job",
        "work",
        "team",
        "able",
        "skills",
        "experience",
        "years",
        "strong",
        "including",
        "using",
        "who",
        "can",
        "must",
        "such",
        "into",
        "from",
        "than",
        "they",
        "them",
        "not",
        "all",
        "any",
        "was",
        "were",
        "has",
        "had",
        "but",
        "about",
        "across",
        "within",
        "other",
        "more",
        "most",
        "some",
        "each",
        "may",
        "also",
        "its",
        "per",
    }
)


def extract_skills(raw_text: str) -> list[str]:
    """Match the curated skill list against the JD text, case-insensitive, whole-token."""
    lowered = raw_text.lower()
    found = []
    for skill in CURATED_SKILLS:
        pattern = re.escape(skill)
        if re.search(rf"(?<!\w){pattern}(?!\w)", lowered):
            found.append(skill)
    return found


def extract_keywords(raw_text: str) -> list[str]:
    """Extract deduplicated, stopword-filtered salient tokens in first-seen order."""
    lowered = raw_text.lower()
    keywords: list[str] = []
    for word in _WORD_PATTERN.findall(lowered):
        if word in STOPWORDS or word in keywords:
            continue
        keywords.append(word)
    return keywords


def extract_seniority(raw_text: str) -> str | None:
    """Detect a seniority signal from title terms first, falling back to years-of-experience."""
    lowered = raw_text.lower()
    for term in SENIORITY_TERMS:
        if re.search(rf"\b{term}\b", lowered):
            return term

    match = _YEARS_PATTERN.search(lowered)
    if match:
        years = int(match.group(1))
        if years >= 8:
            return "senior"
        if years >= 3:
            return "mid"
        return "junior"

    return None


class AIParsingError(RuntimeError):
    """Raised when a configured AI provider cannot parse a job description."""


def _fallback_parse(raw_text: str) -> tuple[list[str], list[str], str | None]:
    return extract_skills(raw_text), extract_keywords(raw_text), extract_seniority(raw_text)


def _parse_ai_response(response: dict[str, Any]) -> tuple[list[str], list[str], str | None]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIParsingError("AI provider returned no choices")

    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise AIParsingError("AI provider returned no JSON content")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIParsingError("AI provider returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise AIParsingError("AI provider returned an invalid parse object")

    skills = parsed.get("skills")
    keywords = parsed.get("keywords")
    seniority = parsed.get("seniority")
    if (
        not isinstance(skills, list)
        or not all(isinstance(value, str) for value in skills)
        or not isinstance(keywords, list)
        or not all(isinstance(value, str) for value in keywords)
        or seniority is not None
        and seniority not in {*SENIORITY_TERMS, "mid"}
    ):
        raise AIParsingError("AI provider returned invalid parse fields")

    def clean(values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))

    return clean(skills), clean(keywords), seniority


def _parse_with_ai(raw_text: str) -> tuple[list[str], list[str], str | None]:
    endpoint = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.ai_model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract job-description signals. Return only a JSON object with exactly "
                    "these fields: skills (array of concise technical or professional skills), "
                    "keywords (array of concise role-specific keywords), and seniority "
                    "(one of principal, staff, senior, lead, junior, intern, mid, or null). "
                    "Do not infer skills that are not supported by the text."
                ),
            },
            {"role": "user", "content": raw_text},
        ],
    }
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.ai_timeout_seconds) as response:
            body = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AIParsingError("AI provider request failed") from exc

    if not isinstance(body, dict):
        raise AIParsingError("AI provider returned an invalid response")
    return _parse_ai_response(body)


def parse_job_description(raw_text: str) -> tuple[list[str], list[str], str | None]:
    if settings.ai_api_key:
        return _parse_with_ai(raw_text)
    return _fallback_parse(raw_text)
