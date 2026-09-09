import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models import SECTIONS, SourceFact

# Fixed per-section target counts a fully-populated profile is expected to reach.
SECTION_TARGETS = {"experience": 3, "project": 3, "education": 1, "skill": 5}


def compute_completeness(db: DbSession, user_id: uuid.UUID) -> tuple[dict[str, float], float]:
    """Return (per-section 0.0-1.0 scores, overall score) from existing source_facts counts."""
    counts = dict.fromkeys(SECTIONS, 0)
    rows = (
        db.query(SourceFact.section, func.count(SourceFact.id))
        .filter(SourceFact.user_id == user_id)
        .group_by(SourceFact.section)
        .all()
    )
    for section, count in rows:
        counts[section] = count

    scores = {
        section: min(counts[section] / SECTION_TARGETS[section], 1.0) for section in SECTIONS
    }
    overall = sum(scores.values()) / len(SECTIONS)
    return scores, overall
