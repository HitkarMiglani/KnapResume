import json
from io import BytesIO

import pytest

from app.config import settings
from app.resume_parsing import (
    clean_line_bullet,
    extract_text,
    extract_text_from_docx,
    extract_text_from_pdf,
    parse_resume,
    parse_resume_fallback,
)


def test_extract_text_from_pdf(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class FakeReader:
        def __init__(self, stream):
            self.pages = [FakePage("Page 1 Content"), FakePage("Page 2 Content")]

    monkeypatch.setattr("pypdf.PdfReader", FakeReader)

    text = extract_text_from_pdf(b"dummy pdf bytes")
    assert text == "Page 1 Content\nPage 2 Content"


def test_extract_text_from_docx(monkeypatch):
    class FakePara:
        def __init__(self, text):
            self.text = text

    class FakeCell:
        def __init__(self, text):
            self.text = text

    class FakeRow:
        def __init__(self, cells):
            self.cells = cells

    class FakeTable:
        def __init__(self, rows):
            self.rows = rows

    class FakeDoc:
        def __init__(self, stream):
            self.paragraphs = [FakePara("Paragraph One"), FakePara("Paragraph Two")]
            self.tables = [
                FakeTable([FakeRow([FakeCell("Cell A"), FakeCell("Cell B")])])
            ]

    monkeypatch.setattr("docx.Document", FakeDoc)

    text = extract_text_from_docx(b"dummy docx bytes")
    assert text == "Paragraph One\nParagraph Two\nCell A\nCell B"


def test_extract_text_general(monkeypatch):
    monkeypatch.setattr(
        "app.resume_parsing.extract_text_from_pdf", lambda content: "PDF Extracted"
    )
    monkeypatch.setattr(
        "app.resume_parsing.extract_text_from_docx", lambda content: "DOCX Extracted"
    )

    assert extract_text(b"bytes", "resume.pdf") == "PDF Extracted"
    assert extract_text(b"bytes", "RESUME.PDF") == "PDF Extracted"
    assert extract_text(b"bytes", "resume.docx") == "DOCX Extracted"
    assert extract_text(b"bytes", "RESUME.DOCX") == "DOCX Extracted"

    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_text(b"bytes", "resume.txt")

    with pytest.raises(ValueError, match="Filename cannot be empty"):
        extract_text(b"bytes", "")


def test_clean_line_bullet():
    assert clean_line_bullet("- Normal Bullet") == "Normal Bullet"
    assert clean_line_bullet("* Another * Bullet") == "Another * Bullet"
    assert clean_line_bullet("• Unicode Bullet") == "Unicode Bullet"
    assert clean_line_bullet("▪ Square Bullet") == "Square Bullet"
    assert clean_line_bullet("1. Numbered List") == "Numbered List"
    assert clean_line_bullet("a) Alphabetic List") == "Alphabetic List"
    assert clean_line_bullet("(1) Parentheses List") == "Parentheses List"
    assert clean_line_bullet("No Bullet Text") == "No Bullet Text"


def test_parse_resume_fallback_flow():
    resume_text = """
    Work Experience
    - Backend software engineer at Acme Corp.
    - Designed scalable databases using postgres.

    Personal Projects & Portfolio
    * Created interactive dashboard using react and d3.

    Education & Certifications
    1. Chitkara University - Bachelor of Engineering
    (2) AWS Certified Cloud Practitioner

    Technical Skills
    • Python, TypeScript, Docker, PostgreSQL
    """

    facts = parse_resume_fallback(resume_text)

    # Filter out empty or header lines, and verify assignments
    exp = [f["raw_text"] for f in facts if f["section"] == "experience"]
    proj = [f["raw_text"] for f in facts if f["section"] == "project"]
    edu = [f["raw_text"] for f in facts if f["section"] == "education"]
    skill = [f["raw_text"] for f in facts if f["section"] == "skill"]

    assert "Backend software engineer at Acme Corp." in exp
    assert "Designed scalable databases using postgres." in exp
    assert "Created interactive dashboard using react and d3." in proj
    assert "Chitkara University - Bachelor of Engineering" in edu
    assert "AWS Certified Cloud Practitioner" in edu
    assert "Python, TypeScript, Docker, PostgreSQL" in skill


def test_parse_resume_ai_unconfigured():
    # If settings.ai_api_key is empty/None
    assert settings.ai_api_key is None or settings.ai_api_key == ""
    facts = parse_resume("Skills\n- Python")
    assert facts == [{"section": "skill", "raw_text": "Python"}]


def test_parse_resume_ai_authorized(monkeypatch):
    response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "facts": [
                                {"section": "skill", "raw_text": "Python"},
                                {"section": "experience", "raw_text": "Software Engineer"},
                            ]
                        }
                    )
                }
            }
        ]
    }

    class FakeResponse(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    monkeypatch.setattr(settings, "ai_api_key", "mocked-api-key")
    monkeypatch.setattr(
        "app.resume_parsing.urlopen",
        lambda *_args, **_kwargs: FakeResponse(json.dumps(response).encode("utf-8")),
    )

    facts = parse_resume("Unimportant text because AI is mocked")
    assert len(facts) == 2
    assert facts[0] == {"section": "skill", "raw_text": "Python"}
    assert facts[1] == {"section": "experience", "raw_text": "Software Engineer"}


def test_parse_resume_ai_fails_fallback(monkeypatch):
    monkeypatch.setattr(settings, "ai_api_key", "mocked-api-key")

    def failing_urlopen(*args, **kwargs):
        raise TimeoutError("LLM response timed out")

    monkeypatch.setattr("app.resume_parsing.urlopen", failing_urlopen)

    # Should fallback to deterministic parser instead of raising error
    facts = parse_resume("Skills\n• Python programming")
    assert facts == [{"section": "skill", "raw_text": "Python programming"}]
